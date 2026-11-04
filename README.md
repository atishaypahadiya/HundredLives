# hundred-lives

I give an LLM agent a made-up background and a goal, for example "grew up in the Bay Area, wants to run a large company," and let it act inside a sandbox. It can write code, browse a mock web, and talk to other agents. It can't spend money. Then I run the same setup many times and look at what it did.

Project page: https://atishaypahadiya.github.io/hundred-lives/

Parked in November 2026 after three experiments. Results are on the project page; each experiment's plan and results are in `experiments/`.

## Questions

1. If I run one persona 100 times, how many meaningfully different paths come out?
2. If I change one detail, like hometown or degree, does what the agent does change?
3. If outcomes come from real data instead of the model's imagination, do the paths change?

## Setup

```
agent A    agent B    agent C        one container each
   │          │          │
   └──── shared world ───┘           chat, files, mock web
         │          │
   egress proxy   trace log
         │
   internet (off by default)
```

- Agent loop: Python on the Anthropic API. Ollama for cheap test runs.
- Isolation: one container per agent (Apple `container` or OrbStack).
- World: Postgres, Redis, and self-hosted WebArena sites.
- Logs: one JSONL file per run, every tool call.

## Limits on the agents

- No payment credentials exist in the sandbox, and the proxy blocks payment and crypto endpoints.
- The default world is self-hosted. Real internet access has to be turned on and goes through an allowlist.
- No real phone numbers or email accounts.
- Each agent has a token budget, and the API account has a spend limit.

## Layout

```
agents/personas/   persona and goal files (YAML)
orchestrator/      agent loop, tools, budgets
sandbox/           container and proxy config
world/             shared state and mock services
runs/              run logs (not committed)
analysis/          notebooks
docs/              project page
```

## Run it

Needs macOS with [OrbStack](https://orbstack.dev) (or Docker), [uv](https://docs.astral.sh/uv/), and `gh` logged in for deploys.

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

Real experiments use Claude models and cost money. Launch them from a script file with a budget guard, as `experiments/03-launch.sh` does:

```bash
uv run python -m orchestrator.sandbox check      # 20/20 before launching
bash experiments/03-launch.sh                    # Self x 5 on world v3, 104 weeks, $15 guard
```

### Publish and deploy

```bash
uv run python analysis/site_facts.py             # refill the project page's numbers and quotes from the logs
scripts/publish_runs.sh                          # rebuild docs/runs/ locally
make deploy                                      # site_facts --check, then publish docs/ and docs/runs/ to gh-pages
```

`make deploy` refuses while `docs/` has uncommitted changes, so commit on master first. Which batches the Runs page shows is set in `viewer/publish.yaml`.

### Checks and stopping

```bash
make check               # the project page matches the logs, and the sandbox's 20 isolation probes pass
make down                # stop Gitea (its data is kept)
```

## Plan

- [ ] One agent, one persona, local model, logs working
- [ ] Three agents in containers with the shared world and proxy
- [ ] 100 runs per persona, then change one detail at a time
- [ ] Replace imagined outcomes with real base rates (career and funding data)
- [ ] Start agents from real 2016 situations and compare against what actually happened by 2026

## Related work

- Generative Agents (Park et al., 2023)
- Generative Agent Simulations of 1,000 People (Park et al., 2024)
- AI Village (AI Digest)
- Project Sid (Altera, 2024)
- Concordia (Google DeepMind)
- Fragile Families Challenge (Salganik et al., 2020)

## License

MIT
