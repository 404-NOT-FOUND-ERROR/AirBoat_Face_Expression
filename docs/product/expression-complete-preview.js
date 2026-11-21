/* Full delivered clips beside the original catalog. One explicit preview clock. */
"use strict";
(() => {
  const data = window.AIRBOAT_EXPRESSIONS, Eaf = window.AirboatEaf;
  const $ = id => document.getElementById(id), dialog = $("compare");
  const names = {neutral:"默认眼神",idle:"待机",listening:"聆听",thinking:"思考",happy:"开心",surprised:"惊喜",shocked:"受惊",question:"好奇",look_around:"张望",winking:"眨眼",beat_swing:"摇摆",confused:"晕乎乎",relaxed:"放松",sleepy:"困倦",laughing:"大笑",funny:"搞怪",loving:"喜欢",embarrassed:"害羞",confident:"得意",delicious:"满足",sad:"难过",crying:"哭泣",silly:"俏皮",angry:"生气",insert:"出现",look_left:"看左",look_right:"看右",eat:"进食",tried:"疲惫"};
  const phaseNames = {entry:"进入",performance:"完整表演",exit:"收尾",done:"整段播完 · 回到绿色",held:"单次播完 · 保持末帧","entry-held":"进入段结束"};
  const decoders = new Map(), stamps = new Map();
  let selected = "happy", clock = 0, running = false, last = null;
  const original = key => key === "listening" ? {...data.original.neutral,overlay:"listen.eaf"} : data.original[key];
  const decoder = file => {
    if (!decoders.has(file)) decoders.set(file,new Eaf(data.assets[file]));
    return decoders.get(file);
  };
  const mode = () => $("compare-mode").value;
  const duration = () => {
    const a = original(selected), b = data.complete[selected];
    return Math.max(data.assets[a.file].frames*1000/a.fps,data.assets[b.file].frames*1000/b.fps);
  };
  function draw(which,p,at) {
    const a = data.assets[p.file], state = Eaf.previewAt(p,a,at,which === "complete" ? mode() : undefined);
    const overlay = p.overlay ? Math.floor(at*15/1000)%data.assets[p.overlay].frames : -1;
    const stamp = p.file+":"+state.frame+":"+overlay;
    if (stamps.get(which) !== stamp) {
      const ctx = $("compare-"+which).getContext("2d");
      Eaf.draw(ctx,decoder(p.file).frame(state.frame),p);
      if (overlay >= 0) {
        const frame = decoder(p.overlay).frame(overlay), s = ctx.canvas.width/360;
        ctx.drawImage(frame,130*s,25*s,frame.width*s,frame.height*s);
      }
      stamps.set(which,stamp);
    }
    const phase = phaseNames[state.phase];
    $("compare-"+which+"-status").textContent = phase+` · ${state.frame+1}/${a.frames} 帧`;
    if (which === "complete") for (const item of $("compare-stages").children)
      item.classList.toggle("active",item.dataset.phase === state.phase);
    return state;
  }
  function paint() {
    draw("original",original(selected),clock);
    const state = draw("complete",data.complete[selected],clock);
    $("compare-time").value = Math.min(clock,Number($("compare-time").max));
    $("compare-clock").value = (clock/1000).toFixed(2)+" s";
    if (running && mode() !== "loop" && clock >= (mode() === "entry" ? state.duration : duration())) running = false;
    $("compare-play").textContent = running ? "暂停" : "播放";
  }
  function reset(play = true) {
    selected = $("compare-semantic").value;
    clock = 0; last = null; running = play; stamps.clear();
    const a = original(selected), b = data.complete[selected], asset = data.assets[b.file];
    $("compare-title").textContent = names[selected]+" · 原版与新表情";
    $("compare-original-meta").textContent = `${a.file} · ${a.fps} fps · ${a.loop ? "整段循环" : "播一遍后保持末帧"}`+(a.overlay ? " · 独立聆听条" : "");
    $("compare-complete-meta").textContent = `${b.file} · ${b.fps} fps · ${(asset.frames/b.fps).toFixed(2)} s`;
    const stages = $("compare-stages"); stages.replaceChildren();
    for (const [part,range] of Object.entries(b.segments)) {
      const button = document.createElement("button");
      button.dataset.phase = part; button.style.flexGrow = String(range[1]-range[0]);
      button.textContent = `${phaseNames[part]} ${((range[1]-range[0])/b.fps).toFixed(2)}s`;
      button.onclick = () => { clock = range[0]*1000/b.fps; running = false; paint(); };
      stages.append(button);
    }
    $("compare-time").max = String(mode() === "entry" ? b.segments.entry[1]*1000/b.fps : mode() === "loop" ? Math.max(duration(),6000) : duration());
    paint();
  }
  function open(key) {
    $("compare-semantic").value = data.complete[key] ? key : selected;
    if (!dialog.open) dialog.showModal();
    document.dispatchEvent(new CustomEvent("airboat:preview-compare",{detail:{open:true}}));
    reset();
  }
  for (const key of Object.keys(data.complete)) $("compare-semantic").append(new Option(names[key]+" · "+key,key));
  $("compare-semantic").value = selected;
  $("compare-open").onclick = () => open(selected);
  $("compare-close").onclick = () => dialog.close();
  dialog.addEventListener("close",() => {
    running = false; last = null;
    document.dispatchEvent(new CustomEvent("airboat:preview-compare",{detail:{open:false}}));
  });
  dialog.addEventListener("click",event => {
    if (event.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
  });
  document.addEventListener("airboat:expression-select",event => {
    if (data.complete[event.detail.semantic]) selected = event.detail.semantic;
  });
  $("compare-semantic").onchange = () => reset();
  $("compare-mode").onchange = () => reset();
  $("compare-replay").onclick = () => reset();
  $("compare-play").onclick = () => {
    if (!running && clock >= Number($("compare-time").max)) clock = 0;
    running = !running; last = null; paint();
  };
  $("compare-time").oninput = event => { clock = Number(event.target.value); running = false; paint(); };
  document.addEventListener("visibilitychange",() => { if (document.hidden) {running = false; last = null;} });
  function tick(now) {
    if (dialog.open && !document.hidden) {
      if (running && last !== null) clock += now-last;
      if (clock > Number($("compare-time").max) && mode() === "loop") $("compare-time").max = String(clock+5000);
      paint(); last = now;
    } else last = null;
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  window.AirboatCompletePreview = {open};
  const requested = new URLSearchParams(location.search).get("compare");
  if (requested) open(requested);
})();
