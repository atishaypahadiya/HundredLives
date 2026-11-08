# hundred-lives

I give an LLM agent a made-up background and a goal, put it in a small simulated world, and let it live a year or two, one week at a time. It can write code, apply to openings, message people it knows and launch things. It can't spend real money or reach the internet. Then I run the same life many times and read what it did.

**Project page: https://atishaypahadiya.github.io/hundred-lives/.** Every life is on it as a valley you can scroll through, and each one can be replayed week by week.

Parked in November 2026 after three experiments. Each experiment's plan and results are in `experiments/`.

## What it found

- **Experiment 01 (Maya, 52 weeks):** 77 of 80 lives ended the year in a full-time job, though each group of 20 took between 6 and 14 different paths to get there.
- **Experiment 02 (Self, 104 weeks):** persona lines that read like instructions tended to change what the agent did; trait words didn't.
- **Experiment 03 (Self in world v3):** given the way to ship it had said it lacked, Self deployed a site in all 5 lives, but in most of them a new reason to stall outlived that wall. No life put its savings into the company.

The project page has the details and limits. Its numbers are generated from the logs by `analysis/site_facts.py`; if this list and the page ever disagree, the page is right.

## How it works

```
persona.yaml + world.yaml
        │
  turn loop (host)          one week per turn, a fresh conversation each week,
        │                   8 actions; facts about past weeks are kept by code
        ├── agent container     shell, files, git → its own Gitea
        │                       private network, no route out, purged after the run
        │
        └── referee (LLM)       estimates the odds of an application or launch;
                                keyed dice decide (lives with the same dice seed get
                                the same draw for the same choice);
                                also voices the persona's fictional contacts
        │
  runs/<id>.jsonl           every call, decision, draw and cost
        │
  analysis/site_facts.py → docs/index.html            every number on the site
  analysis/positions.py  → docs/data/positions.json   where each life stands in the valley
  viewer/export.py       → docs/runs/                  the Runs page and one page per life
```

- **Agent:** Python on the Anthropic API. Claude Haiku 5.5 for Maya, Claude Sonnet 5.5 for Self. Ollama with a small local model checks the plumbing for free.
- **Referee:** Claude Haiku 5.5, kept fixed across experiments. It never sees the agent's goal or thinking and never picks an outcome. Dice are sha256 of `[dice_seed, kind, id, n]` (common random numbers), so lives that share a dice seed can be compared choice by choice.
- **Worlds:** YAML files in `world/` with fictional openings (jobs, accelerators, grants), time costs, gigs and prices. World v3 adds a mock web where deployed sites can be visited.

## Limits on the agents

- **No money.** There are no payment credentials anywhere. Personal cash can't be spent (in world v3 it can only be moved into company funds), and company funds only buy world items (a contractor, launch ads).
- **No internet.** Every container network is internal. Each run gets its own network and its own Gitea user, purged when the run ends. `make check` runs 20 isolation probes.
- **Contained processes.** 1 CPU, 1 GB, read-only root, no capabilities, a 60-second limit per shell call.
- **Budgets.** A per-run token budget, plus a spend guard on paid batches.
- **Fictional people.** Contacts are made up. Publishing scrubs home paths, emails and secrets, and lists every contact for a person to confirm.

## The site

The whole site is one valley: each sheep is a life, the hut is the referee, the mountains are the walls of the sandbox, and the flock bunching into one corner is the main finding. `docs/THEME.md` is the design spec, and every page follows it.

- `docs/valley/world.js`: the 3D valley (three.js), shared by every page.
- `analysis/positions.py`: places each published life on the valley floor week by week. Corners are end states (full-time job, gigs and part-time, building their own thing); lives still searching stay in a loose ring around the hut. The sideways wobble comes from a local embedding of each week's digest, projected with a PCA fitted once and saved, so positions don't shift between runs.
- `viewer/runs.html` and `viewer/life.html`: templates for the Runs page and the life pages.

## Layout

