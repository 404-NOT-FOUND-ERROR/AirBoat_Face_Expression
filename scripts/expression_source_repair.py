"""Repair rounded eye and pupil contours while retaining the source choreography."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageSequence

from expression_beat_study import track


REPAIRED_SOURCE = {'thinking', 'question', 'beat_swing', 'funny', 'tried'}


def eye_outline(white, side):
    """Fit the source's outer arc; the inner edge can be joined or occluded."""
    if side:
        white = white[:, ::-1]
    ys, xs = np.where(white[:, :206])
    left = np.full(480, 480)
    np.minimum.at(left, ys, xs)
    ys = np.flatnonzero(left < 206)
    x, y = (left[ys]-150)/100, (ys-240)/100
    points = np.column_stack((y*y, x, y, np.ones_like(y)))
    keep = np.ones(len(y), dtype=bool)
    for _ in range(3):
        beta = np.linalg.lstsq(points[keep], -(x*x)[keep], rcond=None)[0]
        residual = np.abs(points @ beta + x*x)
        keep = residual <= max(.025, np.quantile(residual, .83))
    b, c, d, e = beta
    cx, cy = -c/2, -d/(2*b)
    radius = math.sqrt(cx*cx+b*cy*cy-e)
    px = 100*cx+150
    return np.array((479-px if side else px, 100*cy+240, 100*radius, 100*radius/math.sqrt(b)))


def pupil_parts(dark):
    # Pupil identities follow the two dark components, not the screen midpoint.
    mask = Image.fromarray(dark.astype(np.uint8)*255)
    found = []
    while len(found) < 2:
        y, x = np.where(np.asarray(mask)==255)
        if not len(x):
            raise ValueError('Expected two separate source pupils')
        ImageDraw.floodfill(mask, (int(x[0]), int(y[0])), 128)
        y, x = np.where(np.asarray(mask)==128)
        if len(x)>200:
            found.append(np.array(((x.min()+x.max())/2, (y.min()+y.max())/2,
                                   (x.max()-x.min()+1)/2, (y.max()-y.min()+1)/2)))
        mask = mask.point(lambda v: 0 if v==128 else v)
    return sorted(found, key=lambda shape: shape[0])


def tween(samples, phase):
    pos = min(1, max(0, phase))*(len(samples)-1)
    i = int(pos)
    if i == len(samples)-1:
        return samples[i]
    u = pos-i
    return samples[i]*(1-u)+samples[i+1]*u


def repair_clip(key, source, pool, polish, fps, idle_layers, score, duration, delays):
    outlines, pupils = [], []
    with Image.open(source) as gif:
        for frame in ImageSequence.Iterator(gif):
            pixels = np.asarray(frame.convert('RGB'))
            outlines.append([eye_outline(pixels.min(axis=2)>205, side) for side in range(2)])
            pupils.append(pupil_parts(pixels.max(axis=2)<15))
    outlines, pupils = np.array(outlines), np.array(pupils)
    channels = [tuple((row[0]/1000, row[i]) for row in score) for i in range(2, 8)]
    delay, pupil_delay, _ = delays
    count = round(duration*fps/1000)
    end = (count-1)/fps
    ease = polish.ease
    frames = []

    def register(mask):
        values = ((np.asarray(mask.resize((192, 192), Image.Resampling.LANCZOS), dtype=np.uint16)*15+127)//255).astype(np.uint8)
        return pool.add(values, (0,0,192,192), None)

    # Reuse one antialiased profile at the original source positions and sizes.
    mask = Image.new('L', (768,768))
    ImageDraw.Draw(mask).ellipse((8,8,759,759), fill=255)
    disc = register(mask)
    @lru_cache(maxsize=17)
    def pupil_cap(level):
        # Preserve fatigue's flat upper lid and ease into it from the open pupil.
        if not level:
            return disc
        return register(mask.crop((0,24*level,768,768)).resize((768,768), Image.Resampling.BICUBIC))

    def place(ref, shape):
        x, y, rx, ry = shape
        margin = 192/188
        return [ref[0], round(x-rx*margin), round(y-ry*margin),
                round(x+rx*margin), round(y+ry*margin), ref[5]]

    for frame in range(count):
        t = frame/fps
        variation = ease(min(t,end-t)/.28)
        blend = ease(min(t,end-t)/.24)
        if not blend:
            frames.append({'layers': idle_layers, 'accent': None})
            continue
        eyes, gaze = [], []
        for side in range(2):
            lt = t-side*delay*variation
            pt = lt-pupil_delay*variation
            at = lambda local, channel: track(local, channels[channel], ease)
            eye = tween(outlines[:, side], at(lt,0))
            pupil_eye = tween(outlines[:, side], at(pt,0))
            pupil = tween(pupils[:, side], at(pt,0))
            dx,dy,sy = (at(lt,j) for j in (1,2,3))
            cx,cy,rx,ry = eye
            eyes.append(np.array((cx+dx,cy+dy,rx,ry*sy)))
            px,py,prx,pry = pupil
            gaze.append(np.array((px+cx-pupil_eye[0]+dx+at(pt,4),
                                  cy+dy+(py-pupil_eye[1])*sy+at(pt,5),prx,pry*sy)))

        # Keep the size swap and tilt; only separate the collision at the inner edges.
        gap = eyes[1][0]-eyes[1][2]-eyes[0][0]-eyes[0][2]
        correction = max(0, 3-gap)/2
        layers = []
        for side in range(2):
            s = (-1,1)[side]
            base_eye = (150 if side==0 else 329,234,82,88)
            base_pupil = (150 if side==0 else 329,264,42,39)
            eyes[side][0] += s*correction
            gaze[side][0] += s*correction
            # Bound only the edge cases where extra gaze offset projects a pupil outside its own eye.
            cx,cy,rx,ry = eyes[side]
            px,py,prx,pry = gaze[side]
            vx,vy = (px-cx)/max(1,rx-.75*prx), (py-cy)/max(1,ry-.75*pry)
            if (distance:=math.hypot(vx,vy))>1:
                gaze[side][:2] = (cx+(px-cx)/distance,cy+(py-cy)/distance)
            layers.append(place(disc, np.array(base_eye)*(1-blend)+eyes[side]*blend))
            pupil = np.array(base_pupil)*(1-blend)+gaze[side]*blend
            layers.append(place(pupil_cap(round(blend*16)) if key=='tried' else disc, pupil))
        frames.append({'layers': layers, 'accent': None})
    # Round off tiny position/size jerks between the interpolated source poses.
    # Keep the clock, distinct beats, and exact shared entry/exit poses.
    filtered = [frames[0]]
    for i, frame in enumerate(frames[1:-1], 1):
        span = min(2, i, count-1-i)
        weights = (1, 4, 6, 4, 1) if span==2 else (1, 2, 1)
        refs = []
        for j, ref in enumerate(frame['layers']):
            bounds = [round(sum(weight*frames[i+k-span]['layers'][j][axis]
                                for k, weight in enumerate(weights))/sum(weights)) for axis in range(1,5)]
            refs.append([ref[0], *bounds, ref[5]])
        filtered.append({'layers': refs, 'accent': None})
    return [*filtered, frames[-1]]
