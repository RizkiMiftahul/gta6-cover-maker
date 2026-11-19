// Screenshot scenes use the same local samples and renderer as the editor.
export async function runShot(shot, query, prepare) {
  if (shot !== 'cover' && shot !== 'editor') return;
  const size=query.get('size');
  if(size){const match=/^(\d{3,4})x(\d{3,4})$/.exec(size);if(match)prepare.setSize(Number(match[1]),Number(match[2]));}
  if(shot==='cover')document.body.classList.add('shot-cover');
  prepare.setLayout(query.get('layout')||'classic');
  await prepare.loadSample(query.get('photo')||'pier',query.get('caption')||'Sunset Heist',(query.get('photos')||'').split(','));
  prepare.setGrade(query.get('grade')||'sunset');
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  window.__shotReady=true;
}
