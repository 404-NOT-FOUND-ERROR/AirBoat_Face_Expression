"""Check native layered storage, exact symmetry and malformed run boundaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('optimized', ROOT / 'scripts/build-optimized-expressions.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest = json.loads((ROOT / 'assets/optimized/manifest.json').read_bytes())
raw = (ROOT / 'assets/optimized/face-motion.afm').read_bytes()
assert raw[:4] == b'AFM1' and struct.unpack_from('<III', raw, 4) == (1, len(manifest['sprites']), len(raw) - 16)
assert hashlib.sha256(raw).hexdigest() == manifest['binary_sha256']
assert len(raw) == manifest['binary_bytes']
assert (ROOT / 'assets/optimized/manifest.json').stat().st_size == manifest['catalog_bytes']
decoded = []
levels = set()
for sprite in manifest['sprites']:
    w, h, at, length = (sprite[k] for k in ('w', 'h', 'offset', 'bytes'))
    assert 0 < w <= 480 and 0 < h <= 480 and at >= 0 and 16 + at + length <= len(raw)
    pixels = module.rle_decode(raw[16 + at:16 + at + length], w * h, sprite['palette'] is None)
    assert hashlib.sha256(pixels).hexdigest() == sprite['sha256']
    if sprite['palette'] is None:
        assert max(pixels) <= 15
        levels.update(pixels)
    else:
        assert max(pixels) < len(sprite['palette']) <= 256
    decoded.append(pixels)
assert {0, 15} <= levels <= set(range(16)) and len(levels) > 4, 'Subpixel coverage must survive storage'
assert len(manifest['clips']) == 28
asymmetric_frames = 0
for key, clip in manifest['clips'].items():
    assert clip['body_frames'] > 1 and len(clip['keyframes']) > 1
    for frame in clip['keyframes']:
        assert len(frame['layers']) == 4
        for ref in [*frame['layers'], frame['accent']]:
            if not ref:
                continue
            s = manifest['sprites'][ref[0]]
            assert ref[3] - ref[1] == s['w'] and ref[4] - ref[2] == s['h']
            assert 0 <= ref[1] < ref[3] <= 480 and 0 <= ref[2] < ref[4] <= 480
            assert ref[5] in (0, 1)
        left, right = frame['layers'][0], frame['layers'][2]
        if left and right and left[0] != right[0]:
            asymmetric_frames += 1
assert asymmetric_frames > 0

# A genuinely reflected eye shares one sprite; a distinct wink does not.
pool = module.Sprites()
pixels = np.array([[0, 3, 15, 15], [0, 8, 15, 15]], dtype=np.uint8)
a = pool.add(pixels, (10, 20, 14, 22), None)
b = pool.add(pixels[:, ::-1], (400, 21, 404, 23), None)
c = pool.add(pixels.copy(), (30, 40, 34, 42), None)
wink = pool.add(np.array([[0, 0, 0, 0], [15, 15, 15, 15]], dtype=np.uint8), (400, 21, 404, 23), None)
assert a[0] == b[0] == c[0] != wink[0] and a[5] != b[5]
assert len(pool.rows) == 2 and pool.reflection_hits == 1
assert a[1:5] != b[1:5], 'Reuse must not overwrite independent eye position'
for pixels in (bytes([0] * 600), bytes(range(16)) * 30, bytes([15] * 271 + [8] * 272)):
    assert module.rle_decode(module.rle_encode(pixels, True), len(pixels), True) == pixels
for data, count, alpha in ((b'\xff', 100, True), (b'\x00\x01', 1, False), (b'\x1e', 2, True), (b'\x01', 1, False)):
    try:
        module.rle_decode(data, count, alpha)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid RLE accepted')
print(json.dumps({'status': 'passed', 'sprites': len(decoded), 'alpha_levels': len(levels),
                  'asymmetric_frames_preserved': asymmetric_frames,
                  'exact_symmetry_fixture': True, 'total_bytes': len(raw) + manifest['catalog_bytes']}))
