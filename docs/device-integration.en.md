# Firmware integration handoff

[简体中文](device-integration.zh-CN.md) · [README](../README.md)

## Candidate

AirBoat's companion firmware workspace contains `projects/airboat_expression_transitions`, on `feat/expression-transitions`, based on `011b565` (three-axis idle play). Its CMake version is **1.32.0**. The local firmware candidate commit is `0d087e8dfe2925c96374a5bc07c3cebf9ae5a258`. This repository publishes the artwork, review tools, EAF candidates and specifications.

## Playback contract

- Rest on green `#28CF60`; enter an emotion, retain its performance loop, then return to green when the interaction ends.
- Continuous replies transition directly from the visible pose. Retargeting during a transition captures that intermediate pose.
- Keep `app_response → app_expression_player` as the sole display path. Existing speech, idle, tilt and preview requests keep their semantic interfaces.
- The firmware catalog contains 28 files for 29 semantics. `neutral` and `idle` share `transition-idle.eaf`; listening uses a full-face clip through the existing API.
- Review EAF files are 240 × 240 at 20 fps, with explicit entry/loop/exit ranges. The device's dynamic transition is 360 ms, with staggered pupils and eye shapes plus a short HSV background path.

## Evidence

| Layer | Result |
| --- | --- |
| Review player | All 841 semantic pairs, in-flight retargeting, return/cancel, clock wrap pass |
| Firmware C player | All 841 semantic pairs, switch continuity, retargeting, cancel and wrap pass |
| Legacy player | 18 files, 1,247 frames and five pixel layouts pass |
| EAF decoder | 29 review candidates, 1,365 frames pass with the existing decoder |
| Browser | Desktop/mobile controls, pause, mirror, guides, sequences and offline loading pass |
| Pinned S31 candidate build | Passed on ESP-IDF `7b9cc1ac79f865983f59bb8ff3ff43eb74ff1dbe`; application 11,951,904 B, 1,614,048 B partition headroom, linked UI 858,448 B, 190,128 B UI headroom; offline `.irisfw` payload hashes match build images |
| Mainline/native/device | Merge and rebuild on the latest primary branch; native UI, heap/frame-time, camera/audio coexistence, installation and physical acceptance remain |

[Build sizes and SHA-256 evidence](firmware-build.json) records run `20261121-021301-build-34376`, SDK revision and the offline package. The source was committed after that successful build.

## Continue in the firmware workspace

1. Read its `AGENTS.md`, pinned build workflow and current AirBoat pipeline. Compare the latest main development branch with the candidate and carry over only the expression-player changes, asset adapter, manifest, EAF files and host tests. Use the version appropriate to that branch.
2. Integrate commit `0d087e8dfe2925c96374a5bc07c3cebf9ae5a258` (or review the candidate diff against `011b565`) on the latest primary branch. Keep its current camera configuration and application-owned changes.
3. Review allocation and timing. The player reserves three compact mask poses, two 240 × 240 RGB565 buffers, a source-index buffer and two decoders: roughly **0.6 MB per player**. Verify allocation fallback, S31 heap placement, free/largest blocks and frame time on the merged build.
4. Rebuild the merged mainline with the pinned SDK and compare its app/UI/partition sizes. The isolated candidate reported an SC101IOT PCLK delay patch application warning; check it against the working camera configuration before selecting the final package.
5. Run shared native UI checks, then use the firmware project's product update workflow for installation.
6. On Mosaico, check idle → listen → think → reply → idle; change expression during a transition; cancel by touch and swipe; show Chinese subtitles; open/close the camera; listen for continuous speech. Record heap, frame time, camera/audio coexistence and restart behavior separately from visual feedback.

The browser runtime dataset remains a review asset. The device extracts bounded masks from decoded EAF frames and uses the existing display owner.
