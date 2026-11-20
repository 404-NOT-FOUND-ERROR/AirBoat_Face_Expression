/* Offline shape sampling. One owner, an explicit millisecond clock, no network. */
"use strict";
class AirboatFaceMotion {
  static decodedMasks = new WeakMap();
  constructor(data) {
    this.data = data;
    this.maskSide = data.mask_side;
    this.masks = AirboatFaceMotion.decodedMasks.get(data);
    if (!this.masks) {
      this.masks = data.masks.map(text => {
        const raw = atob(text), pixels = new Uint8Array(data.mask_side ** 2);
        for (let i = 0; i < pixels.length; i++) pixels[i] = ((raw.charCodeAt(i >> 3) >> (7-i%8)) & 1) * 255;
        return pixels;
      });
      AirboatFaceMotion.decodedMasks.set(data,this.masks);
    }
    this.key = data.base;
    this.started = 0;
    this.transition = null;
    this.resting = true;
  }
  static ease(value) {
    const u = Math.min(1,Math.max(0,value));
    return u*u*(3-2*u);
  }
  static rgb(hex) { return [1,3,5].map(i => parseInt(hex.slice(i,i+2),16)); }
  static hsv(rgb) {
    const [r,g,b] = rgb.map(x => x/255), hi = Math.max(r,g,b), lo = Math.min(r,g,b), d = hi-lo;
    let h = 0;
    if (d) h = (hi === r ? ((g-b)/d+6)%6 : hi === g ? (b-r)/d+2 : (r-g)/d+4)/6;
    return [h,hi ? d/hi : 0,hi];
  }
  static color(a,b,u) {
    if (u <= 0) return a.slice();
    if (u >= 1) return b.slice();
    const x = this.hsv(a), y = this.hsv(b), delta = ((y[0]-x[0]+1.5)%1)-.5;
    const h = (x[0]+delta*u+1)%1, s = x[1]+(y[1]-x[1])*u, v = x[2]+(y[2]-x[2])*u;
    const i = Math.floor(h*6), f = h*6-i, p = v*(1-s), q = v*(1-f*s), t = v*(1-(1-f)*s);
    return [[v,t,p],[q,v,p],[p,v,t],[p,q,v],[t,p,v],[v,p,q]][i%6].map(x => Math.round(x*255));
  }
  pose(frame,color) {
    return {color:AirboatFaceMotion.rgb(color),layers:frame.layers.map(row => row ?
      {mask:this.masks[row[0]],box:row.slice(1),opacity:1} : null),
      accents:frame.accent === null ? [] : [{id:frame.accent,opacity:1}]};
  }
  mixLayer(a,b,u) {
    if (u <= 0) return a;
    if (u >= 1) return b;
    if (!a && !b) return null;
    if (!a) return {...b,opacity:b.opacity*u};
    if (!b) return {...a,opacity:a.opacity*(1-u)};
    const mask = new Uint8Array(a.mask.length);
    for (let i = 0; i < mask.length; i++) mask[i] = Math.round(a.mask[i]*(1-u)+b.mask[i]*u);
    return {mask,box:a.box.map((v,i) => v+(b.box[i]-v)*u),opacity:a.opacity+(b.opacity-a.opacity)*u};
  }
  mix(a,b,u,stagger) {
    const ease = AirboatFaceMotion.ease;
    const layers = a.layers.map((layer,i) => {
      const eye = i >> 1, pupil = i%2;
      const t = !stagger ? u : pupil ? ease((u-eye*35/this.data.transition_ms)/.75) :
        ease((u-.12-eye*25/this.data.transition_ms)/.8);
      return this.mixLayer(layer,b.layers[i],t);
    });
    const accentU = stagger ? ease((u-.12)/.8) : u;
    const accents = new Map();
    for (const row of a.accents) accents.set(row.id,(accents.get(row.id)||0)+row.opacity*(1-accentU));
    for (const row of b.accents) accents.set(row.id,(accents.get(row.id)||0)+row.opacity*accentU);
    return {color:AirboatFaceMotion.color(a.color,b.color,stagger ? ease((u-.08)/.92) : u),layers,
      accents:[...accents].filter(([,opacity]) => opacity > .001).map(([id,opacity]) => ({id,opacity}))};
  }
  loop(key,elapsed) {
    const clip = this.data.clips[key];
    let at = ((elapsed % clip.duration_ms)+clip.duration_ms)%clip.duration_ms, frame = 0;
    while (frame < clip.frames.length-1 && at >= clip.durations[frame]) at -= clip.durations[frame++];
    return this.mix(this.pose(clip.frames[frame],clip.color),
      this.pose(clip.frames[(frame+1)%clip.frames.length],clip.color),at/clip.durations[frame],false);
  }
  sample(now) {
    if (this.transition) {
      const t = this.transition, u = Math.min(1,Math.max(0,(now-t.started)/this.data.transition_ms));
      if (u < 1) return this.mix(t.from,t.to,u,true);
      this.started = t.started+this.data.transition_ms;
      this.transition = null;
    }
    const clip = this.data.clips[this.key];
    const elapsed = now-this.started;
    return this.resting && elapsed < 520 ? this.pose(clip.frames[0],clip.color) :
      this.loop(this.key,elapsed-(this.resting ? 520 : 0));
  }
  request(key,now,resting = false) {
    if (!this.data.clips[key] || !Number.isFinite(now)) return false;
    const from = this.sample(now), clip = this.data.clips[key];
    this.transition = {from,to:this.pose(clip.frames[0],clip.color),started:now};
    this.key = key;
    this.resting = resting;
    return true;
  }
  returnToBase(now) { return this.request(this.data.base,now,true); }
}

