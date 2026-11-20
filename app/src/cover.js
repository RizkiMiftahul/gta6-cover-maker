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
// Cache the expensive pixel treatment; panning, zooming and exporting reuse it.
const gradeCache = new WeakMap();
const clamp = value => Math.max(0, Math.min(255, value));
function gradedPhoto(photo, grade) {
  let cached=gradeCache.get(photo);
  if(!cached){cached=new Map();gradeCache.set(photo,cached);}
  if(cached.has(grade))return cached.get(grade);
  const layer=document.createElement('canvas');
  const scale=Math.min(1,1600/Math.max(photo.naturalWidth,photo.naturalHeight));
  layer.width=Math.round(photo.naturalWidth*scale);layer.height=Math.round(photo.naturalHeight*scale);
  const context=layer.getContext('2d');context.drawImage(photo,0,0,layer.width,layer.height);
  const pixels=context.getImageData(0,0,layer.width,layer.height),data=pixels.data;
  for(let i=0;i<data.length;i+=4){
    let r=data[i],g=data[i+1],b=data[i+2];
    const l=(.2126*r+.7152*g+.0722*b)/255;
    const shadow=Math.pow(1-l,2),light=l*l;
    // Reduce chromatic pushes on warm midtones to retain plausible faces.
    const skin=r>g&&g>b&&r-b>18&&l>.18&&l<.88 ? .38 : 1;
    const x=(i/4)%layer.width,y=Math.floor(i/4/layer.width);
    if(grade==='sunset'){
      const curve=value=>255*(.5+Math.tanh((value/255-.5)*1.22)/(2*Math.tanh(.61)));
      r=curve(r);g=curve(g);b=curve(b);
      const gray=l*255;
      r=gray+(r-gray)*1.35;g=gray+(g-gray)*1.35;b=gray+(b-gray)*1.35;
      const sky=Math.pow(Math.max(0,1-y/(layer.height*.7)),1.3)*(.3+.7*l)*skin;
      r+=58*sky+28*light*skin-28*shadow+5*shadow;
      g+=-37*sky+12*light+17*shadow-5*shadow;
      b+=40*sky-28*light*skin+29*shadow+5*shadow;
      // Magenta high sky transitions into orange lower down.
      const horizon=sky*y/layer.height*2;
      r+=46*horizon;g+=25*horizon;b-=65*horizon;
      const dot=((x%7)-3)**2+((y%7)-3)**2<2 ? shadow*15 : 0;
      r-=dot;g-=dot;b-=dot;
    }else if(grade==='neon'){
      const contrast=value=>255*(.5+Math.tanh((value/255-.5)*1.65)/ (2*Math.tanh(.825)));
      r=contrast(r);g=contrast(g);b=contrast(b);
      const dark=shadow*Math.min(1,l*5); // Preserve true blacks beneath the cyan shadows.
      r+=(-32*dark+45*light)*skin;
      g+=(32*dark-28*light)*skin;
      b+=(49*dark+35*light)*skin;
    }else if(grade==='golden'){
      const curve=value=>255/(1+Math.exp(-6.2*(value/255-.5)));
      r=curve(r)+30*light+14*skin;g=curve(g)+13*light+4*skin;b=curve(b)-27*skin;
    }else if(grade==='noir'){
      const silver=clamp((l-.5)*355+128+18*light);
      r=silver;g=silver;b=silver;
    }
    data[i]=clamp(r);data[i+1]=clamp(g);data[i+2]=clamp(b);
  }
  context.putImageData(pixels,0,0);
  // Add restrained local contrast from a softly blurred luminance plate.
  const clarity=document.createElement('canvas');clarity.width=layer.width;clarity.height=layer.height;
  const cc=clarity.getContext('2d');cc.drawImage(layer,0,0);cc.filter=`blur(${Math.max(1,layer.width*.003)}px)`;cc.drawImage(layer,0,0);cc.filter='none';
  const blurred=cc.getImageData(0,0,layer.width,layer.height).data;
  const detail=context.getImageData(0,0,layer.width,layer.height),cd=detail.data;
  for(let i=0;i<cd.length;i+=4){
    const l=(.2126*cd[i]+.7152*cd[i+1]+.0722*cd[i+2])/255;
    const mid=Math.max(0,1-Math.abs(l-.5)*1.55),amount=.20*mid;
    for(let c=0;c<3;c++)cd[i+c]=clamp(cd[i+c]+(cd[i+c]-blurred[i+c])*amount);
  }
  context.putImageData(detail,0,0);
  // Coordinate-hashed grain is stable across redraws and exports.
  const grain=context.getImageData(0,0,layer.width,layer.height),gd=grain.data;
  for(let i=0;i<gd.length;i+=4){
    const x=(i/4)%layer.width,y=Math.floor(i/4/layer.width);
    const hash=Math.sin(x*127.1+y*311.7+grade.length*74.7)*43758.5453;
    const noise=((hash-Math.floor(hash))-.5)*4.2;
    gd[i]=clamp(gd[i]+noise);gd[i+1]=clamp(gd[i+1]+noise);gd[i+2]=clamp(gd[i+2]+noise);
  }
  context.putImageData(grain,0,0);
  if(grade==='neon'||grade==='sunset'||grade==='golden'){
    // Screen a softly blurred copy for luminous signs and headlights.
    context.save();context.globalCompositeOperation='screen';context.globalAlpha=grade==='neon'?.22:.14;
    context.filter=`blur(${Math.max(3,layer.width*(grade==='neon'?.007:.005))}px)`;
    context.drawImage(layer,0,0);context.restore();
  }
  cached.set(grade,layer);return layer;
}

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
    ctx.drawImage(gradedPhoto(photo,panel.grade||grade),cx-dw/2,cy-dh/2,dw,dh);
  } else drawPlaceholder(ctx,x,y,w,h);
  ctx.restore();
  // Fine printed plate edge and inward shading, clipped to this panel.
  ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();
  const edge=ctx.createLinearGradient(x,y,x+w,y+h);
  edge.addColorStop(0,'rgba(0,0,0,.24)');edge.addColorStop(.18,'rgba(0,0,0,0)');
  edge.addColorStop(.82,'rgba(0,0,0,0)');edge.addColorStop(1,'rgba(0,0,0,.28)');
  ctx.fillStyle=edge;ctx.fillRect(x,y,w,h);
  ctx.strokeStyle='rgba(255,255,255,0.14)';ctx.lineWidth=Math.max(1,Math.min(2,w/500));
  ctx.strokeRect(x+ctx.lineWidth/2,y+ctx.lineWidth/2,w-ctx.lineWidth,h-ctx.lineWidth);ctx.restore();
}
function drawPlaceholder(ctx,x,y,w,h){ctx.fillStyle='#34273a';ctx.fillRect(x,y,w,h);ctx.strokeStyle='#61516a';ctx.lineWidth=2;ctx.strokeRect(x+12,y+12,w-24,h-24);ctx.fillStyle='#9b8da2';ctx.textAlign='center';ctx.font=`700 ${Math.min(w,h)*.06}px system-ui`;ctx.fillText('DROP PHOTO',x+w/2,y+h/2);}

