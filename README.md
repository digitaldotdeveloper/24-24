# 24/24 — solar + storage layer slider

Live: **https://digitaldotdeveloper.github.io/24-24/**

Single file. Open `index.html`. No build step, no plugins — GSAP + MotionPathPlugin off cdnjs.

The brand is a Lebanese solar installer. Slide 00 is a blackout and every slide after it is
literally brighter than the last, so the whole slider powers on as you scroll. The transition is
a current that runs down the cable across the stage — it wipes the background, blows the old
parts off and assembles the new ones behind it.

## URL switches

| | |
|---|---|
| `index.html` | normal 16:9, wheel / arrows / keys / swipe |
| `index.html?reel=1` | 9:16 autoplay loop — screen-record this for Instagram |
| `index.html?auto=1` | autoplay at the normal aspect ratio |
| `index.html?slow=4` | quarter speed, to study the motion |

## The art

Every layer is a real render, not a placeholder. They were generated locally through
**Gemini Studio** (the dashboard on `127.0.0.1:4321`), keyed out of flat colour and written as
WebP with alpha into `img/`. The whole set is about 40 renders and a little over 2 MB.

Each cut-out was asked for on a flat **`#00FF00` green** field, which becomes the alpha channel.
Three layers carry a second key: the parts of them that are *holes* — the four windows in the
house, the LCD and fan openings in the inverter, the four slots in the battery rack — were asked
for as flat **`#FF00FF` magenta**. That gives two things at once: the hole is punched out of the
host's alpha, and the magenta blob's bounding box says exactly where the child layer belongs.
`cut.py` reports those rects in design-space coordinates and `patch.py` moves `win1..4`,
`inv_screen`, `fan`, `bms` and `cell1..3` onto them, so the children land on the openings their
host actually came back with instead of where the layout guessed they would be.

Layers that are pure light — `smoke`, `shadow*`, `beam1..3`, `glow_pool` — are still CSS
gradients on purpose. They are atmosphere, not objects, and a render of them keys badly and
looks worse.

### Rebuilding the art

```bash
cd _gen
py make_jobs.py                 # prompts -> jobs.json
GS_TOKEN=... node gen.mjs 40    # queue on Gemini Studio, download to ../_src/*.png
py cut.py                       # key, trim, pad to each layer's box ratio, -> ../img/*.webp
py patch.py                     # index.src.html + img/ -> index.html
```

`gen.mjs` skips anything already in `_src/`, so re-running it is the retry pass. `patch.py` always
rebuilds from `index.src.html`, the untouched placeholder original, so it is safe to re-run at any
point — a half-finished `img/` just yields a half-filled slider with placeholders for the rest.

`_src/` (the raw PNGs, ~25 MB) is gitignored; `img/*.webp` is the build output and is committed.

## Dropping in different art

Put the file path in `SLIDES[i].images` under the **layer id**:

```js
{ key:'panels', …, images:{ bg:'img/bg-panels.webp', panel_a:'img/panel_a.webp' } }
```

Layer ids per slide live in `LAYOUT` — `blackout`, `panels`, `inverter`, `battery`, `onreal`.
`bg` is the full-bleed background; everything else is a cut-out with alpha. Any id left out falls
back to the dashed placeholder, with its name and size, so the slider stays presentable.
All geometry is in a 1280×900 design space that is scaled to cover the viewport.

## Tuning

- **`LAYOUT`** — geometry plus choreography. `in.from` / `out.to` accept `'top' | 'bottom' |
  'left' | 'right'`, meaning "just outside the stage on that side" (mirrored when you go
  backwards). `glow:n` gives a layer a bloom that ignites `n` seconds after it lands — that is
  how the house wakes up window by window on the last slide.
- **`T`** — the transition timings. `surgeDur` is the current's trip across the stage; `inAt` is
  when the new parts start assembling behind it.
- **`SLIDES[i].lum`** — how lit that slide is, 0–1. This is the narrative: `.22 → .54 → .62 →
  .71 → .95`. Don't flatten it.
- **`SLIDES[i].kwh`** — the counter in the right rail.

## Checking a change

`node tools/shot.js <prefix> <W> <H> <slide> <times>` screenshots through CDP at real device
sizes — device emulation, not `--screenshot`, which crops. `LIVE_URL=<url>` shoots the deployed
page instead. `Browser.close` never resolves, so the tool kills the process; each run gets its own
port and profile dir or a stale headless Chrome answers `/json` with dead targets.

## Known limits

- Spec pins are anchored in the 1280-wide design space, which gets cropped hard at 9:16 and on
  phones, so they are hidden below 900px and in reel mode by design.
- Backgrounds are one wide 1600×900 each; in `?reel=1` they cover-crop to the middle band.
- Arabic uses Tajawal from Google Fonts; offline, Arabic digits fall back and look wrong.