class AirboatFaceRenderer {
  constructor(canvas,data) {
    this.canvas = canvas;
    this.context = canvas.getContext("2d",{alpha:false});
    this.tile = document.createElement("canvas");
    this.tile.width = this.tile.height = data.mask_side;
    this.tileContext = this.tile.getContext("2d");
    this.pixels = this.tileContext.createImageData(data.mask_side,data.mask_side);
    this.accents = data.accents.map(src => { const image = new Image(); image.src = src; return image; });
    this.side = data.side;
  }
  ready() {
    return Promise.all(this.accents.map(image => image.decode()));
  }
  draw(pose,mirror = false,guides = false) {
    const ctx = this.context, scale = this.canvas.width/this.side;
    ctx.save();
    ctx.fillStyle = `rgb(${pose.color.join(",")})`;
    ctx.fillRect(0,0,this.canvas.width,this.canvas.height);
    ctx.scale(scale,scale);
    if (mirror) { ctx.translate(this.side,0); ctx.scale(-1,1); }
    for (const row of pose.accents) {
      ctx.globalAlpha = row.opacity;
      const image = this.accents[row.id];
      if (image.complete && image.naturalWidth) ctx.drawImage(image,0,0,this.side,this.side);
    }
    ctx.globalAlpha = 1;
    const pixels = this.pixels.data;
    for (let i = 0; i < pose.layers.length; i++) {
      const layer = pose.layers[i];
      if (!layer || layer.opacity <= .001) continue;
      const color = i%2 ? 0 : 255;
      for (let p = 0; p < layer.mask.length; p++) {
        pixels[p*4] = pixels[p*4+1] = pixels[p*4+2] = color;
        pixels[p*4+3] = layer.mask[p] >= 128 ? Math.round(255*layer.opacity) : 0;
      }
      this.tileContext.putImageData(this.pixels,0,0);
      const [x0,y0,x1,y1] = layer.box;
      ctx.drawImage(this.tile,x0,y0,Math.max(1,x1-x0),Math.max(1,y1-y0));
    }
    ctx.restore();
    if (guides) {
      ctx.save(); ctx.strokeStyle = "#0007"; ctx.setLineDash([7,7]); ctx.lineWidth = 1;
      for (const y of [.16,.78]) { ctx.beginPath(); ctx.moveTo(0,y*this.canvas.height); ctx.lineTo(this.canvas.width,y*this.canvas.height); ctx.stroke(); }
      ctx.restore();
    }
  }
}
if (typeof module !== "undefined") module.exports = {AirboatFaceMotion};
if (typeof window !== "undefined") {
  let loading;
  window.loadAirboatFaceMotion = () => {
    if (window.AIRBOAT_FACE_MOTION) return Promise.resolve(window.AIRBOAT_FACE_MOTION);
    if (!loading) loading = (async () => {
      const packed = Uint8Array.from(atob(window.AIRBOAT_FACE_MOTION_GZIP),c => c.charCodeAt(0));
      const stream = new Blob([packed]).stream().pipeThrough(new DecompressionStream("gzip"));
      window.AIRBOAT_FACE_MOTION = JSON.parse(await new Response(stream).text());
      return window.AIRBOAT_FACE_MOTION;
    })().catch(error => { loading = null; throw error; });
    return loading;
  };
}
