# ITTEN baseline

The site as it stands, before any change, measured by the ITTEN inspector (`itten/`, pinned at v0.3.4) on 16 November 2026 at master `b810fc2`.

- Pages: the home page (`docs/index.html`), the Runs page and one life (`maya-20261029-012642-001`), served from `docs/` with the published Runs pages copied from gh-pages into the ignored `docs/runs/`. The self replay uses the life template and is left out here; it goes into ITTEN's serial-against-parallel timing run instead.
- Run: `node itten/inspector/inspect.js <url> --full --engines webkit`, one page at a time, on a 14-core Mac. Home took 10 min, Runs 24 min, the life page 10 min.
- The reports, with every finding and its zoomed crops, are kept outside the repository, in ITTEN's `dist/runs/2026-11-16/hundredlives/baseline/`.

Most errors are text over the WebGL scene: the nav, the HUD's week counter, the story line and the scroll hint fall below 4.5:1 where the sky or snow behind them is light. They were sampled at the key widths (320, 768 and 1440 px) at the top of the page; how they change across frames and scroll positions is measured separately when that work starts. The one layout error is the home page's score table, which runs 20 px past the screen at 320 px.

Inspector 0.3.4, full sweep: 320–1920 px every 40 px in Chromium, light and dark, 100% and 200% text, 1x and 2x; WebKit at 320–1920 px every 40 px; motion at 1440 px. No system file yet, so type and spacing are counted, not checked against a scale (distinct-value mode).

| Page | Errors | Warnings | Info |
|---|--:|--:|--:|
| `/` | 14 | 41 | 68 |
| `/runs/` | 7 | 127 | 155 |
| `/runs/maya-20261029-012642-001/` | 6 | 122 | 61 |

## By check

| Check | `/` | `/runs/` | `/runs/maya-20261029-012642-001/` |
|---|--:|--:|--:|
| contrast | 12 E | 7 E, 2 W | 6 E, 3 W |
| font-fallback | 1 W | 2 W | 1 W |
| overflow | 2 E | · | · |
| target-size | 1 I | 1 I | 1 I |
| spacing-scale | · | · | 1 W |
| type-scale | 4 W, 3 I | 4 W, 2 I | 6 W, 2 I |
| text-resize | 1 W | 1 W | 1 W |
| spacing-unit | 23 W | 20 W | 30 W |
| near-miss-edge | 2 W | 31 W | 46 W |
| radius | 1 W | 1 W | 1 W |
| hairline-subpixel | 7 I | 1 W, 8 I | 3 I |
| widow | 4 W | 63 W | 3 W |
| rag | 5 W | · | 8 W |
| text-wrap-balance | 3 I | 1 I | · |
| text-wrap-pretty | 54 I | 143 I | 54 I |
| line-start | · | · | 19 W |
| optical-margin | · | · | 1 I |
| reduced-motion | · | · | 3 W |
| frame-timing | · | 2 W | · |

## Distinct values

Across the sweep, a value that follows the window counts once.

| Page | Font sizes | Spacing values | Radii |
|---|--:|--:|--:|
| `/` | 17 | 24 | 4 |
| `/runs/` | 12 | 21 | 3 |
| `/runs/maya-20261029-012642-001/` | 16 | 30 | 2 |

## Errors

### `/`

- contrast: Text measures 3.01:1 against the pixels behind it (needs 4.5:1). a.mark "HundredLives" (light 320; dark 320)
- contrast: Text measures 2.79:1 against the pixels behind it (needs 4.5:1). a "Self" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 2.79:1 against the pixels behind it (needs 4.5:1). a "Runs" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 2.79:1 against the pixels behind it (needs 4.5:1). a "Source ↗" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 2.24:1 against the pixels behind it (needs 3:1, large text). h1.line "One AI persona, many simulated lives" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 3.26:1 against the pixels behind it (needs 4.5:1). small "Scroll to enter the valley" (light 320; dark 320)
- contrast: Text measures 2.96:1 against the pixels behind it (needs 4.5:1). div "week" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 2.93:1 against the pixels behind it (needs 3:1, large text). span "1" (light 320; dark 320, 1440)
- contrast: Text measures 2.43:1 against the pixels behind it (needs 4.5:1). span.of "of" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 2.63:1 against the pixels behind it (needs 4.5:1). span "52" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 1.08:1 against the pixels behind it (needs 4.5:1). a.anchor "Findings" (light 1440; dark 1440)
- contrast: Text measures 2.19:1 against the pixels behind it (needs 4.5:1). a.anchor "How it works" (light 1440; dark 1440)
- overflow: Text runs 20 px past the right edge, usually a word too long for the line; the page scrolls sideways (WCAG 1.4.10, LAY-03). td.v "partly: cap and total held, per-run ran…" (light 320; 200% text 320; webkit 320)
- overflow: Text spills 36 px out of tr "No life would hit the token cap, each w…". td.v "partly: cap and total held, per-run ran…" (light 320; 200% text 320; webkit 320)

