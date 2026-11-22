/* SPDX-License-Identifier: MIT. Reference for listen_overlay_rgb565.h. */
"use strict";
(() => {
  const pack = p => ((p[0] >> 3) << 11) | ((p[1] >> 2) << 5) | (p[2] >> 3);
  const unpack = p => [Math.floor((p >> 11) * 255 / 31),
    Math.floor(((p >> 5) & 63) * 255 / 63), Math.floor((p & 31) * 255 / 31), 255];
  function blend565(background, mask) {
    const maxima = [31, 63, 31], shifts = [11, 5, 0];
    return shifts.reduce((out, shift, i) => {
      const max = maxima[i], base = (background >> shift) & max;
      const coverage = (mask >> shift) & max;
      return out | ((base + Math.floor(((max-base)*coverage + Math.floor(max/2))/max)) << shift);
    }, 0);
  }
  function draw(context, maskCanvas, mode = "transparent") {
    if (!["transparent", "legacy"].includes(mode)) throw Error("Unknown listen overlay mode");
    if (maskCanvas.width !== 100 || maskCanvas.height !== 46) throw Error("Expected the original listening mask");
    const side = context.canvas.width;
    if (side !== context.canvas.height || ![360, 480].includes(side)) throw Error("Expected a 360 or 480 square");
    const image = context.getImageData(0, 0, side, side), target = image.data;
    const source = maskCanvas.getContext("2d").getImageData(0, 0, 100, 46).data;
    // Match the device's integer logical coordinates, including tile boundaries.
    for (let y=0; y<side; ++y) {
      const sy=Math.floor(y*360/side)-25;
      if (sy<0 || sy>=46) continue;
      for (let x=0; x<side; ++x) {
        const sx=Math.floor(x*360/side)-130;
        if (sx<0 || sx>=100) continue;
        const src=(sy*100+sx)*4, dst=(y*side+x)*4;
        if (!source[src+3]) continue;
        const mask=pack(source.subarray(src,src+4));
        const color=mode === "legacy" ? mask : blend565(pack(target.subarray(dst,dst+4)),mask);
        target.set(unpack(color), dst);
      }
    }
    context.putImageData(image, 0, 0);
  }
  window.AirboatListenOverlay = {blend565, draw, pack, unpack};
})();
