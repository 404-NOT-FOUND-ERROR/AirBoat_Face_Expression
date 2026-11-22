"""25 fps layer cues for the rest of the colorful expression repertoire."""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageSequence

from expression_beat_study import track


def cue(ms, label, phase, eye=(0, 0, 1), gaze=(0, 0), accent=1):
    return (ms, label, phase, *eye, *gaze, accent)


# ms, visible beat, source gesture progress, eye x/y/height, pupil x/y, accent.
# Empty labels are follow-through keys. The first/last poses coincide for loops.
SCORES = {
    'listening': (1840, [
        cue(0, '', 0), cue(160, '聚焦', .12, gaze=(0, -5)),
        cue(320, '音符跟上', .35, (0, -3, 1.02)), cue(560, '', .43),
        cue(760, '停一拍', .54, accent=.32), cue(1000, '轻跳一下', .67, (0, -2, 1.01), accent=.85),
        cue(1440, '', .84, accent=.5), cue(1800, '', 0)]),
    'thinking': (2520, [
        cue(0, '', 0), cue(160, '先抬眼', .09, gaze=(-9, -14)),
        cue(400, '眼形跟上', .27, (-3, -8, 1.02), (-9, -15)),
        cue(840, '停下来想', .40, (-3, -8, .96), (-10, -15)),
        cue(1400, '', .40, (-3, -8, .96), (-10, -15)),
        cue(1640, '慢眨', .62, (-3, -6, .72), (-8, -9)),
        cue(1880, '收回视线', .77, (-3, -6, 1.02)), cue(2480, '', 0)]),
    'surprised': (1680, [
        cue(0, '', 0), cue(120, '瞳孔抢先', .04, gaze=(15, -6), accent=0),
        cue(280, '睁大', .24, (0, -6, 1.17), (11, -5), .45),
        cue(440, '轻弹一下', .41, (0, -3, 1.06), (6, -3)),
        cue(680, '', .42, (0, -3, 1.04), (6, -3)),
        cue(920, '回落', .65, (0, 3, .96)), cue(1640, '', 0)]),
    'question': (2440, [
        cue(0, '', 0), cue(180, '斜看', .08, gaze=(12, -4)),
        cue(440, '歪头', .31, (1, 2, 1.06), (8, -5), .75),
        cue(760, '等你回答', .47, (1, 2, 1.06), (8, -5)),
        cue(1680, '', .47, (1, 2, 1.06), (8, -5)),
        cue(1920, '摆正', .77, (-2, -2, .96), (4, 1)), cue(2400, '', 0)]),
    'winking': (1840, [
        cue(0, '', 0), cue(160, '一只眼先闭', .05),
        cue(360, '停一拍', .23, gaze=(5, -3)), cue(600, '', .23, gaze=(5, -3)),
        cue(820, '弹开', .51, (0, -4, 1.04)),
        cue(960, '轻轻回弹', .61, (0, 2, .96)), cue(1800, '', 0)]),
    'beat_swing': (3000, [
        cue(0, '', 0), cue(360, '左摆重拍', .13, (-16, 3, .89), (3, 3)),
        cue(680, '回摆', .24, (-8, -3, 1.05), (-4, 0)),
        cue(920, '右摆轻拍', .38, (13, 0, .94), (-2, 2)),
        cue(1240, '', .51, (5, 0, 1.01), (3, 0)),
        cue(1680, '再来一拍', .66, (-8, 0, .96)), cue(2140, '收拍', .77, (4, 0, 1.03)), cue(2960, '', 0)]),
    'relaxed': (3200, [
        cue(0, '', 0), cue(480, '眼皮放松', .19, (0, 0, .88)),
        cue(960, '沉下去', .42, (0, 12, .84), (0, 3)),
        cue(1240, '停一口气', .49, (0, 12, .86), (0, 3)),
        cue(2000, '', .49, (0, 12, .86), (0, 3)),
        cue(2360, '先收回视线', .62, (0, 10, .86)), cue(3160, '', 0)]),
    'sleepy': (3480, [
        cue(0, '', 0), cue(760, '慢慢垂下', .21, (0, 4, .71)),
        cue(1320, '眼皮撑住', .43, (0, 9, .53), (0, 4)),
        cue(1840, '', .44, (0, 9, .53), (0, 4)),
        cue(2080, '突然打盹', .61, (0, 16, .30), (0, 3)),
        cue(2280, '勉强抬起', .73, (0, 6, .99)), cue(2760, '', .84, (0, 8, .67)), cue(3440, '', 0)]),
    'funny': (2000, [
        cue(0, '', 0), cue(260, '大小眼交换', .27, gaze=(5, -2)),
        cue(520, '瞳孔交错', .46, (0, -3, 1.04), (-8, 3)),
        cue(760, '定住怪脸', .48, (0, -3, 1.04), (-8, 3)),
        cue(1080, '', .48, (0, -3, 1.04), (-8, 3)),
        cue(1280, '抖一下', .70, (4, 4, .89), (4, -2)),
        cue(1440, '', .84, (-2, -1, 1.03)), cue(1960, '', 0)]),
    'loving': (2520, [
        cue(0, '', 0), cue(320, '眼神放软', .12, (0, 1, .94)),
        cue(560, '心形出现', .35, (0, -2, 1.01)),
        cue(840, '轻轻跳一下', .45, (0, -7, 1.08)),
        cue(1120, '看着你', .47, (0, -2, 1.01)), cue(1840, '', .47, (0, -2, 1.01)), cue(2480, '', 0)]),
    'embarrassed': (2320, [
        cue(0, '', 0, accent=0), cue(160, '先躲视线', .14, gaze=(13, 7), accent=0),
        cue(400, '偏开一点', .32, (3, 5, .94), (11, 8), .2),
        cue(660, '脸红', .47, (3, 6, .92), (11, 8)),
        cue(1400, '', .48, (3, 6, .92), (11, 8)),
        cue(1640, '脸红先退', .58, (2, 5, .94), (8, 7), .15),
        cue(1880, '偷看回来', .79, (-2, 1, .99), (-4, 1), 0), cue(2280, '', 0, accent=0)]),
    'confident': (2120, [
        cue(0, '', 0), cue(300, '抬起一边', .24, (1, -6, 1.06)),
        cue(640, '停住', .43, (1, -9, 1.03)),
        cue(960, '补一眼', .43, (1, -9, 1.03), (5, -2)),
        cue(1560, '', .43, (1, -9, 1.03), (5, -2)), cue(2080, '', 0)]),
    'delicious': (2080, [
        cue(0, '', 0, accent=0), cue(240, '先憋一下', .13, (0, 8, .72), accent=0),
        cue(460, '满足', .32, (0, -18, 1.13), accent=.45),
        cue(640, '亮一下', .44, (0, -7, .99)), cue(860, '', .56, (0, 2, .87)),
        cue(1040, '第二口满足', .65, (0, -10, 1.07), accent=.65),
        cue(1360, '回味', .78, (0, -2, 1.01), accent=0), cue(2040, '', 0, accent=0)]),
    'sad': (3560, [
        cue(0, '', 0), cue(360, '目光先落下', .15, gaze=(0, 10)),
        cue(760, '眼皮垂下', .32, (0, 4, .91), (0, 10)),
        cue(1240, '慢慢低下', .47, (0, 16, .83), (0, 7)),
        cue(2560, '', .47, (0, 16, .83), (0, 7)), cue(3040, '缓缓抬起', .77, (0, 7, .93), (0, 3)),
        cue(3520, '', 0)]),
    'crying': (2520, [
        cue(0, '', 0, accent=0), cue(330, '忍住', .11, (0, 6, .92), (0, 4), 0),
        cue(480, '颤一下', .23, (3, 5, .87), (0, 4), 0),
        cue(600, '', .28, (-2, 7, .92), (0, 3), 0),
        cue(800, '泪珠落下', .41, (0, 8, .94), (0, 4)),
        cue(1440, '渐渐平复', .70, (0, 6, .97), (0, 2), .8),
        cue(1960, '', .86, (0, 2, .99), accent=0), cue(2480, '', 0, accent=0)]),
    'silly': (1680, [
        cue(0, '', 0), cue(200, '瞳孔往里', .18), cue(420, '对眼停住', .35),
        cue(720, '', .35), cue(880, '弹开', .68, (0, -3, .89)),
        cue(1040, '轻微回摆', .78, (0, 2, 1.05)), cue(1640, '', 0)]),
    'angry': (2160, [
        cue(0, '', 0), cue(200, '眼皮压下', .29, (0, 4, .88)),
        cue(560, '瞪住', .40, (0, 4, .88)), cue(1000, '', .40, (0, 4, .88)),
        cue(1160, '短促一哼', .59, (0, -5, 1.07)),
        cue(1320, '收一下', .69, (0, 4, .91)), cue(2120, '', 0)]),
    'insert': (2200, [
        cue(0, '', 0, accent=0), cue(320, '亮起', .19, accent=.7),
        cue(680, '扫过双眼', .44), cue(960, '短停', .59),
        cue(1240, '', .59), cue(1480, '亮点余拍', .70, (0, -1, 1.02), (0, -2), .5),
        cue(2160, '', 0, accent=0)]),
    'eat': (2280, [
        cue(0, '', 0, accent=0), cue(260, '第一口', .23, (0, 7, .62), accent=.3),
        cue(450, '弹起来', .34, (0, -8, 1.06)),
        cue(760, '第二口', .53, (0, 4, .77), accent=.85),
        cue(1000, '小回弹', .65, (0, -5, 1.03), accent=.5),
        cue(1320, '嚼完停一拍', .80, accent=0), cue(2240, '', 0, accent=0)]),
    'tried': (3200, [
        cue(0, '', 0), cue(450, '眼皮先垂', .22, (0, 4, .77)),
        cue(960, '慢慢塌下去', .44, (0, 16, .68), (0, 4)),
        cue(1560, '', .44, (0, 16, .68), (0, 4)),
        cue(1880, '费力抬一下', .66, (0, 3, .96), (0, -3)),
        cue(2120, '又落一点', .75, (0, 9, .82)), cue(3160, '', 0)]),
}

