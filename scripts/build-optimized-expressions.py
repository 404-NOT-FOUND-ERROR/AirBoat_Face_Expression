"""Build native-size layered expressions with exact reflected-sprite sharing.

AFM1 stores cropped 4-bit coverage sprites and indexed accent sprites as RLE.
Background colors and entry/exit motion are metadata, never full frame images.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageFilter, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'output/imagegen/airboat-expression-study-20261120'
DEST = ROOT / 'assets/optimized'
WEB = ROOT / 'docs/product/expression-optimized-data.js'
SIDE, FPS, TRANSITION_FRAMES = 480, 25, 9


def rle_encode(pixels, alpha=False):
    """A byte gives length 1..255, followed by one pixel index/coverage value."""
    values = np.frombuffer(pixels, dtype=np.uint8)
    starts = np.r_[0, np.flatnonzero(values[1:] != values[:-1]) + 1]
    lengths = np.diff(np.r_[starts, len(values)])
    out = bytearray()
    for start, length in zip(starts, lengths):
        value = int(values[start])
        if alpha:
            while length:
                n = min(int(length), 271)
                out.append((value << 4) | min(n - 1, 15))
                if n >= 16:
                    out.append(n - 16)
                length -= n
        else:
            while length > 255:
                out.extend((255, value))
                length -= 255
            out.extend((int(length), value))
    return bytes(out)


def rle_decode(raw, count, alpha=False):
    if not alpha and len(raw) % 2:
        raise ValueError('Incomplete RLE pair')
    out = bytearray()
    at = 0
    while at < len(raw):
        if alpha:
            token = raw[at]
            at += 1
            n, value = (token & 15) + 1, token >> 4
            if n == 16:
                if at == len(raw):
                    raise ValueError('Incomplete long alpha run')
                n += raw[at]
                at += 1
        else:
            n, value = raw[at:at + 2]
            at += 2
        if not n or len(out) + n > count:
            raise ValueError('Invalid RLE length')
        out.extend(bytes((value,)) * n)
    if len(out) != count:
        raise ValueError('Incomplete RLE image')
    return bytes(out)


class Sprites:
    def __init__(self):
        self.rows, self.seen, self.payload, self.literal_seen = [], {}, bytearray(), set()
        self.references = self.reflected_references = self.reflection_hits = 0
        self.saved_by_reflection = 0

    def add_mask(self, mask, box):
        if mask is None:
            return None
        # Rebuild subpixel coverage from the original 480 px silhouette. The
        # broad glow/noisy background from the generated source is excluded.
        soft = mask.filter(ImageFilter.GaussianBlur(.45))
        alpha = ((np.asarray(soft, dtype=np.uint16) * 15 + 127) // 255).astype(np.uint8)
        return self.add(alpha, box, None)

    def add_accent(self, image):
        box = image.getbbox()
        if not box:
            return None
        cropped = np.array(image.crop(box))
        # Palette entries are RGBA; all fully transparent pixels have one value.
        cropped[cropped[:, :, 3] == 0] = 0
        palette, indices = np.unique(cropped.reshape(-1, 4), axis=0, return_inverse=True)
        if len(palette) > 256:
            raise ValueError('Accent has more than 256 unique colors')
        return self.add(indices.reshape(cropped.shape[:2]).astype(np.uint8), box, palette.tolist())

    def add(self, values, box, palette):
        original = values.tobytes()
        reflected = np.ascontiguousarray(values[:, ::-1]).tobytes()
        flip = reflected < original
        canonical = reflected if flip else original
        h, w = values.shape
        color_key = json.dumps(palette, separators=(',', ':'))
        key = (w, h, color_key, canonical)
        mirror_key = (w, h, color_key, original)
        self.references += 1
        if flip:
            self.reflected_references += 1
        if key not in self.seen:
            raw = rle_encode(canonical, alpha=palette is None)
            assert rle_decode(raw, w * h, alpha=palette is None) == canonical
            index = len(self.rows)
            self.seen[key] = index
            self.rows.append({'w': w, 'h': h, 'offset': len(self.payload), 'bytes': len(raw),
                              'palette': palette, 'codec': 'a4rle' if palette is None else 'i8rle',
                              'sha256': hashlib.sha256(canonical).hexdigest()})
            self.payload.extend(raw)
        else:
            index = self.seen[key]
            # Count only actual sharing with a reflected reference; canonical
            # orientation by itself is not a storage saving.
            if mirror_key not in self.literal_seen:
                self.reflection_hits += 1
                self.saved_by_reflection += self.rows[index]['bytes']
        # Position belongs to each reference. Sharing never ties eye timing or
        # forces equal positions, shapes or left/right expressions.
        self.literal_seen.add(mirror_key)
        return [index, *box, int(flip)]


def build():
    spec = importlib.util.spec_from_file_location('polish', ROOT / 'scripts/polish-expression-gifs.py')
    polish = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(polish)
    sprites, clips, provenance = Sprites(), {}, {}
    for key, color in polish.COLORS.items():
        if key == 'neutral':
            continue  # Keep the delivered neutral/idle binding.
        source = STUDY / 'gif' / (key + '.gif')
        with Image.open(source) as gif:
            delay = gif.info.get('duration', 90)
            frames = [frame.convert('RGB') for frame in ImageSequence.Iterator(gif)]
        timeline = []
        for frame in frames:
            pose, accent = polish.channels(frame, key)
            layers = []
            for eye in range(2):
                for layer in range(2):
                    piece = pose[eye][layer]
                    layers.append(sprites.add_mask(*piece) if piece else None)
            timeline.append({'layers': layers, 'accent': sprites.add_accent(accent)})
        # Match the approved processed animation's keyframe interpolation and
        # loop closure, retaining native shapes rather than its 240 px export.
        body_frames = round(len(frames) * delay / 40)
        clips[key] = {'color': color, 'keyframes': timeline, 'body_frames': body_frames}
        provenance[key] = {'file': source.relative_to(ROOT).as_posix(),
                           'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                           'keyframes': len(timeline), 'source_size': [480, 480]}
    payload = b'AFM1' + struct.pack('<III', 1, len(sprites.rows), len(sprites.payload)) + sprites.payload
    manifest = {'format': 'airboat.layered-face.v1', 'canvas': SIDE, 'fps': FPS,
                'alpha_levels': 16, 'transition_frames': TRANSITION_FRAMES,
                'base': 'idle', 'sprites': sprites.rows, 'clips': clips,
                'binary': 'face-motion.afm', 'binary_bytes': len(payload),
                'binary_sha256': hashlib.sha256(payload).hexdigest(), 'sources': provenance,
                'sharing': {'references': sprites.references, 'unique_sprites': len(sprites.rows),
                            'reflected_references': sprites.reflected_references,
                            'reflected_reuse_hits': sprites.reflection_hits,
                            'reflected_reuse_bytes': sprites.saved_by_reflection,
                            'rule': 'exact 4-bit coverage/palette match; independent layer positions and keyframe clocks'}}
    compact = json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + '\n'
    manifest['catalog_bytes'] = len(compact.encode('utf-8'))
    # Fixed point so accounting includes the accounting field itself.
    for _ in range(4):
        compact = json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + '\n'
        manifest['catalog_bytes'] = len(compact.encode('utf-8'))
    compact = json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + '\n'
    assert len(compact.encode('utf-8')) == manifest['catalog_bytes']
    web = '// Generated by scripts/build-optimized-expressions.py; native-size layered candidate.\n'
    web += 'window.AIRBOAT_OPTIMIZED_PACK = ' + compact.strip() + ';\n'
    web += 'window.AIRBOAT_OPTIMIZED_PACK.payload = "' + base64.b64encode(payload).decode('ascii') + '";\n'
    summary = {'canvas': SIDE, 'semantics': len(clips) + 1, 'binary_bytes': len(payload),
               'catalog_bytes': manifest['catalog_bytes'], 'total_bytes': len(payload) + manifest['catalog_bytes'],
               'sharing': manifest['sharing']}
    return payload, compact, web, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload, catalog, web, summary = build()
    for path, raw in ((DEST / 'face-motion.afm', payload), (DEST / 'manifest.json', catalog.encode('utf-8')),
                      (WEB, web.encode('utf-8'))):
        if args.check:
            assert path.read_bytes() == raw, f'Stale optimized asset: {path.name}'
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
