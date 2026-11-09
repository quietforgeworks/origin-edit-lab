'use strict';
// Behavioral tests of the real offline app in a small DOM/event harness.
// This is not a browser-rendering or pointer-capture integration test.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../assets/local-handoff/workbench.template.html'),'utf8');
const app=html.match(/<script>([\s\S]*?)<\/script>/)[1];
class Node {
  constructor(tag='div',doc){this.tagName=tag.toUpperCase();this.doc=doc;this.children=[];this.parentElement=null;this.attributes={};this.style={setProperty(k,v){this[k]=v}};this.dataset={};this.listeners=new Map();this.className='';this.textContent='';this.capture=new Set();this.clientWidth=800;this.clientHeight=600;}
  querySelectorAll(selector){return this.children.filter(c=>c.className.split(' ').includes(selector.slice(1)));}
  remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(c=>c!==this);}
  showModal(){this.open=true;}
  close(){this.open=false;}
  get classList(){return {toggle:(name,on)=>{const classes=new Set(this.className.split(' ').filter(Boolean));if(on===undefined)on=!classes.has(name);if(on)classes.add(name);else classes.delete(name);this.className=[...classes].join(' ');},add:name=>this.classList.toggle(name,true),remove:name=>this.classList.toggle(name,false),contains:name=>this.className.split(' ').includes(name)};}
  append(...nodes){for(const node of nodes){node.parentElement=this;this.children.push(node);}}
  replaceChildren(...nodes){for(const child of this.children)child.parentElement=null;this.children=[];this.append(...nodes);}
  setAttribute(key,value){this.attributes[key]=String(value);}
  addEventListener(type,listener){if(!this.listeners.has(type))this.listeners.set(type,[]);this.listeners.get(type).push(listener);}
  contains(node){return node===this||this.children.some(child=>child.contains(node));}
  closest(){let n=this;while(n){if(['INPUT','TEXTAREA','SELECT'].includes(n.tagName)||['textbox','combobox','spinbutton'].includes(n.attributes.role)||(n.attributes.contenteditable!==undefined&&n.attributes.contenteditable!=='false'))return n;n=n.parentElement;}return null;}
  focus(){this.doc.activeElement=this;this.fire('focus',{bubbles:false});}
  setPointerCapture(id){this.capture.add(id);}
  hasPointerCapture(id){return this.capture.has(id);}
  releasePointerCapture(id){this.capture.delete(id);this.fire('lostpointercapture',{pointerId:id});}
  fire(type,data={}){const event={target:this,button:0,pointerId:1,clientX:0,clientY:0,shiftKey:false,ctrlKey:false,metaKey:false,altKey:false,repeat:false,defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},stopPropagation(){this.propagationStopped=true;},...data};let n=this;do{for(const listener of n.listeners.get(type)||[])listener(event);n=event.bubbles===false?null:n.parentElement;}while(n&&!event.propagationStopped);return event;}
}
function harness(extra={}){
  const document=new Node('document');document.doc=document;document.body=new Node('body',document);document.append(document.body);document.activeElement=document.body;
  const ids=new Map();
  for(const id of [...html.matchAll(/id="([^"]+)"/g)].map(m=>m[1])){const node=new Node(id==='importFile'?'input':id==='restore'||id==='export'?'button':'div',document);node.id=id;ids.set(id,node);document.body.append(node);}
  document.getElementById=id=>ids.get(id);document.createElement=tag=>new Node(tag,document);
  const window=new Node('window',document),storage=new Map();
  const source={schema:'figure-layout-roundtrip/v1',projectId:'synthetic-controls',mapHash:'a'.repeat(64),title:'Synthetic controls',canvas:{width:100,height:80,unit:'mm'},panels:[
    {id:'p1',name:'Left',parentPanelId:'pair',initialBounds:{x:10,y:10,w:20,h:15},preview:'data:image/png;base64,'},
    {id:'p2',name:'Right',parentPanelId:'pair',initialBounds:{x:45,y:20,w:20,h:15},preview:'data:image/png;base64,'},
    {id:'p3',name:'Other',initialBounds:{x:70,y:50,w:15,h:15},preview:'data:image/png;base64,'}
  ],...extra};
  const responses=[];const context=vm.createContext({document,window,console,Blob,setTimeout(){},setInterval(){},clearTimeout(){},confirm(){return true},fetch:async()=>({ok:true,status:200,json:async()=>responses.shift()||{lock:null}}),URL,localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)}});
  vm.runInContext(app.replace('__SOURCE_JSON__',JSON.stringify(source)).replace('poll();\n','\n').replace('setInterval(checkWorkLock,800);checkWorkLock();',''),context);
  const run=code=>vm.runInContext(code,context),plain=code=>JSON.parse(JSON.stringify(run(code)));
  const box=id=>ids.get('canvas').children.find(node=>node.dataset.id===id);
  const click=(id,shiftKey=false)=>{box(id).fire('pointerdown',{shiftKey});ids.get('canvas').fire('pointerup');};
  const key=(key,options={})=>document.fire('keydown',{target:document.activeElement,key,...options});
  const keyup=key=>document.fire('keyup',{target:document.activeElement,key});
  return {responses,document,window,ids,storage,source,run,plain,box,click,key,keyup,bounds:id=>plain(`state.panels.find(p=>p.id===${JSON.stringify(id)}).bounds`)};
}

