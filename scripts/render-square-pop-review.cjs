"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),{pathToFileURL}=require("node:url");
const {chromium}=require(process.env.AIRBOAT_SQUARE_PLAYWRIGHT||"playwright");
const repo=path.resolve(__dirname,".."),art=path.join(repo,"output/imagegen/airboat-square-pop-20261124");
const python=process.env.AIRBOAT_SQUARE_PYTHON||"python";
const encode="import base64,io,json,sys\nfrom PIL import Image\nf=[Image.open(io.BytesIO(base64.b64decode(x))).convert('RGB') for x in json.load(sys.stdin)]\nf[0].save(sys.argv[1],save_all=True,append_images=f[1:],duration=[40]*(len(f)-1)+[350],loop=0,optimize=True)";
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.AIRBOAT_SQUARE_BROWSER,headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:1100},reducedMotion:"reduce"});
    await page.goto(pathToFileURL(path.join(repo,"docs/product/expression-square-review.html")).href+"#funny");
    const collection=await page.evaluate(()=>{
      const pack=AIRBOAT_SQUARE_PACK,data=AIRBOAT_EXPRESSIONS;
      const names=[...document.querySelector("#repertoire").options].map(n=>[n.value,n.textContent]);
      const make=(w,h)=>Object.assign(document.createElement("canvas"),{width:w,height:h});
      const sheet=make(1050,768),s=sheet.getContext("2d");s.fillStyle="#101114";s.fillRect(0,0,1050,768);
      s.font="14px system-ui";s.fillStyle="#f5f5ef";
      const image=c=>c.toDataURL().split(",")[1];
      for(const [i,[key,label]] of names.entries()){
        const p=data.square[key],a=data.assets[p.file],dec=new AirboatEaf(a);
        const frame=p.range[0]+Math.round((p.range[1]-p.range[0])*.38);
        const x=6+i%7*150,y=8+Math.floor(i/7)*192;
        s.drawImage(dec.frame(frame),x,y,138,138);s.fillText(label,x,y+159);
        s.fillStyle="#737984";s.font="10px system-ui";s.fillText(key,x,y+176);s.font="14px system-ui";s.fillStyle="#f5f5ef";
      }
      const thumbnails={};
      for(const [key] of names){
        const p=data.square[key],dec=new AirboatEaf(data.assets[p.file]);
        thumbnails[key]=image(dec.frame(p.range[0]+Math.round((p.range[1]-p.range[0])*.38)));
      }
      const samples=names.map(n=>n[0]);
      const decs=samples.map(key=>new AirboatEaf(data.assets[data.square[key].file]));
      const short=make(840,552),ctx=short.getContext("2d"),frames=[];
      for(let i=0;i<Math.max(...decs.map(d=>d.asset.frames));i++){
        ctx.fillStyle="#101114";ctx.fillRect(0,0,840,552);ctx.font="11px system-ui";
        for(const [j,d] of decs.entries()){
          const x=j%7*120+4,y=Math.floor(j/7)*138+4;
          ctx.drawImage(d.frame(i),x,y,112,112);ctx.fillStyle="#f5f5ef";ctx.fillText(names.find(r=>r[0]===samples[j])[1],x,y+129);
        }
        frames.push(image(short));
      }
      return {sheet:image(sheet),frames,thumbnails};
    });
    fs.writeFileSync(path.join(art,"preview-sheet.png"),Buffer.from(collection.sheet,"base64"));
    cp.execFileSync(python,["-c",encode,path.join(art,"preview/collection.gif")],{input:JSON.stringify(collection.frames),maxBuffer:32*1024*1024});
    fs.mkdirSync(path.join(art,'thumbnails'),{recursive:true});
    for(const [key,png] of Object.entries(collection.thumbnails))fs.writeFileSync(path.join(art,'thumbnails',key+'.png'),Buffer.from(png,'base64'));
    const previews=[];
    for(const key of Object.keys(collection.thumbnails)){
      const frames=await page.evaluate(key=>{
        const data=AIRBOAT_EXPRESSIONS,p=data.square[key],dec=new AirboatEaf(data.assets[p.file]);
        const out=document.createElement("canvas");out.width=out.height=360;const ctx=out.getContext("2d"),result=[];
        for(let i=0;i<dec.asset.frames;i++){ctx.drawImage(dec.frame(i),0,0,360,360);result.push(out.toDataURL().split(",")[1]);}
        return result;
      },key);
      cp.execFileSync(python,["-c",encode,path.join(art,`preview/${key}.gif`)],{input:JSON.stringify(frames),maxBuffer:32*1024*1024});
      previews.push(key);
    }
    const transitions=await page.evaluate(()=>{
      const keys=['happy','thinking','question','laughing','funny','confused','tried'];
      const sheet=document.createElement('canvas');sheet.width=1120;sheet.height=1220;
      const c=sheet.getContext('2d');c.fillStyle='#101114';c.fillRect(0,0,sheet.width,sheet.height);
      c.font='13px system-ui';c.fillStyle='#fff';
      ['待机','进入 ¼','进入 ½','进入 ¾','表演起势','动作高点','回到待机'].forEach((label,j)=>c.fillText(label,8+j*160,24));
      keys.forEach((key,i)=>{
        const p=AIRBOAT_EXPRESSIONS.square[key],d=new AirboatEaf(AIRBOAT_EXPRESSIONS.assets[p.file]),n=AIRBOAT_SQUARE_PACK.transition_frames;
        const frames=[0,Math.round((n-1)*.25),Math.round((n-1)*.5),Math.round((n-1)*.75),n,n+Math.round((p.range[1]-n)*.4),d.asset.frames-1];
        frames.forEach((f,j)=>c.drawImage(d.frame(f),8+j*160,34+i*168,148,148));
        c.fillStyle='#fff';c.fillText(key,8,34+i*168+163);
      });return sheet.toDataURL().split(',')[1];
    });
    fs.writeFileSync(path.join(art,'transition-sheet.png'),Buffer.from(transitions,'base64'));
    await page.screenshot({path:path.join(art,"collection-review-desktop.png"),fullPage:true});
    const workbenches=[
      ['library',path.join(repo,'docs/product/expression-workbench.html')],
      ['airboat',path.resolve(repo,'../docs/product/expression-workbench.html')]
    ];
    for(const [label,file] of workbenches){
      await page.setViewportSize({width:1440,height:1050});
      await page.goto(pathToFileURL(file).href+'?square=funny#expressions');
      await page.waitForSelector('#compare[open]');
      await page.locator('#compare-time').fill('1800');
      await page.locator('#compare-time').dispatchEvent('input');
      await page.screenshot({path:path.join(art,`node-workbench-${label}.png`),fullPage:true});
    }
    const manifest=JSON.parse(fs.readFileSync(path.join(repo,'assets/square-pop/manifest.json')));
    const files=['preview-sheet.png','transition-sheet.png','collection-review-desktop.png','node-workbench-library.png','node-workbench-airboat.png','preview/collection.gif',
      ...previews.flatMap(key=>['preview/'+key+'.gif','thumbnails/'+key+'.png'])];
    const crypto=require('node:crypto');
    fs.writeFileSync(path.join(art,'preview-manifest.json'),JSON.stringify({pack_sha256:manifest.binary_sha256,
      source:'AFM decoder',performances:Object.keys(manifest.clips).length,semanticPreviews:previews.length,fps:manifest.fps,
      files:files.map(file=>{const b=fs.readFileSync(path.join(art,file));return {file,bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex')}})},null,2)+'\n');
    console.log(JSON.stringify({status:"rendered",previews,actualPack:true}));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
