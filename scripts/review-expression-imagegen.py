"""Check the AirBoat study and render the local comparison gallery."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/imagegen/airboat-expression-study-20261120"


def load(path):
    return json.loads(path.read_bytes())


def verify_hash(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Unexpected file contents: {path}")


def diff(a, b):
    h = ImageChops.difference(a,b).convert("L").histogram()
    return round(sum(i*n for i,n in enumerate(h))/(a.width*a.height),2)


def write_gallery(roles):
    old = load(OUT/"motion-analysis.json")
    e = html.escape
    entries = []
    for role in roles:
        key, label = e(role["key"]), e(role["label"])
        source = old["sources"][key]["slug"]
        trial = (f'<a href="motion-study/{key}.gif">本地节拍小样</a>'
                 if key in old["motion_studies"] else "")
        entries.append(f'<article data-search="{label} {key}"><h2>{label} <small>{key}</small></h2>'
                       f'<div class="media"><figure><a href="original/{source}.gif"><img loading="lazy" alt="{label}原版" src="original/{source}.gif"></a><figcaption>原版</figcaption></figure>'
                       f'<figure><a href="png/{key}.png"><img loading="lazy" alt="{label}参考图" src="png/{key}.png"></a><figcaption>参考图</figcaption></figure>'
                       f'<figure><a href="preview/{key}.gif"><img loading="lazy" alt="{label}新动效" src="preview/{key}.gif"></a><figcaption>新 GIF</figcaption></figure></div>'
                       f'<div class="links"><a href="gif/{key}.gif">API 原生 GIF</a><a href="preview/{key}.png">平涂关键帧</a><a href="prompts/gif-{key}.txt">提示词</a><a href="calls/gif-{key}.json">调用参数</a>{trial}</div></article>')
    tpl = """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AirBoat · 表情动效库</title>
