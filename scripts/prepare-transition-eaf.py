"""Stage selected shared-base EAF candidates in the AirBoat asset catalog."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "output/imagegen/airboat-expression-study-20261120/transitions"
DEFAULT_TARGET = ROOT.parent / "firmware/mosaico-vibe/projects/airboat_baseline/components/app_companion_assets/trial"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    args = parser.parse_args()
    target = args.target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((STUDY / "eaf-analysis/manifest.json").read_bytes())
    rows = []
    for item in catalog["candidate_assets"]:
        semantic = item["semantic"]
        if semantic == "neutral":
            continue
        source = STUDY / "eaf-analysis" / item["file"]
        asset_name = f"transition-{semantic}.eaf"
        shutil.copyfile(source, target / asset_name)
        semantics = ["neutral", "idle"] if semantic == "idle" else [semantic]
        rows.append({
            "file": asset_name,
            "source": f"{semantic}.gif",
            "sha256": hashlib.sha256((target / asset_name).read_bytes()).hexdigest(),
            "bytes": (target / asset_name).stat().st_size,
            "frames": item["frames"],
            "period_ms": item["period_ms"],
            "entry_frames": item["entry_frames"],
            "loop_frames": item["loop_frames"],
            "exit_frames": item["exit_frames"],
            "semantics": semantics,
            "fill_square": True,
            "mirror": item["mirror"],
        })
    (target / "manifest.json").write_text(json.dumps({"canvas": 240, "assets": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": len(rows), "bytes": sum(row["bytes"] for row in rows), "target": str(target)}))


if __name__ == "__main__":
    main()
