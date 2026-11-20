# Firmware integration handoff

[简体中文](device-integration.zh-CN.md) · [README](../README.md)

## Candidate

AirBoat's companion firmware workspace contains `projects/airboat_expression_transitions`, on `feat/expression-transitions`, based on `011b565` (three-axis idle play). Its CMake version is **1.32.0**. Player changes and the asset adapter are local candidate changes. This repository publishes the artwork, review tools, EAF candidates and specifications.

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
| S31 build | Incomplete; the latest retained log ends at 201/2827, with no successful result, application ELF/BIN or update package |
| Device | Installation and physical acceptance are next |

## Continue in the firmware workspace

1. Read its `AGENTS.md`, pinned build workflow and current AirBoat pipeline. Compare the latest main development branch with the candidate and carry over only the expression-player changes, asset adapter, manifest, EAF files and host tests. Use the version appropriate to that branch.
2. Review allocation and timing first. The current implementation reserves three compact mask poses, two 240 × 240 RGB565 buffers, a source-index buffer and two decoders: roughly **0.6 MB per player** in total. The former “below 170 KiB” description applies to the earlier player. Verify allocation fallback and actual heap placement on S31.
3. Complete the pinned S31 build. Record the actual application/partition sizes and package hashes. Keep the existing layout and saved device settings.
4. Run shared native UI checks, then use the firmware project's product update workflow for installation.
5. On Mosaico, check idle → listen → think → reply → idle; change expression during a transition; cancel by touch and swipe; show Chinese subtitles; open/close the camera; listen for continuous speech. Record frame time, free/largest heap blocks and restart behavior separately from visual feedback.

The browser runtime dataset remains a review asset. The device extracts bounded masks from decoded EAF frames and uses the existing display owner.
