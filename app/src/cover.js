// Canvas-only poster renderer. Panel rectangles are derived from the destination canvas dimensions.
export const LAYOUTS = [
  { id: 'classic', label: 'Classic', count: 5 },
  { id: 'hero', label: 'Hero Strip', count: 4 },
  { id: 'duo', label: 'Duo', count: 2 },
  { id: 'quad', label: 'Quad', count: 4 },
];
export const GRADES = [
  { id: 'sunset', label: 'Vice Sunset', swatch: '#f37d78' },
  { id: 'neon', label: 'Neon Night', swatch: '#47cad9' },
  { id: 'noir', label: 'Palm Noir', swatch: '#d1d0d2' },
  { id: 'golden', label: 'Golden Hour', swatch: '#efbd62' },
];
export const GRADE_FILTERS = {
  sunset: 'saturate(1.18) contrast(1.05)', neon: 'saturate(1.55) contrast(1.25) hue-rotate(12deg)',
  noir: 'grayscale(1) contrast(1.5)', golden: 'sepia(.32) saturate(1.18) brightness(1.08)',
};

export function panelRects(layout, w, h) {
  const gap = Math.round(Math.min(w, h) * 0.012);
  const m = Math.round(Math.min(w, h) * 0.025);
  const iw = w - 2 * m, ih = h - 2 * m;
  if (layout === 'classic') {
    const left = iw * .59;
    return [{x:m,y:m,w:left-gap/2,h:ih}, ...Array.from({length:4},(_,i)=>({x:m+left+gap/2,y:m+i*(ih+gap)/4,w:iw-left-gap/2,h:(ih-3*gap)/4}))];
  }
  if (layout === 'hero') {
    const upper = ih * .69;
    return [{x:m,y:m,w:iw,h:upper-gap/2}, ...Array.from({length:3},(_,i)=>({x:m+i*(iw+gap)/3,y:m+upper+gap/2,w:(iw-2*gap)/3,h:ih-upper-gap/2}))];
  }
  if (layout === 'duo') return [0,1].map(i=>({x:m+i*(iw+gap)/2,y:m,w:(iw-gap)/2,h:ih}));
  return [0,1,2,3].map(i=>({x:m+(i%2)*(iw+gap)/2,y:m+Math.floor(i/2)*(ih+gap)/2,w:(iw-gap)/2,h:(ih-gap)/2}));
}

function drawPanel(ctx, rect, panel, grade) {
  const {x,y,w,h}=rect, photo=panel?.photo;
  ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();
  ctx.fillStyle='#251927';ctx.fillRect(x,y,w,h);
  if(photo){
    const scale=Math.max(w/photo.naturalWidth,h/photo.naturalHeight)*(panel.zoom||1);
    const dw=photo.naturalWidth*scale,dh=photo.naturalHeight*scale;
    const cx=x+w/2+(panel.panX||0)*w,cy=y+h/2+(panel.panY||0)*h;
    ctx.filter=GRADE_FILTERS[panel.grade||grade]||'none';
    ctx.drawImage(photo,cx-dw/2,cy-dh/2,dw,dh);ctx.filter='none';
    tintPanel(ctx,x,y,w,h,panel.grade||grade);
  } else drawPlaceholder(ctx,x,y,w,h);
  ctx.restore();
}
function tintPanel(ctx,x,y,w,h,grade){
  const color={sunset:'rgba(244,101,119,.19)',neon:'rgba(44,196,219,.13)',noir:'rgba(0,0,0,.12)',golden:'rgba(255,184,76,.16)'}[grade];
  ctx.fillStyle=color||'transparent';ctx.fillRect(x,y,w,h);
  if(grade==='sunset'){const g=ctx.createLinearGradient(x,y+h*.4,x+w,y+h);g.addColorStop(0,'rgba(255,75,124,0)');g.addColorStop(1,'rgba(247,126,52,.37)');ctx.fillStyle=g;ctx.fillRect(x,y,w,h);}
  if(grade==='golden'){const g=ctx.createRadialGradient(x+w*.7,y+h*.12,0,x+w*.7,y+h*.12,w*.9);g.addColorStop(0,'rgba(255,230,155,.3)');g.addColorStop(1,'rgba(255,203,92,0)');ctx.fillStyle=g;ctx.fillRect(x,y,w,h);}
}
function drawPlaceholder(ctx,x,y,w,h){ctx.fillStyle='#34273a';ctx.fillRect(x,y,w,h);ctx.strokeStyle='#61516a';ctx.lineWidth=2;ctx.strokeRect(x+12,y+12,w-24,h-24);ctx.fillStyle='#9b8da2';ctx.textAlign='center';ctx.font=`700 ${Math.min(w,h)*.06}px system-ui`;ctx.fillText('DROP PHOTO',x+w/2,y+h/2);}