test('local page loads source state; manual refresh adopts preview, not source geometry',()=>{
 const h=harness();h.run(`adopt({revision:0,author:'initial',layout:output(),confirmation:null})`);
 assert.equal(h.run('loaded'),true);const before=h.plain('output().selectedPanels');
 h.run(`adopt({revision:1,author:'assistant',layout:output(),displayPreviews:{p1:{dataUrl:'data:image/png;base64,test'}},confirmation:null})`);
 assert.equal(h.run('source.panels[0].preview'),'data:image/png;base64,test');assert.deepEqual(h.plain('output().selectedPanels'),before);
});
test('lock opens modal and disables editing; cancellation restores controls',()=>{
 const h=harness();h.run(`adopt({revision:0,layout:output()});toggleWorkLock({label:'Adding guides',expiresAt:Date.now()/1000+180})`);
 assert.equal(h.ids.get('working').open,true);assert.equal(h.ids.get('viewport').inert,true);
 const before=h.plain('output()');h.click('p1');h.key('ArrowRight');assert.deepEqual(h.plain('output()'),before);
 h.run('toggleWorkLock(null)');assert.equal(h.ids.get('working').open,false);assert.equal(h.ids.get('viewport').inert,false);
});
test('user can select multiple panels and stage outside white canvas without source edits',()=>{
 const h=harness();h.run(`adopt({revision:0,layout:output()})`);h.click('p1');h.click('p2',true);h.key('ArrowLeft',{shiftKey:true});h.keyup('ArrowLeft');
 assert.equal(h.bounds('p1').x,5);assert.equal(h.bounds('p2').x,40);
 h.run(`state.panels[0].bounds.x=-30`);assert.equal(h.run("boundaryState(state.panels[0])"),'outside');assert.equal(h.run('output().scientificSourceEdited'),false);
});
test('save conflict preserves local geometry; does not silently overwrite shared state',async()=>{
 const h=harness();h.run(`adopt({revision:0,layout:output()});state.panels[0].bounds.x=12;queueSave()`);
 h.run(`fetch=async()=>({ok:false,status:409,json:async()=>({error:'version conflict'})})`);await h.run('flush()');
 assert.equal(h.run('conflicted'),true);assert.equal(h.bounds('p1').x,12);assert.equal(h.run('pending'),true);assert.equal(h.ids.get('conflict').hidden,false);
});
test('server canonical proposal status returns to page after save',async()=>{
 const h=harness();h.run(`adopt({revision:0,layout:output()});state.guideWorkflow={mode:'auto',proposalReady:true};queueSave()`);
 const doc={revision:1,layout:h.plain('output()')};doc.layout.guideWorkflow.proposalReady=false;h.responses.push(doc);await h.run('flush()');
 assert.equal(h.run('state.guideWorkflow.proposalReady'),false);
});
test('imported guides reject mismatched semantic color or unknown target before save',()=>{
 const h=harness();assert.throws(()=>h.run(`validateGuides([{id:'g',axis:'x',pos:10,color:'#ffffff',kind:'frame',owner:'user',label:'',targets:[]}])`));
 assert.throws(()=>h.run(`validateGuides([{id:'g',axis:'x',pos:10,color:'#189db7',kind:'frame',owner:'user',label:'',targets:['missing']}])`));
});

test('guide export carries relation policy and import cannot pin absolute positions',()=>{
 const h=harness();h.run(`adopt({revision:0,layout:output()})`);
 assert.equal(h.run('output().guideSemantics'),'alignment-relations/v1');
 const original=h.plain('output()');
 assert.throws(()=>h.run(`validate({...output(),guideSemantics:'absolute-coordinates'})`));
 assert.deepEqual(h.plain('output()'),original);
});
test('moving a relation hint does not move panels or alter their source geometry',()=>{
 const h=harness();h.run(`adopt({revision:0,layout:output()})`);const panels=h.plain('output().selectedPanels');
 h.run(`state.guides=[{id:'hint',axis:'x',pos:10,color:'#189db7',kind:'frame',owner:'user',label:'left frames',targets:['p1','p2']}];renderGuides();`);
 const line=h.ids.get('canvas').children.find(n=>n.dataset.guide==='hint');line.fire('pointerdown');h.ids.get('canvas').fire('pointerup');
 h.key('ArrowRight');h.keyup('ArrowRight');assert.equal(h.run('state.guides[0].pos'),11);
 assert.deepEqual(h.plain('output().selectedPanels'),panels);
});
