"""Make fixed-palette 25fps previews from generated GIFs; retain API originals."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/imagegen/airboat-expression-study-20261120"
COLORS = {
    "neutral":"#28cf60","idle":"#28cf60","listening":"#28cf60","thinking":"#6679ff",
    "happy":"#a8f900","surprised":"#f8f600","shocked":"#ff4264","question":"#00d4e5",
    "look_around":"#a8f900","winking":"#ff3693","beat_swing":"#6e32ff","confused":"#6679ff",
    "relaxed":"#28cf60","sleepy":"#6679ff","laughing":"#f8f600","funny":"#6e32ff",
    "loving":"#ff168c","embarrassed":"#ff168c","confident":"#00d4e5","delicious":"#f8f600",
    "sad":"#4031f5","crying":"#00d4e5","silly":"#a8f900","angry":"#ff4264",
    "insert":"#00d4e5","look_left":"#a8f900","look_right":"#a8f900","eat":"#f8f600","tried":"#6679ff",
}


def filled_holes(mask):
    copy = mask.copy()
    # Mask can touch an edge; a clear one-pixel border gives floodfill a known seed.
    padded = Image.new("L",(482,482))
    padded.paste(copy,(1,1))
    ImageDraw.floodfill(padded,(0,0),128,thresh=0)
    return padded.crop((1,1,481,481)).point(lambda v: 0 if v == 128 else 255)


def channels(frame, key):
    pixels = np.asarray(frame.convert("RGB"))
    white = np.min(pixels,axis=2) >= 232
    mask = Image.fromarray((white*255).astype("uint8"))
    # Remove subpixel noise and keep white shape boundaries.
    full = filled_holes(mask)
    dark = np.max(pixels,axis=2)<65
    allowed = np.asarray(full)>0
    if key in {"angry","confident","relaxed","sleepy","tried"}:
        for ox in (0,240):
            piece = mask.crop((ox,50,ox+240,394)).getbbox()
            if piece:
                x0,y0,x1,y1 = piece
                allowed[50+y0:50+y1,ox+x0:ox+x1] = True
    dark &= allowed
    pupil = Image.fromarray((dark*255).astype("uint8"))
    pairs = []
    for offset in (0,240):
        r = (offset,50,offset+240,394)
        white_piece = full.crop(r)
        pupil_piece = pupil.crop(r)
        pairs.append((sprite(white_piece,offset,50),sprite(pupil_piece,offset,50)))
    accents = Image.new("RGBA",(480,480))
    if key == "listening":
        keep = (pixels[:,:,1]>190)&(pixels[:,:,2]>180)&(pixels[:,:,0]<100)
        keep &= np.indices(keep.shape)[0]<150
        rgba = np.dstack([pixels,(keep*255).astype("uint8")])
        accents = Image.fromarray(rgba.astype("uint8"))
    elif key in {"confused","embarrassed"}:
        keep = (pixels[:,:,0]>205)&(pixels[:,:,1]<170)&(pixels[:,:,2]<205)
        # Sparse colored accents only; reject the full pink field.
        if keep.sum()<14000:
            accents = Image.fromarray(np.dstack([pixels,(keep*255).astype("uint8")]).astype("uint8"))
    elif key == "crying":
        keep = (pixels[:,:,0]>70)&(pixels[:,:,0]<225)&(pixels[:,:,1]>220)&(pixels[:,:,2]>220)
        rows = np.indices(keep.shape)[0]
        keep &= (rows>210)&(rows<394)
        if keep.sum()<12000:
            accents = Image.fromarray(np.dstack([pixels,(keep*255).astype("uint8")]).astype("uint8"))
    return pairs, accents


def sprite(mask, ox, oy):
    box = mask.getbbox()
    if not box:
        return None
    return (mask.crop(box),(box[0]+ox,box[1]+oy,box[2]+ox,box[3]+oy))


def morph(a,b,u):
    if not a and not b:
        return None
    if not a:
        return b[0].point(lambda p:round(p*u)),b[1]
    if not b:
        return a[0].point(lambda p:round(p*(1-u))),a[1]
    box = tuple(round(x+(y-x)*u) for x,y in zip(a[1],b[1]))
    dims = (max(1,box[2]-box[0]),max(1,box[3]-box[1]))
    left = a[0].resize(dims,Image.Resampling.LANCZOS)
    right = b[0].resize(dims,Image.Resampling.LANCZOS)
    # A moving pupil must remain one solid shape, rather than dissolve into two ghosts.
    blended = Image.blend(left,right,u).point(lambda value:255 if value>=128 else 0)
    return blended,box


def compose(a,b,u,key):
    face = Image.new("RGB",(480,480),COLORS[key])
    for i in (0,1):
        for j,color in ((0,"white"),(1,"black")):
            layer = morph(a[0][i][j],b[0][i][j],u)
            if layer:
                mask,box = layer
                face.paste(color,(box[0],box[1],box[0]+mask.width,box[1]+mask.height),mask)
    accent = Image.blend(a[1],b[1],u)
    face.paste(accent,(0,0),accent)
    return face


def main():
    folder = OUT/"preview"
    folder.mkdir(exist_ok=True)
    stats = {}
    for key in COLORS:
        with Image.open(OUT/"gif"/f"{key}.gif") as gif:
            frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(gif)]
            source_delay = gif.info.get("duration",90)
        poses = [channels(frame,key) for frame in frames]
        # One constant backdrop, individual eye/pupil interpolation, closed boundary.
        total = round(len(frames)*source_delay/40)
        polished = []
        for i in range(total):
            step = i*len(frames)/total
            f = int(step)
            polished.append(compose(poses[f],poses[(f+1)%len(poses)],step-f,key))
        polished[0].save(folder/f"{key}.gif",save_all=True,append_images=polished[1:],
                         duration=40,loop=0,optimize=True)
        compose(poses[0],poses[0],0,key).save(folder/f"{key}.png",optimize=True)
        stats[key] = {"native":"gif/"+key+".gif","preview":"preview/"+key+".gif",
                      "fps":25,"frames":len(polished),"processing":"fixed backdrop; per-eye and pupil affine interpolation; loop closure"}
    (OUT/"preview-processing.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(stats)} polished loop previews")


if __name__ == "__main__":
    main()
