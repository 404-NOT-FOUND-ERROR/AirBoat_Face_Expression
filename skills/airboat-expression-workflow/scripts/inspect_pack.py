"""Validate and summarize the current layered pack without rebuilding it."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(root, pack_directory='assets/contour-review'):
    directory = (root / pack_directory).resolve()
    require(directory.is_relative_to(root.resolve()), 'Pack directory must belong to the repository')
    catalog = (directory / 'manifest.json').read_bytes()
    pack = json.loads(catalog)
    binary_path = (directory / pack['binary']).resolve()
    require(binary_path.parent == directory.resolve(), 'Binary must belong to the pack directory')
    binary = binary_path.read_bytes()
    digest = hashlib.sha256(binary).hexdigest()
    require(len(binary) >= 16, 'Truncated AFM header')
    magic, version, sprites, payload_bytes = struct.unpack_from('<4sIII', binary)
    require(magic == b'AFM1' and version == 1, 'Unsupported AFM header')
    require(pack['format'] == 'airboat.layered-face.v1', 'Unsupported catalog format')
    require(pack['canvas'] == 480 and pack['alpha_levels'] == 16, 'Unsupported coverage or canvas')
    require(pack['fps'] > 0 and pack['transition_frames'] >= 2, 'Invalid timing')
    require(sprites == len(pack['sprites']), 'Sprite count mismatch')
    require(payload_bytes == len(binary)-16, 'Payload length mismatch')
    require(pack['binary_bytes'] == len(binary), 'Binary byte count mismatch')
    require(pack['catalog_bytes'] == len(catalog), 'Catalog byte count mismatch')
    require(digest == pack['binary_sha256'], 'Binary SHA-256 mismatch')

    decoded_pixels = 0
    for index, sprite in enumerate(pack['sprites']):
        w, h = sprite['w'], sprite['h']
        require(isinstance(w, int) and isinstance(h, int) and 0 < w <= 480 and 0 < h <= 480,
                f'Invalid sprite dimensions: {index}')
        start, size = sprite['offset'], sprite['bytes']
        require(isinstance(start, int) and isinstance(size, int) and start >= 0 and size > 0 and
                start+size <= payload_bytes, f'Invalid sprite bounds: {index}')
        palette = sprite.get('palette')
        require(sprite.get('codec') == ('i8rle' if palette is not None else 'a4rle'),
                f'Unexpected sprite codec: {index}')
        if palette is not None:
            require(1 <= len(palette) <= 256 and all(len(color) == 4 and
                    all(isinstance(v, int) and 0 <= v <= 255 for v in color) for color in palette),
                    f'Invalid palette: {index}')
        raw, at, stop = bytearray(), 16+start, 16+start+size
        while at < stop:
            token = binary[at]
            at += 1
            if palette is not None:
                require(at < stop, f'Truncated indexed run: {index}')
                count, value = token, binary[at]
                at += 1
                require(count > 0 and value < len(palette), f'Invalid indexed run: {index}')
            else:
                value, count = token >> 4, (token & 15)+1
                if count == 16:
                    require(at < stop, f'Truncated coverage run: {index}')
                    count += binary[at]
                    at += 1
            require(len(raw)+count <= w*h, f'Run exceeds sprite: {index}')
            raw.extend(bytes([value])*count)
        require(len(raw) == w*h, f'Incomplete sprite: {index}')
        require(hashlib.sha256(raw).hexdigest() == sprite['sha256'], f'Sprite hash mismatch: {index}')
        decoded_pixels += w*h

    clips = pack['clips']
    aliases = pack.get('aliases', {})
    require(not set(aliases) & set(clips), 'Alias duplicates a real clip')
    resolved = {}
    for name, target in aliases.items():
        seen = {name}
        while target in aliases:
            require(target not in seen, f'Alias cycle: {name}')
            seen.add(target)
            target = aliases[target]
        require(target in clips, f'Alias target missing: {name}')
        resolved[name] = target
    require(pack['base'] in clips, 'Base clip missing')

    def check_ref(ref):
        if ref is None:
            return
        require(isinstance(ref, list) and len(ref) == 6 and all(type(v) is int for v in ref),
                'Layer references require six integer fields')
        i, x, y, r, b, flip = ref
        require(0 <= i < sprites and 0 <= x < r <= 480 and 0 <= y < b <= 480 and flip in (0, 1),
                f'Invalid layer reference: {ref}')

    body_frames = keyframes = 0
    for name, clip in clips.items():
        count = clip['body_frames']
        require(type(count) is int and count > 0 and len(clip['keyframes']) > 1,
                f'Invalid frame or keyframe count: {name}')
        require(isinstance(clip['color'], str) and len(clip['color']) == 7 and clip['color'][0] == '#',
                f'Invalid clip color: {name}')
        int(clip['color'][1:], 16)
        if pack.get('authored_transitions'):
            require(len(clip.get('entry_keyframes',[])) == pack['transition_frames'] and
                    len(clip.get('exit_keyframes',[])) == pack['transition_frames'],
                    f'Authored transition count mismatch: {name}')
        for frame in [*clip['keyframes'],*clip.get('entry_keyframes',[]),*clip.get('exit_keyframes',[])]:
            require(len(frame['layers']) == 4, f'Expected four eye layers: {name}')
            for ref in [*frame['layers'], frame['accent']]:
                check_ref(ref)
        marks = pack.get('beats', {}).get(name, [])
        require(all(0 <= ms < count*1000/pack['fps'] and isinstance(label, str) for ms, label in marks),
                f'Beat outside the clip: {name}')
        body_frames += count
        keyframes += len(clip['keyframes'])
    return {'status': 'passed', 'validation_layer': 'host-pack', 'binary_sha256': digest,
            'binary_bytes': len(binary), 'catalog_bytes': len(catalog), 'total_bytes': len(binary)+len(catalog),
            'canvas': pack['canvas'], 'fps': pack['fps'], 'alpha_levels': pack['alpha_levels'],
            'clip_count': len(clips), 'semantic_count': len(clips)+len(aliases), 'aliases': resolved,
            'sprite_count': sprites, 'decoded_sprite_pixels': decoded_pixels, 'body_frames': body_frames,
            'stored_keyframes': keyframes,
            'frames_with_entry_exit': body_frames+2*pack['transition_frames']*len(clips),
            'device_validation': 'not assessed by this tool'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--pack-directory', type=Path, default=Path('assets/contour-review'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.repo_root.resolve(), args.pack_directory)
    except (ValueError, KeyError, OSError, TypeError, struct.error) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    rendered = json.dumps(result, ensure_ascii=False, indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8', newline='\n')
    print(rendered, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
