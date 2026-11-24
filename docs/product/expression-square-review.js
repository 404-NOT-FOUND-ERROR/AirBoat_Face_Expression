"use strict";
(() => {
  const data=window.AIRBOAT_EXPRESSIONS, pack=window.AIRBOAT_SQUARE_PACK, $=id=>document.getElementById(id);
  const names={idle:"待机",listening:"聆听",thinking:"思考",happy:"开心",surprised:"突然发现",shocked:"受惊",question:"好奇歪头",look_around:"张望",winking:"眨眼",beat_swing:"摇摆",confused:"晕乎乎",relaxed:"放松",laughing:"大笑",funny:"搞怪",loving:"喜欢",embarrassed:"害羞",confident:"得意",delicious:"好吃",sad:"难过",crying:"哭泣",silly:"俏皮",angry:"生气",insert:"插入动画",look_left:"看左边",look_right:"看右边",eat:"吃东西",sleepy:"困倦",tried:"疲惫"};
  const notes={idle:"默认保持对称双眼。轻微呼吸、小瞥视、慢眨和双眨之后，回到同一个绿色眼神。",listening:"瞳孔先聚焦，小方块随后一格格跳动。",thinking:"竖长方眼和圆眼高低错开，先抬瞳孔，再窄一只眼。",happy:"先蹲下蓄力，再高高弹起。第二下更轻，最后留一点余弹。",surprised:"眼白像气球一样鼓成方圆，瞳孔抢先缩小。",shocked:"长方眼突然竖起来，定住一拍，再微微打颤。",question:"共用「俏皮」表演。",look_around:"瞳孔先出发，长方眼再像望远镜一样伸过去。",winking:"方眼压成一道快门，圆眼鼓起来，再弹开。",beat_swing:"大小眼踩着轻重不同的拍子摆，瞳孔稍晚赶上。",confused:"方形螺旋转得比眼白慢一点，主摆后留下渐弱的晕眩。",relaxed:"宽方眼慢慢呼一口气，眼皮和瞳孔分开沉下去。",laughing:"共用「开心」表演。",funny:"长方眼伸出去，圆眼突然吹大。停在怪脸，再交换大小。",loving:"黑色像素爱心在白色软方块里怦怦跳。",embarrassed:"先躲开视线，小腮红方块才亮起来，最后偷偷看回你。",confident:"一只方眼得意抬高，瞳孔多补一个眼神。",delicious:"共用「搞怪」表演。",sad:"软方块的眼角垂下来，中间还有一点小呼吸。",crying:"共用「难过」表演。",silly:"瞳孔故意挤到中间，定住怪脸，再突然弹开。",angry:"斜切方眼压向中间，短促地哼一下，再收回来。",insert:"共用「俏皮」表演。",look_left:"先看左，左边方眼再伸出去。",look_right:"先看右，右边方眼再伸出去。",eat:"共用「搞怪」表演。",sleepy:"调用「疲惫」动画；困倦和疲惫语义入口分别保留。",tried:"眼皮越沉越扁，撑住一会儿，费力抬起，又塌了下去。"};
  const decoders=new Map(), stamps=new Map();
  const resolve=key=>pack.aliases[key]||key;
  let selected=(pack.clips[location.hash.slice(1)]||pack.aliases[location.hash.slice(1)])?location.hash.slice(1):"funny", elapsed=0,last=null,running=!matchMedia("(prefers-reduced-motion:reduce)").matches;
  function draw(id,profile,frame){
    const a=data.assets[profile.file];
    if(!decoders.has(profile.file))decoders.set(profile.file,new AirboatEaf(a));
    const stamp=profile.file+":"+frame;if(stamps.get(id)===stamp)return;
    $(id).getContext("2d").drawImage(decoders.get(profile.file).frame(frame),0,0,480,480);stamps.set(id,stamp);
  }
  function paint(){
    const p=data.square[selected],a=data.assets[p.file],state=AirboatEaf.previewAt(p,a,elapsed,$("mode").value);
    draw("new-face",p,state.frame);
    const old=data.contour[selected],oa=data.assets[old.file];
    const phase=state.phase in p.segments?state.phase:state.phase==="done"?"exit":"performance";
    const [s,e]=p.segments[phase],[os,oe]=old.segments[phase];
    const u=Math.max(0,Math.min(1,(state.frame-s)/Math.max(1,e-s-1)));
    draw("old-face",old,Math.round(os+u*(oe-os-1)));
    $("time").value=Math.min(elapsed,Number($("time").max));$("clock").value=(elapsed/1000).toFixed(2)+" s";
  }
  function choose(key){
    selected=key;elapsed=0;last=null;history.replaceState(null,"","#"+key);
    $("new-label").textContent=names[key];$("repertoire").value=key;$("motion-note").textContent=notes[key]||"调用「疲惫」动画；困倦和疲惫语义入口分别保留。";
    const actual=resolve(key);
    $("native-link").href=`../../output/imagegen/airboat-square-pop-20261124/preview/${actual}.gif`;
    $("native-link").title=actual===key?"查看交付素材的完整 GIF":"查看共用动画的完整 GIF："+actual;
    $("time").max=String(data.assets[data.square[key].file].frames*40);
    $("beats").replaceChildren();
    for(const [ms,label] of pack.beats[actual]){
      const b=document.createElement("button");b.textContent=label;
      b.onclick=()=>{running=false;$("play").textContent="▶";elapsed=ms+pack.transition_frames*40;paint()};$("beats").append(b);
    }
    for(const b of document.querySelectorAll("[data-expression]"))b.setAttribute("aria-pressed",String(b.dataset.expression===key));
    stamps.clear();paint();
  }
  for(const [key,name] of Object.entries(names)){
    $("repertoire").append(new Option(name,key));
    const b=document.createElement("button"),img=document.createElement("img"),label=document.createElement("span");
    b.className="card";b.dataset.expression=key;b.setAttribute("aria-label",name);img.alt="";img.loading="lazy";
    img.src=`../../output/imagegen/airboat-square-pop-20261124/thumbnails/${key}.png`;label.textContent=name;
    b.append(img,label);b.onclick=()=>choose(key);$("cards").append(b);
  }
  $("repertoire").onchange=e=>choose(e.target.value);
  $("play").onclick=()=>{running=!running;last=null;$("play").textContent=running?"Ⅱ":"▶"};
  $("restart").onclick=()=>{elapsed=0;last=null;running=true;$("play").textContent="Ⅱ";paint()};
  $("time").oninput=e=>{elapsed=Number(e.target.value);running=false;$("play").textContent="▶";paint()};
  $("mode").onchange=()=>{elapsed=0;last=null;paint()};$("speed").onchange=()=>last=null;
  $("pack-size").textContent=`分层资源 ${( (pack.binary_bytes+pack.catalog_bytes)/1048576).toFixed(2)} MiB`;
  document.addEventListener("visibilitychange",()=>last=null);
  function tick(now){
    if(running&&!document.hidden&&last!==null){elapsed+=(now-last)*Number($("speed").value);
      if($("mode").value!=="loop"&&elapsed>Number($("time").max)+450)elapsed=0;paint()}
    last=now;requestAnimationFrame(tick);
  }
  choose(selected);$("play").textContent=running?"Ⅱ":"▶";requestAnimationFrame(tick);
})();
