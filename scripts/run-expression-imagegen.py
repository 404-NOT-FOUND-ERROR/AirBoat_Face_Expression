"""Generate AirBoat reference artwork and GIFs through a local HTTP proxy."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/imagegen/airboat-expression-study-20261120"
CONFIG = None
CLI = Path.home() / ".codex/skills/.system/imagegen/scripts/image_gen.py"
API = "https://api.openai.com/v1"
PROXY = "http://127.0.0.1:7897"
PILOT = {"idle", "happy", "shocked", "confused", "look_around"}
BASE = OUT / "inputs/airboat-idle-reference.png"


def configuration():
    values = {}
    for line in CONFIG.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and key in {"DESKBOT_IMAGE_API_KEY", "DESKBOT_IMAGE_BASE_URL", "DESKBOT_IMAGE_MODEL"}:
            values[key] = value.strip().strip('"').strip("'")
    if values.get("DESKBOT_IMAGE_BASE_URL", "").rstrip("/") != API:
        raise ValueError("The image endpoint must be the official OpenAI endpoint")
    key = values.get("DESKBOT_IMAGE_API_KEY")
    if not key:
        raise ValueError("The image credential is missing")
    return key


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name, data):
    path = OUT / "calls" / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_error(exc):
    code = getattr(exc, "code", None)
    return {
        "exception": type(exc).__name__,
        "http_status": getattr(exc, "status_code", None),
        "code": code if isinstance(code, str) and re.fullmatch("[a-z0-9_]{1,70}", code) else None,
        "request_id": getattr(exc, "request_id", None),
    }


def static(group, key):
    name = "static-" + group["id"]
    dest = OUT / "raw" / (name + ".png")
    path = OUT / "prompts" / (name + ".txt")
    fields = dict(model="gpt-image-2.5-sunburst", size="1024x1024", quality="medium", output_format="png", n=1)
    receipt = {"endpoint": API + "/images/edits", "proxy": PROXY, "fields": fields,
               "prompt": path.relative_to(OUT).as_posix(), "inputs": [{"path": BASE.relative_to(OUT).as_posix(), "sha256": digest(BASE)}]}
    if not dest.exists():
        env = {**os.environ, "OPENAI_API_KEY": key, "OPENAI_BASE_URL": API, "HTTPS_PROXY": PROXY,
               "HTTP_PROXY": PROXY, "NO_PROXY": "", "PYTHONUTF8": "1"}
        args = [sys.executable, str(CLI), "edit", "--model", fields["model"], "--image", str(BASE),
                "--prompt-file", str(path), "--no-augment", "--size", fields["size"], "--quality", fields["quality"],
                "--output-format", fields["output_format"], "--n", str(fields["n"]), "--out", str(dest)]
        started = time.monotonic()
        try:
            result = subprocess.run(args, env=env, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=190)
            if result.returncode:
                codes = re.findall(r"Error code: \d{3}|AuthenticationError|PermissionDeniedError|APIConnectionError|"
                                   r"RateLimitError|BadRequestError|ModuleNotFoundError|ImportError|"
                                   r"invalid_api_key|model_not_found|insufficient_quota", result.stderr)
                record(name, {**receipt, "status":"error", "codes":sorted(set(codes))})
                print(f"{name} error: {' '.join(sorted(set(codes))) or 'CLI exit '+str(result.returncode)}", flush=True)
                return False
        except Exception as exc:
            record(name, {**receipt, "status":"error", **safe_error(exc)})
            print(f"{name} error: {type(exc).__name__}", flush=True)
            return False
        receipt.update(status="ok", duration_s=round(time.monotonic()-started, 2),
                       output=dest.relative_to(OUT).as_posix(), output_sha256=digest(dest))
        record(name, receipt)
    with Image.open(dest) as sheet:
        if sheet.format != "PNG" or sheet.width != sheet.height:
            print(f"{name} unexpected image dimensions", flush=True)
            return False
        half = sheet.width // 2
        for i, role in enumerate(group["roles"]):
            x, y = (i % 2) * half, (i // 2) * half
            final = OUT / "png" / (role["key"]+".png")
            sheet.crop((x,y,x+half,y+half)).convert("RGB").resize((480,480),Image.Resampling.LANCZOS).save(final,optimize=True)
    print(f"{name} ok", flush=True)
    return True


def tired_fix(key):
    name = "static-tried-v2"
    dest = OUT / "raw" / (name + ".png")
    path = OUT / "prompts" / (name + ".txt")
    fields = dict(model="gpt-image-2.5-sunburst", size="1024x1024", quality="medium", output_format="png", n=1)
    env = {**os.environ, "OPENAI_API_KEY": key, "OPENAI_BASE_URL": API, "HTTPS_PROXY": PROXY,
           "HTTP_PROXY": PROXY, "NO_PROXY": "", "PYTHONUTF8": "1"}
    args = [sys.executable,str(CLI),"edit","--model",fields["model"],"--image",str(BASE),
            "--prompt-file",str(path),"--no-augment","--size",fields["size"],"--quality",fields["quality"],
            "--output-format",fields["output_format"],"--n","1","--out",str(dest)]
    if not dest.exists():
        before = time.monotonic()
        run = subprocess.run(args,env=env,capture_output=True,timeout=190)
        if run.returncode:
            print("Static correction CLI returned",run.returncode,flush=True)
            return False
        record(name,{"endpoint": API+"/images/edits","proxy":PROXY,"fields":fields,"status":"ok",
                     "prompt":path.relative_to(OUT).as_posix(),"inputs":[{"path":BASE.relative_to(OUT).as_posix(),"sha256":digest(BASE)}],
                     "output":dest.relative_to(OUT).as_posix(),"output_sha256":digest(dest),"duration_s":round(time.monotonic()-before,2)})
    with Image.open(dest) as ref:
        ref.convert("RGB").resize((480,480),Image.Resampling.LANCZOS).save(OUT/"png"/"tried.png",optimize=True)
    return True


def animate(role, key, assets_ready):
    from httpx2 import Client
    from openai import OpenAI

    tag = role["key"]
    dest = OUT / "gif" / (tag+".gif")
    still = OUT / "png" / (tag+".png")
    reference = still if assets_ready and still.is_file() else BASE
    if dest.exists():
        receipt = json.loads((OUT/"calls"/("gif-"+tag+".json")).read_bytes())
        if receipt.get("status") == "ok" and (not assets_ready or
            receipt["inputs"][0]["path"] == still.relative_to(OUT).as_posix() and receipt["inputs"][0]["sha256"] == digest(still)):
            return True
        import shutil
        shutil.copy2(dest,OUT/"raw"/("gif-"+tag+"-first.gif"))
        shutil.copy2(OUT/"calls"/("gif-"+tag+".json"),OUT/"calls"/("gif-"+tag+"-first.json"))
    path = OUT / "prompts" / ("gif-"+tag+".txt")
    output = "gif"
    tempo = 120 if tag in {"idle","relaxed","sleepy","tried","sad","crying"} else 90
    fields = dict(model="gpt-image-2.6-sunburst", size="480x480", quality="medium",
                  complexity="medium", output_format=output, frame_count=16, frame_duration_ms=tempo, n=1)
    prompt = path.read_text(encoding="utf-8")
    receipt = {"endpoint": API + "/images/edits", "proxy": PROXY, "fields": fields,
               "prompt": path.relative_to(OUT).as_posix(),
               "inputs":[{"path":reference.relative_to(OUT).as_posix(),"sha256":digest(reference)}]}
    started = time.monotonic()
    try:
        with Client(proxy=PROXY, trust_env=False, timeout=175) as transport:
            with OpenAI(api_key=key, base_url=API, max_retries=0, http_client=transport, timeout=175) as client:
                with reference.open("rb") as source:
                    response = client.images.with_raw_response.edit(image=source, prompt=prompt, **fields)
                data = base64.b64decode(response.parse().data[0].b64_json,validate=True)
        from io import BytesIO
        with Image.open(BytesIO(data)) as result:
            if result.format != "GIF" or result.n_frames < 2:
                raise ValueError("Images returned no animated GIF")
            receipt.update(width=result.width, height=result.height, frames=result.n_frames,
                           loop=result.info.get("loop"),
                           delays_ms=[result.info.get("duration") for i in range(result.n_frames) if result.seek(i) is None])
        dest.write_bytes(data)
        receipt.update(status="ok", duration_s=round(time.monotonic()-started,2), request_id=response.headers.get("x-request-id"),
                       output=dest.relative_to(OUT).as_posix(), output_sha256=digest(dest))
        record("gif-"+tag,receipt)
        print(f"gif-{tag} ok ({receipt['frames']} frames)",flush=True)
        return True
    except Exception as exc:
        issue = safe_error(exc)
        # Print no headers, response body, request, environment or key.
        print(f"gif-{tag} error: {issue}",flush=True)
        record("gif-"+tag,{**receipt,"status":"error",**issue})
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=["static","pilot","gif","probe","correct-tried"])
    parser.add_argument("--only",nargs="+",default=[])
    parser.add_argument("--workers",type=int,default=3,choices=range(1,9))
    parser.add_argument("--env-file", type=Path, required=True,
                        help="Local environment file with DESKBOT_IMAGE_API_KEY and DESKBOT_IMAGE_BASE_URL")
    parser.add_argument("--proxy", default=PROXY, help="Local HTTP proxy URL")
    parser.add_argument("--cli", type=Path, default=CLI, help="Official imagegen skill CLI")
    args = parser.parse_args()
    globals().update(CONFIG=args.env_file, PROXY=args.proxy, CLI=args.cli)
    key = configuration()
    groups = json.loads((OUT/"study.json").read_bytes())["groups"]
    roles = [role for group in groups for role in group["roles"]]
    if args.stage == "correct-tried":
        raise SystemExit(0 if tired_fix(key) else 1)
    if args.stage == "probe":
        from httpx2 import Client
        import openai
        try:
            with Client(proxy=PROXY, trust_env=False, timeout=18) as transport:
                with openai.OpenAI(api_key=key,base_url=API,max_retries=0,http_client=transport,timeout=18) as client:
                    found = {model.id for model in client.models.list()}
            print("Clash proxy authenticated: static="+str("gpt-image-2.5-sunburst" in found)
                  +" GIF="+str("gpt-image-2.6-sunburst" in found))
            return
        except Exception as exc:
            print("Clash probe failed:",safe_error(exc))
            raise SystemExit(1) from None
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        if args.stage == "static":
            jobs = [group for group in groups if not args.only or group["id"] in args.only]
            results = list(pool.map(lambda group:static(group,key),jobs))
        else:
            jobs = [role for role in roles if (not args.only or role["key"] in args.only)
                    and (args.stage != "pilot" or role["key"] in PILOT)]
            results = list(pool.map(lambda role:animate(role,key,args.stage=="gif"),jobs))
    print(f"{sum(results)}/{len(jobs)} completed",flush=True)
    raise SystemExit(0 if results and all(results) else 1)


if __name__ == "__main__":
    main()
