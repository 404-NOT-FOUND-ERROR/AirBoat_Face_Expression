"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const zlib = require("node:zlib");
const path = require("node:path");
const {AirboatFaceMotion} = require("../docs/product/expression-motion-player.js");
const dataFile = path.join(__dirname,"../output/imagegen/airboat-expression-study-20261120/transitions/runtime-data.js");
const text = fs.readFileSync(dataFile,"utf8");
const packed = text.match(/AIRBOAT_FACE_MOTION_GZIP = "([^"]+)"/);
assert(packed,"Compressed transition dataset is missing");
const data = JSON.parse(zlib.gunzipSync(Buffer.from(packed[1],"base64")).toString("utf8"));
const motion = new AirboatFaceMotion(data);
assert.equal(Object.keys(data.clips).length,29);
const base = motion.sample(0);
assert.deepEqual(base.color,[40,207,96]);
const samePose = (a,b) => {
  assert.deepEqual(a.color,b.color);
  assert.deepEqual(a.layers,b.layers);
  assert.deepEqual(a.accents,b.accents);
};
const keys = Object.keys(data.clips);
let now = 10, switches = 0;
for (const key of keys) {
  for (const target of keys) {
    const p = new AirboatFaceMotion(data);
    p.request(key,now); p.sample(now+500);
    const interruptedAt = now+677, before = p.sample(interruptedAt);
    assert(p.request(target,interruptedAt));
    samePose(p.sample(interruptedAt),before);
    const halfway = p.sample(interruptedAt+160);
    p.request("happy",interruptedAt+160);
    samePose(p.sample(interruptedAt+160),halfway);
    p.sample(interruptedAt+600);
    const duration = data.clips.happy.duration_ms;
    samePose(p.loop("happy",0),p.loop("happy",duration));
    const exitAt = interruptedAt+711;
    const beforeExit = p.sample(exitAt);
    assert(p.returnToBase(exitAt));
    samePose(p.sample(exitAt),beforeExit);
    samePose(p.sample(exitAt+360),base);
    assert.deepEqual(p.sample(exitAt+10000).color,base.color);
    assert.equal(p.key,data.base);
    now += 4; switches++;
  }
}
const bad = motion.sample(10);
assert.equal(motion.request("missing",10),false);
samePose(motion.sample(10),bad);
console.log(JSON.stringify({status:"passed",semantics:keys.length,pairs:switches,
  rules:["continuous-entry","mid-transition-retarget","exit-from-current-pose","exact-green-return","loop-time-wrap","unknown-no-change"]}));
