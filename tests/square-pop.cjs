"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs/promises"),path=require("node:path"),{pathToFileURL}=require("node:url");
const {chromium}=require(process.argv[2]||"playwright");
(async()=>{
  const repo=path.resolve(__dirname,".."),out=path.join(repo,".test-output/square-pop");await fs.mkdir(out,{recursive:true});
  const manifest=JSON.parse(await fs.readFile(path.join(repo,"assets/square-pop/manifest.json")));
  const binary=await fs.readFile(path.join(repo,"assets/square-pop/square-pop.afm"));
  assert.equal(require("node:crypto").createHash("sha256").update(binary).digest("hex"),manifest.binary_sha256);
  assert.equal(binary.length,manifest.binary_bytes);assert.equal(Object.keys(manifest.clips).length,21);
  assert.deepEqual(manifest.aliases,{neutral:"idle",sleepy:"tried",laughing:"happy",crying:"sad",question:"silly",insert:"silly",delicious:"funny",eat:"funny"});
  assert.equal(manifest.authored_transitions,true);
  for(const [alias,target] of Object.entries(manifest.aliases))assert.equal(Object.hasOwn(manifest.clips,alias),false);
  const crypto=require('node:crypto'),zlib=require('node:zlib');
  const receipt=JSON.parse(await fs.readFile(path.join(repo,'output/imagegen/airboat-square-pop-20261124/inputs/soft-square-idle.json')));
  const exported=await fs.readFile(path.join(repo,'output/imagegen/airboat-square-pop-20261124/inputs',receipt.binary));
  assert.equal(crypto.createHash('sha256').update(exported).digest('hex'),receipt.sha256);
  assert.equal(crypto.createHash('sha256').update(await fs.readFile(path.join(repo,'docs/product/expression-square-idle.js'))).digest('hex'),receipt.renderer_sha256);
  assert.equal(manifest.default_source_sha256,receipt.sha256);
  const acceptedMasks=zlib.gunzipSync(exported),maskCache=new Map();
  const decodeMask=ref=>{
    const out=Buffer.alloc(480*480);if(!ref)return out;
    const [id,x,y,r,b,flip]=ref,s=manifest.sprites[id];
    assert.equal(s.w,r-x);assert.equal(s.h,b-y);
    if(!maskCache.has(id)){
      const values=[];let at=16+s.offset,end=at+s.bytes;
      while(at<end){const token=binary[at++],v=token>>4;let n=(token&15)+1;if(n===16)n+=binary[at++];for(let j=0;j<n;j++)values.push(v)}
      assert.equal(values.length,s.w*s.h);maskCache.set(id,values);
    }
    const values=maskCache.get(id);
    for(let row=0;row<s.h;row++)for(let col=0;col<s.w;col++)out[(y+row)*480+x+col]=values[row*s.w+(flip?s.w-1-col:col)];
    return out;
  };
  assert.equal(manifest.clips.idle.keyframes.length,receipt.frames);
  for(const [i,f] of manifest.clips.idle.keyframes.entries())for(let layer=0;layer<2;layer++){
    const expected=acceptedMasks.subarray((i*2+layer)*480*480,(i*2+layer+1)*480*480);
    const left=decodeMask(f.layers[layer]),right=decodeMask(f.layers[layer+2]);
    const actual=Buffer.from(left.map((v,j)=>Math.max(v,right[j])));
    assert(actual.equals(expected),'Approved idle layer changed: '+i+'/'+layer);
  }
  for(const [key,clip] of Object.entries(manifest.clips)){
    assert.equal(clip.entry_keyframes.length,manifest.transition_frames);
    assert.equal(clip.exit_keyframes.length,manifest.transition_frames);
    for(const {layers,accent} of [...clip.keyframes,...clip.entry_keyframes,...clip.exit_keyframes]){
    assert.equal(layers.length,4);
    for(const r of [...layers,accent].filter(Boolean)){
      assert(r.length===6&&r[0]>=0&&r[0]<manifest.sprites.length&&r[1]>=0&&r[2]>=0&&r[3]>r[1]&&r[4]>r[2]&&r[3]<=480&&r[4]<=480,key+": "+r);
    }
    }
  }
  const browser=await chromium.launch({executablePath:process.argv[3],headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1260,height:1000},reducedMotion:"reduce"});
    const errors=[],network=[];page.on("pageerror",e=>errors.push(e.message));page.on("request",r=>network.push(r.url()));
    await page.goto(pathToFileURL(path.join(repo,"docs/product/expression-square-review.html")).href+"#funny");
    const stats=await page.evaluate(()=>{
      const p=AIRBOAT_SQUARE_PACK,d=AIRBOAT_EXPRESSIONS;
      const base=new AirboatEaf(d.assets[d.square.idle.file]).frame(0).toDataURL();
      const stats={frames:0,changed:0,anchors:0,blackPupilFrames:0,minWhitePixels:Infinity,clipStats:{},transitionSteps:{}};
      const equal=(a,b)=>a.toDataURL()===b.toDataURL();
      const defaults=new AirboatEaf(d.assets[d.square.idle.file]);
      for(let i=0;i<p.clips.idle.body_frames;i++){
        const pixels=defaults.frame(p.transition_frames+i).getContext('2d').getImageData(0,0,480,480).data;
        for(let y=0;y<480;y++)for(let x=0;x<240;x++)for(let c=0;c<3;c++)
          if(pixels[(y*480+x)*4+c]!==pixels[(y*480+479-x)*4+c])throw Error('Default is not symmetric: '+i);
      }
      const pixels=defaults.frame(0).getContext("2d").getImageData(0,0,480,480).data;
      for(let y=0;y<480;y++)for(let x=0;x<240;x++)for(let c=0;c<3;c++)
        if(pixels[(y*480+x)*4+c]!==pixels[(y*480+479-x)*4+c])throw Error("Default is not symmetric");
    for(const key of Object.keys(p.clips)){
        const profile=d.square[key],asset=d.assets[profile.file],decoder=new AirboatEaf(asset),[start,end]=profile.range;
        if(decoder.frame(0).toDataURL()!==base||decoder.frame(asset.frames-1).toDataURL()!==base)throw Error("Shared anchors: "+key);
        if(!equal(decoder.frame(start-1),decoder.frame(start))||!equal(decoder.frame(end-1),decoder.frame(end)))throw Error("Phase boundary: "+key);
        if(!equal(decoder.frame(start),decoder.frame(end-1)))throw Error("Loop mismatch: "+key);
        const anchor=decoder.frame(start).toDataURL();let changed=false,minWhite=Infinity,maxWhite=0,maxBlack=0;
        let previousWhite=null,maxWhiteChange=0,entryMinWhite=Infinity;
        for(let i=0;i<asset.frames;i++){
          const canvas=decoder.frame(i);stats.frames++;
          if(canvas.width!==480||canvas.height!==480)throw Error("Canvas dimensions: "+key);
          if(i<start){
            const rgba=canvas.getContext("2d").getImageData(0,0,480,480).data;
            const white=new Uint8Array(480*480);let count=0,difference=0,union=0;
            for(let q=0;q<white.length;q++){
              white[q]=Math.min(rgba[q*4],rgba[q*4+1],rgba[q*4+2])>246?1:0;count+=white[q];
              if(previousWhite){difference+=white[q]!==previousWhite[q]?1:0;union+=white[q]||previousWhite[q]?1:0;}
            }
            entryMinWhite=Math.min(entryMinWhite,count);
            if(previousWhite)maxWhiteChange=Math.max(maxWhiteChange,difference/Math.max(1,union));
            previousWhite=white;
          }
          if(i<start||i>=end)continue;
          if(!changed&&canvas.toDataURL()!==anchor)changed=true;
          const data=canvas.getContext("2d").getImageData(0,0,480,480).data;let white=0,black=0;
          for(let q=0;q<data.length;q+=4){
            if(data[q]>246&&data[q+1]>246&&data[q+2]>246)white++;
            if(Math.max(data[q],data[q+1],data[q+2])<9)black++;
          }
          minWhite=Math.min(minWhite,white);maxWhite=Math.max(maxWhite,white);maxBlack=Math.max(maxBlack,black);
          if(black>50)stats.blackPupilFrames++;
          if(key==='silly'&&i>=start&&i<end){
            const green=[Math.floor(0x28/8)*255/31|0,Math.floor(0xcf/4)*255/63|0,Math.floor(0x60/8)*255/31|0];
            for(const [x,y] of [[0,0],[479,0],[0,479],[479,479]]){
              const at=(y*480+x)*4;
              if(data[at]!==green[0]||data[at+1]!==green[1]||data[at+2]!==green[2])throw Error('俏皮背景发生变化: '+i);
            }
          }
        }
        if(!changed)throw Error("Frozen animation: "+key);
        if(minWhite<400)throw Error("Eyes disappear: "+key);
        if(maxWhite>190000)throw Error("The white background was misidentified as eyes: "+key);
        if(maxBlack<80)throw Error("Pupils missing: "+key);
        if(entryMinWhite<1500||maxWhiteChange>.58)throw Error("Abrupt or vanishing entry: "+key+" "+maxWhiteChange);
        stats.transitionSteps[key]={minWhitePixels:entryMinWhite,maxWhiteChange:+maxWhiteChange.toFixed(4)};
        stats.clipStats[key]={minWhite,maxWhite,maxBlack};stats.minWhitePixels=Math.min(stats.minWhitePixels,minWhite);stats.changed++;stats.anchors++;
      }
      if(d.square.neutral.file!==d.square.idle.file||d.square.sleepy.file!==d.square.tried.file)throw Error("Aliases do not share one file");
      return stats;
    });
    assert.equal(await page.locator("#cards button").count(),28);assert.equal(await page.locator("#repertoire option").count(),28);
    await page.waitForFunction(()=>[...document.querySelectorAll('#cards img')].length===28&&[...document.querySelectorAll('#cards img')].every(i=>i.complete&&i.naturalWidth===480));
    await page.locator('#repertoire').selectOption('sleepy');
    assert.equal(await page.locator('#new-label').textContent(),'困倦');
    assert.equal(await page.locator('#native-link').getAttribute('href'),'../../output/imagegen/airboat-square-pop-20261124/preview/tried.gif');
    await page.locator('#repertoire').selectOption('tried');
    assert.equal(await page.locator('#new-label').textContent(),'疲惫');
    for(const [alias,target] of Object.entries(manifest.aliases))assert.equal(await page.evaluate(([a,b])=>AIRBOAT_EXPRESSIONS.square[a].file===AIRBOAT_EXPRESSIONS.square[b].file,[alias,target]),true);
    for(const k of ["thinking","question","beat_swing","funny","tried","crying"]){
      await page.locator("#repertoire").selectOption(k);await page.locator("#time").fill("1000");await page.locator("#time").dispatchEvent("input");
      await page.locator(".stage").screenshot({path:path.join(out,k+"-desktop.png")});
    }
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:path.join(out,"mobile.png"),fullPage:true});
    await page.locator("#repertoire").selectOption("funny");
    const still=await page.locator("#new-face").evaluate(c=>c.toDataURL());
    await page.locator("#play").click();await page.waitForFunction(v=>document.querySelector("#new-face").toDataURL()!==v,still);
    const sources=[["library",path.join(repo,"docs/product/expression-workbench.html")]];
    if(process.argv[4])sources.push(["airboat",path.resolve(process.argv[4])]);
    for(const [label,file] of sources){
      await page.setViewportSize({width:1280,height:1000});
      await page.goto(pathToFileURL(file).href+"?square=funny#expressions");
      await page.waitForSelector("#compare[open]");
      assert.equal(await page.locator("#compare-variant").inputValue(),"square");
      await page.locator("#compare-time").fill("1000");await page.locator("#compare-time").dispatchEvent("input");
      await page.screenshot({path:path.join(out,label+"-compare.png")});
      await page.locator("#compare-close").click();
      assert.equal(await page.locator('[data-version="square"]').getAttribute("aria-pressed"),"true");
      assert.equal(await page.locator(".node.semantic-color").count(),29);
      await page.locator('[data-node="semantic:sleepy"]').evaluate(b=>b.click());assert.match(await page.locator("#metadata").textContent(),/square-tried\.afm/);
      await page.locator('[data-node="semantic:tried"]').evaluate(b=>b.click());assert.match(await page.locator("#metadata").textContent(),/square-tried\.afm/);
      await page.locator('[data-version="contour"]').click();assert.equal(await page.locator(".node.semantic-color").count(),29);
      await page.locator('[data-version="square"]').click();
      await page.setViewportSize({width:390,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.screenshot({path:path.join(out,label+"-mobile.png")});
    }
    assert.deepEqual(errors,[]);assert(network.every(u=>u.startsWith("file:")||u.startsWith("data:")),"External request");
    const result={status:"passed",...stats,performances:21,compatibleSemantics:29,approvedDefaultFrames:receipt.frames,approvedDefaultLayerPixels:acceptedMasks.length,approvedDefaultSha256:receipt.sha256,offline:true,desktop:true,mobile:true,playback:true,workbenches:sources.map(s=>s[0]),sha256:manifest.binary_sha256,totalBytes:manifest.binary_bytes+manifest.catalog_bytes};
    await fs.writeFile(path.join(out,"validation.json"),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
