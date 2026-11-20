"""Build reproducible 25 fps GIFs from the browser's actual shape renderer."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"output/imagegen/airboat-expression-study-20261120/transitions/demos"


def main():
    OUT.mkdir(exist_ok=True)
    rows = {}
    for directory in sorted((ROOT/".test-output/transition-demo-frames").iterdir()):
        files = sorted(directory.glob("*.png"))
        if not files:
            continue
        frames = [Image.open(p).convert("RGB") for p in files]
        assert frames[0].tobytes() == frames[-1].tobytes(), directory.name
        atlas = Image.new("RGB",(len(frames)*32,32))
        for i,frame in enumerate(frames):
            atlas.paste(frame.resize((32,32)),(i*32,0))
        palette = atlas.quantize(colors=256)
        indexed = [frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
        dest = OUT/(directory.name+".gif")
        indexed[0].save(dest,save_all=True,append_images=indexed[1:],duration=40,loop=0,optimize=False)
        rows[directory.name] = {"file":dest.name,"fps":25,"duration_ms":len(frames)*40,"source":"browser shape renderer",
                                "sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
    (OUT/"manifest.json").write_text(json.dumps(rows,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(rows))


if __name__ == "__main__":
    main()
