"""Exercise the actual AirBoat EAF player with the local patch in a scratch copy."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from eaf_preview.eaf_preview import compose_display_frame, decode_eaf


def fnv(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return f"{value:016x}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--zig", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    component = project / "components/app_expression_player"
    assets = project / "components/app_companion_assets"
    output.mkdir(parents=True, exist_ok=True)
    before = (component / "app_expression_player.c").read_text(encoding="utf-8")
    before_hash = hashlib.sha256(before.encode()).hexdigest()
    patch = ROOT / "integrations/listen-overlay/airboat-player.patch"
    # Apply the shipped patch to a disposable directory, never the app checkout.
    patch_root = output / "patch"
    dest = patch_root / "components/app_expression_player"
    (dest / "private").mkdir(parents=True, exist_ok=True)
    (dest / "app_expression_player.c").write_text(before, encoding="utf-8")
    run = lambda command, **kwargs: subprocess.run(command, check=True, **kwargs)
    run(["git", "apply", "--unsafe-paths", str(patch)], cwd=patch_root, capture_output=True, text=True)
    patched = dest / "app_expression_player.c"
    header = dest / "private/listen_overlay_rgb565.h"
    assert header.read_bytes() == (ROOT / "integrations/listen-overlay/listen_overlay_rgb565.h").read_bytes()
    generated = output / "assets.c"
    run([sys.executable, str(assets / "tools/embed.py"), "--baseline", "--output", str(generated)], capture_output=True, text=True)
    executable = output / ("test-player.exe" if sys.platform == "win32" else "test-player")
    run([str(args.zig.resolve()), "cc", "-std=c11", "-O2", "-UNDEBUG", "-Wall", "-Wextra", "-Werror",
         "-I" + str(component / "include"), "-I" + str(component / "private"),
         "-I" + str(dest / "private"), "-I" + str(assets / "include"),
         str(patched), str(component / "eaf_decoder.c"), str(generated),
         str(component / "host/test_player.c"), "-o", str(executable)], capture_output=True, text=True)
    result = run([str(executable), str(output)], capture_output=True, text=True)
    (output / "native.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    observed = {}
    for line in result.stdout.splitlines():
        if line.startswith("frame: "):
            _, name, frame, digest = line.split()
            observed[name, int(frame)] = digest
    decoded = {}
    for item in json.loads((assets / "source-manifest.json").read_bytes())["assets"]:
        animation = decode_eaf(assets / "assets" / item["file"])
        decoded[item["file"]] = animation
        for index, frame in enumerate(animation.frames):
            assert observed[item["file"], index] == fnv(frame), (item["file"], index)
    catalog = json.loads((assets / "assets/emote.json").read_bytes())
    checks = ["happy", "eat", "look_left", "idle", "listen"]
    for name in checks:
        semantic = "neutral" if name == "listen" else name
        file = next(row["src"] for row in catalog if row["emote"] == semantic)
        animation = decoded[file]
        rgba = compose_display_frame(animation.frames[5], animation.width, animation.height,
                                     object_kind="eye" if animation.width < 200 else "dialog")
        expected = []
        for i in range(0, len(rgba), 4):
            r, g, b, a = rgba[i:i+4]
            expected.append(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3) if a else 0)
        if name == "listen":
            overlay = decoded["listen.eaf"]
            mask = compose_display_frame(overlay.frames[3], overlay.width, overlay.height, object_kind="listen")
            for i in range(0, len(mask), 4):
                if not mask[i+3]:
                    continue
                base = expected[i//4]
                r, g, b = mask[i:i+3]
                br, bg, bb = base >> 11, (base >> 5) & 63, base & 31
                expected[i//4] = ((br + ((31-br)*(r >> 3)+15)//31) << 11 |
                                 (bg + ((63-bg)*(g >> 2)+31)//63) << 5 |
                                 (bb + ((31-bb)*(b >> 3)+15)//31))
        raw = b"".join(pixel.to_bytes(2, "little") for pixel in expected)
        assert (output / f"{name}.rgb565").read_bytes() == raw, name
    assert hashlib.sha256((component / "app_expression_player.c").read_text(encoding="utf-8").encode()).hexdigest() == before_hash
    summary = {"status": "passed", "source_copy": True, "app_checkout_modified": False,
               "unique_assets": len(decoded), "unique_frames": sum(len(a.frames) for a in decoded.values()),
               "pixel_layouts": checks, "original_player_test": True, "partitioned_draw": True,
               "device_operations": 0}
    (output / "validation.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
