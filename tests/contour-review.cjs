"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs/promises"),path=require("node:path");
const {pathToFileURL}=require("node:url"),{chromium}=require(process.argv[2]||"playwright");
(async()=>{
  const packPath=path.resolve(__dirname,"../assets/contour-review");
  const catalog=await fs.readFile(path.join(packPath,"manifest.json"));
  const manifest=JSON.parse(catalog),binary=await fs.readFile(path.join(packPath,"contour-review.afm"));
  assert.equal(catalog.length,manifest.catalog_bytes);assert.equal(binary.length,manifest.binary_bytes);
  assert.equal(require("node:crypto").createHash("sha256").update(binary).digest("hex"),manifest.binary_sha256);
  assert.equal(Object.keys(manifest.clips).length,28);
  for(const [key,clip] of Object.entries(manifest.clips)) for(const frame of clip.keyframes){
    assert.equal(frame.layers.length,4);
    for(const ref of [...frame.layers,frame.accent].filter(Boolean)){
      const [id,x,y,r,b,flip]=ref;
      assert(manifest.sprites[id]&&x>=0&&y>=0&&x<r&&y<b&&r<=480&&b<=480&&(flip===0||flip===1),`${key}: ${ref}`);
    }
  }
  const browser=await chromium.launch({executablePath:process.argv[3],headless:true});
  const out=path.resolve(__dirname,"../.test-output/contour-review");await fs.mkdir(out,{recursive:true});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:1020},reducedMotion:"reduce"});
    const errors=[],requests=[];page.on("pageerror",e=>errors.push(e.message));page.on("request",r=>requests.push(r.url()));
    await page.goto(pathToFileURL(path.resolve(__dirname,"../docs/product/expression-contour-review.html")).href);
    const result=await page.evaluate(()=>{
      const data=AIRBOAT_EXPRESSIONS,stats={frames:0,loopAnchors:0,idleSymmetricFrames:0,minCentralGap:480,minWhitePixels:Infinity,maxWhitePixels:0,shockPixelsBelow394:0,alphaLevels:new Set()};
      const read=c=>c.getContext("2d", {willReadFrequently:true}).getImageData(0,0,480,480).data;
      const same=(a,b)=>a.toDataURL()===b.toDataURL();
      const d=new AirboatEaf(data.assets[data.contour.idle.file]),base=d.frame(0).toDataURL();
      for(const key of Object.keys(AIRBOAT_CONTOUR_PACK.clips)){
        const p=data.contour[key],a=data.assets[p.file],dec=new AirboatEaf(a);
        if(dec.frame(0).toDataURL()!==base||dec.frame(a.frames-1).toDataURL()!==base)throw Error("Shared review anchor: "+key);
        const [start,end]=p.range;
        if(!same(dec.frame(start-1),dec.frame(start))||!same(dec.frame(end-1),dec.frame(end)))throw Error("Transition jump: "+key);
        if(!same(dec.frame(start),dec.frame(end-1)))throw Error("Loop jump: "+key);
        stats.loopAnchors++;
        let changed=false;
        const anchor=read(dec.frame(start));
        for(let i=0;i<a.frames;i++){
          const c=dec.frame(i);stats.frames++;
          if(c.width!==480||c.height!==480)throw Error("Render dimensions: "+key);
          if(i<p.range[0]||i>=p.range[1])continue;
          if(!changed)changed=read(c).some((value,j)=>value!==anchor[j]);
          if(key!=="idle"&&key!=="shocked")continue;
          const image=read(c);
          let white=0,lastLeft=-1,firstRight=480;
          for(let y=0;y<480;y++)for(let x=0;x<480;x++){
            const at=(y*480+x)*4,r=image[at],g=image[at+1],b=image[at+2];
            if(key==="idle"){
              const m=(y*480+479-x)*4;
              if(image[at]!==image[m]||image[at+1]!==image[m+1]||image[at+2]!==image[m+2])throw Error("Idle asymmetry: "+i);
              if(r>245&&g>245&&b>245){white++;if(x<240)lastLeft=Math.max(lastLeft,x);else firstRight=Math.min(firstRight,x);}
            }else if(key==="shocked"&&y>=394&&r>245&&g>245&&b>245)stats.shockPixelsBelow394++;
          }
          if(key==="idle"){
            stats.idleSymmetricFrames++;stats.minCentralGap=Math.min(stats.minCentralGap,firstRight-lastLeft-1);
            stats.minWhitePixels=Math.min(stats.minWhitePixels,white);stats.maxWhitePixels=Math.max(stats.maxWhitePixels,white);
          }
        }
        if(!changed)throw Error("No performance motion: "+key);
      }
      if(data.contour.neutral.file!==data.contour.idle.file)throw Error("Missing neutral alias");
      const pair=["look_left","look_right"].map(key=>new AirboatEaf(data.assets[data.contour[key].file]));
      let mirrorFrames=0;
      for(let i=0;i<pair[0].asset.frames;i++){
        const a=read(pair[0].frame(i)),b=read(pair[1].frame(i));
        for(let y=0;y<480;y++)for(let x=0;x<480;x++){
          const j=(y*480+x)*4,k=(y*480+479-x)*4;
          if(a[j]!==b[k]||a[j+1]!==b[k+1]||a[j+2]!==b[k+2])throw Error("Directional mirror: "+i);
        }
        mirrorFrames++;
      }
      const maskProbe=new AirboatEaf(data.assets[data.contour.idle.file]);
      const pose=maskProbe.clip.keyframes[0],left=pose.layers.slice(0,2);
      const withRightPupil=pupil=>{
        const keyframe={layers:[...left,null,pupil],accent:null};
        return {a:keyframe,b:keyframe,u:0,to:"#bbff32",transition:false};
      };
      maskProbe.pose=()=>withRightPupil(left[1]);
      const clipped=maskProbe.frame(0);
      maskProbe.pose=()=>withRightPupil(null);
      if(!same(clipped,maskProbe.frame(1)))
        throw Error("Pupil re-used the previous eye's coverage");
      if(stats.minCentralGap<14)throw Error("Central bridge remains");
      if(stats.shockPixelsBelow394<1000)throw Error("Shock still clipped");
      if(stats.minWhitePixels>=stats.maxWhitePixels/4)throw Error("Blink did not close");
      const close=d.frame(data.contour.idle.range[0]+38),pixels=read(close);let black=0;
      for(let i=0;i<pixels.length;i+=4)if(pixels[i]<4&&pixels[i+1]<4&&pixels[i+2]<4)black++;
      if(black)throw Error("Pupil remains visible through fully closed lid");
      const p=AIRBOAT_CONTOUR_PACK;
      for(let i=0;i<p.sprites.length;i++){
        if(p.sprites[i].palette)continue;
        const c=AirboatContour.decodeSprite(i),rgba=c.getContext("2d").getImageData(0,0,c.width,c.height).data;
        for(let j=3;j<rgba.length;j+=4)stats.alphaLevels.add(rgba[j]);
      }
      if(stats.alphaLevels.size<8)throw Error("Coverage lost");
      const center=(key,ms,layer,axis)=>{
        const ref=p.clips[key].keyframes[Math.floor(ms/40)].layers[layer];
        return (ref[axis]+ref[axis+2])/2;
      };
      const happy=[0,320,520,760,960,1120].map(t=>center("happy",t,0,2));
      if(!(happy[1]-happy[0]>=10&&happy[0]-happy[2]>=30&&Math.abs(happy[3]-happy[2])<=6&&happy[4]-happy[5]>12))
        throw Error("Happy lost its squeeze, hold or second bounce");
      const dizzy=[0,520,720,880,1040,1200,1360].map(t=>center("confused",t,0,1));
      const swing=dizzy.slice(1).map(x=>x-dizzy[0]);
      if(!swing.every((x,i)=>Math.sign(x)===(i%2===0?1:-1)&&(!i||Math.abs(swing[i-1])>Math.abs(x))))
        throw Error("Dizzy lost alternating, diminishing aftershocks");
      const look=[0,200,640,2120,2520].map(t=>[center("look_around",t,0,1),center("look_around",t,1,1)]);
      if(look[1][0]!==look[0][0]||look[1][1]-look[0][1]>-25||look[2][0]-look[1][0]>-12||
         look[3][0]-look[2][0]>4||look[3][1]-look[2][1]<45||look[4][0]-look[3][0]<23)
        throw Error("Look lost the pupil lead");
      const laugh=p.clips.laughing, laughY=ms=>{
        const r=laugh.keyframes[Math.round(ms/40)].layers[0];return (r[2]+r[4])/2;
      };
      const laughMotion=[0,160,360,560,760,1200].map(laughY);
      const laughGap=Math.min(...laugh.keyframes.map(f=>f.layers[2][1]-f.layers[0][3]));
      if(laughGap<48||laugh.keyframes.some(f=>f.layers[0][3]-f.layers[0][1]>150))
        throw Error("Laughing eyes crowd the center");
      if(!(laughMotion[1]>laughMotion[0]&&laughMotion[2]<laughMotion[0]&&laughMotion[3]>laughMotion[0]&&
           laughMotion[4]<laughMotion[0]&&laughMotion[4]>laughMotion[2]))throw Error("Laughing lost the lighter second rebound");
      if(!laugh.keyframes.some(f=>f.accent)||laugh.keyframes[0].accent||laugh.keyframes.at(-1).accent)
        throw Error("Laughing hearts must appear and settle");
      const settled=laugh.keyframes.at(-1).layers;
      if(settled[0][0]!==settled[2][0]||settled[0][5]===settled[2][5])throw Error("Laughing arcs lost reflected sharing");
      return {...stats,alphaLevels:[...stats.alphaLevels].sort((a,b)=>a-b),closedPupilPixels:black,
        anchorEndpoints:true,mirrorFrames,timing:{happyY:happy,dizzyOffsets:swing,lookEyePupilX:look,laughY:laughMotion,laughMinGap:laughGap}};
    });
    await page.locator("#time").fill("1100");await page.locator("#time").dispatchEvent("input");
    await page.screenshot({path:path.join(out,"idle-open-desktop.png"),fullPage:true});
    await page.locator("#time").fill("1880");await page.locator("#time").dispatchEvent("input");
    await page.screenshot({path:path.join(out,"idle-blink-desktop.png"),fullPage:true});
    await page.locator("[data-mode=shocked]").click();
    await page.locator("#time").fill("1080");await page.locator("#time").dispatchEvent("input");
    await page.screenshot({path:path.join(out,"shocked-desktop.png"),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:path.join(out,"shocked-mobile.png"),fullPage:true});
    for(const [mode,beat,seconds] of [["happy","弹起","0.88 s"],["confused","余震","1.24 s"],["look_around","先看左","0.56 s"]]){
      await page.locator(`[data-mode=${mode}]`).click();
      await page.getByRole("button",{name:beat,exact:true}).click();
      assert.equal(await page.locator("#clock").textContent(),seconds);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      const original=await page.locator("#old-face").evaluate(c=>c.toDataURL());
      await page.locator("#reference").selectOption("optimized");
      await page.getByRole("button",{name:beat,exact:true}).click();
      assert.notEqual(await page.locator("#old-face").evaluate(c=>c.toDataURL()),original);
      await page.locator("#reference").selectOption("original");
      await page.getByRole("button",{name:beat,exact:true}).click();
      await page.screenshot({path:path.join(out,mode+"-mobile.png"),fullPage:true});
    }
    await page.getByRole("button",{name:"先看右",exact:true}).click();
    await page.screenshot({path:path.join(out,"look-mobile.png"),fullPage:true});
    await page.setViewportSize({width:1280,height:1020});
    await page.screenshot({path:path.join(out,"look-desktop.png"),fullPage:true});
    await page.locator("#speed").selectOption(".5");
    const before=await page.locator("#new-face").evaluate(c=>c.toDataURL());
    await page.locator("#play").click();
    await page.waitForFunction(before=>document.querySelector("#new-face").toDataURL()!==before,before);
    await page.locator("#play").click();await page.locator("#restart").click();
    assert.equal(await page.locator("#repertoire option").count(),29);
    await page.locator("#repertoire").selectOption("thinking");
    await page.getByRole("button",{name:"慢眨",exact:true}).click();
    assert.equal(await page.locator("#clock").textContent(),"2.00 s");
    const sheet=await page.evaluate(()=>{
      const out=document.createElement("canvas"); out.width=936;out.height=804;
      const ctx=out.getContext("2d");ctx.fillStyle="#141619";ctx.fillRect(0,0,out.width,out.height);
      ctx.font="14px system-ui";
      const keys=[...document.querySelector("#repertoire").options].filter(n=>n.value!=="neutral");
      for(const [i,n] of keys.entries()){
        const p=AIRBOAT_EXPRESSIONS.contour[n.value],a=AIRBOAT_EXPRESSIONS.assets[p.file];
        const body=p.range[1]-p.range[0], mark=p.beats?.[1]?.[0];
        const frame=p.range[0]+(mark===undefined ? Math.floor(body/2) : Math.floor(mark*p.fps/1000));
        const x=14+i%7*132,y=14+Math.floor(i/7)*196;
        ctx.drawImage(new AirboatEaf(a).frame(frame),x,y,116,116);
        ctx.fillStyle="#eee";ctx.fillText(n.textContent,x,y+141);
        ctx.fillStyle="#a6a9ae";ctx.fillText(n.value,x,y+163);
      }
      return out.toDataURL().split(",")[1];
    });
    await fs.writeFile(path.join(out,"repertoire.png"),Buffer.from(sheet,"base64"));
    const workbenches=process.argv[4] ? [["airboat",path.resolve(process.argv[4])]] : [];
    workbenches.unshift(["library",path.resolve(__dirname,"../docs/product/expression-workbench.html")]);
    for(const [label,source] of workbenches){
      await page.goto(pathToFileURL(source).href+"?micro=look_around");
      await page.waitForSelector("#compare[open]");
      assert.equal(await page.locator("#compare-variant").inputValue(),"contour");
      await page.locator("#compare-reference").selectOption("optimized");
      await page.locator('#compare-stages [data-phase="performance"]').click();
      await page.locator("#compare-time").fill("1000");
      await page.screenshot({path:path.join(out,label+"-comparison.png")});
      await page.locator("#compare-close").click();
      assert.equal(await page.locator('[data-version="contour"]').getAttribute("aria-pressed"),"true");
      assert.equal(await page.locator('[data-node="semantic:look_around"]').getAttribute("aria-pressed"),"true");
      assert.equal(await page.locator(".node.semantic-color").count(),29);
      await page.locator('[data-node="semantic:listening"]').evaluate(b=>b.click());
      assert.match(await page.locator("#metadata").textContent(),/review-listening\.afm/);
      assert.doesNotMatch(await page.locator("#metadata").textContent(),/listen\.eaf/);
      await page.locator('[data-node="semantic:look_left"]').evaluate(b=>b.click());
      await page.locator("#frames").fill("24");
      const canonical=await page.locator("#face").evaluate(c=>c.toDataURL());
      await page.locator("#mirror").selectOption("off");
      assert.equal(await page.locator("#face").evaluate(c=>c.toDataURL()),canonical);
      await page.locator("#mirror").selectOption("on");
      assert.notEqual(await page.locator("#face").evaluate(c=>c.toDataURL()),canonical);
      await page.locator("#compare-open").click();
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.locator("#compare").evaluate(d=>d.scrollWidth>d.clientWidth),false);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.locator("#compare-close").click();
      await page.screenshot({path:path.join(out,label+"-workbench-mobile.png"),fullPage:true});
      await page.setViewportSize({width:1280,height:1020});
    }
    assert.deepEqual(errors,[]);assert(requests.every(u=>u.startsWith("file:")||u.startsWith("data:")));
    const summary={status:"passed",...result,semantics:29,desktop:true,mobile:true,offline:true,playback:true,workbenches:workbenches.map(([label])=>label)};
    await fs.writeFile(path.join(out,"validation.json"),JSON.stringify(summary,null,2));console.log(JSON.stringify(summary));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
