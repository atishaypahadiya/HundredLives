"""The week loop, end to end, with a scripted agent and no model: money, time, the broke rule,
invalid calls, held offers, and that outcomes depend on choices only through keyed dice."""

import pytest

from orchestrator import referee as ref
from tests.harness import Referee, call, events, persona, play

WAIT = call("wait", idea="x")


def ends(log):
    return {r["week"]: r for r in events(log, "week_end")}


def test_a_quiet_week_costs_the_weekly_expenses(tmp_path):
    run, log, *_ = play(tmp_path, {}, 3)
    assert [r["state"]["cash"] for r in events(log, "week_end")] == [11_000, 10_000, 9_000]  # 12 weeks of savings
    assert all(r["reason"] == "wait" and r["used"] == 0 for r in events(log, "week_end"))


def test_gig_pays_the_same_week_and_uses_five_actions(tmp_path):
    run, log, *_ = play(tmp_path, {1: [[call("gig")], [call("gig")]]}, 1)
    gig, end = events(log, "gig"), ends(log)[1]
    assert len(gig) == 1 and gig[0]["pay"] == 1200 and not gig[0]["forced"]
    assert end["used"] == 5 and end["state"]["cash"] == 12_000 + 1200 - 1000
    assert "gig needs 5 actions and you have 3 left" in events(log, "tool_error")[0]["error"]


def test_one_gig_a_week(tmp_path):
    # In the student world a gig is 2 actions, so a second one would fit; it's refused anyway.
    run, log, *_ = play(tmp_path, {1: [[call("gig")], [call("gig")]]}, 1, persona_dict=persona("self.yaml"),
                        world="student.yaml")
    assert len(events(log, "gig")) == 1
    assert "already took a gig" in events(log, "tool_error")[0]["error"]


def test_invalid_calls_use_no_actions_and_end_the_week_at_three(tmp_path):
    script = {1: [[call("apply"), call("files", action="delete"), call("bogus"), call("gig")]]}
    run, log, agent, _ = play(tmp_path, script, 2)
    end = ends(log)[1]
    assert (end["reason"], end["used"], end["invalid"], end["valid"]) == ("invalid_calls", 0, 3, 0)
    assert not events(log, "gig")  # the call after the third invalid one never ran
    carried = events(log, "week_start")[1]["carried_errors"]
    assert any("gig was not done: the week had already ended" in e for e in carried)


def test_out_of_actions_gives_one_closing_turn(tmp_path):
    writes = [call("files", action="write", path=f"n{i}.md", content="x") for i in range(8)]
    run, log, *_ = play(tmp_path, {1: [writes, [WAIT]]}, 1)
    end = ends(log)[1]
    assert events(log, "closing_turn") and end["reason"] == "wait" and end["closing_turn"]
    assert end["used"] == 8


def test_broke_week_refuses_wait_and_forces_a_gig(tmp_path):
    p = persona(savings_weeks=0)
    run, log, *_ = play(tmp_path, {1: [[WAIT], [WAIT], [WAIT]]}, 1, persona_dict=p)
    assert events(log, "broke") and ends(log)[1]["reason"] == "invalid_calls"
    assert all("can't cover this week's expenses" in r["error"] for r in events(log, "tool_error"))
    assert events(log, "gig")[0]["forced"] is True
    assert ends(log)[1]["state"]["cash"] == 200  # 0 + 1,200 gig - 1,000 expenses


def test_applying_for_a_job_counts_as_acting_on_a_broke_week(tmp_path):
    p = persona(savings_weeks=0)
    run, log, *_ = play(tmp_path, {1: [[call("apply", opening_id="job-01", details="hi"), WAIT]]}, 1,
                        persona_dict=p, referee=Referee(chance=0.0, weeks=4))
    assert ends(log)[1]["reason"] == "wait" and not events(log, "gig")
    assert ends(log)[1]["shortfall"] == 1000 and ends(log)[1]["state"]["cash"] == 0  # cash is floored at $0


