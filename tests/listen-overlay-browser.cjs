"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs/promises"),path=require("node:path");
const {pathToFileURL}=require("node:url");
const {chromium}=require(process.argv[2]||"playwright");
(async()=>{
  const browser=await chromium.launch({executablePath:process.argv[3],headless:true});
  const out=path.resolve(__dirname,"../.test-output");await fs.mkdir(out,{recursive:true});
  try {
    const page=await browser.newPage({viewport:{width:1280,height:1000},reducedMotion:"reduce"});
    const errors=[],requests=[];page.on("pageerror",e=>errors.push(e.message));page.on("request",r=>requests.push(r.url()));
    await page.goto(pathToFileURL(path.resolve(process.argv[4]||path.join(__dirname,"../docs/product/listen-overlay-preview.html"))).href);
    await page.locator("#play").click();
    const result=await page.evaluate(()=>{
      const {blend565,draw,pack,unpack}=AirboatListenOverlay;
      const make=side=>{const c=document.createElement("canvas");c.width=c.height=side;return c;};
      let hash=2166136261;
      for(let i=0;i<=65535;i++){
        if(blend565(i,0)!==i||blend565(i,65535)!==65535||blend565(0,i)!==i)throw Error("RGB565 invariant "+i);
        const actual=blend565(i,i^0xa55a);
        hash=Math.imul(hash^(actual&255),16777619)>>>0;hash=Math.imul(hash^(actual>>8),16777619)>>>0;
      }
      const a=AIRBOAT_EXPRESSIONS.assets["listen.eaf"],decoder=new AirboatEaf(a);
      const colors=[0x0000,0x07e0,0xf800,0x001f,0x53b2];
      let blackUnchanged=0,grayBlended=0,checks=0;
      for(const side of [360,480]){
        const c=make(side),ctx=c.getContext("2d",{willReadFrequently:true});
        for(let frame=0;frame<a.frames;frame++){
          const mask=decoder.frame(frame),raw=mask.getContext("2d").getImageData(0,0,100,46).data;
          for(const bg of colors){
            const rgba=unpack(bg),css=`rgb(${rgba.slice(0,3).join(",")})`;
            ctx.fillStyle=css;ctx.fillRect(0,0,side,side);draw(ctx,mask);
            const actual=ctx.getImageData(0,0,side,side).data;
            for(let y=0;y<side;y++)for(let x=0;x<side;x++){
              const sx=Math.floor(x*360/side)-130,sy=Math.floor(y*360/side)-25,d=(y*side+x)*4;
              if(sx<0||sx>=100||sy<0||sy>=46){
                if(actual[d]!==rgba[0]||actual[d+1]!==rgba[1]||actual[d+2]!==rgba[2])throw Error("Outside region changed");
                continue;
              }
              const s=(sy*100+sx)*4,m=pack(raw.subarray(s,s+4));
              if(!m){
                if(actual[d]!==rgba[0]||actual[d+1]!==rgba[1]||actual[d+2]!==rgba[2])throw Error("Black matte remains");
                blackUnchanged++;
              }else if(m!==65535){
                if(actual[d]<rgba[0]||actual[d+1]<rgba[1]||actual[d+2]<rgba[2])throw Error("Dark fringe");
                grayBlended++;
              }
            }
            if(bg===0){
              const corrected=Array.from(actual);ctx.fillStyle=css;ctx.fillRect(0,0,side,side);draw(ctx,mask,"legacy");
              if(ctx.getImageData(0,0,side,side).data.some((v,i)=>v!==corrected[i]))throw Error("Original black-screen appearance changed");
            }
            checks++;
          }
        }
      }
      // Underlying eye/pupil pixels and local color changes survive zero mask.
      const c=make(360),ctx=c.getContext("2d"),mask=decoder.frame(0);
      ctx.fillStyle="#00ff00";ctx.fillRect(0,0,360,360);ctx.fillStyle="#000";ctx.fillRect(150,25,10,46);
      const base=ctx.getImageData(0,0,360,360).data.slice();draw(ctx,mask);
      const actual=ctx.getImageData(0,0,360,360).data,raw=mask.getContext("2d").getImageData(0,0,100,46).data;
      for(let y=0;y<46;y++)for(let x=0;x<100;x++){
        const s=(y*100+x)*4,d=((y+25)*360+x+130)*4;
        if(!pack(raw.subarray(s,s+4))&&actual.slice(d,d+4).some((v,i)=>v!==base[d+i]))throw Error("Underlying expression changed");
      }
      return {frames:a.frames,sizes:[360,480],backgrounds:colors.length,checks,blackUnchanged,grayBlended,fingerprint:hash};
    });
    assert.equal(result.frames,50);assert(result.blackUnchanged>0&&result.grayBlended>0);
    const nativeResult=process.argv[5]||process.env.LISTEN_OVERLAY_NATIVE_JSON;
    if(nativeResult)assert.equal(result.fingerprint,JSON.parse(await fs.readFile(nativeResult,"utf8")).fingerprint);
    await page.locator("#time").fill("700");await page.locator("#time").dispatchEvent("input");
    assert.notEqual(await page.locator("#before").evaluate(c=>c.toDataURL()),await page.locator("#after").evaluate(c=>c.toDataURL()));
    await page.screenshot({path:path.join(out,"listen-overlay-desktop.png"),fullPage:true});
    await page.locator("#listening").click();
    assert.equal(await page.locator("#before").evaluate(c=>c.toDataURL()),await page.locator("#after").evaluate(c=>c.toDataURL()));
    await page.locator("#listening").click();
    for(const key of ["happy","thinking","sad"]){await page.locator("#semantic").selectOption(key);assert.notEqual(await page.locator("#before").evaluate(c=>c.toDataURL()),await page.locator("#after").evaluate(c=>c.toDataURL()));}
    await page.locator("#side").selectOption("480");assert.equal(await page.locator("#after").evaluate(c=>c.width),480);
    await page.setViewportSize({width:390,height:844});
    await page.locator("#semantic").selectOption("idle");
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:path.join(out,"listen-overlay-mobile.png"),fullPage:true});
    assert.deepEqual(errors,[]);assert(requests.every(u=>u.startsWith("file:")||u.startsWith("data:")));
    const summary={status:"passed",...result,controls:true,exitRestart:true,desktop:true,mobile:true,offline:true};
    await fs.writeFile(path.join(out,"listen-overlay-browser.json"),JSON.stringify(summary,null,2));console.log(JSON.stringify(summary));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