### `/runs/`

- contrast: Text measures 2.40:1 against the pixels behind it (needs 4.5:1). a "Source ↗" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 4.45:1 against the pixels behind it (needs 4.5:1). span "Full-time job" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 4.25:1 against the pixels behind it (needs 4.5:1). span "Building their own thing" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 2.64:1 against the pixels behind it (needs 4.5:1). a.anchor "Findings" (light 1440; dark 1440)
- contrast: Text measures 4.40:1 against the pixels behind it (needs 4.5:1). a "Self" (light 1440; dark 1440)
- contrast: Text measures 3.53:1 against the pixels behind it (needs 4.5:1). a.anchor "How it works" (light 1440; dark 1440)
- contrast: Text measures 3.96:1 against the pixels behind it (needs 4.5:1). a "Runs" (light 1440; dark 1440)

### `/runs/maya-20261029-012642-001/`

- contrast: Text measures 4.24:1 against the pixels behind it (needs 4.5:1). a "Self" (light 320; dark 320)
- contrast: Text measures 4.40:1 against the pixels behind it (needs 4.5:1). a "Runs" (light 320; dark 320)
- contrast: Text measures 2.95:1 against the pixels behind it (needs 4.5:1). a "Source ↗" (light 320; dark 320)
- contrast: Text measures 3.61:1 against the pixels behind it (needs 4.5:1). span "Week" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 3.20:1 against the pixels behind it (needs 4.5:1). span "of 26" (light 320, 1440; dark 320, 1440)
- contrast: Text measures 2.60:1 against the pixels behind it (needs 3:1, large text). b "1" (light 1440; dark 1440)

## Warnings, by check

Three examples each; the full list is in each report.

### font-fallback

`/` 1, `/runs/` 2, `/runs/maya-20261029-012642-001/` 1.

- `/`: 11 glyphs in 9 elements render in .SF NS because "Inter Tight" lacks them. a "Source ↗"
- `/runs/`: 1 form control (input[type=range]) computed in Arial at 13.3333px, not the page's "Inter Tight", system-ui, sans-serif. input "Week"
- `/runs/`: 1 glyph in 1 element render in .SF NS because "Inter Tight" lacks them. a "Source ↗"

### type-scale

`/` 4, `/runs/` 4, `/runs/maya-20261029-012642-001/` 6.

- `/`: Font size 11.5 px is fractional, usually compounded from em or percentage maths; on 3 text elements. div "week"
- `/`: Font size 13.44 px is fractional, usually compounded from em or percentage maths; on 16 text elements. code "files"
- `/`: Font size 13.5 px is fractional, usually compounded from em or percentage maths; on 2 text elements. code "name: Self born: 2005, Indore, India ex…"

### text-resize

`/` 1, `/runs/` 1, `/runs/maya-20261029-012642-001/` 1.

- `/`: 262 of 262 text elements keep their size when the browser's default text size is doubled, so they are set in px or vw alone and ignore the reader's setting. a.mark "HundredLives"
- `/runs/`: 670 of 670 text elements keep their size when the browser's default text size is doubled, so they are set in px or vw alone and ignore the reader's setting. a.mark "HundredLives"
- `/runs/maya-20261029-012642-001/`: 379 of 379 text elements keep their size when the browser's default text size is doubled, so they are set in px or vw alone and ignore the reader's setting. a.mark "HundredLives"

### spacing-unit

`/` 23, `/runs/` 20, `/runs/maya-20261029-012642-001/` 30.

- `/`: 2 px of padding-top, padding-bottom stays 2 px when the browser's text size is doubled, on 45 elements: it is set in px, so the text grows and the gap does not. td "Model sampling alone, with dice and ord…"
- `/`: 4 px of margin-top stays 4 px when the browser's text size is doubled, on 19 elements: it is set in px, so the text grows and the gap does not. b "1OF 52"
- `/`: 5 px of padding-right, padding-left stays 5 px when the browser's text size is doubled, on 17 elements: it is set in px, so the text grows and the gap does not. code "files"

### near-miss-edge

