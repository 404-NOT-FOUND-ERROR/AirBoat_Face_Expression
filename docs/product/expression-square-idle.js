"use strict";
(() => {
  const $=id=>document.getElementById(id),data=window.AIRBOAT_EXPRESSIONS;
  const accepted=data.contour.idle,decoder=new AirboatEaf(data.assets[accepted.file]);
  const fps=25,frameCount=160,duration=6400,cache=new Map(),scale=3;
  const ease=x=>(x=Math.max(0,Math.min(1,x)),x*x*(3-2*x));
  function track(t,keys){
    if(t<=keys[0][0])return keys[0][1];
    for(let i=1;i<keys.length;i++)if(t<=keys[i][0]){
      const [a,x]=keys[i-1],[b,y]=keys[i];return x+(y-x)*ease((t-a)/(b-a));
    }
    return keys.at(-1)[1];
  }
  function shape(ctx,cx,cy,rx,ry){
    // Superellipse n=2.65: flatter sides than an ellipse, large rounded corners.
    ctx.beginPath();
    for(let i=0;i<=240;i++){
      const a=Math.PI*2*i/240,c=Math.cos(a),s=Math.sin(a);
      const x=cx+rx*Math.sign(c)*Math.abs(c)**(2/2.65);
      const y=cy+ry*Math.sign(s)*Math.abs(s)**(2/2.65);
      if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.closePath();
  }
  function renderCandidate(frame,maskLayer=null){
    frame=Math.max(0,Math.min(frameCount-1,Math.round(frame)));
    if(!maskLayer&&cache.has(frame))return cache.get(frame);
    const t=frame===frameCount-1?0:frame/fps;
    const opening=track(t,[[1.44,1],[1.56,0],[1.60,0],[1.80,1],[1.88,1.045],[2,.985],[2.12,1],
      [3.96,1],[4.08,0],[4.12,0],[4.28,1],[4.48,1],[4.56,.06],[4.72,1],[4.80,1.025],[4.96,1]]);
    const breath=track(t,[[0,0],[.68,0],[1.12,1.8],[1.40,.8],[1.76,.8],[2.20,0],
      [2.76,0],[3.24,1.5],[3.72,0],[4.96,0],[5.36,2.2],[6.12,0]]);
    const gazeX=track(t,[[.40,0],[.56,3],[.68,2],[1.20,2],[1.44,0],[2.48,0],[2.64,-3],
      [2.76,-2],[3.40,-2],[3.72,0]]);
    const gazeY=track(t,[[.40,0],[.56,-5],[1.20,-4],[1.44,0],[2.48,0],[2.64,-3],[3.40,-3],[3.72,0]]);
    const canvas=document.createElement("canvas");canvas.width=canvas.height=480;
    const ctx=canvas.getContext("2d");
    if(!maskLayer){ctx.fillStyle="#28cf60";ctx.fillRect(0,0,480,480);}
    const half=document.createElement("canvas");half.width=240*scale;half.height=480*scale;
    const high=half.getContext("2d");high.scale(scale,scale);
    const y=234-breath,h=3+(81+breath)*opening,lidY=y+16*(1-opening);
    shape(high,150,lidY,82,h);high.fillStyle="#fff";high.fill();
    if(maskLayer==="pupil")high.clearRect(0,0,240,480);
    if(maskLayer!=="white"){
      high.save();shape(high,150,lidY,82,h);high.clip();
      high.beginPath();high.ellipse(150+gazeX,y+25+gazeY+37*Math.max(0,1-opening)**2,38,38,0,0,Math.PI*2);
      high.fillStyle=maskLayer?"#fff":"#000";high.fill();high.restore();
    }
    const left=document.createElement("canvas");left.width=240;left.height=480;
    const lc=left.getContext("2d");lc.imageSmoothingEnabled=true;lc.imageSmoothingQuality="high";lc.drawImage(half,0,0,240,480);
    ctx.drawImage(left,0,0);ctx.save();ctx.translate(480,0);ctx.scale(-1,1);ctx.drawImage(left,0,0);ctx.restore();
    if(!maskLayer){cache.set(frame,canvas);if(cache.size>6)cache.delete(cache.keys().next().value);}
    return canvas;
  }
  let elapsed=0,last=null,running=!matchMedia("(prefers-reduced-motion: reduce)").matches,lastFrame=-1;
  function paint(){
    const frame=Math.min(frameCount-1,Math.floor(elapsed*fps/1000));
    if(frame!==lastFrame){
      $("accepted").getContext("2d").drawImage(decoder.frame(accepted.range[0]+frame),0,0);
      $("candidate").getContext("2d").drawImage(renderCandidate(frame),0,0);lastFrame=frame;
    }
    $("time").value=String(elapsed);$("clock").value=(elapsed/1000).toFixed(2)+" s";
  }
  function setRunning(value){running=value;last=null;$("play").textContent=running?"Ⅱ":"▶";$("play").setAttribute("aria-label",running?"暂停":"播放")}
  $("play").onclick=()=>setRunning(!running);
  $("restart").onclick=()=>{elapsed=0;setRunning(true);paint()};
  $("time").oninput=e=>{elapsed=Number(e.target.value);setRunning(false);paint()};
  $("speed").onchange=()=>last=null;document.addEventListener("visibilitychange",()=>last=null);
  function tick(now){if(running&&!document.hidden&&last!==null){elapsed=(elapsed+(now-last)*Number($("speed").value))%duration;paint()}last=now;requestAnimationFrame(tick)}
  setRunning(running);paint();requestAnimationFrame(tick);
  window.AirboatSquareIdleReview={renderCandidate,renderMasks:f=>[renderCandidate(f,"white"),renderCandidate(f,"pupil")],
    frameCount,fps,exponent:2.65,whiteSize:[164,168],green:"#28cf60"};
})();