```
agents/personas/   persona files (maya.yaml is the reference)
world/             world files: openings, time costs, prices
orchestrator/      turn loop, tools, referee, memory, sandbox, mock web
sandbox/           Gitea + internal network (compose), agent image, PID 1
gateway/           Track B: Self drafting posts on X for a person to approve (tested offline, nothing posted)
viewer/            local viewer, export, and the site's Runs and life templates
analysis/          per-experiment analysis, site_facts.py, positions.py
experiments/       one plan and one results file per experiment
scripts/           publish, share image, prompt hashes, smoke tests
docs/              the site (index.html, THEME.md, valley/, data/, replays/)
runs/              run logs (gitignored)
```

## Run it

Needs macOS with [OrbStack](https://orbstack.dev) (the host reaches Gitea on an internal network, which OrbStack routes and Docker Desktop doesn't), [uv](https://docs.astral.sh/uv/), and `gh` logged in for deploys.

```bash
git clone https://github.com/atishaypahadiya/hundred-lives.git
cd hundred-lives
cp .env.example .env     # add ANTHROPIC_API_KEY, only for Claude runs
make up                  # uv sync, start OrbStack, Gitea and the agent image, then the viewer
```

### Viewer

```bash
make viewer              # http://127.0.0.1:8711, read-only on every runs dir that exists
```

It reads `runs/` and the experiment worktrees' `runs/` (`../hundred-lives-viewer`, `../hundred-lives-exp02b`, `../hundred-lives-exp03`). Run logs are gitignored, so a fresh clone has none.

### A run

A free run on a local model checks the loop, sandbox and logging:

```bash
OLLAMA_CONTEXT_LENGTH=16384 ollama serve &
uv run python -m orchestrator.sandbox up         # skip if `make up` already ran
uv run python -m orchestrator.run --persona agents/personas/maya.yaml --runs 1 --horizon 4
uv run python analysis/summarize.py runs/maya-*.jsonl
```

Real experiments use Claude models and cost money. Launch them from a script file with a budget guard, as `experiments/03-launch.sh` does. It runs from a worktree at the plan's commit (`experiments/03-world-v3.md`, Commands) and reads the main tree's `.env`:

```bash
uv run python -m orchestrator.sandbox check      # 20/20 before launching
bash experiments/03-launch.sh                    # Self x 5 on world v3, 104 weeks, $15 guard
```

### Publish and deploy

```bash
uv run python analysis/site_facts.py             # refill the project page's numbers and quotes from the logs
uv run --group positions python analysis/positions.py   # place every life in the valley (reuses the saved PCA)
scripts/publish_runs.sh                          # rebuild docs/runs/ locally
make deploy                                      # site_facts --check, then publish docs/ (minus valley/index.html) and docs/runs/ to gh-pages
```

`make deploy` refuses while `docs/` has uncommitted changes, so commit on `master` first. Which batches the Runs page shows is set in `viewer/publish.yaml`. `positions.py` needs the `positions` uv group (sentence-transformers), which the simulator doesn't install.

### Checks and stopping

```bash
make check               # the project page matches the logs, and the sandbox's 20 isolation probes pass
make down                # stop Gitea (its data is kept)
```

## Related work

- [Generative Agents](https://arxiv.org/abs/2304.03442) (Park et al., 2023)
- [Generative Agent Simulations of 1,000 People](https://arxiv.org/abs/2411.10109) (Park et al., 2024)
- [Project Sid](https://arxiv.org/abs/2411.00114) (Altera, 2024)
- [AI Village](https://theaidigest.org/village) (AI Digest)
- [Concordia](https://github.com/google-deepmind/concordia) (Google DeepMind)
- [Verbalized Sampling](https://arxiv.org/abs/2510.01171) (2025)
- [The Vendi Score](https://arxiv.org/abs/2210.02410) (Friedman and Dieng, 2023)
- [life2vec](https://www.nature.com/articles/s43588-023-00573-5) (Savcisens et al., 2023)
- [Fragile Families Challenge](https://www.pnas.org/doi/10.1073/pnas.1915006117) (Salganik et al., 2020)

## License

MIT
