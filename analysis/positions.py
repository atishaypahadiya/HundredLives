"""Where each published life stands in the valley, week by week (docs/THEME.md, "What position means").

Writes docs/data/positions.json, which docs/valley/world.js reads to draw the real lives, and checks it.

  uv run --group positions python analysis/positions.py           # write and check, reusing the saved PCA
  uv run --group positions python analysis/positions.py --refit   # fit the PCA again (every wobble moves)

Lives: exactly the ones the Runs site publishes (viewer/publish.yaml through viewer.export.select), grouped by
its experiment groups. Each life keeps its own length (26, 52 or 104 weeks): `weeks` and one point per week
from week 0 (the start, at the hut) to the last.

What a life is doing in a week, from that week's log (first match wins):
  job       holds a full-time job: an opening of type `job` costing the world's `time_costs.full_time`
            (5 actions for Maya and Track A, 4 in the later student worlds), from the world text the run logged
  building  holds an accelerator or a `venture` commitment (go_fulltime_on_venture), or did building work that
            week: shell, repo_created, launch, deploy, a hackathon submit, go_fulltime or invest_personal
  gigs      took a gig, or holds paid work below full time (job, internship, on campus, freelance)
  searching anything else (applications, classes only, waiting)
How a life ended uses only its last week_end: a full-time job; else an accelerator or venture; else part-time
paid work held, or a gig in the last 4 weeks; else searching. For experiment 01 the job ending is checked
life by life against site_facts.job_at_end, the rule behind the project page's "77 of 80".

Corners are points on the valley floor with a zone around them. "Still searching" isn't a corner: those weeks
pull toward a loose ring around the hut. A week pulls the life toward its own seat in that week's corner (a
fixed spot per life and corner, so sheep don't stack); the walk eases toward it at a capped speed; over the last
fifth of the life the path blends into the seat of the corner it ended in, so the last week always lands there.

Wobble: each week's week_end.digest (week and commitment tags removed) is embedded locally with
sentence-transformers all-MiniLM-L6-v2, projected onto two PCA components fitted once over every published week
and saved in docs/data/positions-pca.json, so reruns give the same positions. The projection, scaled and capped
at WOBBLE units, is smoothed over the weeks and added to the path, then shortened wherever it would carry a sheep
into a corner zone its unwobbled path isn't in.

Strays: lives that don't end in their group's most common ending (ties go to the earlier corner in END_ORDER).
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))

from viewer import export, server  # noqa: E402
from analysis.site_facts import job_at_end, life_title  # noqa: E402

OUT = ROOT / "docs" / "data" / "positions.json"
PCA_PATH = ROOT / "docs" / "data" / "positions-pca.json"
WORLD_JS = ROOT / "docs" / "valley" / "world.js"
RUNS_DIRS = [ROOT / "runs", ROOT.parent / "hundred-lives-viewer" / "runs",
             ROOT.parent / "hundred-lives-exp02b" / "runs", ROOT.parent / "hundred-lives-exp03" / "runs"]
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# The valley floor in world.js coordinates (x east, z toward the camera). The hut is world.js's HUT.
HUT = (10.0, -20.0)
CORNERS = {
    "job": {"label": "Full-time job", "x": -150.0, "z": 40.0},
    "building": {"label": "Building their own thing", "x": 150.0, "z": -130.0},
    "gigs": {"label": "Gigs and part-time", "x": 105.0, "z": 55.0},
}
ZONE = 60.0         # a corner's zone radius
SEAT = 34.0         # a life's seat lies within this distance of the corner point
RING = (18.0, 40.0)  # "still searching": inner and outer radius around the hut
START = 10.0        # lives start within this distance in front of the hut
WOBBLE = 16.0       # the most the digest wobble moves a sheep
STEP = 14.0         # the most a sheep walks in a week
EASE = 0.3          # share of the way to this week's target walked each week
END_BLEND = 0.8     # from this fraction of the life on, the path blends into its ending seat
GIG_WINDOW = 4      # a gig in the last this-many weeks counts as ending in gigs
END_ORDER = ["job", "gigs", "building", "searching"]
LETTER = {"job": "j", "building": "b", "gigs": "g", "searching": "s"}
PAID_WORK = server.PAID_WORK
BUILD_EVENTS = {"shell", "repo_created", "launch", "deploy", "go_fulltime", "invest_personal"}
WALL_OK = 0.25      # world.js scatters grass only where wallMask <= .25; every point must be on that floor


def u01(*key) -> float:
    """A fixed number in [0, 1) from a key, so seats and starts never change between runs."""
    return int(hashlib.sha256(json.dumps(key).encode()).hexdigest()[:12], 16) / 16 ** 12


def seat(run_id: str, where: str) -> np.ndarray:
    a = 2 * math.pi * u01(run_id, where, "angle")
    if where == "searching":
        r, (cx, cz) = RING[0] + (RING[1] - RING[0]) * u01(run_id, where, "r"), HUT
    else:
        r, cx, cz = SEAT * math.sqrt(u01(run_id, where, "r")), CORNERS[where]["x"], CORNERS[where]["z"]
    return np.array([cx + r * math.cos(a), cz + r * math.sin(a)])


def sm(a, b, x):
    x = min(1.0, max(0.0, (x - a) / (b - a)))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- reading a life

def read_life(c: dict) -> dict:
    path = Path(c["dir"]) / f"{c['run_id']}.jsonl"
    recs = [json.loads(line) for line in path.open() if line.strip()]
    start = next(r for r in recs if r["type"] == "run_start")
    world = yaml.safe_load(start["sources"]["world_text"])
    types = {o["id"]: o.get("type") for o in world.get("openings") or []}
    full = world["time_costs"]["full_time"]
    by_week = {}
    for r in recs:
        if r["type"] == "tool_call" and r.get("tool") == "submit":
            by_week.setdefault(r["week"], Counter())["submit"] += 1
        elif r["type"] in BUILD_EVENTS or r["type"] == "gig":
            by_week.setdefault(r["week"], Counter())[r["type"]] += 1
    weeks = []
    for r in recs:
        if r["type"] != "week_end":
            continue
        held = [c for c in r["state"].get("commitments") or [] if c.get("kind") != "academics"]
        kinds = [(types.get(h.get("opening_id")), h.get("kind"), h.get("time_cost") or 0) for h in held]
        ev = by_week.get(r["week"], Counter())
        weeks.append({
            "week": r["week"],
            "ft_job": any(t == "job" and cost >= full for t, _, cost in kinds),
            "own": any(t == "accelerator" or k == "venture" for t, k, _ in kinds),
            "part": any(t in PAID_WORK and cost < full for t, _, cost in kinds),
            "gig": ev["gig"] > 0,
            "build": sum(n for k, n in ev.items() if k != "gig") > 0,
            "digest": r.get("digest") or "",
        })
    return {"run_id": c["run_id"], "group": c["group"], "batch": c["batch"], "path": path,
            "persona": (start.get("persona") or {}).get("name") or "", "weeks": weeks}


def week_state(w: dict) -> str:
    if w["ft_job"]:
        return "job"
    if w["own"] or w["build"]:
        return "building"
    if w["gig"] or w["part"]:
        return "gigs"
    return "searching"


def end_state(L: dict) -> str:
    last = L["weeks"][-1]
    if last["ft_job"]:
        return "job"
    if last["own"]:
        return "building"
    if last["part"] or any(w["gig"] for w in L["weeks"][-GIG_WINDOW:]):
        return "gigs"
    return "searching"


# ---------------------------------------------------------------- wobble: digest embeddings and a saved PCA

def clean(digest: str) -> str:
    return re.sub(r"\[[wc]\d+\]\s*", "", digest).strip()


def embed(texts: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL, device="cpu")
    return np.asarray(model.encode(texts, batch_size=128, normalize_embeddings=True, show_progress_bar=False), dtype=np.float64)


def fit_pca(X: np.ndarray) -> dict:
    import sentence_transformers
    mean = X.mean(axis=0)
    _, _, vt = np.linalg.svd(X - mean, full_matrices=False)
    comps = vt[:2]
    comps *= np.sign(comps[np.arange(2), np.abs(comps).argmax(axis=1)])[:, None]  # fixed signs
    sd = ((X - mean) @ comps.T).std(axis=0)
    return {"model": MODEL, "sentence_transformers": sentence_transformers.__version__, "fitted_on_weeks": len(X),
            "mean": mean.round(8).tolist(), "components": comps.round(8).tolist(), "sd": sd.round(8).tolist()}


def wobbles(X: np.ndarray, pca: dict) -> np.ndarray:
    """Each week's 2D wobble in world units: the projection over 2 sd, its length capped at 1, times WOBBLE."""
    z = (X - np.array(pca["mean"])) @ np.array(pca["components"]).T / (2 * np.array(pca["sd"]))
    return z / np.maximum(np.linalg.norm(z, axis=1, keepdims=True), 1.0) * WOBBLE


