"use strict";
(() => {
  const $ = id => document.getElementById(id), data = window.AIRBOAT_EXPRESSIONS, Eaf = window.AirboatEaf;
  const beats = window.AIRBOAT_CONTOUR_PACK.beats;
  const names = {neutral:"默认眼神",idle:"待机眨眼",listening:"聆听",thinking:"思考",happy:"开心",surprised:"突然发现",shocked:"受惊",question:"好奇歪头",look_around:"张望",winking:"眨眼",beat_swing:"摇摆",confused:"晕乎乎",relaxed:"放松",sleepy:"困倦",laughing:"大笑",funny:"搞怪",loving:"喜欢",embarrassed:"害羞",confident:"得意",delicious:"好吃",sad:"难过",crying:"哭泣",silly:"俏皮",angry:"生气",insert:"插入动画",look_left:"看左边",look_right:"看右边",eat:"吃东西",tried:"疲惫"};
  const notes = {
    idle: ["留意两眼之间的连桥和眨眼边缘。", "对称双眼，瞳孔随眼皮遮住，再轻轻睁开。"],
    shocked: ["眼睛拉长时，下缘出现平直截口。", "保留伸长节奏，下缘恢复完整圆弧。"],
    happy: ["原版先压扁，再弹起，顶部稍停。", "蓄力向上弹，落下再轻弹一次；两眼和黑色笑弧轻微错拍。"],
    laughing: ["两只笑眼之间留白，外侧有小爱心。", "两只笑眼先后弹起，第二下更轻，小爱心晚一拍浮起。"],
    confused: ["原版眨眼后转动螺旋，再慢慢回稳。", "主摆之后左右交替的小余震逐次减弱，瞳孔和橙点稍晚跟上。"],
    look_around: ["原版停下来眨眼，再换方向。", "瞳孔先看，眼形后跟；左右各驻留一会儿，再收回视线。"],
  };
  const decoders = new Map(), stamps = new Map(), buttons = document.querySelectorAll("[data-mode]");
  const requested = location.hash.slice(1);
  let mode = Object.hasOwn(data.contour, requested) ? requested : "idle";
  let running = !matchMedia("(prefers-reduced-motion: reduce)").matches;
  let elapsed = 0, duration, shown, last, left, right, entry, leftEntry;

  function draw(id, profile, ms) {
    const asset = data.assets[profile.file];
    const {frame} = Eaf.previewAt(profile, asset, ms);
    const overlay = profile.overlay ? Math.floor(ms*15/1000)%data.assets[profile.overlay].frames : -1;
    const stamp = profile.file + ":" + frame + ":" + overlay;
    if (stamps.get(id) === stamp) return;
    if (!decoders.has(profile.file)) decoders.set(profile.file, new Eaf(asset));
    const ctx = $(id).getContext("2d");
    Eaf.draw(ctx, decoders.get(profile.file).frame(frame), profile);
    if (overlay >= 0) {
      if (!decoders.has(profile.overlay)) decoders.set(profile.overlay, new Eaf(data.assets[profile.overlay]));
      const layer = decoders.get(profile.overlay).frame(overlay), s = ctx.canvas.width/360;
      ctx.drawImage(layer,130*s,25*s,layer.width*s,layer.height*s);
    }
    stamps.set(id, stamp);
  }
  function paint() {
    const display = Math.floor(elapsed / 10);
    if (shown === display) return;
    shown = display;
    const time = Math.min(elapsed, duration);
    const referenceTime = beats[mode] ? Math.max(0, time - entry + leftEntry) : time;
    draw("old-face", left, referenceTime);
    draw("new-face", right, time);
    $("time").value = String(time);
    $("clock").value = (time / 1000).toFixed(2) + " s";
  }
  const reference = () => mode === "listening" && $("reference").value === "original" ?
    {...data.original.neutral,overlay:"listen.eaf"} : (beats[mode] ? data[$("reference").value] :
    mode === "shocked" ? data.complete : data.optimized)[mode];
  function setRunning(next) {
    running = next;
    last = undefined;
    $("play").textContent = running ? "Ⅱ" : "▶";
    $("play").setAttribute("aria-label", running ? "暂停动画" : "播放动画");
  }
  function seek(ms) {
    elapsed = Math.min(ms, duration);
    shown = undefined;
    paint();
  }
  function configure() {
    left = reference();
    right = data.contour[mode];
    const authored = Boolean(beats[mode]);
    const length = p => data.assets[p.file].frames * 1000 / p.fps;
    entry = right.segments.performance[0] * 1000 / right.fps;
    leftEntry = left.segments ? left.segments.performance[0] * 1000 / left.fps : 0;
    duration = Math.ceil(Math.max(length(left) + (authored ? entry - leftEntry : 0), length(right)) / 10) * 10;
    $("time").max = String(duration);
    for (const b of buttons) b.setAttribute("aria-pressed", String(b.dataset.mode === mode));
    $("repertoire").value = mode;
    $("old-title").hidden = authored;
    $("old-kind").hidden = authored;
    $("reference").hidden = !authored;
    $("old-kind").textContent = mode === "idle" ? "高清优化 · 480" : "完整素材 · 240";
    $("old-note").textContent = authored && $("reference").value === "optimized" ? "上一版彩色表演。" : notes[mode]?.[0] || "原版素材。";
    $("new-note").textContent = notes[mode]?.[1] || (beats[mode] || []).map(([,label]) => label).join(" → ") || notes.idle[1];
    $("beats").replaceChildren();
    for (const [ms, label] of beats[mode] || []) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = label;
      b.title = ((ms + entry) / 1000).toFixed(2) + " s";
      b.onclick = () => {setRunning(false); seek(ms + entry);};
      $("beats").append(b);
    }
    seek(0);
  }
  for (const key of Object.keys(names)) $("repertoire").append(new Option(names[key],key));
  const choose = next => {mode = next; history.replaceState(null,"","#"+next); configure();};
  for (const b of buttons) b.onclick = () => choose(b.dataset.mode);
  $("repertoire").onchange = e => choose(e.target.value);
  $("reference").onchange = configure;
  $("speed").onchange = () => {last = undefined;};
  $("play").onclick = () => {
    if (!running && elapsed >= duration) seek(0);
    setRunning(!running);
  };
  $("restart").onclick = () => {seek(0); setRunning(true);};
  $("time").oninput = e => {setRunning(false); seek(Number(e.target.value));};
  document.addEventListener("visibilitychange", () => {last = undefined;});
  function tick(now) {
    if (running && !document.hidden && last !== undefined) {
      elapsed = (elapsed + (now - last) * Number($("speed").value)) % (duration + 300);
      paint();
    }
    last = now;
    requestAnimationFrame(tick);
  }
  setRunning(running);
  configure();
  requestAnimationFrame(tick);
})();
