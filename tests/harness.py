"""A run with no model and no sandbox: a scripted agent, a canned referee, the log read back.

The agent plays one list of tool-call batches per week (one batch per turn); when a week's
batches run out it calls wait. The referee answers every application with the same estimate,
so a test sets the odds and the dice decide, as in a real run.
"""

import copy
import json
from pathlib import Path

import yaml

import orchestrator.run as R
from orchestrator.backends import Reply, ToolCall, Usage
from orchestrator.world import load_world

ROOT = Path(__file__).resolve().parent.parent


def call(name, **kw):
    return (name, kw)


WAIT = [call("wait", idea="none", note="done")]


class Agent:
    name, model, deterministic, default_max_tokens = "scripted", "agent", False, 1000

    def __init__(self, script: dict[int, list[list[tuple]]]):
        self.script, self.week, self.prompts, self.results = script, 0, [], []

    def cost(self, reply):
        return 0.0

    def conversation(self, system, tools):
        self.week += 1
        return Convo(self, list(self.script.get(self.week, [])))


class Convo:
    def __init__(self, agent: Agent, batches: list):
        self.agent, self.batches, self.n = agent, batches, 0

    def add_user(self, text):
        self.agent.prompts.append((self.agent.week, text))

    def add_tool_results(self, results, note=None):
        for c, out, err in results:
            self.agent.results.append((self.agent.week, c.name, out, err))

    def size_chars(self):
        return 1000

    def send(self, max_tokens):
        batch = self.batches.pop(0) if self.batches else WAIT
        self.n += 1
        return Reply("", [ToolCall(f"t{self.agent.week}-{self.n}", n, kw) for n, kw in batch],
                     Usage(), "tool_use", 0.0)


class Referee:
    """Answers applications with `chance` and `weeks`; contacts never offer; reflections are fixed."""
    name, model, deterministic, default_max_tokens = "canned", "world", False, 1000

    def __init__(self, chance: float = 1.0, weeks: int = 0):
        self.chance, self.weeks, self.calls = chance, weeks, []

    def cost(self, reply):
        return 0.0

    def complete(self, system, user, max_tokens, schema=None, **kw):
        self.calls.append((system, user))
        props = (schema or {}).get("properties", {})
        if "message_if_success" in props:
            out = {"estimated_chance": self.chance, "decision_in_weeks": self.weeks,
                   "message_if_success": "Welcome aboard.", "message_if_failure": "No.", "rationale": "canned"}
        elif "offer_kind" in props:
            out = {"reply": "Good to hear from you.", "offer_kind": "none", "offer_opening_id": "", "offer_amount": 0}
        elif "comments_if_traction" in props or "replies_if_breakout" in props or "feedback_if_placed" in props:
            out = {"estimated_chance": 0.0, "rationale": "canned"}
        else:
            return Reply("Keep going.", [], Usage(), "end_turn", 0.0)
        return Reply(json.dumps(out), [], Usage(), "end_turn", 0.0)


def persona(name: str = "maya.yaml", **starting_state) -> dict:
    p = yaml.safe_load((ROOT / "agents/personas" / name).read_text())
    if starting_state:
        p = copy.deepcopy(p)
        p.setdefault("starting_state", {}).update(starting_state)
    return p


def play(tmp_path: Path, script: dict, weeks: int, *, persona_dict: dict | None = None,
         world: str = "openings.yaml", referee: Referee | None = None, seed: int = 0):
    """Run `weeks` weeks; returns (run, log records, agent, referee)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    R.RUNS_DIR = tmp_path
    p = persona_dict or persona()
    world_path = ROOT / "world" / world
    agent, ref = Agent(script), referee or Referee()
    run = R.Run("test-001", p, ROOT / "agents/personas/maya.yaml", load_world(world_path), world_path,
                agent, ref, ref, 10**9, weeks, seed=seed, sandbox=False)
    result = run.execute()
    assert result["reason"] == "horizon", result
    log = [json.loads(line) for line in (tmp_path / "test-001.jsonl").read_text().splitlines()]
    return run, log, agent, ref


def events(log: list[dict], kind: str) -> list[dict]:
    return [r for r in log if r["type"] == kind]
