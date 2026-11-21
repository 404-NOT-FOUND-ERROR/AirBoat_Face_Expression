# Native-size layered expressions

[Open quality comparison](expression-workbench.html?quality=happy) · [简体中文](layered-expressions.zh-CN.md)

Choose **高清优化 · 480** in the workbench. The comparison supports original/240 px references, full entry/performance/return playback, phase alignment, scrubbing and mirroring.

The candidate uses native 480×480 silhouettes from the source GIF keyframes, cropped eye/pupil layers, 4-bit edge coverage, procedural backgrounds and generated entry/return motion. Coverage is rebuilt at the extracted silhouette boundary; source background glow is excluded. Eye positions, pupil motion, left/right staggering and asymmetric winks retain independent timelines.

| Resource set | Bytes |
| --- | ---: |
| Original EAF library | 4,311,337 |
| Complete 240 px EAF library | 3,810,366 |
| Native layered candidate, AFM + JSON catalog | 2,083,802 |

The candidate covers 29 semantics through 28 clips, sharing idle/neutral. It is 45.3% smaller than the 240 px EAF resources. Web Base64 overhead and runtime buffers are separate measurements.

Sprites share storage only when dimensions, coverage and palette match exactly, including horizontal reflection. Reference positions and keyframe timing remain independent. Current generated artwork has 1,690 distinct sprites and no exact reflected merge; 680 references use reflected canonical storage. The measured reduction comes from layers, coverage encoding and procedural transitions. Symmetry and asymmetric-wink fixtures pass.

[AFM binary](../../assets/optimized/face-motion.afm) · [Catalog](../../assets/optimized/manifest.json) · [Generator](../../scripts/build-optimized-expressions.py) · [Browser player](expression-optimized-player.js)

This is an offline asset/player candidate. Device integration needs an AFM decoder and bounded row/tile compositor under the existing display owner, followed by target builds, memory/timing measurements and hardware review. Canvas preview caches are not a device memory estimate. The existing EAF decoder continues to serve the previous resources.

The binary header is `AFM1` followed by three little-endian uint32 values: version 1, sprite count and payload length. Sprite offsets are relative to the payload. Bounds must be checked before decoding.

For `a4rle`, the token's high nibble is coverage 0–15; the low nibble plus one is run length. A run field of 16 reads a following byte and uses length `16+byte` (maximum 271). Expand coverage to alpha with `value*17`. Indexed accents use `i8rle` count/index pairs with RGBA palettes in the catalog. All decoders must produce exactly `width*height` pixels and reject truncated/overflowing runs.

Layer references are `[sprite,x0,y0,x1,y1,flip]`, with exclusive right/bottom coordinates. Blend normalized coverage inside the moving layer box, then compose white eyes and black pupils over the generated background and accent layer. See the [Chinese specification](layered-expressions.zh-CN.md) for the review procedure and integration order.
