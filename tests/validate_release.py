"""Verify the portable catalog, artwork manifests and local document links."""
import hashlib
import base64
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT/"output/imagegen/airboat-expression-study-20261120"
TRANSITIONS = STUDY/"transitions"


def load(path):
    return json.loads(path.read_bytes())


def check_hash(path, expected):
    assert path.is_file(), str(path.relative_to(ROOT))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path.relative_to(ROOT))


def main():
    subprocess.run([sys.executable,str(ROOT/"scripts/build-expression-workbench.py"),"--check"],check=True)
    manifest = load(STUDY/"manifest.json")
    assert manifest["png"] == manifest["gif"] == len(manifest["entries"]) == 29
    for row in manifest["entries"]:
        for label in ("reference","polished_reference","animation","polished_animation"):
            with Image.open(STUDY/row[label]) as image:
                assert image.size == (480,480)
                if label in {"animation","polished_animation"}:
                    assert image.format == "GIF" and image.n_frames > 1 and image.info["loop"] == 0
                    assert len({image.seek(i) or image.convert("RGB").tobytes() for i in range(image.n_frames)}) > 1
        for key in ("static_call","gif_call"):
            record = load(STUDY/row[key])
            assert record["status"] == "ok"
            check_hash(STUDY/record["output"],record["output_sha256"])
            for item in record["inputs"]:
                check_hash(STUDY/item["path"],item["sha256"])
    transitions = load(TRANSITIONS/"manifest.json")
    assert transitions["fps"] == 25 and transitions["transition_duration_ms"] == 360
    base_path = STUDY/transitions["base"]["image"]
    with Image.open(base_path) as base_image:
        base_frame = base_image.convert("RGB").tobytes()
    check_hash(base_path,transitions["base"]["sha256"])
    for semantic,item in transitions["entries"].items():
        entry_path = TRANSITIONS/Path(item["entry"]["file"]).relative_to("transitions")
        loop_path = STUDY/item["loop"]["file"]
        exit_path = STUDY/item["exit"]["file"]
        with Image.open(entry_path) as entry:
            assert 1 <= entry.n_frames <= 9 and sum((entry.seek(i) or entry.info.get("duration",40)) for i in range(entry.n_frames)) == 360, semantic
            entry.seek(0); assert entry.convert("RGB").tobytes() == base_frame, semantic
            entry.seek(entry.n_frames-1); enter_end = entry.convert("RGB").tobytes()
        with Image.open(loop_path) as loop:
            loop.seek(0); loop_start = loop.convert("RGB").tobytes()
        assert enter_end == loop_start, semantic
        with Image.open(exit_path) as exit_clip:
            assert 1 <= exit_clip.n_frames <= 9 and sum((exit_clip.seek(i) or exit_clip.info.get("duration",40)) for i in range(exit_clip.n_frames)) == 360, semantic
            exit_clip.seek(0); assert exit_clip.convert("RGB").tobytes() == loop_start, semantic
            exit_clip.seek(exit_clip.n_frames-1); assert exit_clip.convert("RGB").tobytes() == base_frame, semantic
    assert {"listening>thinking","thinking>happy","happy>surprised"} <= set(transitions["bridges"])
    for item in transitions["bridges"].values():
        with Image.open(STUDY/item["file"]) as bridge:
            bridge.seek(0); start = bridge.convert("RGB").tobytes()
            bridge.seek(bridge.n_frames-1); end = bridge.convert("RGB").tobytes()
        with Image.open(STUDY/transitions["entries"][item["from"]]["loop"]["file"]) as a:
            assert start == a.convert("RGB").tobytes()
        with Image.open(STUDY/transitions["entries"][item["to"]]["loop"]["file"]) as b:
            assert end == b.convert("RGB").tobytes()
    runtime = STUDY/"transitions/runtime-data.js"
    assert runtime.is_file() and runtime.stat().st_size > 100_000
    assert "window.AIRBOAT_FACE_MOTION_GZIP =" in runtime.read_text(encoding="utf-8")
    packed = re.fullmatch(r'window.AIRBOAT_FACE_MOTION_GZIP = "([A-Za-z0-9+/=]+)";\s*',runtime.read_text(encoding="utf-8"))
    assert packed, "Invalid offline runtime wrapper"
    dataset = json.loads(gzip.decompress(base64.b64decode(packed[1])))
    assert dataset["version"] == "airboat.face-motion.v1" and dataset["transition_ms"] == 360
    assert set(dataset["clips"]) == set(transitions["entries"])
    for key,clip in dataset["clips"].items():
        assert len(clip["frames"]) == len(clip["durations"]) and clip["duration_ms"] == sum(clip["durations"]), key
        assert all(ms > 0 for ms in clip["durations"]), key
        for frame in clip["frames"]:
            assert len(frame["layers"]) == 4, key
            assert frame["accent"] is None or 0 <= frame["accent"] < len(dataset["accents"]), key
            for layer in filter(None,frame["layers"]):
                assert 0 <= layer[0] < len(dataset["masks"]) and len(layer) == 5, key
    assert all(len(base64.b64decode(mask)) == dataset["mask_side"]**2//8 for mask in dataset["masks"])
    eaf_manifest = STUDY/"transitions/eaf-analysis/manifest.json"
    if eaf_manifest.exists():
        candidate = load(eaf_manifest)
        assert len(candidate["candidate_assets"]) == 29
        assert candidate["total_bytes"] == sum(row["bytes"] for row in candidate["candidate_assets"])
        for row in candidate["candidate_assets"]:
            check_hash(STUDY/"transitions/eaf-analysis"/row["file"],row["sha256"])
            assert row["entry_frames"][0] == 0 and row["entry_frames"][1] == row["loop_frames"][0]
            assert row["loop_frames"][1] == row["exit_frames"][0] < row["exit_frames"][1] == row["frames"]
            assert row["period_ms"] == 50 and row["fill_square"] and not row["mirror"]
    checked = 0
    for file in ROOT.rglob("*"):
        if file.suffix not in {".html",".md"} or ".git" in file.parts:
            continue
        text = file.read_text(encoding="utf-8")
        urls = re.findall(r'(?:href|src)="([^"]+)"',text) if file.suffix == ".html" else [
            x.strip("<>") for x in re.findall(r'\]\(([^)]+)\)',text)]
        for url in urls:
            if urlsplit(url).scheme or url.startswith("#") or not url:
                continue
            target = (file.parent/unquote(urlsplit(url).path)).resolve()
            assert target.is_relative_to(ROOT), str(file.relative_to(ROOT))+" -> "+url
            assert target.exists(), str(file.relative_to(ROOT))+" -> "+url
            checked += 1
    print(f"Release passed: 29 expression studies, shared-frame transitions, native/refined animations, {checked} local links")


if __name__ == "__main__":
    main()