def test_an_accepted_job_pays_and_takes_its_time(tmp_path):
    run, log, *_ = play(tmp_path, {1: [[call("apply", opening_id="job-01", details="hi")]]}, 3,
                        referee=Referee(chance=1.0, weeks=0))
    assert events(log, "commitment_started")[0]["commitment"]["time_cost"] == 5
    assert [r["actions"] for r in events(log, "week_start")] == [8, 3, 3]
    assert [r["state"]["cash"] for r in events(log, "week_end")] == [13_100, 14_200, 15_300]  # +2,100 - 1,000


def test_decision_is_revealed_after_its_delay(tmp_path):
    run, log, *_ = play(tmp_path, {1: [[call("apply", opening_id="job-01", details="hi")]]}, 4,
                        referee=Referee(chance=1.0, weeks=2))
    assert events(log, "referee_decision")[0]["week"] == 1
    assert events(log, "outcome_applied")[0]["week"] == 3


def test_an_offer_that_does_not_fit_is_held_then_lapses(tmp_path):
    both = [call("apply", opening_id="job-01", details="a"), call("apply", opening_id="job-02", details="b")]
    run, log, *_ = play(tmp_path, {1: [both]}, 4)
    held, lapsed = events(log, "offer_held"), events(log, "offer_lapsed")
    assert held[0]["opening_id"] == "job-02" and held[0]["expires_week"] == 3
    assert lapsed[0]["opening_id"] == "job-02" and lapsed[0]["week"] == 4
    assert len(events(log, "commitment_started")) == 1


def test_cannot_reapply_within_26_weeks(tmp_path):
    app = call("apply", opening_id="job-01", details="hi")
    run, log, *_ = play(tmp_path, {1: [[app]], 2: [[app]]}, 2, referee=Referee(chance=0.0, weeks=8))
    assert len(events(log, "referee_decision")) == 1
    assert "job-01" in events(log, "week_start")[1]["openings_hidden_ids"]


def test_student_classes_take_three_actions_and_cannot_be_dropped(tmp_path):
    script = {1: [[call("leave", commitment_id="c1")], [call("apply", opening_id="fr-01", details="x")]]}
    run, log, *_ = play(tmp_path, script, 1, persona_dict=persona("self.yaml"), world="student.yaml")
    assert events(log, "week_start")[0]["actions"] == 5
    errors = [r["error"] for r in events(log, "tool_error")]
    assert "can't drop your classes" in errors[0]
    assert "after you graduate" in errors[1]


# --- common random numbers -------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(4))
def test_same_choice_same_draw_whatever_came_before(tmp_path, seed):
    """Two lives with the same dice seed that make the same application get the same draw, even
    when one took a different path first. This is what makes cross-path comparisons fair."""
    app = call("apply", opening_id="job-01", details="hi")
    straight = {1: [[app]]}
    detour = {1: [[call("gig")]], 2: [[call("apply", opening_id="job-03", details="x")]], 3: [[app]]}
    r = Referee(chance=0.4, weeks=1)
    _, a, *_ = play(tmp_path / "a", straight, 1, referee=r, seed=seed)
    _, b, *_ = play(tmp_path / "b", detour, 3, referee=r, seed=seed)
    da = next(x for x in events(a, "referee_decision") if x["opening_id"] == "job-01")
    db = next(x for x in events(b, "referee_decision") if x["opening_id"] == "job-01")
    assert da["success_draw"] == db["success_draw"] == ref.uniform(seed, "apply", "job-01", 1)[0]
    assert da["outcome"] == db["outcome"]


def test_runs_with_the_same_script_and_seed_are_identical(tmp_path):
    script = {1: [[call("apply", opening_id="job-01", details="hi")]], 2: [[call("gig")]]}
    strip = lambda log: [{k: v for k, v in r.items() if k not in ("ts", "code")} for r in log]
    _, a, *_ = play(tmp_path / "a", script, 3, referee=Referee(chance=0.5, weeks=1), seed=3)
    _, b, *_ = play(tmp_path / "b", script, 3, referee=Referee(chance=0.5, weeks=1), seed=3)
    assert strip(a) == strip(b)


def test_a_bad_files_call_is_a_tool_error_not_the_end_of_the_run(tmp_path):
    script = {1: [[call("files", action="write", path="app/main.py", content="x")],
                  [call("files", action="read", path="app")]]}
    run, log, *_ = play(tmp_path, script, 2)  # play asserts the run reached the horizon
    assert "app is not a file" in events(log, "tool_error")[0]["error"]
