"""Package the AirBoat expression catalog for the offline design workbench."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets/native"
SAMPLES = ROOT / "mosaico-eaf-480"
OUTPUT = ROOT / "docs/product/expression-workbench-data.js"
DEFAULT_REPORT = ROOT / "docs/reference/firmware-baseline-1.29.0.json"


def read_json(path: Path):
    return json.loads(path.read_bytes())


def checked(path: Path, expected: dict) -> bytes:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected["sha256"] or len(raw) != expected["bytes"]:
        raise ValueError(f"Asset manifest mismatch: {path}")
    return raw


def inspect_eaf(raw: bytes) -> dict:
    count, checksum, payload = struct.unpack_from("<III", raw, 4)
    if raw[:4] != b"\x89EAF" or payload != len(raw) - 16 or checksum != sum(raw[16:]):
        raise ValueError("Invalid EAF container")
    start = 16 + count * 8
    sizes = set()
    frames = 0
    for i in range(count):
        length, offset = struct.unpack_from("<II", raw, 16 + i * 8)
        offset += start
        tag = raw[offset:offset+4]
        if length < 4 or offset + length > len(raw) or tag not in {b"ZZ_C", b"ZZ_S"}:
            raise ValueError("Invalid EAF entry")
        if tag == b"ZZ_S":
            if length < 20 or raw[offset + 11] != 8:
                raise ValueError("Expected indexed EAF frame")
            sizes.add(struct.unpack_from("<HH", raw, offset + 12))
            frames += 1
    if len(sizes) != 1:
        raise ValueError("Expected a fixed nonempty canvas")
    (width, height), = sizes
    return {"width": width, "height": height, "frames": frames, "entries": count}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Verified build compatibility report")
    parser.add_argument("--check", action="store_true", help="Check the existing snapshot without writing")
    args = parser.parse_args()
    source = read_json(ASSETS / "source-manifest.json")
    catalog_path = ASSETS / "assets/emote.json"
    if hashlib.sha256(catalog_path.read_bytes()).hexdigest() != source["catalog_sha256"]:
        raise ValueError("Original catalog hash mismatch")
    catalog = read_json(catalog_path)
    assets = {}
    original = {row["emote"]: {
        "file": row["src"], "fps": row["fps"], "loop": row["loop"],
    } for row in catalog}
    current = dict(original)
    for directory, inventory in (
        ("assets", source["assets"]), ("trial", read_json(ASSETS / "trial/manifest.json")["assets"]),
    ):
        for entry in inventory:
            name = entry["file"]
            raw = checked(ASSETS / directory / name, entry)
            meta = inspect_eaf(raw)
            assets[name] = {**meta, "bytes": len(raw), "sha256": entry["sha256"],
                            "kind": directory, "eaf": base64.b64encode(raw).decode("ascii")}
            if directory == "trial":
                if entry["frames"] != meta["frames"]:
                    raise ValueError(f"Trial frame count mismatch: {name}")
                for semantic in entry["semantics"]:
                    if current[semantic] is not original[semantic]:
                        raise ValueError(f"Duplicate trial binding: {semantic}")
                    current[semantic] = {
                        "file": name, "fps": 1000 / entry["period_ms"], "loop": True,
                        "range": entry["loop_frames"], "fill": True,
                    }
    expected = {row["file"] for row in original.values()} | {"listen.eaf"}
    if expected != {name for name, asset in assets.items() if asset["kind"] == "assets"}:
        raise ValueError("Original mapping and asset inventory disagree")
    candidates = {}
    for item in read_json(SAMPLES / "source-manifest.json"):
        name = item["name"]
        candidate = SAMPLES / "eaf" / f"{name}.eaf"
        gif = SAMPLES / "source-gif" / item["source_file"]
        candidates[name] = {
            **item, "gif": "../../" + gif.relative_to(ROOT).as_posix(),
            "source_sha256": hashlib.sha256(gif.read_bytes()).hexdigest(),
            "eaf_bytes": candidate.stat().st_size,
        }
    report = read_json(args.report)
    if not report["passed"]:
        raise ValueError("Use a passing compatibility report")
    priorities, timing, recipes = (report[key] for key in ("priorities", "timing", "recipes"))
    data = {
        "version": report["version"], "revision": source["source_revision"],
        "license": (ASSETS / "LICENSE.assets").read_text(encoding="utf-8"),
        "report": "../../" + args.report.resolve().relative_to(ROOT).as_posix(),
        "budget": {key: report[key] for key in
                   ("main_app_bytes", "main_app_remaining", "ui_apps_bytes", "ui_apps_remaining")},
        "assets": assets, "original": original, "current": current, "candidates": candidates,
        "priorities": priorities, "timing": timing, "recipes": recipes,
    }
    content = "// Generated by scripts/build-expression-workbench.py.\nwindow.AIRBOAT_EXPRESSIONS = "
    content += json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("Snapshot is stale; regenerate it")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{len(original)} semantics; {len(expected)} original and {len(assets)-len(expected)} trial EAF; "
          f"{len(candidates)} source GIF; {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