# ---------------------------------------------------------------- paths

def zones_at(p: np.ndarray) -> set:
    return {k for k, c in CORNERS.items() if math.hypot(p[0] - c["x"], p[1] - c["z"]) < ZONE}


def clamp(base: np.ndarray, off: np.ndarray) -> np.ndarray:
    """The longest part of `off` that doesn't carry `base` into a corner zone it isn't already in."""
    allowed = zones_at(base)
    if zones_at(base + off) <= allowed:
        return off
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if zones_at(base + mid * off) <= allowed else (lo, mid)
    return lo * off


def path(L: dict, wob: np.ndarray) -> list:
    rid, n = L["run_id"], len(L["weeks"])
    a = math.pi * (0.25 + 0.5 * u01(rid, "start", "angle"))  # in front of the hut, toward the camera
    p = np.array([HUT[0], HUT[1] + 6]) + START * u01(rid, "start", "r") * np.array([math.cos(a), math.sin(a)])
    end = seat(rid, L["end"])
    base = [p.copy()]
    for i, w in enumerate(L["weeks"]):
        step = (seat(rid, L["states"][i]) - p) * EASE
        d = np.linalg.norm(step)
        p = p + (step if d <= STEP else step * STEP / d)
        f = (i + 1) / n
        base.append(p + (end - p) * sm(END_BLEND, 1.0, f))
    # the wobble, smoothed so a sheep sways instead of jumping; none at week 0
    off, sm_off, pts = np.zeros(2), [np.zeros(2)], []
    for i in range(n):
        off = off + (wob[i] - off) * 0.5
        sm_off.append(off.copy())
    for b, o in zip(base, sm_off):
        pts.append(b + clamp(b, o))
    return [[round(float(x), 1), round(float(z), 1)] for x, z in pts]


