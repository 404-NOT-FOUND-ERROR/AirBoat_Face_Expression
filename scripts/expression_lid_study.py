"""Continuous eyelid, gaze and accent tracks authored at 480 px."""
import math
from functools import lru_cache

from PIL import Image, ImageDraw
import numpy as np

from expression_beat_study import track


# Each eye: x, y, width change, upper-lid drop, tilt, lower-lid lift.
OPEN = (0,) * 6


def eyes(ms, left=OPEN, right=None):
    return ms, left, left if right is None else right


def gaze(ms, left=(0, 0), right=None):
    return ms, left, left if right is None else right


STUDIES = {
    'relaxed': (3240, [(480, '眼皮放松'), (1120, '呼一口气'), (2080, '轻轻抬眼')], [
        eyes(80), eyes(480, (0,4,-3,28,0,3)), eyes(1120, (0,10,-2,38,0,6)),
        eyes(1560, (0,8,-3,32,0,5)), eyes(2000, (0,10,-3,36,0,6)), eyes(2960),
    ], [gaze(140), gaze(720, (0,8)), gaze(1440, (0,7)), gaze(2080, (0,5)), gaze(2700)]),
    'confident': (2520, [(520, '抬起一边'), (840, '得意地停住'), (1200, '补一眼'), (1760, '慢慢放下')], [
        eyes(120), eyes(520, (-3,5,-4,33,-5,2), (2,-14,-3,12,-6,0)),
        eyes(840, (-3,5,-4,38,-5,2), (2,-11,-3,17,-6,0)),
        eyes(1520, (-3,5,-4,37,-5,2), (2,-11,-3,15,-6,0)),
        eyes(1840, (-2,3,-3,23,-3,0), (1,-6,-3,10,-3,0)), eyes(2320),
    ], [gaze(100), gaze(480,(7,-11)), gaze(880,(7,-11)), gaze(1200,(16,-13)),
        gaze(1480,(13,-12)), gaze(2160)]),
    'sad': (3560, [(420, '目光先落下'), (1240, '眼皮跟着垂下'), (2000, '小小吸气'), (2840, '慢慢抬眼')], [
        eyes(440), eyes(1240, (0,14,-5,26,15,5), (0,14,-5,26,-15,5)),
        eyes(1680, (0,15,-5,28,15,5), (0,15,-5,28,-15,5)),
        eyes(2000, (0,11,-5,24,13,5), (0,11,-5,24,-13,5)),
        eyes(2360, (0,14,-5,28,14,5), (0,14,-5,28,-14,5)), eyes(3320),
    ], [gaze(80), gaze(420,(4,19),(-4,19)), gaze(1630,(4,19),(-4,19)),
        gaze(2040,(3,14),(-3,14)), gaze(2360,(4,18),(-4,18)), gaze(3160)]),
    'crying': (3000, [(360, '轻轻忍住'), (600, '颤一下'), (1000, '滑下第一滴'), (1720, '另一滴落下'), (2280, '平复')], [
        eyes(100), eyes(360, (0,7,-5,47,13,12), (0,8,-5,42,-13,9)),
        eyes(600, (-2,12,-5,68,12,22), (-2,13,-5,64,-12,20)),
        eyes(760, (1,8,-5,42,12,10), (1,9,-5,39,-12,10)),
        eyes(920, (-1,11,-5,51,13,16), (-1,11,-5,49,-13,15)),
        eyes(1200, (0,9,-5,40,13,10), (0,10,-5,38,-13,10)),
        eyes(1480, (0,8,-4,38,11,7), (0,8,-4,37,-11,8)),
        eyes(1720, (0,9,-4,43,10,9), (0,9,-4,42,-10,9)),
        eyes(2280, (0,5,-2,18,6,3), (0,5,-2,18,-6,3)), eyes(2800),
    ], [gaze(80), gaze(360,(0,12)), gaze(600,(0,23)), gaze(760,(0,14)), gaze(1040,(0,17)),
        gaze(1800,(0,13)), gaze(2600)]),
}


