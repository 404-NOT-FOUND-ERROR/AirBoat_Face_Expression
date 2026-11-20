"""Decode existing assets and retime user art for offline motion review."""
from __future__ import annotations

import html
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/imagegen/airboat-expression-study-20261120"
ASSETS = ROOT / "assets/native/assets"

# Native rhythm samples: t, horizontal pan, vertical pan, squash, eye spacing.
RHYTHM = {
    "idle": [(0,0,0,0,0),(.61,0,-3,.02,0),(.90,0,-1,0,0),
             (1.02,0,1,-.96,0),(1.13,0,-1,.05,0),(1.28,0,0,0,0),(2.4,0,0,0,0)],
    "happy": [(0,0,0,0,0),(.18,0,7,-.18,2),(.31,0,-15,.14,3),(.44,0,-18,.03,4),
              (.54,0,-11,-.04,2),(.63,0,-13,.02,2),(.81,0,-4,-.05,1),
              (.95,0,-8,.025,2),(1.18,0,0,0,0),(1.7,0,0,0,0)],
    "shocked": [(0,0,0,0,0),(.18,0,0,0,0),(.245,-4,-13,.32,9),(.35,-5,-13,.32,9),
                (.46,3,-11,.23,7),(.54,-1,-12,.24,7),(.68,0,-11,.23,6),
                (.89,0,-10,.21,6),(1.23,0,0,-.095,0),(1.37,0,0,.025,0),(1.8,0,0,0,0)],
    "confused": [(0,0,0,0,0),(.22,0,0,0,0),(.30,16,6,-.12,2),
                 (.41,-13,-7,.09,-4),(.52,9,5,-.08,2),(.64,-5,-4,.05,-2),
                 (.77,3,2,-.02,1),(.95,0,0,0,0),(1.42,0,0,0,0),(1.69,0,0,0,0)],
    "look_around": [(0,0,0,0,0),(.27,0,0,0,0),(.43,-23,-3,.025,0),(.83,-23,-3,.025,0),
                    (.99,25,2,-.04,0),(1.34,25,2,-.04,0),(1.54,-3,0,.02,0),
                    (1.66,0,0,0,0),(1.96,0,0,0,0)],
}
RHYTHM_CN = {
    "idle":"长停顿 → 一次快速眨眼 → 慢慢归位",
    "happy":"先压低 → 弹起 → 落下 → 两次小幅回弹",
    "shocked":"突然拉高 → 盯住 → 极短横抖 → 放松",
    "confused":"左右交替 → 振幅变小 → 完全站稳",
    "look_around":"瞳孔先左看 → 停住 → 右看 → 回中",
}


def save_gif(frames, dest, ms):
    frames[0].save(dest, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)