<style>
:root{color-scheme:dark;font:15px/1.5 "Segoe UI","Microsoft YaHei",sans-serif;color:#f4f5eb;background:#101110}
*{box-sizing:border-box}body{margin:auto;max-width:1520px;padding:20px}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid #40423a;padding-bottom:12px}
h1{color:#c5ff38;margin:0;font-size:23px}header nav{display:flex;gap:11px;align-items:center;flex-wrap:wrap}
input{padding:6px 8px;border:1px solid #505249;background:#222;color:inherit;border-radius:5px;font:inherit;min-width:0}
section{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,365px),1fr));gap:20px;padding:18px 0}
article{border-top:2px solid #c5ff38;padding-top:8px;min-width:0}article:nth-child(4n+2){border-color:#ff91c5}
article:nth-child(4n+3){border-color:#98c6ff}article:nth-child(4n){border-color:#ffd769}article[hidden]{display:none}
h2{font-size:17px;margin:0 0 8px}small{color:#bcbfb0;font:12px Consolas,monospace}
.media{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}
figure{margin:0;min-width:0}img{width:100%;aspect-ratio:1;display:block;background:#000;border-radius:5px}
figcaption{font-size:12px;color:#cecfbf;margin-top:4px}.links{display:flex;gap:10px;flex-wrap:wrap;font-size:12px;margin-top:7px}a{color:#c5ff38}
</style>
<body><header><h1>AirBoat · 表情动效库</h1><nav><a href="reference-sheet.png">参考图总览</a><a href="manifest.json">生成记录</a>
<input type="search" id="filter" placeholder="搜索表情" aria-label="搜索表情语义"></nav></header>
<section>__ENTRIES__</section>
<script>
const input=document.querySelector('#filter');
input.addEventListener('input',()=>{const q=input.value.trim().toLowerCase();
  for(const row of document.querySelectorAll('[data-search]'))row.hidden=!row.dataset.search.includes(q)});
</script></body></html>
"""
    (OUT/"gallery.html").write_text(tpl.replace("__ENTRIES__","\n".join(entries)),encoding="utf-8")


def sheet(roles, selected=False):
    font_path = Path("C:/Windows/Fonts/msyh.ttc")
    font = ImageFont.truetype(str(font_path), 15) if font_path.is_file() else ImageFont.load_default()
    if selected:
        keys = {"idle","happy","shocked","confused","look_around","listening"}
        rows = [role for role in roles if role["key"] in keys]
        w, h, edge = 144, 174, 136
    else:
        rows = roles
        w, h, edge = 144, 174, 136
    board = Image.new("RGB",(w*6,h*(len(rows) if selected else (len(rows)+5)//6)),(18,19,17))
    pen = ImageDraw.Draw(board)
    for i, role in enumerate(rows):
        key = role["key"]
        if selected:
            with Image.open(OUT/"preview"/f"{key}.gif") as image:
                frames = []
                for frame in [round((image.n_frames-1)*f/5) for f in range(6)]:
                    image.seek(frame)
                    frames.append(image.convert("RGB"))
        else:
            frames = [Image.open(OUT/"preview"/f"{key}.png").convert("RGB")]
        for j, frame in enumerate(frames):
            x, y = (j*w,i*h) if selected else (i%6*w,i//6*h)
            board.paste(frame.resize((edge,edge),Image.Resampling.LANCZOS),(x+4,y+4))
            pen.text((x+5,y+143),role["label"]+(f" · {1+3*j}" if selected else ""),font=font,fill="#f5f6eb")
    board.save(OUT/("motion-frames.png" if selected else "reference-sheet.png"),optimize=True)


def main():
    source = load(OUT/"study.json")
    roles = [role for group in source["groups"] for role in group["roles"]]
    meta = []
    for group in source["groups"]:
        rec = load(OUT/"calls"/f"static-{group['id']}.json")
        if rec["status"] != "ok" or rec["fields"]["model"] != "gpt-image-2.5-sunburst":
            raise ValueError("Unexpected static generation record")
        verify_hash(OUT/rec["output"],rec["output_sha256"])
        for role in group["roles"]:
            key = role["key"]
            still = OUT/"png"/f"{key}.png"
            gif = OUT/"gif"/f"{key}.gif"
            call = load(OUT/"calls"/f"gif-{key}.json")
            if call["status"] != "ok" or call["fields"]["model"] != "gpt-image-2.6-sunburst":
                raise ValueError("Unexpected GIF generation record")
            for reference in call["inputs"]:
                verify_hash(OUT/reference["path"],reference["sha256"])
            verify_hash(gif,call["output_sha256"])
            with Image.open(still) as image:
                assert image.format == "PNG" and image.size == (480,480)
                image.verify()
            with Image.open(gif) as image:
                assert image.format == "GIF" and image.size == (480,480) and image.n_frames == 16
                loop = image.info.get("loop")
                frames = [f.convert("RGB").resize((120,120),Image.Resampling.BOX) for f in ImageSequence.Iterator(image)]
            assert len({f.tobytes() for f in frames}) > 1
            with Image.open(OUT/"preview"/f"{key}.gif") as preview:
                assert preview.format == "GIF" and preview.size == (480,480) and preview.n_frames > 1
                preview_frames = [f.convert("RGB").resize((120,120),Image.Resampling.BOX)
                                  for f in ImageSequence.Iterator(preview)]
            motion = [diff(a,b) for a,b in zip(frames,frames[1:])]
            still_call = "static-tried-v2" if key == "tried" else f"static-{group['id']}"
            if still_call == "static-tried-v2":
                corrected = load(OUT/"calls"/f"{still_call}.json")
                verify_hash(OUT/corrected["output"],corrected["output_sha256"])
            meta.append({"semantic":key,"reference":still.relative_to(OUT).as_posix(),
                         "animation":gif.relative_to(OUT).as_posix(),"loop":loop,
                         "polished_reference":"preview/"+key+".png","polished_animation":"preview/"+key+".gif",
                         "static_call":f"calls/{still_call}.json","gif_call":f"calls/gif-{key}.json",
                         "adjacent_frame_change_p50":median(motion),"last_first_change":diff(frames[-1],frames[0]),
                         "preview_last_first_change":diff(preview_frames[-1],preview_frames[0])})
    write_gallery(roles)
    sheet(roles)
    sheet(roles,selected=True)
    manifest = {"project":"AirBoat","base":"1.29.0","png":len(meta),"gif":len(meta),"entries":meta}
    transitions = OUT/"transitions/manifest.json"
    if transitions.exists():
        manifest["transitions"] = "transitions/manifest.json"
        table = load(transitions)["entries"]
        for row in meta:
            row["entry_animation"] = table[row["semantic"]]["entry"]["file"]
            row["exit_animation"] = table[row["semantic"]]["exit"]["file"]
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Verified {len(meta)} PNG, {len(meta)} GIF, {len(meta)*16} animation frames")
    print("Highest loop-boundary changes:",[(r["semantic"],r["last_first_change"]) for r in
          sorted(meta,key=lambda r:r["last_first_change"],reverse=True)[:6]])
    print("Highest polished loop-boundary changes:",[(r["semantic"],r["preview_last_first_change"]) for r in
          sorted(meta,key=lambda r:r["preview_last_first_change"],reverse=True)[:6]])
    print("Loop flags:",sorted({r["loop"] for r in meta}))


if __name__ == "__main__":
    main()
