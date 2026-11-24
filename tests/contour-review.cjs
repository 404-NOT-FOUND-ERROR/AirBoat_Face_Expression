"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs/promises"),path=require("node:path");
const {pathToFileURL}=require("node:url"),{chromium}=require(process.argv[2]||"playwright");
(async()=>{
  const packPath=path.resolve(__dirname,"../assets/contour-review");
  const catalog=await fs.readFile(path.join(packPath,"manifest.json"));
  const manifest=JSON.parse(catalog),binary=await fs.readFile(path.join(packPath,"contour-review.afm"));
  assert.equal(catalog.length,manifest.catalog_bytes);assert.equal(binary.length,manifest.binary_bytes);
  assert.equal(require("node:crypto").createHash("sha256").update(binary).digest("hex"),manifest.binary_sha256);
  assert.equal(Object.keys(manifest.clips).length,27);
  assert.deepEqual(manifest.aliases,{neutral:"idle",sleepy:"tried"});
  assert(!manifest.clips.sleepy);
  for(const [key,count] of [["thinking",63],["question",61],["beat_swing",75],["funny",50],["tried",101]])
    assert.equal(manifest.clips[key].body_frames,count,"Preserve the established score: "+key);
  assert.deepEqual(manifest.beats.thinking,[[160,"先抬眼"],[400,"眼形跟上"],[840,"停下来想"],[1640,"慢眨"],[1880,"收回视线"]]);
  const idleAnchor=manifest.clips.idle.keyframes[0];
  // The shared transition anchor stays pixel-identical across idle revisions.
  const lidHash="8cda7e56087b4017dd934e2c0267159c0fbf5ecaecf68f2eedc0ce7d7df0f455";
  const pupilHash="3ac07936de3fd5fc65eb4894e0f75faf54b60646b98db257274fa5f27e77d6b2";
  assert.equal(manifest.clips.idle.color,"#28cf60");
  assert.deepEqual(idleAnchor.layers.map(([id,...box])=>[manifest.sprites[id].sha256,...box]),[
    [lidHash,65,143,235,325,0],[pupilHash,105,222,195,306,0],
    [lidHash,245,143,415,325,1],[pupilHash,285,222,375,306,1]
  ]);
  for(const [key,clip] of Object.entries(manifest.clips)) for(const frame of clip.keyframes){
    assert.equal(frame.layers.length,4);
    for(const ref of [...frame.layers,frame.accent].filter(Boolean)){
      const [id,x,y,r,b,flip]=ref;
      assert(manifest.sprites[id]&&x>=0&&y>=0&&x<r&&y<b&&r<=480&&b<=480&&(flip===0||flip===1),`${key}: ${ref}`);
    }
  }
  const left=manifest.clips.look_left,right=manifest.clips.look_right;
  const mirrorRef=ref=>{
    if(!ref)return null;
    const [id,x,y,r,b,flip]=ref;
    return [id,480-r,y,480-x,b,flip^1];
  };
  assert.equal(left.color,right.color);
  assert.equal(left.body_frames,right.body_frames);
  assert.deepEqual(right.keyframes,left.keyframes.map(({layers,accent})=>({
    layers:[layers[2],layers[3],layers[0],layers[1]].map(mirrorRef),accent:mirrorRef(accent)
  })));
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
          const idleFrame=key==="idle"?AIRBOAT_CONTOUR_PACK.clips.idle.keyframes[i-start]:null;
          const centered=idleFrame && JSON.stringify(idleFrame.layers[3])===JSON.stringify(idleFrame.layers[1]&&
            [idleFrame.layers[1][0],480-idleFrame.layers[1][3],idleFrame.layers[1][2],
             480-idleFrame.layers[1][1],idleFrame.layers[1][4],idleFrame.layers[1][5]^1]);
          let white=0,lastLeft=-1,firstRight=480;
          for(let y=0;y<480;y++)for(let x=0;x<480;x++){
            const at=(y*480+x)*4,r=image[at],g=image[at+1],b=image[at+2];
            if(key==="idle"){
              const m=(y*480+479-x)*4;
              if(centered && (image[at]!==image[m]||image[at+1]!==image[m+1]||image[at+2]!==image[m+2]))throw Error("Centered idle asymmetry: "+i);
              if(r>245&&g>245&&b>245){white++;if(x<240)lastLeft=Math.max(lastLeft,x);else firstRight=Math.min(firstRight,x);}
            }else if(key==="shocked"&&y>=394&&r>245&&g>245&&b>245)stats.shockPixelsBelow394++;
          }
          if(key==="idle"){
            if(centered)stats.idleSymmetricFrames++;
            stats.minCentralGap=Math.min(stats.minCentralGap,firstRight-lastLeft-1);
            stats.minWhitePixels=Math.min(stats.minWhitePixels,white);stats.maxWhitePixels=Math.max(stats.maxWhitePixels,white);
          }
        }
        if(!changed)throw Error("No performance motion: "+key);
      }
      if(data.contour.neutral.file!==data.contour.idle.file)throw Error("Missing neutral alias");
      if(data.contour.sleepy.file!==data.contour.tried.file||data.contour.sleepy.beats!==data.contour.tried.beats)
        throw Error("Sleepy and tired must share the same performance and beat markers");
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
      const p=AIRBOAT_CONTOUR_PACK;
      const idleAt=ms=>p.clips.idle.keyframes[Math.round(ms/40)].layers;
      const closed=[1560,4080].map(ms=>{
        const pixels=read(d.frame(data.contour.idle.range[0]+Math.round(ms/40)));
        let black=0;
        for(let i=0;i<pixels.length;i+=4)if(pixels[i]<4&&pixels[i+1]<4&&pixels[i+2]<4)black++;
        return black;
      });
      if(closed.some(Boolean))throw Error("Pupil remains visible through fully closed lid");
      const centerX=r=>(r[1]+r[3])/2, height=r=>r[4]-r[2];
      const initial=idleAt(0), gaze=[560,2640].map(ms=>[1,3].map(i=>centerX(idleAt(ms)[i])-centerX(initial[i])));
      if(!gaze[0].every(x=>x>=10)||!gaze[1].every(x=>x<=-9)||
         JSON.stringify(idleAt(560)[0])!==JSON.stringify(initial[0]))throw Error("Idle lost the pupil lead or coherent gaze");
      const idleOpening=[1560,1880,4080,4280,4560,4720].map(ms=>height(idleAt(ms)[0]));
      if(!(idleOpening[0]<14&&idleOpening[1]>height(initial[0])&&idleOpening[2]<14&&
           idleOpening[3]>160&&idleOpening[4]<25&&idleOpening[5]>160))throw Error("Idle lost the blink, rebound, or double blink");
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
      const laugh=p.clips.laughing, laughAt=ms=>laugh.keyframes[Math.round(ms/40)];
      const laughY=ms=>{
        const r=laughAt(ms).layers[0];return (r[2]+r[4])/2;
      };
      const laughMotion=[400,480,640,840,1040].map(laughY);
      const laughGap=Math.min(...laugh.keyframes.map(f=>f.layers[2][1]-f.layers[0][3]));
      // The idle reference bounds include the low-coverage antialiasing fringe.
      if(laughGap<10||laughAt(400).layers[2][1]-laughAt(400).layers[0][3]<48)
        throw Error("Laughing eyes crowd the center");
      if(!(laughMotion[1]>laughMotion[0]&&laughMotion[2]<laughMotion[0]&&laughMotion[3]>laughMotion[0]&&
           laughMotion[4]<laughMotion[0]&&laughMotion[4]>laughMotion[2]))throw Error("Laughing lost the lighter second rebound");
      if(!laugh.keyframes.some(f=>f.accent)||laugh.keyframes[0].accent||laugh.keyframes.at(-1).accent)
        throw Error("Laughing hearts must appear and settle");
      const settled=laughAt(1440).layers;
      if(settled[0][0]!==settled[2][0]||settled[0][5]===settled[2][5])throw Error("Laughing arcs lost reflected sharing");
      const laughPreview=data.contour.laughing;
      const laughDecoder=new AirboatEaf(data.assets[laughPreview.file]);
      const laughBlack=ms=>{
        const image=read(laughDecoder.frame(laughPreview.range[0]+Math.round(ms/40)));
        let black=0;
        for(let y=140;y<330;y++)for(let x=60;x<238;x++){
          const i=(y*480+x)*4;
          if(Math.max(image[i],image[i+1],image[i+2])<4)black++;
        }
        return black;
      };
      const pupilCoverage=[0,80,200,240,280,400,1800,1880,2040].map(laughBlack);
      if(laughAt(80).layers[1][2]>=laughAt(0).layers[1][2]||
         pupilCoverage[1]!==pupilCoverage[0]||
         !(pupilCoverage[1]>pupilCoverage[2]&&pupilCoverage[2]>pupilCoverage[3]&&
           pupilCoverage[3]>pupilCoverage[4]&&pupilCoverage[4]>0&&pupilCoverage[5]===0&&
           pupilCoverage[6]>0&&pupilCoverage[7]>pupilCoverage[6]&&pupilCoverage[8]===pupilCoverage[0]))
        throw Error("Laughing pupil must lift, occlude, and reopen with the lid");
      const anchorPose=p.clips.idle.keyframes[0];
      if(JSON.stringify(laugh.keyframes[0])!==JSON.stringify(anchorPose)||
         JSON.stringify(laugh.keyframes.at(-1))!==JSON.stringify(anchorPose))
        throw Error("Laughing must enter and leave through the green idle geometry");
      const revisions=["thinking","question","beat_swing","funny","relaxed","confident","tried","sad","crying"];
      const restored=["thinking","question","beat_swing","funny","tried"];
      const maxPupilStep={};
      for(const key of revisions){
        const {keyframes}=p.clips[key];
        if(JSON.stringify(keyframes[0])!==JSON.stringify(anchorPose)||JSON.stringify(keyframes.at(-1))!==JSON.stringify(anchorPose))
          throw Error("Expected a geometry-only transition from the shared anchor: "+key);
        let max=0;
        for(let i=0;i<keyframes.length;i++)for(const j of [1,3]){
          const ref=keyframes[i].layers[j], base=anchorPose.layers[j];
          if(!restored.includes(key) && (ref[0]!==base[0]||ref[5]!==base[5]||ref[3]-ref[1]!==base[3]-base[1]||ref[4]-ref[2]!==base[4]-base[2]))
            throw Error("Pupil shape changed instead of moving behind the eyelid: "+key);
          if(i){const prev=keyframes[i-1].layers[j];max=Math.max(max,Math.hypot(centerX(ref)-centerX(prev),
            (ref[2]+ref[4]-prev[2]-prev[4])/2));}
        }
        if(max>22)throw Error("Pupil jumps between frames: "+key+" "+max);
        maxPupilStep[key]=+max.toFixed(2);
      }
      const funnyWidth=(ms,eye)=>{const r=p.clips.funny.keyframes[Math.round(ms/40)].layers[eye*2];return r[3]-r[1]};
      if(funnyWidth(120,0)-funnyWidth(120,1)<16||funnyWidth(760,1)-funnyWidth(760,0)<35)
        throw Error("Goofy lost the original size swap");
      const tiredY=[0,1120,2160,2760].map(ms=>center("tried",ms,0,2));
      if(tiredY[1]-tiredY[0]<70||tiredY[1]-tiredY[2]<40||tiredY[3]-tiredY[2]<30)
        throw Error("Tired lost the deep drop, lift or sag");
      const tearRuns=[];
      for(const {accent} of p.clips.crying.keyframes){
        if(!accent){if(tearRuns.at(-1)?.length)tearRuns.push([]);continue;}
        if(!tearRuns.length)tearRuns.push([]);
        tearRuns.at(-1).push([(accent[1]+accent[3])/2,(accent[2]+accent[4])/2]);
      }
      const drops=tearRuns.filter(r=>r.length);
      if(drops.length!==2||drops[0][0][0]>=240||drops[1][0][0]<=240||drops.some(run=>run.at(-1)[1]-run[0][1]<35))
        throw Error("The crying performance must show two separate falling tears");
      return {...stats,alphaLevels:[...stats.alphaLevels].sort((a,b)=>a-b),closedPupilPixels:closed,
        anchorEndpoints:true,mirrorFrames,maxPupilStep,tearRuns:drops.map(r=>[r[0],r.at(-1)]),timing:{happyY:happy,dizzyOffsets:swing,lookEyePupilX:look,tiredY,
          laughY:laughMotion,laughMinGap:laughGap,laughPupilCoverage:pupilCoverage,idleOpening,gaze}};
    });
    await page.locator("#time").fill("1100");await page.locator("#time").dispatchEvent("input");
    await page.screenshot({path:path.join(out,"idle-open-desktop.png"),fullPage:true});
    await page.getByRole("button",{name:"慢眨一下",exact:true}).click();
    await page.screenshot({path:path.join(out,"idle-blink-desktop.png"),fullPage:true});
    await page.locator("#repertoire").selectOption("neutral");
    await page.getByRole("button",{name:"双眨·第二下",exact:true}).click();
    assert.equal(await page.locator("#clock").textContent(),"4.92 s");
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
    assert.equal(await page.locator('#repertoire option[value="sleepy"]').count(),1);
    await page.locator("#repertoire").selectOption("tried");
    await page.getByRole("button",{name:"费力抬眼",exact:true}).click();
    assert.equal(await page.locator("#clock").textContent(),"2.52 s");
    await page.locator("#repertoire").selectOption("laughing");
    await page.getByRole("button",{name:"月牙成形",exact:true}).click();
    assert.equal(await page.locator("#clock").textContent(),"0.76 s");
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
      assert.equal(await page.locator('[data-node="semantic:sleepy"]').count(),1);
      await page.locator('[data-node="semantic:tried"]').evaluate(b=>b.click());
      assert.match(await page.locator("#metadata").textContent(),/review-tried\.afm/);
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
