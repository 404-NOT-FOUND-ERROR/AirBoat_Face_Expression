"""Prepare local references and prompts for the AirBoat expression art pass."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/imagegen/airboat-expression-study-20261120"
ROWS = [
    ("neutral", "默认", "two fully open round eyes, centered pupils", "small anticipatory uplift, one soft blink, settle", "electric lime"),
    ("idle", "待机", "relaxed open eyes with slightly low pupils", "slow float down, lazy double blink, settle", "electric lime"),
    ("listening", "聆听", "attentive open eyes looking ahead; small cyan three-bar listening pulse in the top band", "pulse the three cyan bars in sequence while eyes stay calm", "ion cyan on electric lime"),
    ("thinking", "思考", "uneven eyes, both pupils look up to one side", "gaze up-left, thoughtful pause, one eye narrows, return", "digital periwinkle"),
    ("happy", "开心", "wide eyes curve into cheerful upward crescents", "notice, brighten, rebound in a small buoyant bounce, settle", "electric lime"),
    ("surprised", "突然发现", "very round white eyes and small pupils; one lime spark between eyes", "fast delighted widening, small rise, gentle settle", "acid yellow"),
    ("shocked", "受惊", "rigid tall whites, pin-point pupils, squashed gap", "sharp recoil, hold very still for a beat, cautious recovery", "hot coral"),
    ("question", "好奇歪头", "white eyes lean together diagonally, near eye a bit larger", "ease into a diagonal tilt, hold two beats, straighten", "ion cyan"),
    ("look_around", "张望", "balanced open whites with pupils turned outward to explore", "hold a left glance, sweep to right, center", "electric lime"),
    ("winking", "眨眼", "left eye closed as a clean white crescent; right eye wide", "one distinct left wink, playful hold, reopen both", "hot pink"),
    ("beat_swing", "摇摆", "two open rounded eyes offset in height", "two rhythmic side-to-side leaning beats, mirror timing not the art", "punchy violet"),
    ("confused", "晕乎乎", "wonky eye sizes, offset pupils, two tiny coral orbit marks at eye level", "small off-balance left then right wobble; damp quickly", "digital periwinkle with coral"),
    ("relaxed", "放松", "gently half-closed eyes, broad horizontal white shapes", "exhale-like slow lowering of lids and float back up", "mint green"),
    ("sleepy", "困倦", "almost closed white eyelids, a sliver of black pupil", "two sleepy dips, briefly almost shut, lift halfway", "soft periwinkle"),
    ("laughing", "大笑", "two tightly happy clamped white curves, compressed shapes", "two elastic laughing pulses and a held smile-shaped eye pose", "acid yellow"),
    ("funny", "搞怪", "one large stretched eye, one tiny round eye, crossed pupils", "small left-right switch in eye scale, freeze on the silly pose", "punchy violet"),
    ("loving", "喜欢", "two rounded soft white eyes with dark heart-shaped pupils", "dark pupils round into hearts and gently pulse once", "hot pink"),
    ("embarrassed", "害羞", "two lowered white eyes looking down sideways, tiny hot pink cheek dashes", "quick glance away, pink dashes briefly light up, slow peek back", "hot pink"),
    ("confident", "得意", "two forward-looking white half lids, one lid slightly raised", "brief diagonal lifting of one eye, hold the confident look", "ion cyan"),
    ("delicious", "好吃", "two small delighted white crescents with a tiny yellow sparkle between them", "small anticipatory squish, open into pleased crescents, two compact beats", "acid yellow"),
    ("sad", "难过", "downturned eye pairs and low gaze, gently sagging outer corners", "slow downward droop, linger, slow partial lift", "blue-violet"),
    ("crying", "哭泣", "downturned eyes with one discrete cyan tear beside one eye", "one clear tear slips and vanishes above subtitle margin, slight tremble", "ion cyan"),
    ("silly", "俏皮", "close-set eyes with both pupils pointing inward", "pupils converge, hold, pop back apart", "electric lime"),
    ("angry", "生气", "bold angled white upper lids narrow toward the center", "fast narrowing, brief huff-like compression, release halfway", "hot coral"),
    ("insert", "插入动画", "two white eyes with crisp square-corner scan highlights", "short modular scan alignment, briefly hold, dissolve accents", "ion cyan"),
    ("look_left", "看左边", "both pupils clearly on the viewer's left", "move both pupils from center to the viewer's left; hold; return", "electric lime"),
    ("look_right", "看右边", "both pupils clearly on the viewer's right", "move both pupils from center to the viewer's right; hold; return", "electric lime"),
    ("eat", "吃东西", "alternately squashed rounded white eyes, a single tiny acid sparkle", "two distinct chew-like squash beats using eye shapes alone", "acid yellow"),
    ("tried", "疲惫", "low, uneven drooping half-lids, centered gaze", "heavy slow sink, hold, one effortful partial lift", "muted periwinkle"),
]

STYLE = """AirBoat, a fictional tiny floating companion, shown only as its two eyes inside a square digital face. Match the first local reference for mascot identity, two oversized white shapes with black pupils, no outline or texture. Use flat bold chromatic electric fields and crisp motion graphics, mildly asymmetric but friendly. Black or one uniform saturated field, accent details confined to the eyes. Keep each field's upper 16% and lower 22% empty for actual device overlays. Use comparable overall eye size across all shots and keep the pair spatially centered around x=50%, y=49%, about 52% total width. No lettering, labels, borders, gradients, 3D, glasses, eyebrows, mouth, body, grid rules, device or photo."""


