"use strict";
(() => {
  const $=id=>document.getElementById(id), data=AIRBOAT_EXPRESSIONS;
  const listen=new AirboatEaf(data.assets["listen.eaf"]), decoders=new Map();
  let elapsed=0,playing=true,listening=true,last=null;
  function render(ms) {
    const p=data.optimized[$("semantic").value],asset=data.assets[p.file];
    if (!decoders.has(p.file)) decoders.set(p.file,new AirboatEaf(asset));
    const frame=AirboatEaf.previewAt(p,asset,ms,"loop").frame;
    const base=decoders.get(p.file).frame(frame);
    const mask=listen.frame(Math.floor(ms*15/1000)%data.assets["listen.eaf"].frames);
    for (const [id,mode] of [["before","legacy"],["after","transparent"]]) {
      const context=$(id).getContext("2d");
      context.drawImage(base,0,0,$(id).width,$(id).height);
      if (listening) AirboatListenOverlay.draw(context,mask,mode);
    }
    $("time").value=ms%3333;$("clock").value=`${(ms/1000).toFixed(2)} s`;
  }
  $("semantic").onchange=()=>render(elapsed);
  $("side").onchange=()=>{for(const id of ["before","after"])$(id).width=$(id).height=Number($("side").value);render(elapsed);};
  $("play").onclick=()=>{playing=!playing;$("play").textContent=playing?"暂停":"播放";};
  $("listening").onclick=()=>{listening=!listening;$("listening").setAttribute("aria-pressed",String(listening));$("listening").textContent=listening?"结束聆听":"开始聆听";render(elapsed);};
  $("time").oninput=()=>{elapsed=Number($("time").value);playing=false;$("play").textContent="播放";render(elapsed);};
  function tick(time) {if(last!==null&&playing)elapsed+=Math.min(time-last,100);last=time;if(playing)render(elapsed);requestAnimationFrame(tick);}
  render(0);requestAnimationFrame(tick);
})();
