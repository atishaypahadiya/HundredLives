# Teardown: HundredLives

The look is approved: the valley, Inter Tight and Geist Mono. This teardown measures the site as built and finds the system it is close to. It changes nothing on the pages.

## References

| ID | What | Where |
|---|---|---|
| S1 | Home page | `docs/index.html`, served locally |
| S2 | Runs page | `viewer/runs.html`, published as `docs/runs/index.html` |
| S3 | One life | `viewer/life.html`, published as `docs/runs/<id>/` (measured on `maya-20261029-012642-001`) |
| T | The theme | `docs/THEME.md` |

All three pages are at master `b810fc2`. Their styles are identical to the build on gh-pages (`ac64c68`, 2026-11-08).

Every value below is measured: read from the style blocks (each declaration with its selector), or from the inspector's distinct-value report on the rendered page. Counts are numbers of declarations unless they say "rendered", which counts elements on S1 at 1440 px.

## Findings

### Type

36 distinct font-size values are declared across the three pages; S1 renders 15 distinct sizes at one width.

- Sizes cluster in half-pixel steps between 11 and 17 px: 11, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15, 15.5, 16, 16.5, 17. The most rendered on S1 are 16 (92), 17 (67), 14 (40) and 15 (22).
- Above body: 18, 19, 20, 21, 23, 24, 28, 32.
- Five fluid sizes, all written as `clamp(min, n·vw, max)`: story lines 28–70 (5vw), home h2 28–38 (3.4vw), Runs and life h2 26–36 (3.2vw), pull quote 26–38 (3vw), life title 30–44 (3vw).
- The life title is 32 px below 900 px, then 30 px from 900 to 999 px (the clamp's minimum), then grows. It shrinks across the breakpoint, which is not intended.
- Inline `code` is `.84em`, so it renders at 14.28 px in body text and 13.44 px in 16 px text (both rendered on S1). These are the fractional sizes.
- Body is 17/1.55 (26.35 px line, fractional), 16 px below 600 px on S1 and S2 and below 900 px on S3.
- Mono: 500 weight for labels (11, 11.5, 12), 400 for log lines (12, 12.5, 13.5).
- Weights: 300 (story lines, life title), 400, 500 (site mark, small headings, linked names).
- Tracking: 10 values. Story line −.035em, headings −.03 and −.025, numbers −.02, mono labels .14em (captions) and .12em (HUD).

### Spacing

Margins, paddings and gaps use 36 distinct px values; S1 renders 22.

- By count: 16 (23), 10 (22), 8 (21), 12 (18), 18 (15), 22 (13), 14 (12), 2 (11), 4 (11), 6 (10), 40 (10), 28 (8).
- 2 px divides 89% of declarations. 4 px divides 51%. The large values are all on 4 or 8: 24, 28, 40, 48, 56, 64, 72, 96, 112. The ones that are not are mostly small: 10, 14, 18, 22 inside chips, table cells and nav.
- Odd values come in pairs that make a box look optically even: chip padding 7/11, tooltip 8/11, bubble 12/15/13, corner label 6/10/7.
- Viewport-relative: the life page's header padding (38svh, 22svh below 900 px) and its column offset (−100svh).

### Edges and grid

- Content width: 1120 px on S1, 1280 px on S2 and S3, with 40 px side margins, 16 px below the breakpoint.
- Breakpoints: 600, 640, 860 and 899 px. 600 and 640 both switch the phone layout (S1 uses both). 860 and 899 both switch multi-column layouts (S1 strip, S3 column).
- The S1 strip is three columns with a 28 px gap, one column below 860 px.
- The S3 weeks column is `min(600px, max(36vw, 440px))` wide, over the right of the stage.

### Density

- Body measure: 60–68ch caps (`max-width: 60ch` and `68ch`), 17 px text.

### Corners

Five radii: 3 px (8 declarations: caption chips, tooltips, legend swatches, bubbles), 6 px (code blocks, search field), 4 px (inline code, 44 rendered on S1), 2 px (legend keys), and 50% (dots, play button, slider thumb).

### Colour

The site has one appearance (`color-scheme: dark`). Text colours on `--paper` #0f1611:

| Token | Value | On paper | Used for |
|---|---|--:|---|
| --ink | #eef2ec | 16.2 | headings |
| --ink-2 | #d2dad3 | 12.9 | strong text |
| --body | #b9c4bb | 10.2 | body |
| chart ink | #9eaca1 | 7.8 | chart marks |
| --grey-2 | #8d9a90 | 6.3 | secondary text (44 declarations) |
| --ochre | #a8876b | 5.6 | the stray flag |
| --grey | #56645a | 2.9 | link underlines only |
| --line | #253129 | 1.4 | table rules |

Gold #ffc960 and ghost white are scene colours (T rule 6). Bubbles are #2b2420 on #f3eee3 (13.2). Text over the WebGL scene (nav, HUD, captions, scroll hint) has no fixed background; its contrast has to be sampled on the rendered scene.

### Texture

The grain overlay from T, on every stage: SVG turbulence, overlay blend at .42, `steps(4)` over 1 s.

### Motion

Transitions: story lines fade .7 s and move .9 s, chips .6 s, the loading note .8 s, week rows .3 s, the details marker turns in .18 s. Reduced motion turns off the grain, the line and chip fades and the loading fade. The life page's `.wk` fade is not turned off under reduced motion.

### Deliberately broken

- The odd paddings that balance a chip's box (7/11 and the like) are optical, not errors. The system rounds them to the scale; if any chip then looks uneven, that one gets an override.

## Carry into the system

Into `itten.system.json`:

- Spacing on a 4 px rhythm with 2 and 6 for fine work: 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 56, 72, 96 (14 steps, from 36 values).
- Type sizes 12, 14, 15, 16, 17, 20, 24, 28 and three fluid ranges (story, heading, life title), from 36 declared values. Every line height a whole pixel.
- Radii 3 and 6, plus full rounding for dots.
- Colour roles from the tokens, with More values for the two text colours under 7:1.
- Breakpoints 640 and 900, from four.

## Deliberately not carried

- Half-pixel sizes and `.84em` code.
- The .12em HUD tracking (labels take .14em, as captions do).
- The life page's viewport-relative header padding: it shapes the stage, not the text. It gets an override entry with that reason.
