'use strict';
// Behavioral tests of the real offline app in a small DOM/event harness.
// This is not a browser-rendering or pointer-capture integration test.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const app=fs.readFileSync(path.join(__dirname,'../assets/web-layout/app.js'),'utf8');
class Node {
  constructor(tag='div',doc){this.tagName=tag.toUpperCase();this.doc=doc;this.children=[];this.parentElement=null;this.attributes={};this.style={};this.dataset={};this.listeners=new Map();this.className='';this.textContent='';this.capture=new Set();this.clientWidth=800;this.clientHeight=600;}
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
  fire(type,data={}){const event={target:this,button:0,pointerId:1,clientX:0,clientY:0,shiftKey:false,ctrlKey:false,metaKey:false,altKey:false,repeat:false,defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},...data};let n=this;do{for(const listener of n.listeners.get(type)||[])listener(event);n=event.bubbles===false?null:n.parentElement;}while(n);return event;}
}
function harness(extra={}){
  const document=new Node('document');document.doc=document;document.body=new Node('body',document);document.append(document.body);document.activeElement=document.body;
  const ids=new Map();
  for(const id of ['status','selection','canvas','sizer','viewport','restore','export','importFile']){const node=new Node(id==='importFile'?'input':id==='restore'||id==='export'?'button':'div',document);node.id=id;ids.set(id,node);document.body.append(node);}
  document.getElementById=id=>ids.get(id);document.createElement=tag=>new Node(tag,document);
  const window=new Node('window',document),storage=new Map();
  const source={schema:'figure-layout-roundtrip/v1',projectId:'synthetic-controls',mapHash:'a'.repeat(64),title:'Synthetic controls',canvas:{width:100,height:80,unit:'mm'},panels:[
    {id:'p1',name:'Left',parentPanelId:'pair',initialBounds:{x:10,y:10,w:20,h:15},preview:'data:image/png;base64,'},
    {id:'p2',name:'Right',parentPanelId:'pair',initialBounds:{x:45,y:20,w:20,h:15},preview:'data:image/png;base64,'},
    {id:'p3',name:'Other',initialBounds:{x:70,y:50,w:15,h:15},preview:'data:image/png;base64,'}
  ],...extra};
  const context=vm.createContext({document,window,console,Blob,setTimeout(){},URL,localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)}});
  vm.runInContext(app.replace('__LAYOUT_PROJECT__',JSON.stringify(source)),context);
  const run=code=>vm.runInContext(code,context),plain=code=>JSON.parse(JSON.stringify(run(code)));
  const box=id=>ids.get('canvas').children.find(node=>node.dataset.id===id);
  const click=(id,shiftKey=false)=>{box(id).fire('pointerdown',{shiftKey});ids.get('canvas').fire('pointerup');};
  const key=(key,options={})=>document.fire('keydown',{target:document.activeElement,key,...options});
  const keyup=key=>document.fire('keyup',{target:document.activeElement,key});
  return {document,window,ids,storage,source,run,plain,box,click,key,keyup,bounds:id=>plain(`state.panels.find(p=>p.id===${JSON.stringify(id)}).bounds`)};
}
test('Shift-click toggles independent selections and keeps parent/source identities unchanged',()=>{
  const h=harness();h.click('p1');h.click('p2',true);
  assert.deepEqual(h.plain('[...selected]'),['p1','p2']);assert.equal(h.ids.get('selection').textContent,'已选 2 张');
  assert.equal(h.box('p1').attributes['aria-pressed'],'true');assert.equal(h.box('p1').classList.contains('sole-selection'),false);
  h.click('p1',true);assert.deepEqual(h.plain('[...selected]'),['p2']);assert.equal(h.box('p2').classList.contains('sole-selection'),true);
  h.click('p3');assert.deepEqual(h.plain('[...selected]'),['p3']);h.click('p3',true);assert.equal(h.run('selected.size'),0);
  assert.equal(h.run('source.panels[0].parentPanelId'),'pair');assert.equal(h.run('past.length'),0);
  const out=h.plain('output()');assert.equal(out.schema,'figure-layout-roundtrip/v1');assert.equal(out.mapHash,h.source.mapHash);assert.equal(out.scientificSourceEdited,false);
  assert.deepEqual(out.selectedPanels.map(p=>p.id),['p1','p2','p3']);assert.deepEqual(out.omittedPanelIds,[]);
});
test('arrows move the selected group by 1 mm; Shift moves by 5 mm; one undo covers a held key',()=>{
  const h=harness();h.click('p1');h.click('p2',true);const before=h.plain('state');
  assert.equal(h.key('ArrowRight').defaultPrevented,true);h.key('ArrowRight',{repeat:true});h.key('ArrowRight',{repeat:true});h.keyup('ArrowRight');
  assert.equal(h.bounds('p1').x,13);assert.equal(h.bounds('p2').x,48);assert.equal(h.bounds('p3').x,70);assert.equal(h.run('past.length'),1);
  h.key('z',{ctrlKey:true});assert.deepEqual(h.plain('state'),before);assert.equal(h.run('future.length'),1);
  h.key('z',{ctrlKey:true,shiftKey:true});assert.equal(h.bounds('p1').x,13);
  h.click('p1');h.click('p2',true);h.key('ArrowDown',{shiftKey:true});h.keyup('ArrowDown');assert.equal(h.bounds('p1').y,15);assert.equal(h.bounds('p2').y,25);assert.equal(h.run('past.length'),2);
});
test('group movement is clamped as one displacement and boundary no-ops create no undo entry',()=>{
  const h=harness();h.click('p1');h.click('p2',true);
  for(let i=0;i<20;i++)h.key('ArrowLeft',{shiftKey:true,repeat:i>0});h.keyup('ArrowLeft');
  assert.equal(h.bounds('p1').x,0);assert.equal(h.bounds('p2').x,35);assert.equal(h.run('past.length'),1);
  h.key('ArrowLeft');h.keyup('ArrowLeft');assert.equal(h.run('past.length'),1);
  for(let i=0;i<30;i++)h.key('ArrowRight',{shiftKey:true,repeat:i>0});h.keyup('ArrowRight');
  assert.equal(h.bounds('p1').x,45);assert.equal(h.bounds('p2').x,80);assert.equal(h.bounds('p2').x+h.bounds('p2').w,100);
  assert.equal(h.bounds('p2').x-h.bounds('p1').x,35);assert.equal(h.run('past.length'),2);
});
test('selected group drags together and can be undone as one transaction',()=>{
  const h=harness();h.click('p1');h.click('p2',true);const before=h.plain('state');
  h.box('p2').fire('pointerdown',{clientX:100,clientY:100});
  h.ids.get('canvas').fire('pointermove',{clientX:10000,clientY:10000});
  h.ids.get('canvas').fire('pointermove',{clientX:20000,clientY:20000});
  h.ids.get('canvas').fire('pointerup');
  assert.equal(h.bounds('p2').x,80);assert.equal(h.bounds('p2').y,65);assert.equal(h.bounds('p1').x,45);assert.equal(h.bounds('p1').y,55);
  assert.equal(h.run('past.length'),1);h.key('z',{metaKey:true});assert.deepEqual(h.plain('state'),before);
});
test('cancelled drags roll back; empty clicks and Escape clear selection without geometry edits',()=>{
  const h=harness();h.click('p1');h.click('p2',true);const before=h.plain('state');
  h.box('p1').fire('pointerdown');h.ids.get('canvas').fire('pointermove',{clientX:100});h.ids.get('canvas').fire('pointercancel');
  assert.deepEqual(h.plain('state'),before);assert.equal(h.run('past.length'),0);
  h.box('p1').fire('pointerdown');h.ids.get('canvas').fire('pointermove',{clientY:100});h.key('Escape');
  assert.deepEqual(h.plain('state'),before);assert.equal(h.run('selected.size'),0);assert.equal(h.run('past.length'),0);
  h.click('p1');h.ids.get('canvas').fire('pointerdown',{shiftKey:true});assert.equal(h.run('selected.size'),1);
  h.ids.get('canvas').fire('pointerdown');assert.equal(h.run('selected.size'),0);
});
test('form controls, editable descendants, composition and modified arrows retain native key behavior',()=>{
  const h=harness();h.click('p1');const before=h.plain('state');
  for(const tag of ['input','textarea','select']){
    const input=h.document.createElement(tag);h.document.body.append(input);input.focus();
    for(const key of ['ArrowRight','Delete','Backspace','z'])assert.equal(h.key(key,{ctrlKey:key==='z'}).defaultPrevented,false);
  }
  const editable=h.document.createElement('div'),child=h.document.createElement('span');editable.setAttribute('contenteditable','true');editable.append(child);h.document.body.append(editable);child.focus();assert.equal(h.key('ArrowDown').defaultPrevented,false);
  h.ids.get('restore').focus();assert.equal(h.key('ArrowRight').defaultPrevented,false);assert.equal(h.key('Delete').defaultPrevented,false);
  h.ids.get('canvas').focus();for(const modifier of ['altKey','ctrlKey','metaKey','isComposing','defaultPrevented'])assert.equal(h.key('ArrowRight',{[modifier]:true}).defaultPrevented,modifier==='defaultPrevented');
  assert.deepEqual(h.plain('state'),before);assert.equal(h.run('past.length'),0);
});
test('Delete removes only selected panels from the layout, with a single undo',()=>{
  const h=harness();h.click('p1');h.click('p2',true);h.key('Delete');
  assert.deepEqual(h.plain('output().omittedPanelIds'),['p1','p2']);assert.deepEqual(h.plain('state.panels.map(p=>p.id)'),['p3']);assert.equal(h.run('source.panels.length'),3);
  assert.equal(h.run('past.length'),1);h.key('z',{ctrlKey:true});assert.deepEqual(h.plain('output().omittedPanelIds'),[]);
});
test('single-panel resize stays within the canvas; multi-selection does not stretch panels',()=>{
  const h=harness();h.click('p1');let handle=h.box('p1').children.find(n=>n.dataset.dir==='se');handle.fire('pointerdown');
  h.ids.get('canvas').fire('pointermove',{clientX:10000,clientY:10000});h.ids.get('canvas').fire('pointerup');
  assert.deepEqual(h.bounds('p1'),{x:10,y:10,w:90,h:70});h.key('z',{ctrlKey:true});
  h.click('p1');h.click('p2',true);handle=h.box('p1').children.find(n=>n.dataset.dir==='se');handle.fire('pointerdown');
  h.ids.get('canvas').fire('pointermove',{clientX:100,clientY:100});h.ids.get('canvas').fire('pointerup');
  assert.equal(h.bounds('p1').w,20);assert.equal(h.bounds('p1').h,15);assert.equal(h.bounds('p2').w,20);assert.equal(h.bounds('p2').h,15);
});
test('separate arrow presses make separate undo steps and blur finalizes a held key',()=>{
  const h=harness();h.click('p1');h.key('ArrowRight');h.keyup('ArrowRight');h.key('ArrowDown');h.keyup('ArrowDown');assert.equal(h.run('past.length'),2);
  h.key('ArrowRight');h.key('ArrowRight',{repeat:true});h.window.fire('blur');assert.equal(h.run('past.length'),3);
  h.key('z',{ctrlKey:true});assert.deepEqual(h.bounds('p1'),{x:11,y:11,w:20,h:15});
});
