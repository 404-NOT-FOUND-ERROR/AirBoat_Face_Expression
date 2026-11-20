"use strict";
const fs = require("node:fs/promises");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require(process.argv[2] || "playwright");
(async () => {
  const root = path.resolve(__dirname,"..");
  const output = path.join(root,".test-output/transition-demo-frames");
  await fs.mkdir(output,{recursive:true});
  const browser = await chromium.launch({executablePath:process.argv[3],headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1100,height:900}});
    await page.goto(pathToFileURL(path.join(root,"docs/product/expression-transition-studio.html")).href);
    await page.waitForSelector('body[data-ready="true"]');
    for (const name of ["happy-return","listen-think-happy","happy-surprised"]) {
      const dir = path.join(output,name);
      await fs.mkdir(dir,{recursive:true});
      for (const file of await fs.readdir(dir)) {
        if (/^\d{4}\.png$/.test(file)) await fs.unlink(path.join(dir,file));
      }
      const count = await page.evaluate(async name => {
        window.demoMotion = new AirboatFaceMotion(AIRBOAT_FACE_MOTION);
        const canvas = document.createElement("canvas"); canvas.width = canvas.height = 480;
        window.demoRender = new AirboatFaceRenderer(canvas,AIRBOAT_FACE_MOTION);
        await demoRender.ready();
        const keys = AIRBOAT_TRANSITIONS.sequences[name];
        window.demoEvents = keys.map((key,i) => ({at:400+i*1680,key}));
        demoEvents.push({at:400+keys.length*1680,key:null});
        return Math.ceil((demoEvents.at(-1).at+800)/40);
      },name);
      for (let i = 0; i < count; i++) {
        const png = await page.evaluate(time => {
          while (demoEvents.length && time >= demoEvents[0].at) {
            const event = demoEvents.shift();
            if (event.key) demoMotion.request(event.key,event.at);
            else demoMotion.returnToBase(event.at);
          }
          demoRender.draw(demoMotion.sample(time));
          return demoRender.canvas.toDataURL("image/png").split(",")[1];
        },i*40);
        await fs.writeFile(path.join(dir,String(i).padStart(4,"0")+".png"),Buffer.from(png,"base64"));
      }
      console.log(`${name}: ${count} frames`);
    }
  } finally { await browser.close(); }
})();