export function drawCover(canvas, state) {
  const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
  ctx.fillStyle='#120f16';ctx.fillRect(0,0,w,h);
  const rects=panelRects(state.layout||'classic',w,h);
  rects.forEach((r,i)=>drawPanel(ctx,r,state.panels[i],state.grade||'sunset'));
  drawWholeFinish(ctx,w,h,!!state.texture);
  drawLettering(ctx,w,h,state);
  return rects;
}
function drawWholeFinish(ctx,w,h,enabled){
  const edge=ctx.createRadialGradient(w*.5,h*.44,Math.min(w,h)*.24,w*.5,h*.5,Math.max(w,h)*.72);edge.addColorStop(0,'rgba(0,0,0,0)');edge.addColorStop(1,'rgba(0,0,0,.57)');ctx.fillStyle=edge;ctx.fillRect(0,0,w,h);
  if(!enabled)return;
  ctx.save();ctx.globalAlpha=.12;const step=Math.max(7,Math.round(Math.min(w,h)/125));ctx.fillStyle='#fff';
  for(let y=0;y<h;y+=step)for(let x=0;x<w;x+=step){if(((x/step|0)+(y/step|0))%2===0){ctx.beginPath();ctx.arc(x,y,Math.max(1,step*.12),0,Math.PI*2);ctx.fill();}}
  ctx.globalAlpha=.08;for(let i=0;i<Math.min(3500,w*h/700);i++){ctx.fillStyle=i%2?'#fff':'#000';ctx.fillRect(Math.random()*w,Math.random()*h,Math.max(1,w/1300),Math.max(1,h/1300));}ctx.restore();
}
function drawLettering(ctx,w,h,state){
  const title=(state.title||'').trim().toUpperCase();
  if(title){let size=h*.125;ctx.textAlign='center';ctx.textBaseline='middle';ctx.font=`1000 ${size}px Impact, "Arial Narrow", system-ui, sans-serif`;while(ctx.measureText(title).width>w*.91&&size>10){size*=.94;ctx.font=`1000 ${size}px Impact, "Arial Narrow", system-ui, sans-serif`;}
    const y=h*.805;ctx.save();ctx.lineJoin='round';ctx.shadowColor='rgba(0,0,0,.8)';ctx.shadowBlur=size*.23;ctx.shadowOffsetY=size*.08;ctx.strokeStyle='#120f15';ctx.lineWidth=size*.17;ctx.strokeText(title,w/2,y,w*.93);ctx.shadowColor='transparent';ctx.fillStyle='#fff';ctx.fillText(title,w/2,y,w*.93);ctx.restore();}
  const subtitle=(state.subtitle||'').trim();if(subtitle){const bandH=h*.055, y=h*.88;ctx.fillStyle='#e64f8d';ctx.fillRect(w*.06,y,w*.88,bandH);ctx.fillStyle='#fff';ctx.font=`900 ${bandH*.48}px system-ui, sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(subtitle.toUpperCase(),w/2,y+bandH/2,w*.82);}
  const tag=(state.tagline||'').trim();if(tag){ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='rgba(255,255,255,.9)';ctx.font=`800 ${h*.021}px system-ui,sans-serif`;ctx.fillText(tag.toUpperCase(),w/2,h*.963,w*.9);}
}
