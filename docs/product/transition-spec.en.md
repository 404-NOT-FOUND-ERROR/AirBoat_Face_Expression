# Expression transitions

[简体中文](transition-spec.zh-CN.md) · [Preview studio](expression-transition-studio.html)

## Shared identity

Each expression has **entry → performance loop → return**. The common anchor is the first stable idle pose on AirBoat green, `#28CF60`. Every standalone entry starts with that same image. The performance keeps its emotion color through the loop; green appears again when the character settles.

In continuous interaction, the next expression starts from the currently visible eye pose. It can also interrupt a transition already in progress. Green remains the resting identity and is not inserted between every dialogue state.

## Timing

- Entry and return use 360 ms at 25 fps for the review pass.
- Pupils lead the eye shape by about 40 ms. The second pupil starts 35 ms later; the second eye shape starts 25 ms later.
- Backdrops follow an eased short HSV hue arc, retaining vivid saturation.
- White eye shapes and black pupils morph in separate normalized coordinate spaces. Whole-face crossfading is not used.
- Performance loops retain their original blink, rebound, tremor, and hold timing.
- On return, the face settles briefly at the shared anchor, then resumes the green idle animation.

## Files

`output/imagegen/airboat-expression-study-20261120/transitions/manifest.json` describes entry, loop, and return clips for all 29 semantics. Three authored direct-bridge GIFs accompany the listening/thinking/happy and happy/surprised examples. Each transition is sampled at 25 fps with a nominal nine-frame duration; identical consecutive frames may be merged by GIF encoding while preserving duration.

The browser studio uses a gzip-compressed `runtime-data.js` containing 160 × 160 per-frame eye/pupil masks, bounds, accents, timing, and palette. It is decompressed locally in the browser. A single display owner samples the current pose and morphs toward any new target. This supports all 841 pairs without storing a separate GIF for every pair. Its clock pauses when the page is hidden or playback is paused.

The release checks verify common entry frames, matching entry/loop endpoints, exact returns, and direct-bridge endpoints. The motion tests cover every pair and interruption during an active transition. Browser checks cover the actual controls, mirror, caption guides, cancellation, three sequences, offline loading, and mobile layout.

## Device delivery

The review package contains 29 EAF candidates at 240 × 240 and 20 fps, with explicit entry, loop and exit ranges. Authored EAF entry/return clips occupy 400 ms after resampling. The browser and the dynamic device transition use 360 ms.

The separate AirBoat 1.32.0 firmware candidate preserves `app_response → app_expression_player` and uses 28 EAF files for 29 semantics; `neutral` and `idle` share one resource. It captures the visible pose and target pose, morphs eye/pupil masks, and resumes the target EAF loop. A new request retargets the visible intermediate pose. Listening keeps its public API and uses a full-face clip.

The implementation reserves three compact mask poses, bounded source indices and two RGB565 buffers. Total player memory is about 0.6 MB, pending S31 measurement. Host semantic-pair, retargeting, cancellation and legacy checks pass. The S31 build, measured partition size, native UI and device display/audio acceptance are the next steps. Continue with the [firmware handoff](../device-integration.en.md).

## Rebuild

```sh
python scripts/polish-expression-gifs.py
python scripts/build-transition-runtime.py
python scripts/measure-transition-eaf.py
python tests/validate_release.py
node tests/transition-motion.cjs
```
