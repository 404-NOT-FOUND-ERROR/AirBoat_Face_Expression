"""Add independently timed pupils, eyelids, and follow-through to the GIF prompts."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/imagegen/airboat-expression-study-20261120"
TIMINGS = {
    "neutral": "F1–5 mostly still, F6 lids start down, F7 blink, F8 eyes spring open, F9 tiny vertical overshoot, then settle. Keep pupils stable between blinks.",
    "idle": "F1–5 pause, F6–8 eyelids descend gently, F9 quick narrow blink, F10 overshoot open a little, F11–16 let the lids settle without another large gesture.",
    "listening": "Eyes barely move. The small top bars start at different frames: center first, outer bars one frame later, then quiet low values. Keep the entire bar separate from the eyes.",
    "thinking": "At F4 pupils glance upward first; the eye pair follows by a few pixels two frames later. Pause briefly. One lid narrows before the pupils return; the eye shapes settle last.",
    "happy": "F1–3 hold. F4 eye shapes press down, F5–6 spring upward. F7 hold a beat. F8–10 drop and make a weaker second rebound. F11–13 two tiny diminishing wobbles, with the pupils catching up one frame after the whites.",
    "surprised": "Pupils flick toward what was spotted around F4. At F5 the white eyes widen abruptly. The small spark appears a beat later and fades first. One buoyant overshoot, then a happy soft settle.",
    "shocked": "F1–3 hold. At F4 immediately pull the whites tall and pupils small. F5–8 hold the stare with just a short left-right-left residual tremor that decays by F9; then settle.",
    "question": "Pupils glance across at F4, then at F6 the whole pair leans about 10 degrees. Hold through F10. Straighten with one two-pixel overshoot, pupils return last.",
    "look_around": "F1–3 hold. At F4 only pupils move left. At F6 the eye pair shifts a few pixels to catch up. Hold that direction. At F10 pupils dart right before the whites. Return to center in two small beats.",
    "winking": "One lid shuts sharply while the other is still. The open pupil moves slightly later. Hold the wink for about three frames, spring back open and add a small settling twitch.",
    "beat_swing": "Two beats with unequal amplitudes: eye pair leans left, briefly pauses, leans right with a shorter overshoot. The pupils trail each turn by one frame.",
    "confused": "F1–3 pause before a stagger. At F4 the eye pair moves right, at F6 left with the pupils slightly delayed, at F8 right smaller, F10 left even smaller, F12 two-pixel residual tremor, F13–16 still.",
    "relaxed": "The lids soften before the whole pair sinks. Hold one breath. Pupils drift back to center while the lids are still low; let the whites float up last.",
    "sleepy": "Independently lower each lid, one frame apart. A short involuntary dip is quicker than the first droop; rebound barely above the starting height before settling.",
    "laughing": "Two fast squashes, second one smaller. A slight overshoot between them and a pause afterward. Both lids compress before the entire pair lifts.",
    "funny": "The small eye grows a beat before the bigger eye shrinks; at mid-clip pupils cross with a tiny overshoot. Put a one-frame ripple after the comic pose.",
    "loving": "Pupils round into hearts after the whites become soft. One low-amplitude pulse, then a pause with the heart shapes still readable.",
    "embarrassed": "Eyes glance away first, then pink cheek dashes light up a beat later. Hold the side glance softly, and let the colored dashes fade before the eyes peek back.",
    "confident": "A smooth lid raise and tiny up-tilt; keep a deliberate hold. One pupil makes a small corrective movement after the larger eye shape stops.",
    "delicious": "One squash anticipating the reward, then two pleasure beats of unequal height. The small accent appears after the first beat and vanishes after the second.",
    "sad": "Very slight downward pupil movement leads the lids. The eye pair sinks last and stays low for longer than the initial move. Recover gently.",
    "crying": "Hold the sad gaze. Quiver for two frames, then one tear drops from the outer edge as quivering decays. Keep the tear within the central region.",
    "silly": "Pupils converge one frame apart while whites stay nearly still. Brief hold. Fast release outward with a small squash, and quick recovery.",
    "angry": "Lids snap diagonally in, eyes hold, then one short outward huff followed by a tiny contraction. Stop before the small rebound turns into repeated jitter.",
    "insert": "Fixed eye forms. The scan shape moves and stops in a short sequence, with one afterbeat in the eye highlights. No sweeping background movement.",
    "look_left": "Pupils travel left before the whites. Let the pupils almost reach the edge, settle inward by a pixel, hold, then return eyes and pupils to center one beat apart.",
    "look_right": "Pupils travel right before the whites. Let the pupils almost reach the edge, settle inward by a pixel, hold, then return eyes and pupils to center one beat apart.",
    "eat": "Two clear squash pulses with unequal amplitudes. Accent lags one frame behind the first pulse. Let the last pulse settle with a small rebound.",
    "tried": "Lids and eye pair droop one after the other. Hold a little longer than expected. A weak lift leads into a small settling afterbeat.",
}
MARKER = "\n\nTiming and layers:"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-completed", action="store_true")
    args = parser.parse_args()
    for key, timing in TIMINGS.items():
        if (OUT / "gif" / f"{key}.gif").exists() and not args.include_completed:
            continue
        path = OUT / "prompts" / f"gif-{key}.txt"
        prior = path.read_text(encoding="utf-8").split(MARKER)[0]
        path.write_text(prior + MARKER +
                        " Frame numbers describe the intended beats in a 16-frame loop. "
                        "Move eyelids, pupils and the eye pair separately. Avoid drifting or flashing backgrounds. "
                        "Prefer a deliberate hold, a clear gesture, then physically small follow-through. "
                        + timing + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
