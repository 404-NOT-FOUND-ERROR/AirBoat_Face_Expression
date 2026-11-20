# Mosaico expression artwork pack

Nine original animations for the 480 × 480 Mosaico display.

[English overview](../README.md) · [中文总览](../README.zh-CN.md)

| Semantic | Artwork | Source rate | Loop interval |
| --- | --- | --- | --- |
| idle | Idle / 待机 | 20 fps | Whole sequence, 208 frames |
| waiting | Waiting / 等待 | 20 fps | [10,218) |
| confused | Confused / 困惑 | 20 fps | [16,224) |
| happy | Happy / 开心 | 20 fps | [16,224) |
| surprised | Surprised / 惊讶 | 20 fps | [16,224) |
| angry | Angry / 生气 | 20 fps | [16,224) |
| sad | Sad / 伤心 | 20 fps | [16,224) |
| bored | Bored / 无聊 | 20 fps | [16,224) |
| drowsy | Drowsy / 打盹 | 20 fps | [16,224) |

The interval is zero based with an exclusive end. Animated faces retain the green field, white eyes, and black pupils from the source art.

## Files

- source-gif/: original animation inputs; bracketed filename ranges describe the loop.
- eaf/: individual ESP Emote GFX animation files.
- emote_assets.bin: the complete 7,500,826-byte MMAP pack.
- index.json: semantic, file, position, frame rate, and loop metadata.
- source-manifest.json: dimensions, frame counts, labels, and timing.
- validation.json: conversion checks, image comparisons, and seams.
- converter.json: source converter and build identifier.
- integration/: player patches for the original 20 fps cadence and exit timing.

## Playback and integration

The artwork uses entry, loop, and exit segments. Waiting has a 10-frame entry and exit; the other non-idle animations have 16-frame entry and exit segments.

Keep the player rate at 20 fps and the exit frame step at 1 to preserve the original cadence. The included patches target esp_emote_gen_player 0.0.2 and esp_emote_gfx 3.0.5. Apply them when integrating those component versions.

For the AirBoat 1.29.0 indexed-RLE player, use the trial conversion path described in the main production guide. The workbench contains original and current maps together, and its JSON draft supplies the selected semantic bindings.
