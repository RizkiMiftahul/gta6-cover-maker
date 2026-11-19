// Editor state, file handling, interactions, and PNG export.
import { drawCover, LAYOUTS, GRADES, panelRects } from './cover.js';
import { runShot } from './shots.js';
const canvas=document.getElementById('cover'),ctx=canvas.getContext('2d');
const $=id=>document.getElementById(id);
const state={layout:'classic',grade:'sunset',panels:[],photos:[],selected:0,texture:true,title:'SUNSET HEIST',subtitle:'VICE CITY • EST. 2026',tagline:'NO RULES AFTER DARK'};
let activePhoto=null,drag=null;
const sampleNames=['boulevard','pier','neon'];

function setStatus(message){$('status').textContent=message;}
function resizePanels(){const old=state.panels;state.panels=panelRects(state.layout,1000,1000).map((_,i)=>old[i]||{photo:null,zoom:1,panX:0,panY:0,grade:''});state.selected=Math.min(state.selected,state.panels.length-1);renderPanelControls();redraw();}
function redraw(){state.title=$('titleInput').value;state.subtitle=$('subtitleInput').value;state.tagline=$('taglineInput').value;state.texture=$('texture').checked;drawCover(canvas,state);}
function renderLayoutButtons(){
  $('layouts').innerHTML='';for(const layout of LAYOUTS){const button=document.createElement('button');button.type='button';button.className='layout-button'+(layout.id===state.layout?' active':'');button.innerHTML=`<span class="mini ${layout.id}">${'<b></b>'.repeat(layout.count)}</span><span>${layout.label}</span>`;button.addEventListener('click',()=>{state.layout=layout.id;renderLayoutButtons();resizePanels();});$('layouts').append(button);}
}
function renderGradeButtons(){
  $('grades').innerHTML='';for(const grade of GRADES){const button=document.createElement('button');button.type='button';button.className='grade-button'+(grade.id===state.grade?' active':'');button.innerHTML=`<i style="background:${grade.swatch}"></i>${grade.label}`;button.addEventListener('click',()=>{state.grade=grade.id;renderGradeButtons();redraw();});$('grades').append(button);}
  $('panelGrade').innerHTML='<option value="">Use overall grade</option>'+GRADES.map(g=>`<option value="${g.id}">${g.label}</option>`).join('');
}
function renderPanelControls(){const panel=state.panels[state.selected];$('panelName').textContent=`${state.selected+1} of ${state.panels.length}`;$('zoom').value=panel?.zoom||1;$('zoomValue').value=`${(panel?.zoom||1).toFixed(1)}×`;$('panelGrade').value=panel?.grade||'';}
function renderThumbs(){
  const root=$('thumbnails');root.innerHTML='';state.photos.forEach((photo,index)=>{const button=document.createElement('button');button.className='thumb'+(activePhoto===photo?' selected':'');button.type='button';button.title=`${photo.name} — click then choose a panel`;const img=document.createElement('img');img.src=photo.src;img.alt=photo.name;const name=document.createElement('span');name.textContent=photo.name;button.append(img,name);button.addEventListener('click',()=>{activePhoto=photo;renderThumbs();assignPhoto(state.selected,photo);});root.append(button);});
}
function addImage(image,name,src){const photo={image,name,src};state.photos.push(photo);if(!activePhoto)activePhoto=photo;renderThumbs();return photo;}
function loadImage(src){return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=reject;image.src=src;});}
function assignPhoto(index,photo){const panel=state.panels[index];if(!panel)return;panel.photo=photo.image;panel.name=photo.name;panel.panX=0;panel.panY=0;redraw();setStatus(`Assigned ${photo.name} to panel ${index+1}.`);}
function pickPanel(x,y){const box=canvas.getBoundingClientRect(),px=(x-box.left)/box.width*canvas.width,py=(y-box.top)/box.height*canvas.height;return panelRects(state.layout,canvas.width,canvas.height).findIndex(r=>px>=r.x&&px<=r.x+r.w&&py>=r.y&&py<=r.y+r.h);}
function pointerDown(event){const index=pickPanel(event.clientX,event.clientY);if(index<0)return;state.selected=index;renderPanelControls();drag={x:event.clientX,y:event.clientY,panel:state.panels[index],moved:false};canvas.setPointerCapture(event.pointerId);}
function pointerMove(event){if(!drag)return;const dx=(event.clientX-drag.x)/canvas.clientWidth,dy=(event.clientY-drag.y)/canvas.clientHeight;if(Math.abs(dx)+Math.abs(dy)>.002)drag.moved=true;if(drag.moved){drag.panel.panX+=dx;drag.panel.panY+=dy;drag.x=event.clientX;drag.y=event.clientY;redraw();}}
function pointerUp(){if(!drag)return;if(!drag.moved&&activePhoto)assignPhoto(state.selected,activePhoto);drag=null;}
function exportPng(size){const [w,h]=size.split('x').map(Number),output=document.createElement('canvas');output.width=w;output.height=h;drawCover(output,state);output.toBlob(blob=>{if(!blob){setStatus('PNG export failed.');return;}const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=`vice-panels-${size}.png`;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);setStatus(`Saved vice-panels-${size}.png`);},'image/png');}
async function loadSample(name,caption){if(!sampleNames.includes(name))name='pier';const src=`./samples/${name}.jpg`;const image=await loadImage(src);let photo=state.photos.find(item=>item.name===name);if(!photo)photo=addImage(image,name,src);state.panels.forEach((panel,index)=>{if(index===0||!panel.photo)panel.photo=image;});activePhoto=photo;$('titleInput').value=caption.toUpperCase();renderThumbs();redraw();}
function setLayout(layout){if(LAYOUTS.some(item=>item.id===layout)){state.layout=layout;renderLayoutButtons();resizePanels();}}
function setGrade(grade){const aliases={vice:'sunset',sunset:'sunset',neon:'neon',noir:'noir',golden:'golden'};state.grade=aliases[grade]||'sunset';renderGradeButtons();redraw();}
function setSize(w,h){canvas.width=w;canvas.height=h;$('canvasDimensions').textContent=`${w} × ${h}`;redraw();}

