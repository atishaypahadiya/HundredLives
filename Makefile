# Everyday commands. Paid model runs are never started from here (see README, "Run it").

# Where run logs live: this tree plus the three experiment worktrees (see CLAUDE.md). Missing ones are skipped.
RUNS_DIRS := $(wildcard runs ../hundred-lives-viewer/runs ../hundred-lives-exp02b/runs ../hundred-lives-exp03/runs)

.PHONY: up viewer deploy check down

# Bring the project back after parking: dependencies, Gitea and the agent image, then the viewer.
up:
	uv sync
	orb start
	uv run python -m orchestrator.sandbox up
	$(MAKE) viewer

# The read-only viewer on every runs dir, at http://127.0.0.1:8711
viewer:
	uv run python -m viewer.server $(addprefix --runs-dir ,$(RUNS_DIRS))

# Check the project page, rebuild the Runs site and publish it on gh-pages (needs `gh` logged in).
deploy:
	uv run python analysis/site_facts.py --check
	scripts/publish_runs.sh --deploy

# The project page matches the logs, and the sandbox's isolation probes pass (needs `make up` or `sandbox up`).
check:
	uv run python analysis/site_facts.py --check
	uv run python -m orchestrator.sandbox check

# Stop Gitea. Its data volume is kept, so `make up` resumes where this left off.
down:
	uv run python -m orchestrator.sandbox down
