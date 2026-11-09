"""What each side of the simulation may see. These are the experiment's design, not style: a
leak here changes what the results mean."""

import pytest
import yaml

from orchestrator import referee as ref
from orchestrator.run import HIDDEN_FROM_AGENT
from tests.harness import ROOT, play, persona

VARIANTS = ("self-nosolo.yaml", "self-socialgoal.yaml", "self-goalonly.yaml")


def person(p):
    return ref._person(p, 5, [], [], 0.0)


@pytest.mark.parametrize("name", ["maya.yaml", "self.yaml", *VARIANTS])
def test_referee_never_sees_goal_traits_or_interests(name):
    p = persona(name)
    shown = yaml.safe_load(person(p).split("Money raised")[0].removeprefix("Person:\n"))
    assert set(shown) <= set(ref.PUBLIC_FIELDS) | {"network"}
    text = person(p)
    for private in ("goal", "traits", "interests", "childhood"):
        if isinstance(p.get(private), str):
            assert p[private] not in text, private
        for item in p.get(private) or [] if isinstance(p.get(private), list) else []:
            assert str(item) not in text, (private, item)


@pytest.mark.parametrize("name", VARIANTS)
def test_sensitivity_variants_look_like_the_base_persona_to_the_referee(name):
    # A changed trait may reach outcomes only through the agent's choices.
    assert person(persona(name)) == person(persona("self.yaml"))


def test_referee_view_is_hidden_from_the_agent(tmp_path):
    # goal-only strips the agent's own background; the referee still sees the base persona's.
    p = persona("self-goalonly.yaml")
    run, _, agent, _ = play(tmp_path, {}, 1, persona_dict=p, world="student.yaml")
    seen = run.system + "\n".join(text for _, text in agent.prompts)
    assert "referee_view" in HIDDEN_FROM_AGENT and "referee_view" not in seen
    assert p["referee_view"]["family"] not in seen and p["referee_view"]["network"] not in seen
    assert p["referee_view"]["family"] in person(p)


@pytest.mark.parametrize("name,world", [("maya.yaml", "openings.yaml"), ("self.yaml", "student.yaml")])
def test_agent_never_sees_horizon_or_rates(name, world, tmp_path):
    run, log, agent, _ = play(tmp_path, {}, 2, persona_dict=persona(name), world=world)
    p = persona(name)
    seen = run.system + "\n".join(text for _, text in agent.prompts)
    assert "horizon" not in seen and f"{p['horizon']} weeks" not in seen
    assert "base_rate" not in seen and "reply_rate" not in seen
    for c in p["contacts"]:
        assert "reply_rate" not in c["voice"]  # voices are prose for the contact model only
        assert c["voice"] not in seen


def test_the_referee_prompt_carries_no_rates_other_than_the_base_rate(tmp_path):
    from tests.harness import Referee, call
    r = Referee(chance=0.0)
    play(tmp_path, {1: [[call("apply", opening_id="job-01", details="I ship Python.")]]}, 1, referee=r)
    system, user = next((s, u) for s, u in r.calls if "Opening:" in u)
    assert "base rate" in (system + user).lower()
    assert "reply_rate" not in user
    p = persona("maya.yaml")
    assert p["goal"] not in user
