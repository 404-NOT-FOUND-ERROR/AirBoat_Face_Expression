"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto"),{pathToFileURL}=require("node:url");
const {chromium}=require(process.env.AIRBOAT_SQUARE_PLAYWRIGHT||"playwright");
(async()=>{
  const repo=path.resolve(__dirname,".."),dest=path.join(repo,"output/imagegen/airboat-square-pop-20261124/inputs");
  const browser=await chromium.launch({executablePath:process.env.AIRBOAT_SQUARE_BROWSER,headless:true});
  try{
    const page=await browser.newPage({reducedMotion:"reduce"});
    await page.goto(pathToFileURL(path.join(repo,"docs/product/expression-square-idle.html")).href);
    const exported=await page.evaluate(async()=>{
      const {renderMasks,frameCount,fps,exponent,whiteSize,green}=AirboatSquareIdleReview;
      const stream=new ReadableStream({start(controller){
        try{
          for(let f=0;f<frameCount;f++)for(const layer of renderMasks(f)){
            const rgba=layer.getContext("2d").getImageData(0,0,480,480).data,mask=new Uint8Array(480*480);
            for(let i=0;i<mask.length;i++)mask[i]=Math.round(rgba[i*4+3]*15/255);
            controller.enqueue(mask);
          }
          controller.close();
        }catch(e){controller.error(e)}
      }}).pipeThrough(new CompressionStream("gzip"));
      const bytes=new Uint8Array(await new Response(stream).arrayBuffer());
      let raw="";for(let i=0;i<bytes.length;i+=8192)raw+=String.fromCharCode(...bytes.subarray(i,i+8192));
      return {payload:btoa(raw),frames:frameCount,fps,exponent,whiteSize,green,canvas:480,layers:["white","pupil"],
        format:"airboat.mask-coverage.a4-u8.gzip.v1"};
    });
    const bytes=Buffer.from(exported.payload,"base64");delete exported.payload;
    exported.binary="soft-square-idle.a4.gz";exported.sha256=crypto.createHash("sha256").update(bytes).digest("hex");
    exported.renderer_sha256=crypto.createHash("sha256").update(fs.readFileSync(path.join(repo,"docs/product/expression-square-idle.js"))).digest("hex");
    fs.mkdirSync(dest,{recursive:true});fs.writeFileSync(path.join(dest,exported.binary),bytes);
    fs.writeFileSync(path.join(dest,"soft-square-idle.json"),JSON.stringify(exported,null,2)+"\n");
    console.log(JSON.stringify({status:"exported",frames:exported.frames,sha256:exported.sha256,bytes:bytes.length}));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
