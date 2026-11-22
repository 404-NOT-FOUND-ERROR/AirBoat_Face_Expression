"""Build the isolated contour and expression timing review pack."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import base64

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageSequence
from expression_beat_study import PERFORMANCES, frames as performance_frames
from expression_repertoire import SCORES, compose, laughing, one_look

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'assets/contour-review'
SIDE, SCALE, FPS = 480, 4, 25


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ellipse(box):
    mask = Image.new('L', (SIDE * SCALE, SIDE * SCALE))
    ImageDraw.Draw(mask).ellipse(tuple(round(x * SCALE) for x in box), fill=255)
    return mask.resize((SIDE, SIDE), Image.Resampling.LANCZOS)


def idle_pose(t, polish):
    """Symmetric contours; a clipped round pupil, never a squashed pupil."""
    # 1.36 s quiet -> 120 ms close -> 40 ms closed -> 200 ms reopen.
    # Short settling and independent pupil movement keep the face alive.
    close = polish.ease((t - 1.36) / .12)
    reopen = polish.ease((t - 1.52) / .20)
    openness = 1 - close + reopen
    settle = 1.2 * math.exp(-max(0, t - 1.72) * 18) * math.sin(max(0, t - 1.72) * 36)
    cy = 234 + .65 * math.sin(2 * math.pi * t / 3.6) + settle
    h = 3.0 + 85 * openness
    lid_cy = cy + 16 * (1 - openness)
    white = ellipse((68, lid_cy - h, 232, lid_cy + h))
    # Gaze anticipates the lid slightly; the pupil stays circular while occluded.
    saccade = 2 * (polish.ease((t - .55) / .08) - polish.ease((t - .84) / .13))
    pupil = ellipse((108 + saccade, cy - 9, 192 + saccade, cy + 69))
    pupil = ImageChops.multiply(pupil, white)
    pupil = pupil.point(lambda v: round(v * polish.ease((openness - .10) / .25)))
    # Generate the right side by exact reflection. Positions and masks agree.
    return [
        (polish.sprite(white, 0, 0), polish.sprite(pupil, 0, 0)),
        (polish.sprite(white.transpose(Image.Transpose.FLIP_LEFT_RIGHT), 0, 0),
         polish.sprite(pupil.transpose(Image.Transpose.FLIP_LEFT_RIGHT), 0, 0)),
    ], Image.new('RGBA', (SIDE, SIDE))


def shocked_pose(frame, polish):
    pixels = np.asarray(frame.convert('RGB'))
    white = Image.fromarray((np.min(pixels, axis=2) >= 232).astype('uint8') * 255)
    full = polish.filled_holes(white)
    dark = Image.fromarray(((np.max(pixels, axis=2) < 65) & (np.asarray(full) > 0)).astype('uint8') * 255)
    pairs = []
    for x in (0, 240):
        # Entire source height: the tall shock reaches row 426, beyond old 394.
        box = (x, 0, x + 240, SIDE)
        pairs.append(tuple(polish.sprite(mask.filter(ImageFilter.GaussianBlur(.45)).crop(box), x, 0)
                           for mask in (full, dark)))
    return pairs, Image.new('RGBA', (SIDE, SIDE))


def build():
    optimized = load('optimized_review', 'build-optimized-expressions.py')
    polish = load('polish_review', 'polish-expression-gifs.py')
    pool, clips = optimized.Sprites(), {}
    idle = [idle_pose(i / FPS, polish) for i in range(89)]
    idle.append(idle[0])
    source = ROOT / 'output/imagegen/airboat-expression-study-20261120/gif/shocked.gif'
    with Image.open(source) as gif:
        delay = gif.info.get('duration', 90)
        frames = [f.convert('RGB') for f in ImageSequence.Iterator(gif)]
    shocked = [shocked_pose(f, polish) for f in frames]
    shocked.append(shocked[0])
    inputs = [('idle', idle, 90), ('shocked', shocked, round(len(frames) * delay / 40))]
    beats = {}
    art_sources = {}
    for key, (_, count, marks) in PERFORMANCES.items():
        art = None
        if key == 'happy':
            path = source.with_name(key + '.gif')
            with Image.open(path) as gif:
                art = gif.convert('RGB')
            art_sources[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        inputs.append((key, performance_frames(key, art, polish, ellipse, FPS), count))
        beats[key] = marks
    for key, poses, count in inputs:
        timeline = []
        for pose, accent in poses:
            refs = []
            for eye in pose:
                for layer in eye:
                    if layer:
                        mask, box = layer
                        alpha = ((np.asarray(mask, dtype=np.uint16) * 15 + 127) // 255).astype(np.uint8)
                        refs.append(pool.add(alpha, box, None))
                    else:
                        refs.append(None)
            timeline.append({'layers': refs, 'accent': pool.add_accent(accent)})
        clips[key] = {'color': polish.COLORS[key], 'keyframes': timeline, 'body_frames': count}
    for key, (_, score) in SCORES.items():
        path = source.with_name(key + '.gif')
        timeline = compose(key, path, pool, polish, ellipse, FPS)
        clips[key] = {'color': polish.COLORS[key], 'keyframes': timeline, 'body_frames': len(timeline)}
        beats[key] = [(row[0], row[1]) for row in score if row[1]]
        art_sources[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    timeline, beats['laughing'] = laughing(pool, polish, FPS)
    clips['laughing'] = {'color': polish.COLORS['laughing'], 'keyframes': timeline, 'body_frames': len(timeline)}
    for key, direction in [('look_left', -1), ('look_right', 1)]:
        timeline, marks = one_look(direction, pool, polish, ellipse, FPS)
        clips[key] = {'color': polish.COLORS[key], 'keyframes': timeline, 'body_frames': len(timeline)}
        beats[key] = marks
    assert set(clips) == set(polish.COLORS) - {'neutral'}
    payload = b'AFM1' + struct.pack('<III', 1, len(pool.rows), len(pool.payload)) + pool.payload
    pack = {'format': 'airboat.layered-face.v1', 'canvas': SIDE, 'fps': FPS, 'alpha_levels': 16,
            'transition_frames': 9, 'base': 'idle', 'sprites': pool.rows, 'clips': clips,
            'binary': 'contour-review.afm', 'binary_bytes': len(payload),
            'binary_sha256': hashlib.sha256(payload).hexdigest(), 'catalog_bytes': 0,
            'review': 'complete repertoire; independent layer timing and symmetric idle anchor',
            'clip_pupils': True, 'exit_from_last': True,
            'beats': beats, 'art_sources_sha256': art_sources,
            'sharing': {'references': pool.references, 'unique_sprites': len(pool.rows),
                        'reflected_reuse_hits': pool.reflection_hits, 'reflected_reuse_bytes': pool.saved_by_reflection},
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    for _ in range(8):
        catalog = json.dumps(pack, ensure_ascii=False, separators=(',', ':')) + '\n'
        pack['catalog_bytes'] = len(catalog.encode())
    catalog = json.dumps(pack, ensure_ascii=False, separators=(',', ':')) + '\n'
    assert len(catalog.encode()) == pack['catalog_bytes']
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'contour-review.afm').write_bytes(payload)
    (DEST / 'manifest.json').write_text(catalog, encoding='utf-8', newline='\n')
    web = '// Isolated art review, generated by scripts/build-contour-review.py.\n'
    web += 'window.AIRBOAT_CONTOUR_PACK=' + catalog.strip() + ';\n'
    web += 'window.AIRBOAT_CONTOUR_PACK.payload="' + base64.b64encode(payload).decode() + '";\n'
    (ROOT / 'docs/product/expression-contour-data.js').write_text(web, encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'built', 'clips': list(clips), 'frames': sum(c['body_frames'] for c in clips.values()),
                      'total_bytes': len(payload) + len(catalog.encode()), 'sharing': pack['sharing']}))


if __name__ == '__main__':
    build()
