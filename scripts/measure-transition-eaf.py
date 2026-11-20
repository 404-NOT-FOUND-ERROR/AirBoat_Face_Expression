"""Measure an indexed EAF delivery without changing firmware or source GIFs."""
import hashlib
from itertools import groupby
import json
from pathlib import Path
import struct

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT/"output/imagegen/airboat-expression-study-20261120"
DEST = STUDY/"transitions/eaf-analysis"
SIDE = 240
PERIOD = 50


def encode(frame):
    indexed = frame.convert("RGB").resize((SIDE,SIDE),Image.Resampling.BOX).quantize(colors=16,dither=Image.Dither.NONE)
    rgb = indexed.getpalette()
    palette = bytes(c for r,g,b in zip(rgb[0::3],rgb[1::3],rgb[2::3]) for c in (b,g,r,255)).ljust(1024,b"\0")
    pixels,blocks = indexed.tobytes(),[]
    for start in range(0,len(pixels),SIDE*32):
        data = bytearray(b"\0")
        for value,run in groupby(pixels[start:start+SIDE*32]):
            count = sum(1 for _ in run)
            while count>255:
                data.extend((255,value)); count-=255
            data.extend((count,value))
        blocks.append(bytes(data))
    return b"ZZ_S"+bytes(7)+b"\x08"+struct.pack("<4H",SIDE,SIDE,len(blocks),32)+b"".join(struct.pack("<I",len(b)) for b in blocks)+palette+b"".join(blocks)


def sample(path):
    frames,durations = [],[]
    with Image.open(path) as gif:
        for frame in ImageSequence.Iterator(gif):
            frames.append(frame.convert("RGB")); durations.append(frame.info.get("duration",40))
    count = (sum(durations)+PERIOD-1)//PERIOD
    result,frame,end = [],0,durations[0]
    for i in range(count):
        at = i*PERIOD
        while frame<len(frames)-1 and at>=end:
            frame+=1; end+=durations[frame]
        result.append(frames[frame])
    return result


def container(frames):
    payload,table,seen = bytearray(),bytearray(),{}
    for frame in frames:
        raw = encode(frame)
        if raw not in seen:
            seen[raw] = len(payload); payload.extend(raw)
        table.extend(struct.pack("<II",len(raw),seen[raw]))
    body = table+payload
    return b"\x89EAF"+struct.pack("<III",len(frames),sum(body)&0xffffffff,len(body))+body


def main():
    manifest = json.loads((STUDY/"transitions/manifest.json").read_bytes())
    DEST.mkdir(exist_ok=True)
    rows = []
    for key,item in manifest["entries"].items():
        entry = sample(STUDY/item["entry"]["file"])
        loop = sample(STUDY/item["loop"]["file"])
        exit_frames = sample(STUDY/item["exit"]["file"])
        raw = container(entry+loop+exit_frames)
        file = f"{key}.eaf"
        (DEST/file).write_bytes(raw)
        rows.append({"semantic":key,"file":file,"bytes":len(raw),"frames":len(entry+loop+exit_frames),
                     "entry_frames":[0,len(entry)],"loop_frames":[len(entry),len(entry)+len(loop)],
                     "exit_frames":[len(entry)+len(loop),len(entry)+len(loop)+len(exit_frames)],
                     "period_ms":PERIOD,"fill_square":True,"mirror":False,
                     "sha256":hashlib.sha256(raw).hexdigest()})
    result = {"canvas":SIDE,"period_ms":PERIOD,"total_bytes":sum(r["bytes"] for r in rows),
              "candidate_assets":rows,"status":"offline-format-and-budget-probe",
              "firmware_budget_reference":{"version":"1.29.1","remaining_bytes":175424},
              "runtime_note":"Intro/loop/outro table only; graceful-exit state machine still required in firmware."}
    native = ROOT/"assets/native"
    sources = json.loads((native/"source-manifest.json").read_bytes())
    trial = json.loads((native/"trial/manifest.json").read_bytes())
    catalog = json.loads((native/"assets/emote.json").read_bytes())
    assignments = {row["emote"]:row["src"] for row in catalog}
    sizes = {row["file"]:row["bytes"] for row in sources["assets"]}
    for row in trial["assets"]:
        sizes[row["file"]] = row["bytes"]
        for semantic in row["semantics"]:
            assignments[semantic] = row["file"]
    current = sum(sizes[name] for name in set(assignments.values())|{"listen.eaf"})
    result["replacement_estimate"] = {"current_unique_eaf_bytes":current,
        "candidate_eaf_bytes":result["total_bytes"],"resource_bytes_released":current-result["total_bytes"],
        "estimate_only":True,"reference_catalog":"AirBoat 1.29.0 expression trial catalog",
        "note":"Candidate includes full-face listening. Linker/code costs and on-device performance need a build."}
    (DEST/"manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"assets":len(rows),"total_bytes":result["total_bytes"],"max_bytes":max(r["bytes"] for r in rows)}))


if __name__ == "__main__":
    main()
