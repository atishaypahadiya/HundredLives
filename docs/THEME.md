# The valley theme

The look of the whole hundred-lives site. Every page follows this file.
The reference build is `docs/valley/index.html`. When this file and that page disagree, the page wins, and this file gets updated.

## The idea

The site is one place: a valley.

| In the valley | In the project |
|---|---|
| the valley floor | the sandbox |
| one sheep | one life (one run of a persona) |
| its trail | what it did, week by week |
| the hut in the middle | the referee (odds from the LLM, the outcome from the dice) |
| the mountains | the walls of the sandbox |
| the flock bunching in one corner | the main finding (77 of 80 lives ended in a full-time job) |
| the strays | the interesting lives |
| the ghost cam | following one life while the others run beside it as ghosts |

The feeling: standing in daylight looking at a big landscape. Lively and fresh, with real scale.
The voice: half technical paper, half human story. Exact numbers set in a quiet, warm frame.

## Rules

1. **The landscape is the page.** No boxed widgets, no cards floating on a grey background. Content sits on top of the world or directly below it.
2. **Daylight only.** Blue sky, green meadow, red-ochre rock, snow on the peaks. No dark-mode landscape and no night.
3. **The camera moves on rails.** The reader scrolls, the camera follows a fixed path. No free orbit and no drag-to-rotate.
4. **Every number comes from the data.** Numbers on the page come from `analysis/site_facts.py` or the trace files. Never type a number by hand.
5. **Paths are honest.** Where a sheep stands must come from the run logs (see "What position means"). Until that's wired, any page that shows made-up paths says so in a line of small text.
6. **One colour that means something.** Gold = the life you're following, plus the strays. White = everyone else. Nothing else gets an accent colour.
7. **Grain on everything.** The film grain overlay sits on every full-screen scene.
8. **Respect reduced motion.** With `prefers-reduced-motion`, swap the scroll-driven camera for still frames at each story beat.

## Tokens

```css
--paper:#0f1611;      /* below-the-fold background, deep meadow green-black */
--gold:#ffc960;       /* the followed life and strays */
--ghost:#ffffff;      /* other lives, trails at ~50% opacity */
--sky-top:#4f8fd0; --haze:#c9dbe6;
--grass:#3d6328; --grass-light:#6a8338;
--rust:#8a543f; --ochre:#a8876b; --snow:#f2f4f7;
--sans:"Inter Tight",system-ui,sans-serif;     /* everything people read */
--mono:"Geist Mono",ui-monospace,Menlo,monospace; /* labels, weeks, numbers in the HUD only */
```

Type:
- Story line over the scene: Inter Tight 300, `clamp(28px,5vw,70px)`, line-height 1.04, letter-spacing -0.035em, white, soft text-shadow, centred, balanced wrap.
- Caption under a story line: Geist Mono 500, 12px, uppercase, letter-spacing .14em, on a small blurred dark chip (`rgba(20,30,40,.38)`, 6px blur, 3px radius).
- HUD (week counter, "following" chip): bottom corners, Geist Mono 11.5px uppercase, with the number in Inter Tight 28px.
- Body text below the scene: Inter Tight 400, 16–18px, line-height 1.55, `#b9c4bb` on `--paper`, max 60ch.

Grain overlay (copy exactly):
```css
.stage::after{content:"";position:absolute;inset:-50%;pointer-events:none;mix-blend-mode:overlay;opacity:.42;animation:grain 1s steps(4) infinite;
 background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
```

## Building blocks (all in the reference page)

- **Stage:** a tall scroll track (`900vh`) holding a sticky full-screen stage. Scroll progress 0..1 drives the camera and the week.
- **Camera rails:** a list of shots `{p, pos, look}`, blended with smoothstep. Two shots can be `'chase'`, which is the ghost cam behind one life. The camera never goes below the terrain.
- **Story lines:** `.line` elements with `data-a`/`data-b` scroll ranges that fade in and out. One idea per line, short.
- **Ghost cam:** while chasing one life, everyone else drops to ~38% opacity and the followed life stays solid, with its trail in gold.
- **Terrain:** eroded-noise mountains with per-pixel rock, strata and snow. Reuse it as is, don't rebuild it per page.
- **The world lives in `docs/valley/world.js`,** and every page reuses it: noise, terrain and its shader, sky, lights, clouds, the hut, ground scatter, sheep, trails and the camera rails. A page calls `createValley(canvas, {lives, hero, strays, corner, weeks, time, ghost, shots})` and gets back `{update(progress), resize()}`; the options are documented at the top of the file. Pages keep their own story lines, HUD and scroll handling.
- **Message bubbles:** for a life's actual messages, grainy paper bubbles (warm off-white, the same grain, slight rotation). Never chat-app UI.

## Pages

- **Home (`docs/index.html`):** the valley scroll from the reference page, driven by the real lives, followed by the essay text on `--paper`.
- **Runs (`docs/runs/`):** the same valley seen from the final wide shot. Pick an experiment (01, 02, 03) and the flock walks again with that experiment's lives. Below it, a plain table of the runs.
- **One life (`docs/runs/<id>/`):** opens in the ghost cam on that sheep. Scroll moves through its weeks. Each week's real messages show as grainy bubbles beside the scene. The week counter is the spine.
- **Self replay (`docs/replays/self/`):** the same as a life page, with that persona's details on top.

## What position means

Corners of the meadow are end states (full-time job, founded something, freelance, still searching). Each week, a sheep moves toward the corner that matches what the logs say it's doing that week. Its sideways wobble comes from an embedding of that week's actions, so similar lives walk close together. The mapping lives in one script (`analysis/positions.py`) that writes `positions.json`. Pages only read that file.

## Don't

- Purple or neon gradients, glassy cards, pills and tags, section numbers, small labels above headings, emoji.
- More than one accent colour.
- Free-orbit 3D controls.
- Hand-typed numbers.
