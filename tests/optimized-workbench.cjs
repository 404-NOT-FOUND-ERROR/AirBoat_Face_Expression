"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs/promises"),path=require("node:path");
const {pathToFileURL}=require("node:url");
const {chromium}=require(process.argv[2]||"playwright");
(async()=>{
  const browser=await chromium.launch({executablePath:process.argv[3],headless:true});
  const out=path.resolve(__dirname,"../.test-output");await fs.mkdir(out,{recursive:true});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1080},reducedMotion:"reduce"});
    const errors=[],requests=[];page.on("pageerror",e=>errors.push(e.message));page.on("request",r=>requests.push(r.url()));
    await page.goto(pathToFileURL(path.resolve(process.argv[4]||path.join(__dirname,"../docs/product/expression-workbench.html"))).href+"?quality=happy");
    await page.waitForSelector("#compare[open]");
    const result=await page.evaluate(()=>{
      const data=AIRBOAT_EXPRESSIONS;
      let frames=0,moving=0;
      for(const [key,p]of Object.entries(data.optimized)){
        const a=data.assets[p.file],dec=new AirboatEaf(a),hashes=new Set();
        for(let i=0;i<a.frames;i++){
          const c=dec.frame(i);if(c.width!==480||c.height!==480)throw Error("Resolution: "+key);
          if(i>=p.segments.performance[0]&&i<p.segments.performance[1])hashes.add(c.toDataURL());
          frames++;
        }
        if(hashes.size<2)throw Error("Static clip: "+key);moving++;
        const start=dec.frame(0).toDataURL(),end=dec.frame(a.frames-1).toDataURL();
        const idle=new AirboatEaf(data.assets[data.optimized.idle.file]).frame(0).toDataURL();
        if(start!==idle||end!==idle)throw Error("Common base endpoint: "+key);
        const state=AirboatEaf.previewAt(p,a,5000,"loop");
        if(state.frame<p.range[0]||state.frame>=p.range[1])throw Error("Loop range: "+key);
      }
      const p=data.optimized.winking,d=new AirboatEaf(data.assets[p.file]),c=d.frame(p.range[0]);
      const context=c.getContext("2d"),left=context.getImageData(0,100,240,300).data,right=context.getImageData(240,100,240,300).data;
      let mismatch=0;for(let y=0;y<300;y++)for(let x=0;x<240;x++)if(left[(y*240+x)*4]!==right[(y*240+239-x)*4])mismatch++;
      if(mismatch<100)throw Error("Wink asymmetry was lost");
      return {semantics:moving,frames,winkAsymmetricPixels:mismatch,...AirboatOptimized.statistics};
    });
    assert.equal(result.semantics,29);
    await page.locator("#compare-time").fill("720");await page.locator("#compare-time").dispatchEvent("input");
    await page.screenshot({path:path.join(out,"optimized-comparison-desktop.png"),fullPage:true});
    await page.locator("#compare-reference").selectOption("original");
    await page.locator("#compare-semantic").selectOption("winking");
    await page.locator("#compare-close").click();
    assert.equal(await page.locator('[data-version="optimized"]').getAttribute("aria-pressed"),"true");
    assert.match(await page.locator("#metadata").textContent(),/480×480/);
    await page.locator('[data-node="semantic:winking"]').evaluate(b=>b.click());
    await page.locator("#mirror").selectOption("off");await page.locator('[data-clip-stage="performance"]').click();
    const before=await page.locator("#face").evaluate(c=>c.toDataURL());
    await page.locator("#mirror").selectOption("on");
    assert.notEqual(before,await page.locator("#face").evaluate(c=>c.toDataURL()));
    await page.locator('[data-version="complete"]').click();await page.locator('[data-version="optimized"]').click();
    await page.locator("#compare-open").click();
    await page.locator("#compare-semantic").selectOption("happy");
    await page.setViewportSize({width:390,height:844});
    await page.locator("#compare-time").fill("720");await page.locator("#compare-time").dispatchEvent("input");
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    assert.equal(await page.locator("#compare").evaluate(d=>d.scrollWidth>d.clientWidth),false);
    await page.screenshot({path:path.join(out,"optimized-comparison-mobile.png"),fullPage:true});
    assert.deepEqual(errors,[]);assert(requests.every(u=>u.startsWith("file:")||u.startsWith("data:")));
    const summary={status:"passed",...result,desktop:true,mobile:true,offline:true};
    await fs.writeFile(path.join(out,"optimized-workbench.json"),JSON.stringify(summary,null,2));console.log(JSON.stringify(summary));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
