const { spawn } = require('child_process'), fs=require('fs'), path=require('path'), os=require('os');
const CHROME=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'].find(fs.existsSync);
const PORT=9700+(process.pid%200), PROFILE=path.join(os.tmpdir(),'probe-'+Date.now().toString(36));
const root=path.resolve(__dirname,'..');
const url='file:///'+path.join(root,'index.html').split(String.fromCharCode(92)).join('/');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const ch=spawn(CHROME,['--headless=new',`--remote-debugging-port=${PORT}`,`--user-data-dir=${PROFILE}`,'--allow-file-access-from-files','about:blank'],{stdio:'ignore'});
  let t; for(let i=0;i<60&&!t;i++){await sleep(250);try{t=await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()}catch{}}
  const ws=new WebSocket(t.find(x=>x.type==='page').webSocketDebuggerUrl);
  await new Promise(r=>ws.onopen=r);
  let n=0; const p={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(p[m.id]){p[m.id](m.result||m.error); delete p[m.id]}};
  const send=(method,params={})=>new Promise(r=>{p[++n]=r; ws.send(JSON.stringify({id:n,method,params}))});
  await send('Runtime.enable'); await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:810,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url}); await sleep(2500);
  await send('Runtime.evaluate',{expression:'window.pw&&window.pw.goTo(1)'}); await sleep(1800);
  const q=(e)=>send('Runtime.evaluate',{expression:e,returnByValue:true});
  let r=await q("(()=>{const l=document.getElementById('lum');const c=getComputedStyle(l);return JSON.stringify({z:c.zIndex,op:c.opacity,pos:c.position,parent:l.parentElement.className,idx:[...l.parentElement.children].indexOf(l),stageIdx:[...l.parentElement.children].findIndex(n=>n.id==='stage')})})()");
  console.log('LUM', r.result.value);
  const shot=async(tag)=>{const s=await send('Page.captureScreenshot',{format:'png'});require('fs').writeFileSync(require('path').join(root,'_shots','probe-'+tag+'.png'),Buffer.from(s.data,'base64'));};
  r=await q("(()=>{const el=[...document.querySelectorAll('[data-layer=\"sun\"]')].find(n=>n.offsetParent!==null)||document.querySelector('[data-layer=\"sun\"]');const out=[];let e=el;while(e&&e!==document.documentElement){const c=getComputedStyle(e);out.push(e.className+' z='+c.zIndex+' tr='+(c.transform==='none'?'-':'YES')+' op='+c.opacity+' wc='+c.willChange+' vis='+c.visibility);e=e.parentElement;}return out.join(String.fromCharCode(10));})()");
  console.log('CHAIN AFTER goTo(1):'); console.log(r.result.value);
  await shot('with');
  await q("document.getElementById('lum').style.opacity=0");
  await sleep(300);
  await shot('without');
  ws.close(); ch.kill(); try{fs.rmSync(PROFILE,{recursive:true,force:true})}catch{}
  process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
