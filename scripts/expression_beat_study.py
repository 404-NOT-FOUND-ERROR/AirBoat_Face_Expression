"""Performance tracks for the three contour review clips."""
from PIL import Image, ImageChops, ImageFilter

SIDE = 480


def track(t, keys, ease):
    if t <= keys[0][0]:
        return keys[0][1]
    for (start, a), (end, b) in zip(keys, keys[1:]):
        if t <= end:
            return a + (b - a) * ease((t - start) / (end - start))
    return keys[-1][1]


def place(piece, x, y, w, h):
    mask, _ = piece
    sx, sy = mask.width / w, mask.height / h
    return mask.transform((SIDE, SIDE), Image.Transform.AFFINE,
                          (sx, 0, -(x - w / 2) * sx, 0, sy, -(y - h / 2) * sy),
                          resample=Image.Resampling.BICUBIC)


def smiling_eye(pair, x, y, w, h, lag, ellipse):
    white, pupil = pair
    a, b, c, d = white[1]
    shape = ellipse((x - w/2, y - h/2, x + w/2, y + h/2))
    if pupil is None:
        return shape, None
    l, t, r, bottom = pupil[1]
    sx, sy = w / (c - a), h / (d - b)
    pupil_mask = place(pupil, x + (l + r - a - c) * sx / 2,
                       y + (t + bottom - b - d) * sy / 2 + lag,
                       (r - l) * sx, (bottom - t) * sy)
    return shape, ImageChops.multiply(pupil_mask, shape)


def happy(t, source, e, ellipse):
    rise = ((0, 0), (.16, 0), (.32, 12), (.52, -36), (.64, -31), (.76, -32),
            (.96, 1), (1.12, -15), (1.24, -6), (1.36, -10), (1.52, -1), (1.72, 0))
    height = ((0, 1), (.16, 1), (.32, .61), (.52, 1.10), (.64, .94), (.76, .94),
              (.96, .75), (1.12, 1.02), (1.28, .94), (1.44, 1), (1.68, 1),
              (1.82, .70), (2.04, 1))
    pairs = []
    for eye, x in enumerate((150, 330)):
        local = t - eye * .035
        dy, sy = track(local, rise, e), track(local, height, e)
        lag = track(local - .045, rise, e) - dy
        pairs.append(smiling_eye(source[eye], x, 239 + dy, 160 + (1 - sy) * 15, 150 * sy,
                                 lag * .32, ellipse))
    return pairs, Image.new('RGBA', (SIDE, SIDE))


def confused(t, source, e, ellipse):
    swing = ((0, 0), (.32, 0), (.52, 23), (.72, -17), (.88, 10), (1.04, -6),
             (1.20, 3.5), (1.36, -1.7), (1.56, 0))
    orbit_x = ((0, 0), (.25, 0), (.44, -6), (.66, 17), (.84, -12), (1.04, 8),
               (1.22, -5), (1.40, 2), (1.62, 0))
    orbit_y = ((0, 0), (.24, 0), (.48, -14), (.66, 8), (.88, 12), (1.06, -7),
               (1.28, 4), (1.60, 0))
    blink = ((0, 1), (.12, 1), (.24, .45), (.36, 1), (3.30, 1), (3.46, .30), (3.62, 1))
    settle = ((0, 0), (1.60, 0), (1.84, -3), (2.20, -3), (2.70, 0))
    pairs, accent = [], Image.new('RGBA', (SIDE, SIDE))
    for eye, (x, w, h, y) in enumerate(((146, 149, 149, 228), (322, 122, 122, 249))):
        local = t - eye * .035
        dx = track(local, swing, e)
        dy = dx * (-.37 if eye == 0 else .55) + track(local, settle, e)
        sy = track(local, blink, e)
        cx, cy = x + dx, y + dy
        white = ellipse((cx - w/2, cy - h*sy/2, cx + w/2, cy + h*sy/2))
        px = cx + (19 if eye == 0 else -17) + track(local - .055, orbit_x, e)
        py = cy + (-25 if eye == 0 else 19) * sy + track(local - .055, orbit_y, e)
        r = 27 if eye == 0 else 25
        pupil = ellipse((px - r, py - r, px + r, py + r))
        pairs.append((white, ImageChops.multiply(pupil, white)))
        dot_x = (45 if eye == 0 else 417) + track(local - .09, swing, e) * .8
        dot_y = 231 + dy * .5
        dot = Image.new('RGBA', (SIDE, SIDE), '#ff7665')
        dot.putalpha(ellipse((dot_x - 7, dot_y - 7, dot_x + 7, dot_y + 7)))
        accent = Image.alpha_composite(accent, dot)
    return pairs, accent


def look_around(t, source, e, ellipse):
    gaze = ((0, 0), (.08, 0), (.20, -31), (.72, -31), (.84, -29), (1.96, -29),
            (2.12, 30), (2.60, 30), (2.72, 27), (4.40, 27), (4.56, -4), (4.80, 0))
    follow = ((0, 0), (.25, 0), (.64, -15), (1.00, -13), (2.16, -13), (2.53, 17),
              (2.75, 15), (4.58, 15), (5.02, -2), (5.25, 0))
    lift = ((0, 0), (.25, 0), (.63, -10), (4.59, -10), (5.18, 0))
    lid = ((0, 1), (1.00, 1), (1.12, .15), (1.24, 1), (3.49, 1), (3.61, .09), (3.78, 1))
    pairs = []
    for eye, base in enumerate((150, 330)):
        local = t - eye * .019
        x = base + track(local, follow, e)
        y = 232 + track(local, lift, e)
        openness = track(local, lid, e)
        ry = 77 * openness
        white = ellipse((x - 78, y - ry, x + 78, y + ry))
        px, py = base + track(local, gaze, e) + (x - base) * .5, y + 10
        black = ellipse((px - 31, py - 31, px + 31, py + 31))
        black = ImageChops.multiply(black, white).point(lambda v: round(v * e((openness - .10) / .35)))
        pairs.append((white, black))
    return pairs, Image.new('RGBA', (SIDE, SIDE))


PERFORMANCES = {
    'happy': (happy, 53, ((320, '蓄力'), (520, '弹起'), (760, '停一拍'), (1120, '二次回弹'))),
    'confused': (confused, 96, ((240, '轻闭眼'), (520, '失衡'), (880, '余震'), (1560, '回稳'))),
    'look_around': (look_around, 156, ((200, '先看左'), (640, '眼形跟上'), (2120, '先看右'),
                                     (2520, '眼形跟上'), (4560, '视线回中'))),
}


def frames(key, artwork, polish, ellipse, fps):
    perform, count, _ = PERFORMANCES[key]
    source = None
    if artwork is not None:
        source, _ = polish.channels(artwork, key)
        source = [[(piece[0].filter(ImageFilter.GaussianBlur(.55)), piece[1]) if piece else None
                   for piece in pair] for pair in source]
    for i in range(count):
        pairs, accent = perform(i / fps, source, polish.ease, ellipse)
        yield [tuple(polish.sprite(mask, 0, 0) if mask is not None else None for mask in pair)
               for pair in pairs], accent
