"""Prepare and generate the separate Square Pop art round through the existing API runner."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/imagegen/airboat-square-pop-20261124'
ROLES = [
    ('idle','待机','two soft square whites slowly become one rectangle and one large round white, playful asymmetric gaze',
     'quiet breath, one pupil darts first; left white extends as a rectangle while right eye inflates round; pause, blink, quick double blink and elastic return','green'),
    ('listening','聆听','one wide square white and one round white, black pupils facing forward, three tiny cyan square pulse marks above',
     'pupils focus first, then whites lean forward; three square pulse marks rise in staggered rhythm; one blink and settle','green'),
    ('thinking','思考','one huge upright rectangular white and a smaller circular white, black pupils both far up-left',
     'pupils shoot up-left first, one white telescopes into an upright rectangle while the other tilts; hold a long thought; a tiny corrective pupil glance, a one-eye blink, return','periwinkle'),
    ('happy','开心','two inflated white rounded tiles, black crescent pupils, unequal eye sizes',
     'squash low, spring high, freeze a beat, drop with a smaller second rebound, two tiny settling bounces, round-square corners flex elastically','lime'),
    ('surprised','突然发现','two large white square-circle hybrids, tiny centered black pupils, one small yellow pixel spark',
     'pupils shrink before the whites pop outward into oversized square eyes, quick anticipatory flinch, hold, soft wobble back','yellow'),
    ('shocked','受惊','extremely tall white rounded rectangles, pinpoint black pupils at different heights',
     'both whites recoil upward and stretch tall, far eye catches up one frame later, shocked freeze, two diminishing tremors, cautiously return','coral'),
    ('question','好奇歪头','a big round eye and a narrow horizontal rectangular white lean along one diagonal, black pupils glance sideways',
     'pupils glance first, rectangle extends like a telescope then both whites tilt diagonally; hold and a small secondary tilt, blink, straighten with a tiny rebound','cyan'),
    ('look_around','张望','one white rectangular telescope and one circular white, black pupils near their edges',
     'pupils snap to left, whites follow and left rectangle telescopes out; long curious hold; pupils dart right before whites follow; small overshoot, center','lime'),
    ('winking','眨眼','one eye is a flat white rectangular shutter, the other a huge lively circle with black pupil',
     'one square white closes decisively into a horizontal bar while the circular eye inflates, hold, spring the shutter open with a small bounce','pink'),
    ('beat_swing','摇摆','two white eyes form a diagonal lever, one square and one circle, black pupils with opposite vertical offsets',
     'strong left downbeat with squash, pause, lighter right upbeat with stretch, two smaller offset swings; pupils arrive late and overshoot subtly','violet'),
    ('confused','晕乎乎','uneven square and circular whites, black square spiral pupils with small coral orbit pixels',
     'one strong off-balance wobble followed by alternating smaller aftershocks; square spiral pupils lag and turn after the whites stop, two tiny colored squares catch up last','periwinkle'),
    ('relaxed','放松','wide soft rectangular whites, droopy horizontal upper lids, small low black half pupils',
     'pupils sink a little, eyelids descend, whites exhale into broad rectangles; long soft hold with a small breathing swell, reopen gently','green'),
    ('laughing','大笑','two chunky white crescent eyes with squared outer corners, two little coral square-heart accents',
     'lower lids rise to hide solid pupils, whites curl into broad cheeky crescents; two powerful unequal laugh pulses, far eye delayed, small hearts pop late, two settling rebounds','yellow'),
    ('funny','搞怪','a huge circular white attached visually to a narrow rectangular white with black pupils pointing in strange directions, match the reference spirit',
     'rectangle shoots outward while the other eye balloons into a giant circle; pause in the ridiculous pose; eye sizes swap across sides, pupils react late; two sharp tiny shakes, spring back','violet'),
    ('loving','喜欢','two bright white rounded-square eyes, black chunky pixel-heart pupils, pink square accents',
     'pupils turn into crisp stepped hearts, whites lean together, one huge affection pulse then a smaller heart pulse, cheeks light up late and fade before return','pink'),
    ('embarrassed','害羞','slanted white rectangular and round eyes glance down-sideways, two short pink pixel cheek blocks',
     'pupils flee sideways, one white partly hides behind its own sliding rectangular lid; pink cheek blocks appear after a pause, one shy tiny shake, peek back slowly','pink'),
    ('confident','得意','one lifted tall square white and one half-closed round eye, black pupils slyly offset',
     'one rectangle lifts as if raising an eyebrow but without separate brows; smug deliberate hold; pupils make one extra sideways check, subtle self-satisfied bounce and return','cyan'),
    ('delicious','好吃','chunky delighted white arcs with squared corners and one tiny yellow pixel star',
     'anticipatory squish, eyes spring into big pleased arcs, unequal two delight pulses; pixel star appears one beat late; hold satisfaction and settle','yellow'),
    ('sad','难过','drooping white soft-square eyes with sagging outer corners, black pupils looking down',
     'pupils lower first, heavy white corners sag after them; long low hold with a small inhalation rise, slow partial lift then return','blue'),
    ('crying','哭泣','drooping white rounded tiles and black half pupils, two distinct blue chunky pixel teardrops',
     'try to hold back, two small uneven quivers, left pixel tear slides and accelerates down, right tear falls later, trembling diminishes and eyes calm','cyan'),
    ('silly','俏皮','one squarish white and one circular white touch near center, solid black pupils cross inward comically',
     'pupils converge one at a time, whites squeeze into a squarish cross-eyed pose, hold, suddenly pop apart, soft elastic overshoot and return','lime'),
    ('angry','生气','bold angled rectangular white eyes narrowing toward the center, round black pupils',
     'rectangular lids snap diagonally inward with a preparatory squeeze, hold glare, short huff expanding whites, one recoil and smaller settling contraction','coral'),
    ('insert','插入动画','two white square-circle eyes with tiny crisp square scan highlights',
     'rectangular scan blocks align around whites one at a time, pupils anticipate each scan, short locked hold, a final pixel spark and soft return','cyan'),
    ('look_left','看左边','both solid black pupils at the viewers left, left eye stretched into a white rectangle while right stays round',
     'pupils move left decisively first, left white telescopes as a rectangle, both whites follow with overshoot, long hold, pupils and whites return on separate beats','lime'),
    ('look_right','看右边','both solid black pupils at the viewers right, right eye stretched into a white rectangle while left stays round',
     'pupils move right decisively first, right white telescopes as a rectangle, both whites follow with overshoot, long hold, pupils and whites return on separate beats','lime'),
    ('eat','吃东西','alternating white rectangular and round squashed eyes with black oval pupils, one tiny acid pixel accent',
     'two clear exaggerated chew beats, left squashes into horizontal rectangle then right compresses; little satisfied hold, pixel accent lags the first bite, quick rebound','yellow'),
    ('tried','疲惫','very low drooping white pancake-rectangles, thin solid black half pupils, far eye more collapsed',
     'whites sink dramatically and elongate sideways, hesitate at bottom, two small attempts to hold up, inhale and effortfully lift, pause, collapse down again before slowly recovering','periwinkle'),
]

PALETTE = {'green':'#28cf60','lime':'#a8f900','yellow':'#f8f600','coral':'#ff4264',
           'cyan':'#00d4e5','pink':'#ff168c','violet':'#6e32ff','periwinkle':'#6679ff','blue':'#4031f5'}
STYLE = '''Make a bold, mischievous digital pet eye-expression study inspired by the reference image. The reference is a STYLE reference: playful absurd proportions, a large round white eye contrasted with a crisp rectangular or square white eye, solid black pupils, vivid flat green. Develop a consistent family with playful graphic geometry. Only TWO white eye forms and their own solid black pupils, with small optional colored pixel accents. Use creative rectangle-to-circle shape changes, asymmetry, huge squash and stretch, crisp edges and clean flat color. Keep it charming and funny, not generic symmetrical emoji. No mouth, nose, body, text, outlines, texture, 3D, shadows, gradients, devices, border or screenshot UI. Full square face, eye pair centered around y=49%, use about 74% of face width, retain 7% side margins, 18% clean top and 20% clean bottom for device overlays. Different expressions must have clearly different silhouettes.'''


def prepare():
    for folder in ('inputs','prompts','raw','png','gif','calls','preview'):
        (OUT/folder).mkdir(parents=True, exist_ok=True)
    reference = OUT/'inputs/user-reference.png'
    with Image.open(reference) as im:
        # Remove the workbench borders and dimensions from the user's screenshot.
        a=im.convert('RGB')
        w,h=a.size
        a.crop((18,4,w-9,h-18)).resize((480,480),Image.Resampling.LANCZOS).save(OUT/'inputs/style-reference.png')
    groups=[]
    for start in range(0,len(ROLES),4):
        roles=[dict(zip(('key','label','pose','motion','palette'),row)) for row in ROLES[start:start+4]]
        number=f'{start//4+1:02}'
        tiles=[]
        for where,role in zip(('top-left','top-right','bottom-left','bottom-right'),roles):
            tiles.append(f"{where}: {role['pose']}. Background flat {PALETTE[role['palette']]}. Show its most characteristic pose, not a neutral default.")
            prompt=(STYLE+f"\n\nAnimate ONLY {role['key']} ({role['label']}). Use supplied still as the art reference, keep one complete face in each frame.\n"
                    f"Choreography: {role['motion']}. Use fast anticipations, a readable held pose, then two weaker follow-throughs. The pupils, lids and whites start/stop on different beats. Geometry should deform elastically rather than the entire face sliding as a single rigid sticker. Camera locked, background constant {PALETTE[role['palette']]}. End near the starting arrangement for a loop. Return an actual animated GIF, never a sprite sheet.\n")
            (OUT/'prompts'/f"gif-{role['key']}.txt").write_text(prompt,encoding='utf-8')
        if len(roles)<4:
            tiles.append('bottom-right: a close variant of the first tile, same style, no text.')
        text=STYLE+'\n\nCreate a precise 2 by 2 full-bleed square atlas, split at exactly 50% width and height. Four equal tiles, no gutters or separators. Each tile has its own complete face and solid background, in this order:\n'+'\n'.join(tiles)
        (OUT/'prompts'/f'static-{number}.txt').write_text(text,encoding='utf-8')
        groups.append({'id':number,'roles':roles})
    spec={'project':'AirBoat','round':'Square Pop / 方圆怪趣','date':'2026-11-24','groups':groups,
          'aliases':{'neutral':'idle','sleepy':'tried'},'palette':PALETTE,'style':STYLE,
          'source_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
          'coverage':'27 independent performances, 29 compatible semantics, 28 visible entries'}
    (OUT/'study.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'prepared','performances':len(ROLES),'groups':len(groups),'directory':str(OUT)}))


def main():
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        prepare()
        return
    spec=importlib.util.spec_from_file_location('square_pop_api',ROOT/'scripts/run-expression-imagegen.py')
    api=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    api.OUT=OUT
    api.BASE=OUT/'inputs/style-reference.png'
    api.main()


if __name__=='__main__':
    main()