`/` 2, `/runs/` 31, `/runs/maya-20261029-012642-001/` 46.

- `/`: Left edges 2.91 px apart: i at 120.66, i at 123.56. i
- `/`: Right edges 2.91 px apart: i at 132.66, i at 135.56. i
- `/runs/`: Left edges 2 px apart: button "Experiment 01 Maya, 80 lives" at 14, button.play "Play" at 16. button "Experiment 01 Maya, 80 lives"

### radius

`/` 1, `/runs/` 1, `/runs/maya-20261029-012642-001/` 1.

- `/`: 4 different corner radii: 2, 3, 4, 6 px. i
- `/runs/`: 3 different corner radii: 2, 3, 6 px. i
- `/runs/maya-20261029-012642-001/`: 2 different corner radii: 2, 3 px. i

### widow

`/` 4, `/runs/` 63, `/runs/maya-20261029-012642-001/` 3.

- `/`: The last line holds one word, "container", under 1 full line, and text-wrap: pretty does not move it. td "Run a command in its container"
- `/`: The last line holds one word, "accepted", under 1 full line, and text-wrap: pretty does not move it. td "Turn down an offer it accepted"
- `/`: The last line holds one word, "workspace", under 1 full line, and text-wrap: pretty does not move it. td "Read and write files in its workspace"

### rag

`/` 5, `/runs/maya-20261029-012642-001/` 8.

- `/`: Line 2 of 4 ends 33% short of the measure, a hole in the rag. div "AI Village AI Digest. Frontier models w…"
- `/`: Line 1 of 7 ends 29% short of the measure, a hole in the rag. p.dek "I give an AI agent a made-up background…"
- `/`: Line 1 of 3 ends 31% short of the measure, a hole in the rag. span.verb "As written: parents messaged 10+ times …"

### contrast

`/runs/` 2, `/runs/maya-20261029-012642-001/` 3.

- `/runs/`: Text drops to 3.95:1 over a tenth of the background behind it (median 4.62:1, needs 4.5:1). span "Gigs and part-time"
- `/runs/`: Text drops to 2.63:1 over a tenth of the background behind it (median 3.37:1, needs 3:1). h1.headline "Experiment 01"
- `/runs/maya-20261029-012642-001/`: Text drops to 3.06:1 over a tenth of the background behind it (median 9.55:1, needs 4.5:1). a.mark "HundredLives"

### hairline-subpixel

`/runs/` 1.

- `/runs/`: A hairline off the device-pixel grid at 1×: top border at 750.72 px, 1 px wide; bottom border at 789.72 px, 1 px wide. button.play "Play"

### frame-timing

`/runs/` 2.

- `/runs/`: While clicking this element, with the CPU slowed 9.54 times to the reference device (benchmark index 378, reference 400; this machine 3814), 4 of 23 animation frames ran past the 16.7 ms budget of a … button "Experiment 01 Maya, 80 lives"
- `/runs/`: While clicking this element, with the CPU slowed 9.54 times to the reference device (benchmark index 378, reference 400; this machine 3814), 3 of 33 animation frames ran past the 16.7 ms budget of a … button "Experiment 02 A Self, 5 lives"

### spacing-scale

`/runs/maya-20261029-012642-001/` 1.

- `/runs/maya-20261029-012642-001/`: 14.5 px is fractional, usually compounded from em or percentage maths; used 2 times as margin-top, margin-bottom. p.empty "Exported from the private code host whe…"

### line-start

`/runs/maya-20261029-012642-001/` 19.

- `/runs/maya-20261029-012642-001/`: Line 2 of 2 begins with "·". div "applied to job-10 · odds 0.10 (base 0.0…"
- `/runs/maya-20261029-012642-001/`: Line 2 of 2 begins with "·". div "applied to job-01 · odds 0.090 (base 0.…"
- `/runs/maya-20261029-012642-001/`: Line 2 of 2 begins with "·". div "applied to job-04 · odds 0.090 (base 0.…"

### reduced-motion

`/runs/maya-20261029-012642-001/` 3.

- `/runs/maya-20261029-012642-001/`: The transition of transform still runs with prefers-reduced-motion: reduce, moving transform (180 ms). summary "Run details" ::before
- `/runs/maya-20261029-012642-001/`: The transition of transform still runs with prefers-reduced-motion: reduce, moving transform (180 ms). summary "Everything logged this week" ::before
- `/runs/maya-20261029-012642-001/`: The transition of transform still runs with prefers-reduced-motion: reduce, moving transform (180 ms). summary "Everything logged this week" ::before

