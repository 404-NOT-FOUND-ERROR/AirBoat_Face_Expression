"""Verify the portable catalog, artwork manifests and local document links."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT/"output/imagegen/airboat-expression-study-20261120"


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
    print(f"Release passed: 29 expression studies, native/refined animations, {checked} local links")


if __name__ == "__main__":
    main()
