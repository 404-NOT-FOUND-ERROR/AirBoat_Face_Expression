"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require(process.argv[2] || "playwright");
(async () => {
  const output = path.resolve(__dirname,"../.test-output");
  await fs.mkdir(output,{recursive:true});
  const browser = await chromium.launch({executablePath:process.argv[3],headless:true});
  const target = path.resolve(process.argv[4] || path.join(__dirname,"../docs/product/expression-workbench.html"));
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:"reduce"});
    const errors = [], requests = [];
    page.on("pageerror",e => errors.push(e.message)); page.on("request",r => requests.push(r.url()));
    await page.goto(pathToFileURL(target).href+"?compare=happy#expressions");
    await page.waitForSelector("#compare[open]");
    const result = await page.evaluate(() => {
      const data = AIRBOAT_EXPRESSIONS;
      let checked = 0, frames = 0;
      for (const [key,p] of Object.entries(data.complete)) {
        const a = data.assets[p.file], decoder = new AirboatEaf(a), [begin,end] = p.segments.performance;
        const entry = AirboatEaf.previewAt(p,a,0,"complete");
        const body = AirboatEaf.previewAt(p,a,begin*1000/p.fps,"complete");
        const exit = AirboatEaf.previewAt(p,a,end*1000/p.fps,"complete");
        const done = AirboatEaf.previewAt(p,a,a.frames*1000/p.fps,"complete");
        const loop = AirboatEaf.previewAt(p,a,(end+4)*1000/p.fps,"loop");
        const only = AirboatEaf.previewAt(p,a,10000,"entry");
        if (entry.phase !== "entry" || body.phase !== "performance" || exit.phase !== "exit" ||
            done.phase !== "done" || !done.finished || only.phase !== "entry-held" ||
            loop.frame !== begin+4%(end-begin)) throw Error("Segment failure: "+key);
        const hashes = new Set();
        for (let i = 0; i < a.frames; i++) {
          const image = decoder.frame(i);
          if (i >= begin && i < end) hashes.add(image.toDataURL());
          frames++;
        }
        if (hashes.size < 2) throw Error("Missing performance motion: "+key);
        checked++;
      }
      return {semantics:checked,decodedFrames:frames};
    });
    assert.equal(result.semantics,29);
    await page.locator("#compare-time").fill("650"); await page.locator("#compare-time").dispatchEvent("input");
    assert.match(await page.locator("#compare-complete-status").textContent(),/完整表演/);
    const body = await page.locator("#compare-complete").evaluate(c => c.toDataURL());
    await page.locator("#compare-time").fill("1000"); await page.locator("#compare-time").dispatchEvent("input");
    assert.notEqual(body,await page.locator("#compare-complete").evaluate(c => c.toDataURL()));
    await page.screenshot({path:path.join(output,"complete-comparison-desktop.png")});
    await page.locator('#compare-stages [data-phase="exit"]').click();
    assert.match(await page.locator("#compare-complete-status").textContent(),/收尾/);
    await page.locator("#compare-mode").selectOption("entry");
    await page.waitForFunction(() => document.querySelector("#compare-complete-status").textContent.includes("进入段结束"));
    await page.locator("#compare-mode").selectOption("complete");
    await page.waitForFunction(() => document.querySelector("#compare-complete-status").textContent.includes("整段播完"));
    await page.locator("#compare-semantic").selectOption("look_left");
    await page.waitForFunction(() => document.querySelector("#compare-original-status").textContent.includes("保持末帧"));
    await page.locator("#compare-close").click();
    await page.locator('[data-version="complete"]').click();
    assert.equal(await page.locator('[data-version="complete"]').getAttribute("aria-pressed"),"true");
    await page.locator('[data-clip-stage="performance"]').click();
    assert.match(await page.locator("#expression-phase-label").textContent(),/完整表演/);
    await page.locator('[data-version="original"]').click();
    assert.match(await page.locator("#metadata").textContent(),/Happy.eaf/);
    assert.equal(await page.locator("#complete-controls").isVisible(),false);
    await page.locator('[data-version="current"]').click();
    assert.match(await page.locator("#metadata").textContent(),/trial-happy.eaf/);
    await page.locator('[data-version="complete"]').click();
    assert.match(await page.locator("#metadata").textContent(),/transition-happy.eaf/);
    await page.locator("#compare-open").click();
    await page.locator("#compare-variant").selectOption("complete");
    await page.setViewportSize({width:390,height:844});
    await page.locator("#compare-semantic").selectOption("happy");
    await page.locator("#compare-time").fill("650"); await page.locator("#compare-time").dispatchEvent("input");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    assert.equal(await page.locator("#compare").evaluate(d => d.scrollWidth > d.clientWidth),false);
    await page.screenshot({path:path.join(output,"complete-comparison-mobile.png"),fullPage:true});
    assert.deepEqual(errors,[]);
    assert(requests.every(u => u.startsWith("file:") || u.startsWith("data:")));
    const summary = {status:"passed",...result,offline:true,desktop:true,mobile:true,
      checks:["real-eaf-decoding","body-moves","entry-body-exit","loop-window","one-shot-hold","version-switch","scrub","side-by-side"]};
    await fs.writeFile(path.join(output,"complete-workbench.json"),JSON.stringify(summary,null,2));
    console.log(JSON.stringify(summary));
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exitCode = 1;});