def native_surface(frame, dims, kind):
    w, h = dims
    sprite = Image.frombytes("RGBA", dims, frame)
    surface = Image.new("RGB", (360, 360))
    if kind == "listen":
        surface.paste(sprite, (130, 25), sprite)
    elif w < 200 and h > 60:
        y = (360 - h) // 2 + 10
        mirror = ImageOps.mirror(sprite)
        surface.paste(sprite, (10, y), sprite)
        surface.paste(mirror, (350-w, y), mirror)
    else:
        surface.paste(sprite, ((360-w)//2, (360-h)//2), sprite)
    return surface.resize((480, 480), Image.Resampling.NEAREST)


def activity(a, b):
    diff = ImageChops.difference(a, b).convert("L")
    return sum(i * n for i, n in enumerate(diff.histogram())) / (a.width * a.height)


def extract_eyes(art):
    backdrop = art.getpixel((0, 0))
    # Image has a solid full-bleed background and two touching but distinct eyes.
    eyes = []
    for x, limit in ((0, 240), (240, 480)):
        crop = art.crop((x, 0, limit, 480))
        mask = ImageChops.difference(crop, Image.new("RGB", crop.size, backdrop)).convert("L")
        mask = mask.point(lambda c: 255 if c > 17 else 0)
        b = mask.getbbox()
        if not b:
            raise ValueError("The user's idle reference has no eye on one side")
        eyes.append((crop.crop(b), mask.crop(b), (x+(b[0]+b[2])/2, (b[1]+b[3])/2)))
    return backdrop, eyes


def interpolate(keys, time):
    for a, b in zip(keys, keys[1:]):
        if time <= b[0]:
            u = (time-a[0])/(b[0]-a[0])
            u = u*u*(3-2*u)
            return tuple(i+(j-i)*u for i,j in zip(a[1:],b[1:]))
    return keys[-1][1:]


def puppet_frame(art, key, t):
    backdrop, eyes = art
    canvas = Image.new("RGB", (480,480), backdrop)
    dx, dy, squash, spread = interpolate(RHYTHM[key],t)
    for index, (eye, mask, (cx, cy)) in enumerate(eyes):
        cx += dx*(.17 if key == "look_around" else 1) + spread*(index*2-1)
        cy += dy * (1 if index == 0 or key != "confused" else .58)
        if key == "look_around":
            eye = Image.new("RGB", eye.size, backdrop)
            pen = ImageDraw.Draw(eye)
            w,h = eye.size
            pen.ellipse((0,0,w-1,h-1),fill="white")
            px,py = w*.50 + dx*.76, h*.48
            pr = min(w,h)*.28
            pen.ellipse((px-pr,py-pr,px+pr,py+pr),fill="black")
        shape = (int(eye.width*(1-squash*.13)), max(3, int(eye.height*(1+squash))))
        resample = Image.Resampling.LANCZOS
        canvas.paste(eye.resize(shape,resample),
                     (round(cx-shape[0]/2),round(cy-shape[1]/2)),mask.resize(shape,resample))
    return canvas


def gallery(study, sources, proofs):
    e = html.escape
    cards = []
    for role in [r for group in study["groups"] for r in group["roles"]]:
        k = role["key"]
        card = sources[k]
        p = (f'<figure><img src="motion-study/{k}.gif" loading="lazy" alt=""><figcaption>{RHYTHM_CN[k]}</figcaption></figure>'
             if k in proofs else "")
        cards.append(f'<article><h2>{role["label"]} <small>{k}</small></h2><div class="media">'
                     f'<figure><img src="original/{card["slug"]}.png" loading="lazy" alt=""><figcaption>原版关键帧 · {card["peak"]} ms</figcaption></figure>'
                     f'<figure><img src="original/{card["slug"]}.gif" loading="lazy" alt=""><figcaption>原版动效 · {card["frames"]} 帧</figcaption></figure>'
                     f'{p}</div><p>{e(role["motion"])}</p></article>')
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AirBoat · 表情动作研究</title><style>
:root{color-scheme:dark;font:15px/1.5 "Segoe UI","Microsoft YaHei",sans-serif;color:#f4f5eb;background:#101110}
*{box-sizing:border-box}body{margin:auto;max-width:1520px;padding:22px}header{border-bottom:1px solid #40423a;padding-bottom:14px}
h1{color:#c5ff38;margin:0;font-size:26px}p{margin:7px 0;color:#bcbfb0}
section{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,365px),1fr));gap:20px;padding:18px 0}
article{border-top:2px solid #c5ff38;padding-top:8px;min-width:0}article:nth-child(4n+2){border-color:#ff91c5}
article:nth-child(4n+3){border-color:#98c6ff}article:nth-child(4n){border-color:#ffd769}
h2{font-size:17px;margin:0 0 8px}small{color:#bcbfb0;font:12px Consolas,monospace}
.media{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:7px}
figure{margin:0;min-width:0}img{width:100%;aspect-ratio:1;display:block;background:#000;border-radius:6px}
figcaption{font-size:11px;color:#cecfbf;margin-top:4px}article p{font-size:12px}
</style><body><header><h1>AirBoat · 表情动作研究</h1><p>原版关键帧 · 原版动画 · 五段本地动作小样</p></header><section>""" + "\n".join(cards) + "</section></body></html>\n"


def main():
    # Reuse the bounded local preview decoder; this never opens device or secret files.
    from eaf_preview.eaf_preview import decode_eaf
    study = json.loads((OUT / "study.json").read_bytes())
    for folder in ("original","motion-study"):
        (OUT / folder).mkdir(exist_ok=True)
    orig = {r["emote"]:r for r in json.loads((ASSETS/"emote.json").read_bytes())}
    assets = {}
    sources = {}
    for row in list(orig.values())+[{"emote":"listening","src":"listen.eaf","fps":15,"loop":True}]:
        source = row["src"]
        slug = Path(source).stem.lower()
        if slug not in assets:
            a = decode_eaf(ASSETS/source,fps=row["fps"])
            frames = [native_surface(v,(a.width,a.height),slug) for v in a.frames]
            if slug == "listen":
                base = Image.open(OUT/"original/winking.png").convert("RGB")
                frames = [ImageChops.lighter(base,frame) for frame in frames]
            deltas = [0] + [activity(a,b) for a,b in zip(frames,frames[1:])]
            brightest = [f.convert("L").histogram() for f in frames]
            peak = max(range(len(frames)),key=lambda n:deltas[n]+sum(i*x for i,x in enumerate(brightest[n]))/240000)
            if not frames[peak].getbbox():
                peak = next((i for i,f in enumerate(frames) if f.getbbox()),0)
            frames[peak].save(OUT/"original"/f"{slug}.png",optimize=True)
            delay = [round(100*(i+1)/row["fps"])*10 - round(100*i/row["fps"])*10 for i in range(len(frames))]
            if slug == "listen":
                save_gif(frames,OUT/"original"/f"{slug}.gif",delay)
            else:
                save_gif(frames,OUT/"original"/f"{slug}.gif",delay)
            assets[slug] = {"source":source,"slug":slug,"frames":len(frames),"fps":row["fps"],
                            "peak":round(peak*1000/row["fps"]),
                            "change_peaks_ms":[round(i*1000/row["fps"]) for i in sorted(
                                sorted(range(len(frames)),key=deltas.__getitem__,reverse=True)[:5])]}
        if row["emote"] == "listening":
            # Keep a still of the isolated overlay above the same default eye state shown by the workbench.
            pass
        sources[row["emote"]] = {**assets[slug],"native_loop":row["loop"]}
    base = Image.open(OUT/"inputs/airboat-idle-reference.png").convert("RGB")
    art = extract_eyes(base)
    for key, poses in RHYTHM.items():
        frames = [puppet_frame(art,key,n/25) for n in range(math.ceil(poses[-1][0]*25))]
        save_gif(frames,OUT/"motion-study"/f"{key}.gif",40)
    report = {"sources":sources,"motion_studies":RHYTHM_CN, "gif_sampling_hz":25,
              "motion_study_source":"Local transforms of user artwork. No remote generation."}
    (OUT/"motion-analysis.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"index.html").write_text(gallery(study,sources,RHYTHM),encoding="utf-8")
    print(f"{len(sources)} semantic comparisons, {len(assets)} decoded previews, {len(RHYTHM)} motion studies")


if __name__ == "__main__":
    main()
