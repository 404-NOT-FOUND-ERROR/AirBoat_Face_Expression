"""Compile the unchanged firmware decoder and read every candidate frame."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler",required=True,type=Path)
    parser.add_argument("--component",required=True,type=Path)
    args = parser.parse_args()
    output = ROOT/".test-output/eaf-decoder"
    output.mkdir(parents=True,exist_ok=True)
    cache = output/"cache"
    env = os.environ.copy()
    env["ZIG_LOCAL_CACHE_DIR"] = str(cache/"local")
    env["ZIG_GLOBAL_CACHE_DIR"] = str(cache/"global")
    exe = output/("eaf-format.exe" if os.name == "nt" else "eaf-format")
    decoder = args.component/"eaf_decoder.c"
    subprocess.run([str(args.compiler),"cc","-std=c11","-O2","-UNDEBUG","-Wall","-Wextra","-Werror",
                    "-I"+str(args.component/"private"),str(decoder),str(ROOT/"tests/eaf-format.c"),
                    "-o",str(exe)],check=True,env=env)
    assets = sorted((ROOT/"output/imagegen/airboat-expression-study-20261120/transitions/eaf-analysis").glob("*.eaf"))
    assert len(assets) == 29
    run = subprocess.run([str(exe),*[str(p) for p in assets]],check=True,capture_output=True,text=True)
    result = json.loads(run.stdout)
    result.update(decoder_sha256=hashlib.sha256(decoder.read_bytes()).hexdigest(),firmware_modified=False)
    (output/"validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