export function drawCover(canvas, state) {
  const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
  ctx.fillStyle='#120f16';ctx.fillRect(0,0,w,h);
  const rects=panelRects(state.layout||'classic',w,h);
  rects.forEach((r,i)=>drawPanel(ctx,r,state.panels[i],state.grade||'sunset'));
  drawWholeFinish(ctx,w,h,!!state.texture);
  drawLettering(ctx,w,h,state);
  ctx.save();ctx.strokeStyle='rgba(255,239,218,.92)';ctx.lineWidth=2;ctx.strokeRect(3,3,w-6,h-6);
  ctx.strokeStyle='rgba(24,17,27,.9)';ctx.lineWidth=1;ctx.strokeRect(7.5,7.5,w-15,h-15);ctx.restore();
  return rects;
}
function drawWholeFinish(ctx,w,h,enabled){
  const edge=ctx.createRadialGradient(w*.5,h*.44,Math.min(w,h)*.24,w*.5,h*.5,Math.max(w,h)*.72);edge.addColorStop(0,'rgba(0,0,0,0)');edge.addColorStop(1,'rgba(0,0,0,.54)');ctx.fillStyle=edge;ctx.fillRect(0,0,w,h);
  if(!enabled)return;
  ctx.save();ctx.globalAlpha=.12;const step=Math.max(7,Math.round(Math.min(w,h)/125));ctx.fillStyle='#fff';
  for(let y=0;y<h;y+=step)for(let x=0;x<w;x+=step){if(((x/step|0)+(y/step|0))%2===0){ctx.beginPath();ctx.arc(x,y,Math.max(1,step*.12),0,Math.PI*2);ctx.fill();}}
  ctx.globalAlpha=.08;for(let i=0;i<Math.min(3500,w*h/700);i++){ctx.fillStyle=i%2?'#fff':'#000';ctx.fillRect(Math.random()*w,Math.random()*h,Math.max(1,w/1300),Math.max(1,h/1300));}ctx.restore();
}
function drawLettering(ctx,w,h,state){
  const mastH=h*.048;ctx.save();ctx.fillStyle='rgba(12,9,17,.46)';ctx.fillRect(0,0,w,mastH);
  const mastSize=Math.max(9,h*.018);ctx.font=`700 ${mastSize}px system-ui,sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.letterSpacing=`${Math.max(1,h*.002)}px`;
  ctx.fillStyle='rgba(255,255,255,.85)';ctx.fillText('✦  V I C E  P A N E L S  ✦',w/2,mastH*.52);ctx.letterSpacing='0px';
  const ruleY=mastH*.52,ruleEnd=w*.36;ctx.strokeStyle='rgba(255,255,255,.55)';ctx.lineWidth=Math.max(1,h*.0012);
  ctx.beginPath();ctx.moveTo(w*.08,ruleY);ctx.lineTo(w*.34,ruleY);ctx.moveTo(w*.66,ruleY);ctx.lineTo(w*.92,ruleY);ctx.stroke();ctx.restore();
  const title=(state.title||'').trim().toUpperCase();
  if(title){let size=h*.125;ctx.textAlign='center';ctx.textBaseline='middle';ctx.font=`1000 ${size}px Impact, "Arial Narrow", system-ui, sans-serif`;while(ctx.measureText(title).width>w*.91&&size>10){size*=.94;ctx.font=`1000 ${size}px Impact, "Arial Narrow", system-ui, sans-serif`;}
    const y=h*.805;ctx.save();ctx.lineJoin='round';ctx.shadowColor='rgba(0,0,0,.8)';ctx.shadowBlur=size*.23;ctx.shadowOffsetY=size*.08;
    ctx.strokeStyle='#e65c91';ctx.lineWidth=size*.205;ctx.strokeText(title,w/2+1,y+1,w*.93);
    ctx.strokeStyle='#120f15';ctx.lineWidth=size*.17;ctx.strokeText(title,w/2,y,w*.93);ctx.shadowColor='transparent';
    const titleFill=ctx.createLinearGradient(0,y-size*.55,0,y+size*.55);titleFill.addColorStop(0,'#ffffff');titleFill.addColorStop(.48,'#ffe3f1');titleFill.addColorStop(1,'#b8adb0');ctx.fillStyle=titleFill;ctx.fillText(title,w/2,y,w*.93);ctx.restore();}
  const subtitle=(state.subtitle||'').trim();if(subtitle){const bandH=h*.055, y=h*.88;const band=ctx.createLinearGradient(w*.06,y,w*.94,y);band.addColorStop(0,'#d92d92');band.addColorStop(1,'#f58a42');ctx.fillStyle=band;ctx.fillRect(w*.06,y,w*.88,bandH);ctx.fillStyle='#fff';ctx.font=`900 ${bandH*.48}px system-ui, sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(subtitle.toUpperCase(),w/2,y+bandH/2,w*.82);}
  const tag=(state.tagline||'').trim();if(tag){ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='rgba(255,255,255,.9)';ctx.font=`800 ${h*.021}px system-ui,sans-serif`;ctx.fillText(tag.toUpperCase(),w/2,h*.963,w*.9);}
}
