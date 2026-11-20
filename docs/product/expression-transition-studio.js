"use strict";
(async () => {
  const labels = {neutral:"默认",idle:"待机",listening:"聆听",thinking:"思考",happy:"开心",surprised:"惊喜",shocked:"受惊",question:"好奇",look_around:"张望",winking:"眨眼",beat_swing:"摇摆",confused:"晕乎乎",relaxed:"放松",sleepy:"困倦",laughing:"大笑",funny:"俏皮",loving:"亲昵",embarrassed:"害羞",confident:"自信",delicious:"满足",sad:"难过",crying:"哭泣",silly:"淘气",angry:"生气",insert:"出现",look_left:"看左",look_right:"看右",eat:"进食",tried:"疲倦"};
  const select = document.querySelector("#expression"), status = document.querySelector("#status");
  const data = await window.loadAirboatFaceMotion(), manifest = window.AIRBOAT_TRANSITIONS;
  const player = new AirboatFaceMotion(data), renderer = new AirboatFaceRenderer(document.querySelector("#face"),data);
  let clock = 0, last = 0, lastPaint = -Infinity, paused = false, schedule = [], stage = "base", hiddenAt = null;
  function state(name) {
    stage = name;
    const order = ["base","entry","loop","exit"], at = order.indexOf(name);
    document.querySelectorAll(".stage").forEach((item,i) => {
      item.classList.toggle("active",i === at); item.classList.toggle("complete",i < at);
    });
    const label = player.key === "idle" && player.resting ? "绿色待机" : labels[player.key];
    status.textContent = label + (name === "entry" ? " · 进入" : name === "exit" ? " · 回归" : name === "loop" ? " · 表演" : "");
  }
  function paint() {
    renderer.draw(player.sample(clock),document.querySelector("#mirror").checked,document.querySelector("#guides").checked);
  }
  function start(key) {
    paused = false; document.querySelector("#pause").textContent = "暂停";
    player.request(key,clock); state("entry"); paint();
  }
  function stop() {
    schedule = [];
    paused = false; document.querySelector("#pause").textContent = "暂停";
    player.returnToBase(clock); state("exit"); paint();
  }
  function single(key) {
    start(key);
    schedule = [{at:clock+data.transition_ms+2100,base:true}];
  }
  function sequence(name) {
    const keys = manifest.sequences[name];
    start(keys[0]);
    schedule = keys.slice(1).map((key,i) => ({at:clock+(i+1)*(data.transition_ms+1700),key}));
    schedule.push({at:clock+keys.length*(data.transition_ms+1700),base:true});
  }
  function tick(time) {
    if (!last) last = time;
    if (!paused && hiddenAt === null) clock += time-last;
    last = time;
    if (schedule.length && clock >= schedule[0].at) {
      const item = schedule.shift();
      if (item.base) { player.returnToBase(clock); state("exit"); }
      else { player.request(item.key,clock); select.value = item.key; state("entry"); }
    }
    if (clock-lastPaint >= 40 || paused) {
      paint(); lastPaint = clock;
      if (!player.transition && (stage === "entry" || stage === "exit")) state(player.resting ? "base" : "loop");
    }
    requestAnimationFrame(tick);
  }
  for (const key of Object.keys(data.clips)) {
    const option = document.createElement("option"); option.value = key; option.textContent = labels[key] || key;
    select.append(option);
  }
  select.value = "happy";
  select.addEventListener("change",() => single(select.value));
  document.querySelector("#play").addEventListener("click",() => single(select.value));
  document.querySelector("#stop").addEventListener("click",stop);
  document.querySelector("#pause").addEventListener("click",event => {
    paused = !paused; event.currentTarget.textContent = paused ? "继续" : "暂停"; paint();
  });
  for (const id of ["mirror","guides"]) document.querySelector("#"+id).addEventListener("change",paint);
  document.querySelectorAll("[data-sequence]").forEach(button => button.addEventListener("click",() => sequence(button.dataset.sequence)));
  document.addEventListener("visibilitychange",() => { hiddenAt = document.hidden ? performance.now() : null; last = performance.now(); });
  await renderer.ready();
  state("base"); paint();
  document.querySelectorAll("main button, main select, main input").forEach(control => { control.disabled = false; });
  document.body.dataset.ready = "true";
  requestAnimationFrame(tick);
})().catch(error => {
  document.body.dataset.ready = "error";
  document.querySelector("#status").textContent = "素材加载失败：" + error.message;
});
