"""Package approved GIF shapes for an offline, interruptible canvas player."""
import base64
import hashlib
import gzip
import importlib.util
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"output/imagegen/airboat-expression-study-20261120"
SIDE = 160


def main():
    spec = importlib.util.spec_from_file_location("polish",ROOT/"scripts/polish-expression-gifs.py")
    polish = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(polish)
    masks, indices, accents, accent_indices = [], {}, [], {}

    def pack_sprite(sprite):
        if sprite is None:
            return None
        image,box = sprite
        normalized = np.asarray(image.resize((SIDE,SIDE),Image.Resampling.LANCZOS)) >= 128
        bits = np.packbits(normalized).tobytes()
        digest = hashlib.sha256(bits).hexdigest()
        if digest not in indices:
            indices[digest] = len(masks)
            masks.append(base64.b64encode(bits).decode("ascii"))
        return [indices[digest],*box]

    def pack_accent(image):
        if not image.getbbox():
            return None
        buffer = io.BytesIO()
        image.save(buffer,format="PNG",optimize=True)
        png = buffer.getvalue()
        digest = hashlib.sha256(png).hexdigest()
        if digest not in accent_indices:
            accent_indices[digest] = len(accents)
            accents.append("data:image/png;base64,"+base64.b64encode(png).decode("ascii"))
        return accent_indices[digest]

    clips = {}
    for key,color in polish.COLORS.items():
        with Image.open(OUT/"preview"/f"{key}.gif") as gif:
            frames, durations = [], []
            for frame in ImageSequence.Iterator(gif):
                pose,accent = polish.channels(frame.convert("RGB"),key)
                frames.append({"layers":[pack_sprite(pose[e][layer]) for e in (0,1) for layer in (0,1)],
                               "accent":pack_accent(accent)})
                durations.append(frame.info.get("duration",90))
        clips[key] = {"color":color,"frames":frames,"durations":durations,"duration_ms":sum(durations)}
    data = {"version":"airboat.face-motion.v1","side":480,"mask_side":SIDE,"base":"idle",
            "transition_ms":360,"fps":25,"masks":masks,"accents":accents,"clips":clips}
    dest = OUT/"transitions/runtime-data.js"
    raw = json.dumps(data,separators=(",",":")).encode("utf-8")
    packed = gzip.compress(raw,compresslevel=9,mtime=0)
    dest.write_text("window.AIRBOAT_FACE_MOTION_GZIP = \""+base64.b64encode(packed).decode("ascii")+"\";\n",encoding="utf-8")
    print(json.dumps({"clips":len(clips),"masks":len(masks),"accents":len(accents),
                      "uncompressed_bytes":len(raw),"gzip_bytes":len(packed),"script_bytes":dest.stat().st_size}))


if __name__ == "__main__":
    main()