# Right eye, pupil, and accent have their own phase offsets.
DELAYS = {'listening': (0, 0, .13), 'thinking': (.04, -.10, 0),
          'surprised': (.035, -.06, .075), 'question': (.08, -.06, .12),
          'winking': (.07, .045, 0), 'beat_swing': (.07, .07, .10),
          'relaxed': (.04, -.06, 0), 'sleepy': (.115, .045, 0),
          'funny': (.09, .04, 0), 'loving': (.025, .07, .08),
          'embarrassed': (.06, -.075, .085), 'confident': (.10, .08, 0),
          'delicious': (.04, .05, .085), 'sad': (.06, -.08, 0),
          'crying': (.04, .05, .10), 'silly': (.055, .03, 0), 'angry': (.04, .03, 0),
          'insert': (.01, .08, .03), 'eat': (.035, .06, .065), 'tried': (.09, .04, 0)}


def mask_ref(pool, piece):
    if piece is None:
        return None
    mask, box = piece
    soft = mask.filter(ImageFilter.GaussianBlur(.52))
    alpha = ((np.asarray(soft, dtype=np.uint16) * 15 + 127) // 255).astype(np.uint8)
    return pool.add(alpha, box, None)


def shift(ref, dx, dy, sy=1):
    if not ref:
        return None
    i, x, y, r, b, flip = ref
    half = (b-y)*sy/2
    mid = (b+y)/2+dy
    return [i, round(x+dx), round(mid-half), round(r+dx), round(mid+half), flip]


def accent_for(key, original, t, level, ellipse):
    accent = original.copy()
    if level > 0 and key in {'embarrassed', 'delicious', 'surprised', 'crying'}:
        dot = Image.new('RGBA', (480, 480), '#fff1a8' if key in {'surprised', 'delicious'} else '#aef7ff' if key == 'crying' else '#ffabbd')
        if key == 'crying':
            x, y = 371, 292 + min(74, max(0, t-.80)*110)
            alpha = ellipse((x-9, y-13, x+9, y+13))
        elif key == 'embarrassed':
            x, y = 72, 274
            alpha = ellipse((x-15, y-4, x+15, y+4))
            other = ellipse((393, y-4, 423, y+4))
            alpha = ImageChops.lighter(alpha, other)
        else:
            x, y = 240, 152 if key == 'delicious' else 130
            alpha = ellipse((x-5, y-8, x+5, y+8))
        dot.putalpha(alpha)
        accent = Image.alpha_composite(accent, dot)
    if level < 1:
        accent.putalpha(accent.getchannel('A').point(lambda v: round(v*level)))
    return pool_palette(accent)


def pool_palette(image):
    # Preserve alpha while bounding indexed accent colors.
    if not image.getbbox():
        return image
    return image.quantize(colors=64, method=Image.Quantize.FASTOCTREE).convert('RGBA')


def source_refs(source, key, pool, polish):
    refs, accents = [], []
    with Image.open(source) as gif:
        for frame in ImageSequence.Iterator(gif):
            rgb = frame.convert('RGB')
            pose, accent = polish.channels(rgb, key, eye_rows=(0, 480))
            refs.append([mask_ref(pool, piece) for pair in pose for piece in pair])
            accents.append(accent)
    return refs, accents


def compose(key, source, pool, polish, ellipse, fps):
    duration, score = SCORES[key]
    refs, accents = source_refs(source, key, pool, polish)
    channels = [tuple((row[0]/1000, row[i]) for row in score) for i in range(2, 9)]
    delay, pupil_delay, accent_delay = DELAYS[key]
    sample = lambda time, i: track(time, channels[i], polish.ease)

    def at(t, i=0):
        return round(sample(t, i)*(len(refs)-1))

    frames = []
    count = round(duration*fps/1000)
    for i in range(count):
        t = i/fps
        end = (count-1)/fps
        # Blend the delays back to zero as the layers meet the loop anchor.
        envelope = polish.ease(min(t, end-t)/.28)
        layers = []
        for eye in (0, 1):
            local = t - eye*delay*envelope
            ptime = local - pupil_delay*envelope
            x, y, sy = (sample(local, n) for n in (1, 2, 3))
            r = refs[at(local)][eye*2]
            p = refs[at(ptime)][eye*2+1]
            # Keep the pupil attached to its eye while offsetting its gaze separately.
            if p and r:
                center_x, center_y = (r[1]+r[3])/2, (r[2]+r[4])/2
                own_eye = refs[at(ptime)][eye*2]
                if own_eye:
                    xmatch, ymatch = center_x-(own_eye[1]+own_eye[3])/2, center_y-(own_eye[2]+own_eye[4])/2
                else:
                    xmatch = ymatch = 0
                py = y + ymatch + ((p[2]+p[4])/2+ymatch-center_y)*(sy-1) + sample(ptime, 5)
                p = shift(p, x+xmatch+sample(ptime, 4), py, sy)
            layers += [shift(r, x, y, sy), p if r else None]
        atime = t - accent_delay*envelope
        accent = accent_for(key, accents[at(atime)], atime, sample(atime, 6), ellipse)
        frames.append({'layers': layers, 'accent': pool.add_accent(accent)})
    return frames


def laugh_arc():
    """A rounded crescent reused by both eyes, rendered above native resolution."""
    scale = 4
    mask = Image.new('L', (150 * scale, 80 * scale))
    draw = ImageDraw.Draw(mask)
    for step in range(181):
        angle = math.pi * step / 180
        x = 74.875 - 60 * math.cos(angle)
        y = 66 - 50 * math.sin(angle)
        radius = 9 + 4 * math.sin(angle)
        box = (x - radius, y - radius, x + radius, y + radius)
        draw.ellipse(tuple(round(value * scale) for value in box), fill=255)
    return mask.resize((150, 80), Image.Resampling.LANCZOS)


def laugh_heart():
    scale = 4
    mask = Image.new('L', (38 * scale, 38 * scale))
    points = []
    for step in range(120):
        angle = math.tau * step / 120
        x = 19 + 16 * math.sin(angle) ** 3
        y = 17 - (13 * math.cos(angle) - 5 * math.cos(2 * angle)
                  - 2 * math.cos(3 * angle) - math.cos(4 * angle))
        points.append((round(x * scale), round(y * scale)))
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.resize((38, 38), Image.Resampling.LANCZOS)


def laughing(pool, polish, fps):
    marks = [(160, '第一下笑'), (360, '弹起来'), (560, '第二下笑'),
             (760, '短回弹'), (1200, '笑着停住')]
    lift = ((0, 0), (.16, 7), (.36, -25), (.48, -12), (.56, 5), (.76, -14),
            (.92, 1), (1.04, -3), (1.20, 0))
    height = ((0, 1), (.16, .72), (.36, 1.10), (.56, .81), (.76, 1.05), (.96, .94), (1.20, 1))
    left = mask_ref(pool, polish.sprite(laugh_arc(), 59, 191))
    index, x, y, right_edge, bottom, flip = left
    right = [index, 480 - right_edge, y, 480 - x, bottom, flip ^ 1]
    heart = laugh_heart()
    pulse = ((0, 0), (.12, 1), (.20, .86), (.46, 0))
    frames = []
    for i in range(round(2.08 * fps)):
        t = i / fps
        layers = []
        accent = Image.new('RGBA', (480, 480))
        for eye, arc_ref in enumerate((left, right)):
            # The far eye catches up one frame after each compression and rebound.
            local = t - eye * .04 * polish.ease(t / .16)
            dy = track(local, lift, polish.ease)
            sy = track(local, height, polish.ease)
            outward = -1 if eye == 0 else 1
            layers += [shift(arc_ref, outward * max(0, -dy) * .12, dy, sy), None]
            pulse_time = t - (.18 + eye * .08)
            size = 1
            if pulse_time >= .48:
                pulse_time -= .48
                size = .77
            level = track(pulse_time, pulse, polish.ease)
            if level > 0:
                width = round((14 + 18 * level) * size)
                alpha = heart.resize((width, width), Image.Resampling.LANCZOS)
                alpha = alpha.point(lambda value: round(value * level / 17) * 17)
                sticker = Image.new('RGBA', alpha.size, '#ff4264')
                sticker.putalpha(alpha)
                cx = 240 + outward * (167 + pulse_time * 29)
                cy = 178 - pulse_time * 64
                accent.alpha_composite(sticker, (round(cx - width / 2), round(cy - width / 2)))
        frames.append({'layers': layers, 'accent': pool.add_accent(accent)})
    return frames, marks


def one_look(direction, pool, polish, ellipse, fps):
    e = polish.ease
    marks = [(200, '瞳孔先转'), (520, '眼形跟上'), (1200, '驻留'), (1880, '收回视线')]
    frames = []
    for i in range(60):
        t = i/fps
        shift_x = track(t, ((0,0), (.24,0), (.52,-15), (.76,-12), (1.88,-12), (2.20,2), (2.36,0)), e)
        gaze = track(t, ((0,0), (.08,0), (.20,-32), (.34,-29), (1.60,-29), (1.88,3), (2.08,0)), e)
        lid = track(t, ((0,1), (1.08,1), (1.20,.24), (1.32,1)), e)
        layers = []
        for x in (150, 330):
            xc, yc = x+shift_x, 232+shift_x*.16
            white = ellipse((xc-78, yc-77*lid, xc+78, yc+77*lid))
            px, py = x+gaze+shift_x*.5, yc+10
            black = ImageChops.multiply(ellipse((px-31, py-31, px+31, py+31)), white)
            black = black.point(lambda v: round(v*e((lid-.20)/.45)))
            layers += [mask_ref(pool, polish.sprite(m, 0, 0)) for m in (white, black)]
        if direction > 0:
            layers = [[a, 480-r, y, 480-x, b, flip^1] if ref else None
                      for ref in (layers[2:]+layers[:2]) for a, x, y, r, b, flip in [ref or (0,)*6]]
        frames.append({'layers': layers, 'accent': None})
    return frames, marks
