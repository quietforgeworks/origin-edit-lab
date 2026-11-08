'use strict';
const $=id=>document.getElementById(id),PX=3.6,clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),round=v=>Math.round(v*1000)/1000;
const source=__LAYOUT_PROJECT__;
let state,selected=new Set(),zoom=1,drag=null,nudge=null,past=[],future=[],dirty=false,boxNodes=new Map();
const element=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
const key=`figure-layout:${source.projectId}:offline`;
function status(text,kind=''){ $('status').textContent=text;$('status').dataset.kind=kind; }
function initial(){return {panels:source.panels.map(p=>({id:p.id,bounds:{...p.initialBounds}})),refinement:{mode:source.refinement?.mode==='user-references'?'user-references':'existing-aesthetics',references:[]},note:''};}
function migrate(raw){const m=source.layoutMigration;if(!m||raw?.projectId!==source.projectId||raw.mapHash!==m.fromMapHash)return raw;const out=JSON.parse(JSON.stringify(raw)),panels=[];for(const p of out.selectedPanels||[]){const children=m.splitPanels[p.id];if(!children){panels.push(p);continue;}if(!p.bounds)throw Error('旧布局坐标缺失');children.forEach((id,i)=>panels.push({id,bounds:{x:p.bounds.x+p.bounds.w*i/children.length,y:p.bounds.y,w:p.bounds.w/children.length,h:p.bounds.h}}));}out.selectedPanels=panels;out.omittedPanelIds=(out.omittedPanelIds||[]).flatMap(id=>m.splitPanels[id]||[id]);out.mapHash=source.mapHash;return out;}
function validate(raw){raw=migrate(raw);if(raw?.schema!=='figure-layout-roundtrip/v1'||raw.projectId!==source.projectId||raw.mapHash!==source.mapHash)throw Error('这份布局不属于当前任务，原布局已保留。');if(!raw.canvas||raw.canvas.unit!==source.canvas.unit||!['width','height'].every(k=>Number.isFinite(raw.canvas[k])&&raw.canvas[k]===source.canvas[k]))throw Error('画布不匹配，原布局已保留。');const known=new Set(source.panels.map(p=>p.id)),seen=new Set(),p=raw.selectedPanels;if(!Array.isArray(p)||!Array.isArray(raw.omittedPanelIds))throw Error('布局格式无效，原布局已保留。');const panels=p.map(p=>{if(!known.has(p.id)||seen.has(p.id))throw Error('图片编号重复或不匹配，原布局已保留。');seen.add(p.id);const b=p.bounds,c=source.canvas;if(!b||!['x','y','w','h'].every(k=>Number.isFinite(b[k]))||b.x<0||b.y<0||b.w<=0||b.h<=0||b.x+b.w>c.width+.01||b.y+b.h>c.height+.01)throw Error('布局坐标无效，原布局已保留。');return {id:p.id,bounds:{x:b.x,y:b.y,w:b.w,h:b.h}};});for(const id of raw.omittedPanelIds){if(!known.has(id)||seen.has(id))throw Error('图片选择不完整，原布局已保留。');seen.add(id);}if(seen.size!==known.size)throw Error('图片选择不完整，原布局已保留。');return {panels,refinement:{mode:raw.refinement?.mode==='user-references'?'user-references':'existing-aesthetics',references:[]},note:typeof raw.note==='string'?raw.note.slice(0,2000):''};}
function output(){return {schema:'figure-layout-roundtrip/v1',projectId:source.projectId,mapHash:source.mapHash,interaction:'offline-browser-layout',canvas:{...source.canvas},selectedPanels:state.panels.map(p=>({id:p.id,bounds:{...p.bounds}})),omittedPanelIds:source.panels.filter(p=>!state.panels.some(a=>a.id===p.id)).map(p=>p.id),refinement:state.refinement,note:state.note,geometryIsApproximateIntent:true,previewStretchIsNotScientificEdit:true,semanticGuideApprovalRequired:true,userChatApprovalStillRequired:true,scientificSourceEdited:false};}
function readLocal(k){try{return JSON.parse(localStorage.getItem(k)||'null');}catch{return null;}}
function cache(){try{localStorage.setItem(key,JSON.stringify({layout:output(),updatedAt:new Date().toISOString()}));return true;}catch{return false;}}
function checkpoint(before=JSON.stringify(state)){past.push(before);if(past.length>50)past.shift();future=[];}
function changed(text){dirty=true;const saved=cache();status(text||(saved?'已在本机暂存。完成后截图发回对话；也可导出备份。':'本机暂存不可用。完成后截图发回对话；可选导出备份。'));}
function selectedPanels(){return state.panels.filter(p=>selected.has(p.id));}
function refreshSelection(){
  for(const [id,box] of boxNodes){
    box.classList.toggle('selected',selected.has(id));
    box.classList.toggle('sole-selection',selected.size===1&&selected.has(id));
    box.setAttribute('aria-pressed',String(selected.has(id)));
  }
  $('selection').textContent=selected.size?`已选 ${selected.size} 张`:'未选中图片';
}
function clearSelection(){selected.clear();refreshSelection();}
function focusCanvas(){ $('canvas').focus({preventScroll:true}); }
function finishNudge(){
  if(nudge&&JSON.stringify(state)!==nudge.before)checkpoint(nudge.before);
  nudge=null;
}
// Clamp one shared displacement, preserving every selected panel's relative position.
function translateGroup(originals,dx,dy){
  const c=source.canvas;
  const minX=Math.min(...originals.map(p=>p.bounds.x)),minY=Math.min(...originals.map(p=>p.bounds.y));
  const maxX=Math.max(...originals.map(p=>p.bounds.x+p.bounds.w)),maxY=Math.max(...originals.map(p=>p.bounds.y+p.bounds.h));
  dx=clamp(dx,-minX,c.width-maxX);dy=clamp(dy,-minY,c.height-maxY);
  for(const original of originals){
    const panel=state.panels.find(p=>p.id===original.id);
    panel.bounds.x=round(original.bounds.x+dx);panel.bounds.y=round(original.bounds.y+dy);
    position(boxNodes.get(panel.id),panel.bounds);
  }
}
function snapshotSelection(){return selectedPanels().map(p=>({id:p.id,bounds:{...p.bounds}}));}
function position(box,b){Object.assign(box.style,{left:b.x*PX+'px',top:b.y*PX+'px',width:b.w*PX+'px',height:b.h*PX+'px'});}
function render(){
  const canvas=$('canvas'),hadFocus=canvas.contains(document.activeElement);
  canvas.replaceChildren();boxNodes=new Map();
  canvas.style.width=source.canvas.width*PX+'px';canvas.style.height=source.canvas.height*PX+'px';canvas.style.transform=`scale(${zoom})`;
  $('sizer').style.width=source.canvas.width*PX*zoom+'px';$('sizer').style.height=source.canvas.height*PX*zoom+'px';
  for(const p of state.panels){
    const a=source.panels.find(a=>a.id===p.id),box=element('div','box');
    box.dataset.id=p.id;box.tabIndex=0;box.setAttribute('role','button');
    box.setAttribute('aria-label',`${p.id} ${a.name}，Shift 点击多选，方向键移动`);
    position(box,p.bounds);
    const im=element('img');im.src=a.preview;im.alt=a.name;
    box.append(im,element('span','label',p.id));
    for(const dir of ['e','s','se','nw','ne','sw']){const h=element('span','handle');h.dataset.dir=dir;box.append(h);}
    box.addEventListener('pointerdown',e=>startDrag(e,p.id,e.target.dataset.dir));
    box.addEventListener('focus',()=>{
      if(!selected.has(p.id)){finishNudge();selected=new Set([p.id]);refreshSelection();}
    });
    canvas.append(box);boxNodes.set(p.id,box);
  }
  selected=new Set([...selected].filter(id=>boxNodes.has(id)));refreshSelection();
  if(hadFocus)focusCanvas();
}
function fit(){zoom=clamp(Math.min(($('viewport').clientWidth-40)/(source.canvas.width*PX),($('viewport').clientHeight-40)/(source.canvas.height*PX)),.12,2);render();}
function startDrag(e,id,dir){
  if(e.button!==0||drag)return;
  e.preventDefault();finishNudge();
  if(e.shiftKey){
    if(selected.has(id)){selected.delete(id);refreshSelection();focusCanvas();return;}
    selected.add(id);dir=null;
  }else if(!selected.has(id))selected=new Set([id]);
  // Multi-selection moves together; resizing is intentionally a single-panel operation.
  if(selected.size>1)dir=null;
  refreshSelection();focusCanvas();
  drag={id,dir,pointerId:e.pointerId,x:e.clientX,y:e.clientY,originals:snapshotSelection(),before:JSON.stringify(state),moved:false};
  $('canvas').setPointerCapture(e.pointerId);
}
$('canvas').addEventListener('pointermove',e=>{
  if(!drag||e.pointerId!==drag.pointerId)return;
  const dx=(e.clientX-drag.x)/(zoom*PX),dy=(e.clientY-drag.y)/(zoom*PX);
  if(Math.abs(dx)+Math.abs(dy)<.25&&!drag.moved)return;
  drag.moved=true;
  if(!drag.dir){translateGroup(drag.originals,dx,dy);return;}
  const b=state.panels.find(p=>p.id===drag.id).bounds,o=drag.originals[0].bounds,c=source.canvas;
  const minW=Math.min(12,o.w),minH=Math.min(12,o.h);
  if(drag.dir.includes('e'))b.w=round(clamp(o.w+dx,minW,c.width-o.x));
  if(drag.dir.includes('s'))b.h=round(clamp(o.h+dy,minH,c.height-o.y));
  if(drag.dir.includes('w')){b.x=round(clamp(o.x+dx,0,o.x+o.w-minW));b.w=round(o.x+o.w-b.x);}
  if(drag.dir.includes('n')){b.y=round(clamp(o.y+dy,0,o.y+o.h-minH));b.h=round(o.y+o.h-b.y);}
  position(boxNodes.get(drag.id),b);
});
function finishDrag(cancel=false){
  if(!drag)return;
  const before=drag.before,pointerId=drag.pointerId;
  drag=null;
  if(cancel)state=JSON.parse(before);
  else if(JSON.stringify(state)!==before){checkpoint(before);changed();}
  if($('canvas').hasPointerCapture(pointerId))$('canvas').releasePointerCapture(pointerId);
  render();
}
$('canvas').addEventListener('pointerup',e=>{if(drag&&e.pointerId===drag.pointerId)finishDrag();});
$('canvas').addEventListener('pointercancel',e=>{if(drag&&e.pointerId===drag.pointerId)finishDrag(true);});
$('canvas').addEventListener('lostpointercapture',e=>{if(drag&&e.pointerId===drag.pointerId)finishDrag();});
$('canvas').addEventListener('pointerdown',e=>{
  if(e.target===$('canvas')&&e.button===0&&!drag){finishNudge();if(!e.shiftKey)clearSelection();focusCanvas();}
});
function undo(redo=false){
  finishNudge();finishDrag(true);
  const from=redo?future:past,to=redo?past:future;if(!from.length)return;
  to.push(JSON.stringify(state));state=JSON.parse(from.pop());selected.clear();render();
  changed(redo?'已重做，可继续调整。':'已撤销，可继续调整。');
}
function editingControl(target){
  return !!target&&(target.isContentEditable||!!target.closest?.('input, textarea, select, [contenteditable]:not([contenteditable="false"]), [role="textbox"], [role="combobox"], [role="spinbutton"]'));
}
const arrowKeys=new Set(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown']);
document.addEventListener('keydown',e=>{
  if(e.defaultPrevented||e.isComposing||editingControl(e.target)||editingControl(document.activeElement))return;
  if((e.ctrlKey||e.metaKey)&&!e.altKey&&e.key.toLowerCase()==='z'){e.preventDefault();undo(e.shiftKey);return;}
  // Layout shortcuts apply only to the canvas, not buttons or other page controls.
  if(!$('canvas').contains(e.target))return;
  if(e.key==='Escape'){e.preventDefault();finishNudge();finishDrag(true);clearSelection();return;}
  if(e.altKey||e.ctrlKey||e.metaKey||drag||!selected.size)return;
  if(['Delete','Backspace'].includes(e.key)){
    e.preventDefault();finishNudge();checkpoint();state.panels=state.panels.filter(p=>!selected.has(p.id));
    selected.clear();render();changed('已从布局移除所选图片，原始素材不变。⌘ / Ctrl Z 可撤销。');return;
  }
  if(arrowKeys.has(e.key)){
    e.preventDefault();if(!e.repeat)finishNudge();
    const before=JSON.stringify(state),step=e.shiftKey?5:1;
    translateGroup(snapshotSelection(),e.key==='ArrowLeft'?-step:e.key==='ArrowRight'?step:0,e.key==='ArrowUp'?-step:e.key==='ArrowDown'?step:0);
    if(JSON.stringify(state)===before)return;
    if(!nudge)nudge={before};
    changed();
  }
});
document.addEventListener('keyup',e=>{if(arrowKeys.has(e.key))finishNudge();});
window.addEventListener('blur',()=>{finishNudge();finishDrag();});
async function restore(file){try{if(!file||file.size>1048576)throw Error('布局文件过大，原布局已保留。');const checked=validate(JSON.parse(await file.text()));finishNudge();finishDrag(true);checkpoint();state=checked;selected.clear();render();changed('布局已恢复。⌘ / Ctrl Z 可撤销这次恢复。');}catch(e){status(e instanceof SyntaxError?'不是有效的布局文件，原布局已保留。':e.message,'error');}}
$('viewport').addEventListener('dragover',e=>{if([...e.dataTransfer.types].includes('Files')){e.preventDefault();e.dataTransfer.dropEffect='copy';$('viewport').classList.add('file-hover');}});
$('viewport').addEventListener('dragleave',e=>{if(!$('viewport').contains(e.relatedTarget))$('viewport').classList.remove('file-hover');});
$('viewport').addEventListener('drop',e=>{e.preventDefault();$('viewport').classList.remove('file-hover');if(e.dataTransfer.files.length!==1){status('请每次拖入一个布局文件。','error');return;}restore(e.dataTransfer.files[0]);});
$('restore').onclick=()=>$('importFile').click();$('importFile').onchange=e=>{const f=e.target.files[0];if(f)restore(f);e.target.value='';};
$('export').onclick=()=>{finishNudge();finishDrag();const url=URL.createObjectURL(new Blob([JSON.stringify(output(),null,2)],{type:'application/json'})),link=element('a');link.href=url;link.download=(source.title||'科研图布局').replace(/[\\/:*?"<>|]/g,'_')+'.layout.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);dirty=false;cache();status('布局备份已导出。完成后截图发回对话，也可附上此文件。');};
window.addEventListener('resize',fit);window.addEventListener('beforeunload',e=>{if(dirty){cache();e.preventDefault();e.returnValue='';}});
try{state=initial();let restored=false;for(const k of [key,`figure-layout:${source.projectId}:sync`,`figure-layout:${source.projectId}`]){const data=readLocal(k);if(!data)continue;try{state=validate(data.layout||data);restored=true;break;}catch{}}render();fit();status(restored?'已恢复此浏览器保存的布局。':'离线运行 · 完成后截图发回对话 · 原始 PPT 不会修改');}catch(e){status('加载失败：'+e.message,'error');}