# ---------------------------------------------------------------- checks

def wall_masks(points: list) -> list:
    """world.js's own wallMask at each [x, z], evaluated in Node."""
    js = ("const vm=require('vm'),fs=require('fs');const ctx={THREE:{Color:function(){}},window:{},Math};"
          "vm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);"
          "const t=ctx.window.createValley.terrain;let s='';process.stdin.on('data',d=>s+=d);"
          "process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(s).map(p=>t.wallMask(p[0],p[1])))));")
    r = subprocess.run(["node", "-e", js, str(WORLD_JS)], input=json.dumps(points), capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def checks(lives: list, groups: list) -> bool:
    ok = True
    print("End states per group (counts):")
    for g in groups:
        c = Counter(L["end"] for L in g["lives"])
        tie = " (tie, broken by corner order)" if g["mode_tie"] else ""
        print(f"  {g['id']:9} {len(g['lives']):3} lives  " + ", ".join(f"{k} {c[k]}" for k in END_ORDER if c[k])
              + f"  | most common: {g['mode']}{tie}")
    e01 = [L for L in lives if L["group"] == "exp01"]
    ours = sum(L["end"] == "job" for L in e01)
    theirs = sum(job_at_end(L["path"]) for L in e01)
    differ = [L["run_id"] for L in e01 if (L["end"] == "job") != job_at_end(L["path"])]
    print(f"\nExperiment 01 job corner: {ours} of {len(e01)}; site_facts.job_at_end: {theirs}; lives that differ: {differ or 'none'}")
    ok &= not differ
    print("\nStrays (not ending in their group's most common corner):")
    for g in groups:
        for L in g["lives"]:
            if L["stray"]:
                print(f"  {g['id']:9} {L['end']:9} {L['title']:32} {L['run_id']}")
    probes = [[c["x"], c["z"]] for c in CORNERS.values()]
    probes += [[c["x"] + ZONE * math.cos(t), c["z"] + ZONE * math.sin(t)] for c in CORNERS.values()
               for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    probes += [[HUT[0] + RING[1] * math.cos(t), HUT[1] + RING[1] * math.sin(t)] for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    pts = [p for L in lives for p in L["points"]]
    m = wall_masks(probes + pts)
    centres, rest, life_pts = m[:3], m[3:len(probes)], m[len(probes):]
    print("\nWall mask (world.js; 0 = valley floor, 1 = mountains; must be <= %.2f):" % WALL_OK)
    for (k, c), v in zip(CORNERS.items(), centres):
        print(f"  {k:9} corner point ({c['x']:.0f}, {c['z']:.0f}): {v:.3f}")
    print(f"  max on the corner zone edges and the hut ring ({len(rest)} points): {max(rest):.3f}")
    print(f"  max over every life's every week ({len(life_pts)} points): {max(life_pts):.3f}")
    ok &= max(m) <= WALL_OK
    ends_in_zone = all(L["end"] == "searching" or L["end"] in zones_at(np.array(L["points"][-1])) for L in lives)
    print(f"\nEvery life's last week inside its ending corner's zone: {ends_in_zone}")
    ok &= ends_in_zone
    return ok


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refit", action="store_true", help="fit the PCA again instead of reusing docs/data/positions-pca.json")
    a = ap.parse_args(argv)

    server.runs_dirs = [d.resolve() for d in RUNS_DIRS if d.is_dir()]
    publish = yaml.safe_load(export.PUBLISH.read_text())
    chosen, _ = export.select(publish)
    lives = [read_life(c) for c in chosen]

    X = embed([clean(w["digest"]) for L in lives for w in L["weeks"]])
    if a.refit or not PCA_PATH.exists():
        pca = fit_pca(X)
        PCA_PATH.parent.mkdir(parents=True, exist_ok=True)
        PCA_PATH.write_text(json.dumps(pca) + "\n")
        print(f"fitted the PCA on {len(X)} weeks: {PCA_PATH.relative_to(ROOT)}")
    else:
        pca = json.loads(PCA_PATH.read_text())
        if pca["model"] != MODEL or len(pca["mean"]) != X.shape[1]:
            raise SystemExit(f"{PCA_PATH.relative_to(ROOT)} was fitted with another model; rerun with --refit")
        print(f"reused the PCA in {PCA_PATH.relative_to(ROOT)} (fitted on {pca['fitted_on_weeks']} weeks)")
    W = wobbles(X, pca)

    i = 0
    for L in lives:
        n = len(L["weeks"])
        L["states"] = [week_state(w) for w in L["weeks"]]
        L["end"] = end_state(L)
        L["title"] = life_title(L["run_id"], L["persona"])
        L["points"] = path(L, W[i:i + n])
        i += n

    groups = []
    for g in publish["groups"]:
        gl = [L for L in lives if L["group"] == g["id"]]
        if not gl:
            continue
        c = Counter(L["end"] for L in gl)
        top = max(c.values())
        mode = next(k for k in END_ORDER if c[k] == top)
        for L in gl:
            L["stray"] = L["end"] != mode
        groups.append({"id": g["id"], "title": g["title"], "mode": mode,
                       "mode_tie": sum(v == top for v in c.values()) > 1, "lives": gl})

    out = {
        "about": "Where each published life stands in the valley, week by week. Built by analysis/positions.py; "
                 "the rules are in its docstring. points[i] is [x, z] at week i (0 = the start, at the hut).",
        "hut": {"x": HUT[0], "z": HUT[1], "ring": list(RING), "label": "Still searching"},
        "corners": {k: {**c, "zone": ZONE} for k, c in CORNERS.items()},
        "letters": {v: k for k, v in LETTER.items()},
        "wobble": {"model": MODEL, "pca": PCA_PATH.name, "max": WOBBLE},
        "groups": [{"id": g["id"], "title": g["title"], "most_common_end": g["mode"], "tie": g["mode_tie"],
                    "lives": [{"run_id": L["run_id"], "title": L["title"], "batch": L["batch"], "weeks": len(L["weeks"]),
                               "end": L["end"], "stray": L["stray"], "states": "".join(LETTER[s] for s in L["states"]),
                               "points": L["points"]} for L in g["lives"]]} for g in groups],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(lives)} lives in {len(groups)} groups, {OUT.stat().st_size // 1024} KB\n")
    return 0 if checks(lives, groups) else 1


if __name__ == "__main__":
    sys.exit(main())
