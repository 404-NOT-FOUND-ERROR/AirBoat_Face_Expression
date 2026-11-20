"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require(process.argv[2] || "playwright");
(async () => {
  const output = path.join(__dirname,"../.test-output");
  await fs.mkdir(output,{recursive:true});
  const browser = await chromium.launch({executablePath:process.argv[3],headless:true});
  const url = pathToFileURL(path.join(__dirname,"../docs/product/expression-transition-studio.html")).href;
  try {
    const page = await browser.newPage({viewport:{width:1440,height:960},reducedMotion:"reduce"});
    const errors = [], requests = [];
    page.on("pageerror",error => errors.push(error.message));
    page.on("request",request => requests.push(request.url()));
    await page.goto(url);
    await page.waitForSelector('body[data-ready="true"]');
    assert.equal(await page.locator("#expression option").count(),29);
    const canvas = page.locator("#face");
    const snapshot = () => canvas.evaluate(c => c.toDataURL());
    const base = await snapshot();
    await page.locator("#play").click();
    await page.waitForFunction(() => document.querySelector("#status").textContent.includes("表演"));
    assert.notEqual(await snapshot(),base);
    await page.locator("#expression").selectOption("surprised");
    await page.waitForTimeout(170);
    await page.locator("#expression").selectOption("thinking");
    await page.waitForFunction(() => document.querySelector("#status").textContent.includes("思考 · 表演"));
    await page.locator("#pause").click();
    const paused = await snapshot();
    await page.waitForTimeout(180);
    assert.equal(await snapshot(),paused);
    await page.locator("#mirror").check();
    assert.notEqual(await snapshot(),paused);
    await page.locator("#mirror").uncheck();
    assert.equal(await snapshot(),paused);
    await page.locator("#guides").check();
    assert.notEqual(await snapshot(),paused);
    await page.locator("#guides").uncheck();
    await page.screenshot({path:path.join(output,"transition-desktop.png")});
    await page.locator("#stop").click();
    await page.waitForFunction(() => document.querySelector("#status").textContent === "绿色待机");
    assert.equal(await snapshot(),base);
    for (const name of ["happy-return","listen-think-happy","happy-surprised"]) {
      await page.locator(`[data-sequence="${name}"]`).click();
      await page.waitForFunction(() => document.querySelector("#status").textContent === "绿色待机",{},{timeout:12000});
      assert.equal(await snapshot(),base);
    }
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(output,"transition-mobile.png"),fullPage:true});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    const failure = await browser.newPage();
    await failure.addInitScript(() => {
      window.DecompressionStream = class { constructor() { throw new Error("test decode failure"); } };
    });
    await failure.goto(url);
    await failure.waitForSelector('body[data-ready="error"]');
    assert.match(await failure.locator("#status").textContent(),/test decode failure/);
    assert.equal(await failure.locator("#play").isDisabled(),true);
    await failure.close();
    assert.deepEqual(errors,[]);
    assert(requests.every(url => url.startsWith("file:") || url.startsWith("data:")));
    const result = {status:"passed",semantics:29,sequences:3,offline:true,desktop:true,mobile:true,
      checks:["selection","interrupt","pause","mirror","guides","return","sequence-return","decode-error"]};
    await fs.writeFile(path.join(output,"transition-browser.json"),JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})();