def main():
    for folder in ("inputs", "prompts", "raw", "png", "gif", "calls"):
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    pack = ROOT / "mosaico-eaf-480"
    source = json.loads((pack / "source-manifest.json").read_bytes())
    base = next(item for item in source if item["name"] == "idle")
    source_path = pack / "source-gif" / base["source_file"]
    with Image.open(source_path) as gif:
        gif.seek(0)
        gif.convert("RGB").save(OUT / "inputs/airboat-idle-reference.png", optimize=True)
    groups = []
    for pos in range(0, len(ROWS), 4):
        items = ROWS[pos:pos + 4]
        number = f"{pos // 4 + 1:02}"
        locations = ("top-left", "top-right", "bottom-left", "bottom-right")
        roles = [dict(key=key, label=label, pose=pose, motion=motion, palette=palette)
                 for key, label, pose, motion, palette in items]
        for role in roles:
            prompt = (f"{STYLE}\n\nUse the supplied square still as the exact identity and starting arrangement. "
                      f"Make ONE full-bleed square eye animation, no sheet or split screen. Keep the backdrop "
                      f"and palette nearly identical across frames. Express {role['key']} through {role['motion']}. "
                      "Soft acceleration. Fixed camera. Ease to a pose compatible with the first frame so the "
                      "GIF repeats naturally. Do not add elements outside the eye region.")
            (OUT / "prompts" / f"gif-{role['key']}.txt").write_text(prompt, encoding="utf-8")
        tiles = "\n".join(f"{where}: {role['pose']}; {role['palette']} solid field."
                          for where, role in zip(locations, roles))
        prompt = (f"{STYLE}\n\nGenerate a 2 by 2 expression atlas, four exact edge-to-edge equally sized square "
                  "tiles, split at EXACTLY 50% width and 50% height. No gutters or dividers. Each tile is a "
                  "separate complete centered face; all geometry and margins above are relative to that tile. "
                  "Render strictly in this reading order, one pair of eyes per tile:\n"+tiles)
        (OUT / "prompts" / f"static-{number}.txt").write_text(prompt, encoding="utf-8")
        groups.append({"id":number,"roles":roles})
    data = {"project":"AirBoat", "firmware_catalog":"1.29.0", "groups":groups,
            "identity_reference":{"source":source_path.relative_to(ROOT).as_posix(), "frame":0,
                                  "sha256":hashlib.sha256(source_path.read_bytes()).hexdigest()},
            "coverage":"28 firmware semantics plus the synthetic listening composite"}
    (OUT / "study.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
