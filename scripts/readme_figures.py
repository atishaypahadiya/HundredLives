"""The README's figures, drawn from docs/data/positions.json so they always match the site.

  uv run --with matplotlib python scripts/readme_figures.py            # writes .github/readme/*.png
  uv run --with matplotlib python scripts/readme_figures.py --fonts DIR  # use Inter Tight / Geist Mono TTFs from DIR

Figures:
  flock.png    experiment 01 seen from above: every path, the strays in gold, each corner with its count
  weeks.png    what every life was doing each week: experiment 01 (Maya) beside the Self experiments
  endings.png  how lives ended, per experiment
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".github" / "readme"

# The valley palette (docs/THEME.md)
PAPER = "#0f1611"
MEADOW = "#22361f"
INK = "#e9eee8"
MUTED = "#9aa79b"
GOLD = "#ffc960"
STATE = {  # what a life is doing in a week
    "j": ("Full-time job", "#e9eee8"),
    "g": ("Gigs and part-time", "#7f9e58"),
    "b": ("Building their own thing", "#d4895a"),
    "s": ("Still searching", "#2c3a2d"),
}
END_ORDER = ["job", "gigs", "building", "searching"]
END_LABEL = {"job": "Full-time job", "gigs": "Gigs and part-time", "building": "Building their own thing", "searching": "Still searching"}
END_COLOR = {"job": STATE["j"][1], "gigs": STATE["g"][1], "building": STATE["b"][1], "searching": STATE["s"][1]}


def fonts(directory):
    sans, mono = "DejaVu Sans", "DejaVu Sans Mono"
    if directory:
        for f in Path(directory).glob("*.ttf"):
            font_manager.fontManager.addfont(str(f))
        names = {f.name for f in font_manager.fontManager.ttflist}
        sans = "Inter Tight" if "Inter Tight" in names else sans
        mono = "Geist Mono" if "Geist Mono" in names else mono
    plt.rcParams.update({"font.family": sans, "text.color": INK, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED, "savefig.facecolor": PAPER})
    return sans, mono


def legend(fig, items, x, y):
    """A row of colour swatches with labels, spaced by the real width of each label."""
    r = fig.canvas.get_renderer()
    for color, label in items:
        fig.patches.append(Rectangle((x, y - .011), .011, .022 * fig.get_figwidth() / fig.get_figheight() * .55,
                                     color=color, transform=fig.transFigure, figure=fig))
        t = fig.text(x + .016, y, label, fontsize=13, color=INK, va="center")
        w = t.get_window_extent(renderer=r).width / fig.bbox.width
        x += .016 + w + .028


def group(data, gid):
    return next(g for g in data["groups"] if g["id"] == gid)


def flock(data, mono, path):
    g = group(data, "exp01")
    lives = g["lives"]
    fig = plt.figure(figsize=(16, 8.2), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(MEADOW)
    fig.patch.set_facecolor(MEADOW)
    # soft light falling on the meadow
    import numpy as np
    yy, xx = np.mgrid[-1:1:300j, -1:1:600j]
    glow = np.exp(-((xx + .1) ** 2 * 1.2 + (yy - .2) ** 2 * 2.2))
    ax.imshow(glow, extent=[-230, 230, -150, 190], cmap=ListedColormap(["#1b2b19", "#2b4526"], N=256) if False else
              matplotlib.colors.LinearSegmentedColormap.from_list("m", ["#182616", "#2e4a28"]), aspect="auto", zorder=0)

    def xy(p):  # north (negative z) is up, as seen from the home page's camera
        return p[0], -p[1]

    def smooth(pts, k=6):  # Catmull-Rom through the weekly points, k samples per week
        out = []
        P = [pts[0]] + pts + [pts[-1]]
        for i in range(1, len(P) - 2):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            for j in range(k):
                t = j / k
                out.append(tuple(.5 * (2 * p1[d] + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t * t
                                       + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t ** 3) for d in (0, 1)))
        out.append(tuple(pts[-1]))
        return out

    for L in sorted(lives, key=lambda L: L["stray"]):
        xs, ys = zip(*smooth([xy(p) for p in L["points"]]))
        if L["stray"]:
            ax.plot(xs, ys, color=GOLD, lw=2.4, alpha=.95, solid_capstyle="round", zorder=4)
            ax.scatter([xs[-1]], [ys[-1]], s=70, color=GOLD, zorder=5, edgecolors=MEADOW, linewidths=1.5)
        else:
            ax.plot(xs, ys, color="white", lw=.9, alpha=.32, solid_capstyle="round", zorder=2)
            ax.scatter([xs[-1]], [ys[-1]], s=10, color="white", alpha=.9, zorder=3, linewidths=0)

    hut = data["hut"]
    hx, hy = hut["x"], -hut["z"]
    ax.scatter([hx], [hy], s=150, marker="s", color="#4f7fa6", edgecolors="#ece6d8", linewidths=2, zorder=6)
    ax.text(hx + 7, hy + 9, "the hut", fontsize=13, color=INK, family=mono, zorder=7)

    ends = Counter(L["end"] for L in lives)
    for key, c in data["corners"].items():
        n = ends.get(key, 0)
        cx, cy = c["x"], -c["z"]
        # the job flock gets its label underneath; the stray corners get theirs out to the right
        lx, ly, ha = {"job": (cx - 10, cy - 55, "left"), "gigs": (cx + 45, cy + 18, "left")}.get(key, (cx - 12, cy + 22, "left"))
        ax.text(lx, ly, f"{n}", fontsize=40, fontweight=300, color=GOLD if key != g["most_common_end"] else INK,
                ha=ha, va="top", zorder=7)
        ax.text(lx, ly - 30, c["label"], fontsize=15, color=MUTED, ha=ha, va="top", zorder=7)

    ax.text(-222, 150, f"Experiment 01  ·  {len(lives)} lives of Maya  ·  {max(L['weeks'] for L in lives)} weeks  ·  seen from above",
            fontsize=13, color=MUTED, family=mono, va="top")
    ax.set_xlim(-230, 230)
    ax.set_ylim(-150, 160)
    ax.axis("off")
    fig.savefig(path, facecolor=MEADOW)
    plt.close(fig)


def strip_panel(ax, lives, weeks, title, mono):
    import numpy as np
    code = {"j": 0, "g": 1, "b": 2, "s": 3}
    order = {"job": 0, "gigs": 1, "building": 2, "searching": 3}

    def first(L, ch):
        i = L["states"].find(ch)
        return i if i >= 0 else 999

    lives = sorted(lives, key=lambda L: (order[L["end"]], first(L, "j"), -L["states"].count("j")))
    grid = np.full((len(lives), weeks), np.nan)
    for r, L in enumerate(lives):
        for w, ch in enumerate(L["states"][:weeks]):
            grid[r, w] = code.get(ch, 3)
    cmap = ListedColormap([STATE[k][1] for k in "jgbs"])
    cmap.set_bad(PAPER)
    ax.imshow(grid, cmap=cmap, vmin=-.5, vmax=3.5, aspect="auto", interpolation="nearest")
    # hairline gaps between lives
    for r in range(1, len(lives)):
        ax.axhline(r - .5, color=PAPER, lw=.6 if len(lives) > 40 else 1.2)
    for r, L in enumerate(lives):
        if L["stray"]:
            ax.add_patch(Rectangle((weeks - .5 + weeks * .012, r - .4), weeks * .018, .8, color=GOLD, clip_on=False))
    ax.set_title(title, loc="left", fontsize=16, color=INK, pad=12, fontweight=500)
    ax.set_yticks([])
    ticks = [0] + list(range(12, weeks, 13 if weeks <= 52 else 26)) + [weeks - 1]
    ax.set_xticks(ticks, [f"{t + 1}" for t in ticks], family=mono, fontsize=10)
    ax.set_xlabel("week", family=mono, fontsize=10, labelpad=2)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, pad=6)


def weeks(data, mono, path):
    maya = group(data, "exp01")["lives"]
    self_lives = [L for gid in ("exp02a", "exp02b", "exp03") for L in group(data, gid)["lives"]]
    fig = plt.figure(figsize=(16, 9), dpi=110)
    fig.patch.set_facecolor(PAPER)
    a1 = fig.add_axes([.04, .12, .42, .7])
    a2 = fig.add_axes([.53, .12, .42, .7])
    wm, ws = max(L["weeks"] for L in maya), max(L["weeks"] for L in self_lives)
    strip_panel(a1, maya, wm, f"Maya, experiment 01: {len(maya)} lives, {wm} weeks", mono)
    strip_panel(a2, self_lives, ws, f"Self, experiments 02 and 03: {len(self_lives)} lives, {ws} weeks", mono)
    legend(fig, [(STATE[k][1], STATE[k][0]) for k in "jgbs"] + [(GOLD, "a stray")], .04, .936)
    fig.text(.04, .015, "One row per life, one cell per week, sorted by how the life ended. From docs/data/positions.json.",
             fontsize=11, color=MUTED, family=mono)
    fig.savefig(path)
    plt.close(fig)


def endings(data, mono, path):
    rows = [("exp01", "Experiment 01 · Maya"), ("exp02a", "Experiment 02 A · Self"),
            ("exp02b", "Experiment 02 B · Self"), ("exp03", "Experiment 03 · Self, world v3")]
    fig = plt.figure(figsize=(16, 4.6), dpi=110)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([.25, .16, .71, .62])
    ax.set_facecolor(PAPER)
    for i, (gid, label) in enumerate(rows):
        g = group(data, gid)
        n = len(g["lives"])
        c = Counter(L["end"] for L in g["lives"])
        left = 0
        y = len(rows) - 1 - i
        for key in END_ORDER:
            k = c.get(key, 0)
            if not k:
                continue
            w = k / n
            ax.barh(y, w, left=left, height=.62, color=END_COLOR[key], edgecolor=PAPER, linewidth=2)
            dark = key == "job"
            if w > .05:
                ax.text(left + w / 2, y, str(k), ha="center", va="center", fontsize=13,
                        color=PAPER if dark else INK, family=mono, fontweight=500)
            left += w
        ax.text(-.012, y, f"{label}", ha="right", va="center", fontsize=13, color=INK)
        ax.text(-.012, y - .27, f"{n} lives", ha="right", va="top", fontsize=10.5, color=MUTED, family=mono)
        if g.get("tie"):
            ax.text(1.005, y, "tie", va="center", fontsize=11, color=MUTED, family=mono)
    ax.set_xlim(0, 1)
    ax.set_ylim(-.6, len(rows) - .4)
    ax.axis("off")
    legend(fig, [(END_COLOR[k], END_LABEL[k]) for k in END_ORDER[:3]], .25, .895)
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", help="directory with Inter Tight and Geist Mono .ttf files")
    a = ap.parse_args()
    _, mono = fonts(a.fonts)
    data = json.loads((ROOT / "docs" / "data" / "positions.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    flock(data, mono, OUT / "flock.png")
    weeks(data, mono, OUT / "weeks.png")
    endings(data, mono, OUT / "endings.png")
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