def translated(ref, dx, dy):
    return [ref[0], round(ref[1]+dx), round(ref[2]+dy), round(ref[3]+dx), round(ref[4]+dy), ref[5]]


def reflected(ref):
    i, x, y, r, b, flip = ref
    return [i, 480-r, y, 480-x, b, flip ^ 1]


def rounded_lid(width, drop, tilt, lift):
    half = 82 + width
    scale = 4
    mask = Image.new('L', (200*scale, 224*scale))
    points = []
    for step in range(240):
        a = math.tau * step / 240
        c, s = math.cos(a), math.sin(a)
        y = tilt*c + s*(88-lift if s >= 0 else 88-drop)
        if s < 0 and drop:
            # Keep rounded corners as the upper lid lowers and flattens.
            y += .10 * min(drop, 176-lift-drop) * (-s) * c * c
        points.append((round((100+half*c)*scale), round((112+y)*scale)))
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.resize((200, 224), Image.Resampling.LANCZOS)


def tear(sprite_level):
    supersample = 4
    size = (24, 35)
    body = Image.new('RGBA', tuple(v*supersample for v in size))
    draw = ImageDraw.Draw(body)
    def box(*coords):
        return tuple(round(v*supersample) for v in coords)
    alpha = 17*sprite_level
    draw.polygon([box(*p) for p in [(12,2),(10,7),(4,16),(2,24),(22,24),(20,16),(14,7)]], fill=(55,146,245,alpha))
    draw.ellipse(box(2,13,22,33), fill=(55,146,245,alpha))
    draw.ellipse(box(6,19,10,26), fill=(218,250,255,alpha))
    # Limit the accent to a compact palette without flattening the shape.
    return body.resize(size, Image.Resampling.LANCZOS).quantize(colors=32, method=Image.Quantize.FASTOCTREE).convert('RGBA')


def continuous_clip(key, pool, polish, fps, idle_layers):
    duration, marks, eyelids, gazes = STUDIES[key]
    ease = polish.ease
    frames = []

    @lru_cache(maxsize=None)
    def lid(width, drop, tilt, lift):
        mask = rounded_lid(width, drop, tilt, lift)
        cropped, box = polish.sprite(mask, 50, 122)
        values = ((np.asarray(cropped, dtype=np.uint16)*15+127)//255).astype(np.uint8)
        return pool.add(values, box, None)

    @lru_cache(maxsize=None)
    def drop_sprite(level):
        return pool.add_accent(tear(level))

    def accent(t):
        if key != 'crying':
            return None
        for side, start in enumerate((860, 1580)):
            local = (t-start)/680
            if 0 < local < 1:
                amount = min(ease(local/.2), ease((1-local)/.25))
                level = round(amount*15)
                if not level:
                    return None
                i, l, top, r, b, flip = drop_sprite(level)
                cx = 112 - local*10 if not side else 370 + local*10
                cy = 308 + 65 * local**1.65
                scale = .72 + .25*ease(local/.6)
                return [i, round(cx+(l-12)*scale), round(cy+(top-17)*scale),
                        round(cx+(r-12)*scale), round(cy+(b-17)*scale), flip]
        return None

    def channels(keys, n):
        return [[tuple((row[0], row[side+1][i]) for row in keys) for i in range(n)] for side in (0,1)]

    lids, gaze_keys = channels(eyelids, 6), channels(gazes, 2)
    for i in range(round(duration*fps/1000)):
        t = i*1000/fps
        refs = []
        for side in range(2):
            x, y, width, drop, tilt, lift = (track(t, c, ease) for c in lids[side])
            gx, gy = (track(t, c, ease) for c in gaze_keys[side])
            shape = tuple(round(v*2)/2 for v in (width, drop, -tilt if side else tilt, lift))
            white, pupil = idle_layers[side*2:side*2+2]
            if any(shape):
                white = lid(*shape)
                if side:
                    white = reflected(white)
            refs += [translated(white, x, y), translated(pupil, x+gx, y+gy)]
        frames.append({'layers': refs, 'accent': accent(t)})
    return frames, marks
