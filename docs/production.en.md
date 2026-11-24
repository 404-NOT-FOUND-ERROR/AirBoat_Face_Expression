# Production workflow

[简体中文](production.zh-CN.md) · [README](../README.md)

For the current AFM workflow, use the [reusable methods](reusable-methods.zh-CN.md) and [project skill](../skills/airboat-expression-workflow/SKILL.md). The EAF layout, frame rates, and 1.29.0 partition numbers below describe an earlier snapshot; check the [current integration guide](product/expression-micro-motion.zh-CN.md) and manifest for new work.

## From an idea to the display

1. **Choose the response.** Select a semantic in the workbench. Trace its trigger and shared asset group.
2. **Design the pose.** Draw a complete face at 480 × 480, or a single left eye for the paired-eye layout.
3. **Design the timing.** Split a movement into anticipation, gesture, hold, follow-through, and rest. Specify when pupils, lids, and the eye pair start and stop.
4. **Compare the animation.** Review its keyframes and loop alongside the original. Check both a large view and the Mosaico-sized preview.
5. **Map the artwork.** Export a replacement draft with the semantic targets, source file, mirror preference, and notes.
6. **Convert and integrate.** Convert to the firmware's EAF format, update frame period and loop interval, then measure the compiled partition size.
7. **Review on Mosaico.** Check eye readability, subtitles, touch cancellation, page transitions, dialogue, and idle playback.

## Formats and layout

| Item | Current implementation |
| --- | --- |
| Display | 480 × 480 |
| Device composition | 360 × 360 logical canvas scaled to the display |
| Paired eyes | Original narrow assets use a left eye at x=10 with a mirrored right eye |
| Full face | Square trial artwork fills the display |
| Listening | A separate 100 × 46 overlay at logical (130,25), 15 fps |
| Original animation | Usually 20 fps; once-only assets hold their final frame |
| Current trial animation | 240 × 240, 10 fps, full-face rendering |
| EAF encoding | 8-bit indexed-color RLE, maximum edge 360 px |
| EAF container | Up to 256 entries including metadata, up to 4 MiB per file |
| Loop notation | [start,end), with a zero-based start and exclusive end |

The workbench's guide overlays mark suggested space for top status and bottom captions. The 1.29.0 app partition has 176,480 B available; the UI partition has 189,808 B. EAF assets are stored in the application partition. Shared files are counted once.

## Motion language

| Expression | Timing idea |
| --- | --- |
| Happy | Press down, spring upward, then two smaller rebounds |
| Dizzy | Alternate direction with decreasing amplitude and a final still pose |
| Curious | Pupils glance first; eye shapes follow, pause, then settle |
| Startled | Quick shape change, a held stare, then a small residual tremor |
| Sleepy | Eyelids lower at slightly different times before a weak recovery |

The study uses 16 native frames per API GIF. Its local review pass interpolates eye shapes and pupils separately onto a fixed palette and samples the motion at 25 fps. The native GIF and the processed preview are saved together.

Transitions use a common green anchor, separate performance loops, and a continuous current-pose handoff. See the [transition specification](product/transition-spec.en.md) and [preview studio](product/expression-transition-studio.html).

## Generation

Install dependencies:

~~~sh
python -m pip install -r requirements.txt
~~~

Use the [OpenAI imagegen skill CLI](https://github.com/openai/skills/tree/main/skills/.curated/imagegen) for static artwork. The repository's GIF runner uses the [official Images API](https://developers.openai.com/api/docs/guides/image-generation). Pass your credential file as an argument:

~~~sh
python scripts/run-expression-imagegen.py probe --env-file /path/to/imagegen.env --proxy http://127.0.0.1:7897
python scripts/run-expression-imagegen.py static --env-file /path/to/imagegen.env --cli /path/to/image_gen.py --proxy http://127.0.0.1:7897
python scripts/run-expression-imagegen.py gif --env-file /path/to/imagegen.env --proxy http://127.0.0.1:7897
~~~

The local file uses DESKBOT_IMAGE_API_KEY and DESKBOT_IMAGE_BASE_URL, with the official base URL https://api.openai.com/v1. The runner reads these values at execution time and passes credentials to the image subprocess. Model, proxy, prompts, input hashes, and output hashes are recorded in the study directory. Each saved call identifies its model explicitly.

## Reproduce and check

~~~sh
python scripts/build-expression-workbench.py --check
python scripts/review-expression-imagegen.py
python scripts/polish-expression-gifs.py
python scripts/build-transition-runtime.py
python scripts/measure-transition-eaf.py
python tests/validate_release.py
node tests/transition-motion.cjs
~~~

For the browser interaction checks, install Playwright in your development environment and run:

~~~sh
node tests/workbench.cjs /path/to/playwright /path/to/chromium
~~~

The checks exercise animation decoding, mirroring, current/original mappings, search, playback, canvas controls, source GIFs, replacement drafts, and desktop/mobile layouts.
