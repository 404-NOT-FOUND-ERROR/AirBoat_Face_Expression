"""Make fixed-palette 25fps previews from generated GIFs; retain API originals."""
import json
import colorsys
import hashlib
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


def channels(frame, key, eye_rows=(50, 394)):
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
    top, bottom = eye_rows
    for offset in (0,240):
        r = (offset,top,offset+240,bottom)
        white_piece = full.crop(r)
        pupil_piece = pupil.crop(r)
        pairs.append((sprite(white_piece,offset,top),sprite(pupil_piece,offset,top)))
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
    if a is b:
        return a
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
    accent = Image.blend(a[1],b[1],u)
    face.paste(accent,(0,0),accent)
    for i in (0,1):
        for j,color in ((0,"white"),(1,"black")):
            layer = morph(a[0][i][j],b[0][i][j],u)
            if layer:
                mask,box = layer
                face.paste(color,(box[0],box[1],box[0]+mask.width,box[1]+mask.height),mask)
    return face


def ease(value):
    value = max(0.0,min(1.0,value))
    return value*value*(3.0-2.0*value)


def hue_blend(start,end,u):
    """Move along the short HSV hue arc while retaining saturated color."""
    a = tuple(int(start[i:i+2],16)/255 for i in (1,3,5))
    b = tuple(int(end[i:i+2],16)/255 for i in (1,3,5))
    ah,as_,av = colorsys.rgb_to_hsv(*a)
    bh,bs,bv = colorsys.rgb_to_hsv(*b)
    delta = (bh-ah+0.5)%1.0-0.5
    rgb = colorsys.hsv_to_rgb((ah+delta*u)%1.0,as_+(bs-as_)*u,av+(bv-av)*u)
    return tuple(round(channel*255) for channel in rgb)


def transition_frame(source,target,u,source_color,target_color):
    frame = Image.new("RGB",(480,480),hue_blend(COLORS[source_color],COLORS[target_color],ease((u-.08)/.92)))
    accent = Image.blend(source[1],target[1],ease((u-.12)/.8))
    frame.paste(accent,(0,0),accent)
    for eye in (0,1):
        pupil_u = ease((u-eye*35/360)/.75)
        white_u = ease((u-.12-eye*25/360)/.8)
        for layer,color,amount in ((0,"white",white_u),(1,"black",pupil_u)):
            sprite_layer = morph(source[0][eye][layer],target[0][eye][layer],amount)
            if sprite_layer:
                mask,box = sprite_layer
                frame.paste(color,(box[0],box[1],box[0]+mask.width,box[1]+mask.height),mask)
    return frame


def save_transition(folder,name,source,target,source_color,target_color):
    frames = [transition_frame(source,target,i/8,source_color,target_color) for i in range(9)]
    frames[0] = compose(source,source,0,source_color)
    frames[-1] = compose(target,target,0,target_color)
    path = folder/f"{name}.gif"
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=40,optimize=False)
    with Image.open(path) as saved:
        frame_count = saved.n_frames
        duration = sum((saved.seek(i) or saved.info.get("duration",40)) for i in range(saved.n_frames))
    return {"file":path.relative_to(OUT).as_posix(),"frames":frame_count,"fps":25,"duration_ms":duration,
            "from":source_color,"to":target_color}


def main():
    folder = OUT/"preview"
    folder.mkdir(exist_ok=True)
    transitions = OUT/"transitions"
    for name in ("entry","exit","bridge"):
        (transitions/name).mkdir(parents=True,exist_ok=True)
    stats = {}
    first_poses = {}
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
        first_poses[key] = poses[0]
        stats[key] = {"native":"gif/"+key+".gif","preview":"preview/"+key+".gif",
                      "fps":25,"frames":len(polished),"processing":"fixed backdrop; per-eye and pupil affine interpolation; loop closure"}
    base = first_poses["idle"]
    entries = {}
    for key in COLORS:
        entries[key] = {
            "entry":save_transition(transitions/"entry",key,base,first_poses[key],"idle",key),
            "loop":{"file":f"preview/{key}.gif","frames":stats[key]["frames"],"fps":25,
                    "duration_ms":stats[key]["frames"]*40},
            "exit":save_transition(transitions/"exit",key,first_poses[key],base,key,"idle"),
        }
        stats[key]["entry"] = entries[key]["entry"]["file"]
        stats[key]["exit"] = entries[key]["exit"]["file"]
    bridge_specs = (("listening","thinking"),("thinking","happy"),("happy","surprised"))
    bridges = {}
    for source,target in bridge_specs:
        name = f"{source}-to-{target}"
        bridges[f"{source}>{target}"] = save_transition(
            transitions/"bridge",name,first_poses[source],first_poses[target],source,target)
    base_path = folder/"idle.png"
    manifest = {
        "version":1,"fps":25,"transition_frames":9,"transition_duration_ms":360,
        "base":{"semantic":"idle","color":COLORS["idle"],"image":"preview/idle.png",
                "sha256":hashlib.sha256(base_path.read_bytes()).hexdigest()},
        "motion":{"color":"short-arc HSV hue; eased saturation and value",
                  "pupil":"starts first; 35 ms left/right stagger",
                  "eye_shape":"starts after gaze; 25 ms left/right stagger",
                  "loop":"expression loop only; shared base is never inserted at loop seam",
                  "return":"authored inverse endpoint back to shared idle pose"},
        "entries":entries,"bridges":bridges,
        "sequences":{"listen-think-happy":["listening","thinking","happy"],
                      "happy-surprised":["happy","surprised"],"happy-return":["happy"]},
    }
    serialized = json.dumps(manifest,ensure_ascii=False,indent=2)
    (transitions/"manifest.json").write_text(serialized+"\n",encoding="utf-8")
    (transitions/"manifest.js").write_text("window.AIRBOAT_TRANSITIONS = "+serialized+";\n",encoding="utf-8")
    (OUT/"preview-processing.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    main_manifest = OUT/"manifest.json"
    if main_manifest.exists():
        catalog = json.loads(main_manifest.read_bytes())
        catalog["transitions"] = "transitions/manifest.json"
        for row in catalog.get("entries",[]):
            item = entries.get(row["semantic"])
            if item:
                row["entry_animation"] = item["entry"]["file"]
                row["exit_animation"] = item["exit"]["file"]
        main_manifest.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(stats)} polished loop previews")
    print(f"{len(entries)} shared-base entry/return pairs and {len(bridges)} direct bridges")


if __name__ == "__main__":
    main()
