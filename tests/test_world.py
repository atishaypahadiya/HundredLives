"""World files: every shipped world and persona loads, the loader refuses broken ones, and the
time and work-authorization rules do what the world files' comments say."""

import copy

import pytest
import yaml

from orchestrator import world as W
from tests.harness import ROOT, persona

WORLDS = sorted((ROOT / "world").glob("*.yaml"))
PERSONAS = sorted((ROOT / "agents/personas").glob("*.yaml"))
STUDENT = W.load_world(ROOT / "world/student.yaml")


@pytest.mark.parametrize("path", WORLDS, ids=lambda p: p.name)
def test_every_world_loads_and_is_marked_illustrative(path):
    w = W.load_world(path)
    assert w["illustrative"] is True  # no number in these files is sourced yet
    assert len({o["id"] for o in w["openings"]}) == len(w["openings"])


@pytest.mark.parametrize("path", PERSONAS, ids=lambda p: p.name)
def test_every_persona_fits_its_world(path):
    p = yaml.safe_load(path.read_text())
    world = W.load_world(ROOT / "world" / ("openings.yaml" if path.name == "maya.yaml" else "student.yaml"))
    W.check_contacts(p, world, path)


def test_sensitivity_variants_share_the_base_contacts():
    base = persona("self.yaml")["contacts"]
    for name in ("self-nosolo.yaml", "self-socialgoal.yaml", "self-goalonly.yaml"):
        assert persona(name)["contacts"] == base, name


def test_hidden_streak_world_differs_only_in_the_streak():
    a = yaml.safe_load((ROOT / "world/student.yaml").read_text())
    b = yaml.safe_load((ROOT / "world/student-hiddenstreak.yaml").read_text())
    assert b["training"].pop("show_streak") is False
    assert "streak" in a["training"]["description"] and "streak" not in b["training"]["description"]
    a["training"].pop("description"), b["training"].pop("description")
    assert a == b


def broken(edit):
    w = yaml.safe_load((ROOT / "world/openings.yaml").read_text())
    edit(w)
    return yaml.safe_dump(w)


@pytest.mark.parametrize("edit,says", [
    (lambda w: w.pop("illustrative"), "illustrative"),
    (lambda w: w["openings"].append(copy.deepcopy(w["openings"][0])), "duplicate opening id"),
    (lambda w: w["openings"][0].update(base_rate=0), "base_rate must be in (0, 1]"),
    (lambda w: w["openings"][0].update(reply_rate=1.5), "reply_rate must be in (0, 1]"),
    (lambda w: w["openings"][0].update(type="lottery"), "unknown type"),
    (lambda w: w["openings"][0].pop("schedule"), "need a schedule"),
    (lambda w: w["gig"].pop("pay"), "gig.pay"),
    (lambda w: w["time_costs"].pop("part_time"), "time_costs"),
    (lambda w: w.update(openings=[]), "no openings"),
])
def test_loader_refuses_broken_worlds(edit, says):
    with pytest.raises(ValueError, match=None) as e:
        W.load_world(ROOT / "world/openings.yaml", text=broken(edit))
    assert says in str(e.value)


def test_contact_offers_must_point_at_real_openings():
    p = persona("maya.yaml")
    p["contacts"][1]["offers"] = [{"kind": "referral", "openings": ["job-999"]}]
    with pytest.raises(ValueError, match="unknown openings"):
        W.check_contacts(p, W.load_world(ROOT / "world/openings.yaml"), "maya.yaml")


# --- time ------------------------------------------------------------------------------------

@pytest.mark.parametrize("hours,actions", [(5, 1), (10, 1), (15, 1), (16, 2), (20, 2), (26, 2), (27, 3), (40, 4)])
def test_hours_to_actions_rounds_half_up(hours, actions):
    # 10.5 hours an action: 15.75 is the half-way point between 1 and 2.
    assert W.time_cost({"schedule": "part_time", "hours_weekly": hours}, STUDENT["time_costs"]) == actions


def test_schedules_and_non_commitments():
    costs = STUDENT["time_costs"]
    assert W.time_cost({"schedule": "full_time"}, costs) == 4
    assert W.time_cost({"schedule": "part_time"}, costs) == 2
    assert W.time_cost({"type": "grant"}, costs) == 0


# --- work authorization (illustrative F-1 rules) ---------------------------------------------

def opening(kind):
    return {"auth": kind}


def test_auth_rules():
    assert W.auth_problem(STUDENT, opening("none"), 5, 4) is None
    assert W.auth_problem(STUDENT, opening("on_campus"), 5, 1) is None
    assert "at most 2 actions" in W.auth_problem(STUDENT, opening("on_campus"), 5, 3)
    assert "at most 2 actions" in W.auth_problem(STUDENT, opening("internship"), 5, 1, others=2)  # the cap is on the total
    assert W.auth_problem(STUDENT, opening("internship"), 18, 4) is None  # a break: full-time is fine
    assert "after you graduate" in W.auth_problem(STUDENT, opening("off_campus"), 5, 4)
    assert W.auth_problem(STUDENT, opening("off_campus"), 89, 4) is None
    assert "only allowed while you're enrolled" in W.auth_problem(STUDENT, opening("on_campus"), 89, 1)
    assert W.auth_problem(W.load_world(ROOT / "world/openings.yaml"), opening("off_campus"), 5, 4) is None


def test_terms_and_listing():
    assert W.semester(STUDENT, 1)["name"] == "Fall semester (year 1)"
    assert W.semester(STUDENT, 18) is None
    assert W.term(STUDENT, 18) == "Fall semester (year 1)"  # a break counts with the semester before
    assert W.term(STUDENT, 21) == "Spring semester (year 1)"
    assert W.enrolled(STUDENT, 88) and not W.enrolled(STUDENT, 89)
    assert W.listed({"listed_weeks": [3, 5]}, 4) and not W.listed({"listed_weeks": [3, 5]}, 6)
    assert W.listed({}, 999)


def test_shuffle_is_a_seeded_permutation():
    openings = W.load_world(ROOT / "world/openings.yaml")["openings"]
    a, b, c = W.shuffled(openings, 1), W.shuffled(openings, 1), W.shuffled(openings, 2)
    assert [o["id"] for o in a] == [o["id"] for o in b] != [o["id"] for o in c]
    assert sorted(o["id"] for o in a) == sorted(o["id"] for o in openings)


@pytest.mark.parametrize("path", WORLDS, ids=lambda p: p.name)
def test_catalog_never_shows_rates(path):
    w = W.load_world(path)
    text = W.catalog(w["openings"], w["time_costs"])
    assert "base_rate" not in text and "reply_rate" not in text
    for o in w["openings"]:
        assert f"- {o['id']} [{o['type']}]" in text
