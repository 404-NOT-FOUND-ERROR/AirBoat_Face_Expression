# Transparent Listening Overlay

Date: 2026-11-22. Local handoff for AirBoat / Mosaico and DeskBot.

The original `listen.eaf` is a 100 × 46 grayscale animation with 50 image frames and one metadata entry. All 4,600 pixels of its first frame are opaque in the legacy decoder; 3,560 are black. A black face hid the matte, while green and colorful faces expose the rectangle.

## Composition

Draw the current complete face first. Treat the white-on-black listening animation as a coverage mask and blend each RGB565 channel as `background + (white - background) × coverage`. Black reveals the face, gray edges blend into the current color, and white bars stay bright. Preserve the common EAF opacity rule and all eye/pupil pixels.

[listen_overlay_rgb565.h](listen_overlay_rgb565.h) owns no memory, global state or timing. Arguments use host-order RGB565; panel byte swapping follows composition.

## AirBoat / Mosaico

Inside the existing listening branch of `app_expression_player_draw()`, replace the direct overlay sample with:

```c
uint16_t listen_mask = 0;
if (sample_frame(&player->overlay, logical_x - 130, logical_y - 25, &listen_mask)) {
    color = airboat_listen_over_rgb565(color, listen_mask);
}
```

Keep the original bounds, opacity, and display owner. The layout uses a 360 logical square at `(130,25)` and scales to 480. If the current implementation already uses a full-face listening expression and disables the legacy bar, keep the legacy bar disabled.

The [AirBoat patch](airboat-player.patch) contains the header and sampling change. It passed application checks against the source inspected for this delivery; recheck it against the main developer's current branch before applying.

## DeskBot

Find the final `listen.eaf` composition in the active DeskBot source, then use the same blend over the freshly drawn face. Preserve its Emote/GFX lock, dirty-region redraw, rotation, and flush lifetime. `SetStatus()` still controls listening; drawing frames never re-triggers `SetEmotion()`, base actions, or subtitles.

Invalidate the whole old bar region when listening starts, ends, or leaves the page. For each frame, rebuild the face underneath before blending the bar; blending repeatedly over a previous bar accumulates white. Swap panel bytes once, after blending.

## Validation and delivery

Native C and browser references share RGB565 rounding. Tests cover every RGB565 background, all source frames, gray edges, 360/480 displays, color changes, listening exit, and restart. Each main developer then integrates, runs host regression and the target build, and records physical validation separately.

The actual AirBoat patch was compiled in a scratch copy and passed its original player test: 18 assets, 1,247 frames, layouts, and partitioned redraw. Re-run with `tests/airboat-listen-integration.py --project <airboat-project> --zig <zig.exe> --output <scratch-output>`.

[Open the animated comparison](../../docs/product/listen-overlay-preview.html). This delivery contains the shared algorithm and computer preview. Firmware integration and installation remain with each project's main developer. Both projects can read this local folder and vendor the adopted source.
