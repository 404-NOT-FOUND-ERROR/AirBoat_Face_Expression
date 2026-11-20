// Usage: node verify.cjs <playwright package directory> <Chromium executable>
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require(process.argv[2] || "playwright");

const url = pathToFileURL(path.resolve(__dirname, "../docs/product/expression-workbench.html")).href;
const proof = (name) => path.join(__dirname, "../.test-output", name);
const wait = (page, selector) => page.locator(selector).waitFor({state:"visible"});

(async () => {
  await fs.mkdir(path.join(__dirname, "../.test-output"), {recursive:true});
  const browser = await chromium.launch({executablePath:process.argv[3],headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:960},reducedMotion:"reduce",acceptDownloads:true});
    const errors = [], requests = [];
    page.on("pageerror",e => errors.push(e.message));
    page.on("request",r => requests.push(r.url()));
    await page.goto(url);
    await wait(page,".node.selected");
    assert.match(await page.locator("#node-detail h1").innerText(), /neutral/);
    assert.equal(await page.locator(".node.semantic-color").count(),29);
    assert.equal(await page.locator(".node.asset-color").count(),18);
    assert.match(await page.locator("#metadata").innerText(), /winking\.eaf/);
    assert.equal(await page.locator("#mirror").inputValue(),"device");
    const hash = () => page.locator("canvas#face").evaluate(c => c.toDataURL());
    const auto = await hash();
    await page.locator("#mirror").selectOption("off");
    assert.notEqual(await hash(),auto);
    await page.locator("#mirror").selectOption("on");
    assert.equal(await hash(),auto);
    await page.locator("#mirror").selectOption("device");
    await page.locator("#guides").check();
    await wait(page,"#screen-guides");
    await page.locator("#guides").uncheck();
    assert((await page.locator(".edge.hot").count()) >= 3);
    await page.screenshot({path:proof("desktop.png")});

    const counts = await page.evaluate(() => {
      let frames = 0;
      for (const asset of Object.values(AIRBOAT_EXPRESSIONS.assets)) {
        const decoder = new AirboatEaf(asset);
        let lit = 0;
        for (let f=0;f<asset.frames;f++) {
          const surface = decoder.frame(f);
          const rgba = surface.getContext("2d").getImageData(0,0,asset.width,asset.height).data;
          if (rgba.some((v,i) => i%4 !== 3 && v > 0)) lit++;
          frames++;
        }
        if (!lit) throw Error("Blank animation");
      }
      return {assets:Object.keys(AIRBOAT_EXPRESSIONS.assets).length,frames};
    });
    assert.equal(counts.assets,21);
    assert(counts.frames > 1000);
    await page.locator('[data-version="current"]').click();
    assert.equal(await page.locator(".node.asset-color").count(),21);
    assert.match(await page.locator("#metadata").innerText(), /trial-idle\.eaf/);
    const fullOriginal = await hash();
    await page.locator("#mirror").selectOption("on");
    assert.notEqual(await hash(),fullOriginal);
    await page.locator("#mirror").selectOption("off");
    assert.equal(await hash(),fullOriginal);
    await page.locator("#mirror").selectOption("device");
    await page.locator("#replay").click();
    await page.waitForFunction(() => Number(document.querySelector("#frames").value) >= 2);
    assert.notEqual(await hash(),auto);
    await page.locator("#play").click();
    const paused = await page.locator("#frames").inputValue();
    await page.waitForTimeout(150);
    assert.equal(await page.locator("#frames").inputValue(),paused);
    await page.locator("#frames").fill("27");
    assert.equal(await page.locator("#frame-number").innerText(),"28/104");

    const search = page.locator("#search");
    await search.fill("聆听合成");
    await search.press("Enter");
    assert.match(await page.locator("#metadata").innerText(), /trial-idle\.eaf[\s\S]*listen\.eaf/);
    await page.locator("#metadata button").filter({hasText:"listen.eaf"}).click();
    assert.match(await page.locator("#metadata").innerText(), /listen\.eaf[\s\S]*15 fps/);
    assert.doesNotMatch(await page.locator("#metadata").innerText(),/trial-idle\.eaf/);
    await page.waitForFunction(() => !document.querySelector(".sliding"));
    const transform = () => page.locator("#world").evaluate(n => n.style.transform);
    const initial = await transform();
    await page.locator("#zoom-in").click();
    assert.notEqual(await transform(),initial);
    const viewport = await page.locator("#viewport").boundingBox();
    const afterZoom = await transform();
    // Start the drag from blank space at the top left.
    await page.mouse.move(viewport.x + 4,viewport.y + 4);
    await page.mouse.down();
    await page.mouse.move(viewport.x + 80,viewport.y + 48,{steps:5});
    await page.mouse.up();
    assert.notEqual(await transform(),afterZoom);
    await page.locator("#fit").click();

    await search.fill("开心");
    await search.press("Enter");
    await page.locator('[data-node="asset:trial-happy.eaf"] canvas').waitFor({state:"visible"});
    await page.screenshot({path:proof("current.png")});
    await page.locator("#candidate").selectOption("confused");
    await page.waitForFunction(() => document.querySelector("#candidate-gif").naturalWidth === 480);
    assert.match(await page.locator("#candidate-meta").innerText(), /480×480/);
    assert.match(await page.locator("#scope-info").innerText(), /happy/);
    await page.locator("#note").fill("实测替换");
    await page.locator("#save-plan").click();
    assert.equal(await page.locator("#plan-count").innerText(),"1");
    await page.locator("#plan-open").click();
    assert.match(await page.locator("#plan-list").innerText(), /实测替换/);
    const [download] = await Promise.all([page.waitForEvent("download"),page.locator("#export").click()]);
    const draft = JSON.parse(await fs.readFile(await download.path(),"utf8"));
    assert.equal(draft.firmware_baseline,"1.29.0");
    assert.deepEqual(draft.mappings[0].targets,["happy"]);
    assert.equal(draft.mappings[0].previous_current_files.happy,"trial-happy.eaf");
    await page.reload();
    assert.equal(await page.locator("#plan-count").innerText(),"1");
    await search.fill("开心");
    await search.press("Enter");
    await page.locator("#scope").selectOption("shared");
    assert.match(await page.locator("#scope-info").innerText(), /laughing/);
    await page.locator("#rules-open").click();
    assert.match(await page.locator("#rules").innerText(), /172\.3 KiB[\s\S]*185\.4 KiB[\s\S]*256/);
    await page.screenshot({path:proof("specs.png")});
    assert.deepEqual(errors,[]);
    assert(requests.every(u => u.startsWith("file:")));

    const phone = await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:"reduce"});
    phone.on("pageerror",e => errors.push(e.message));
    await phone.goto(url);
    await wait(phone,".node.selected");
    assert(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const frame = await phone.locator("#face").boundingBox();
    assert(frame.x >= 0 && frame.x+frame.width <= 390 && frame.width === frame.height);
    await phone.locator('[data-version="current"]').tap();
    await phone.locator("#zoom-out").tap();
    await phone.locator("#search").fill("思考");
    await phone.locator("#search-results button").first().tap();
    assert.match(await phone.locator("#node-detail h1").innerText(), /思考/);
    await phone.screenshot({path:proof("mobile.png")});
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({...counts,viewportChecks:["1440x960","390x844"],requests:"file only",status:"passed"}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