renderGradeButtons();renderLayoutButtons();resizePanels();
for(const name of sampleNames){loadImage(`./samples/${name}.jpg`).then(image=>{addImage(image,name,`./samples/${name}.jpg`);if(name==='pier'){state.panels[0].photo=image;redraw();}}).catch(()=>{});}
$('photoUpload').addEventListener('change',async event=>{for(const file of event.target.files){if(!file.type.startsWith('image/'))continue;const src=URL.createObjectURL(file);try{const image=await loadImage(src);const photo=addImage(image,file.name,src);assignPhoto(state.selected,photo);}catch{URL.revokeObjectURL(src);setStatus(`Could not load ${file.name}.`);}}event.target.value='';});
$('zoom').addEventListener('input',event=>{const panel=state.panels[state.selected];if(panel){panel.zoom=Number(event.target.value);$('zoomValue').value=`${panel.zoom.toFixed(1)}×`;redraw();}});
$('panelGrade').addEventListener('change',event=>{const panel=state.panels[state.selected];if(panel){panel.grade=event.target.value;redraw();}});
['titleInput','subtitleInput','taglineInput','texture'].forEach(id=>$(id).addEventListener('input',redraw));
canvas.addEventListener('pointerdown',pointerDown);canvas.addEventListener('pointermove',pointerMove);canvas.addEventListener('pointerup',pointerUp);canvas.addEventListener('pointercancel',pointerUp);
canvas.addEventListener('dragover',event=>event.preventDefault());canvas.addEventListener('drop',async event=>{event.preventDefault();const index=pickPanel(event.clientX,event.clientY),file=event.dataTransfer.files[0];if(index<0||!file)return;state.selected=index;renderPanelControls();const src=URL.createObjectURL(file);try{const image=await loadImage(src);assignPhoto(index,addImage(image,file.name,src));}catch{setStatus('Could not load dropped image.');}});
document.querySelectorAll('[data-size]').forEach(button=>button.addEventListener('click',()=>exportPng(button.dataset.size)));
const shotQuery=new URLSearchParams(location.search);if(shotQuery.has('shot'))runShot(shotQuery.get('shot'),shotQuery,{loadSample,setLayout,setGrade,setSize});else redraw();
