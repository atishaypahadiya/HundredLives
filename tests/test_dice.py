"""Keyed dice: every draw is a pure function of (dice seed, kind, target, attempt)."""

import hashlib
import json
import statistics

import pytest

from orchestrator import referee as ref
from orchestrator.world import load_world
from tests.harness import ROOT

FORUM = load_world(ROOT / "world/openings.yaml")["forum"]
FEED = load_world(ROOT / "world/student.yaml")["feed"]


def test_uniform_is_a_function_of_its_key():
    u, key = ref.uniform(7, "apply", "job-01", 1)
    assert json.loads(key) == [7, "apply", "job-01", 1]
    for _ in range(3):
        ref.uniform(7, "apply", "job-02", 1)  # other draws in between change nothing
        assert ref.uniform(7, "apply", "job-01", 1) == (u, key)


def test_uniform_matches_the_logged_scheme():
    # keyed-sha256-v1, derived here from its definition: the first 53 bits of sha256(json key).
    # If this changes, every logged draw stops being replayable.
    assert ref.DICE_SCHEME == "keyed-sha256-v1"
    key = json.dumps([0, "apply", "job-01", 1])
    expected = (int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") >> 11) / 2**53
    assert ref.uniform(0, "apply", "job-01", 1)[0] == expected == 0.7776442342609045


@pytest.mark.parametrize("change", [(1, "apply", "job-01", 1), (0, "reply", "job-01", 1),
                                    (0, "apply", "job-02", 1), (0, "apply", "job-01", 2)])
def test_every_part_of_the_key_matters(change):
    assert ref.uniform(*change)[0] != ref.uniform(0, "apply", "job-01", 1)[0]


def test_uniform_range_and_spread():
    us = [ref.uniform(s, "apply", "x", 1)[0] for s in range(4000)]
    assert all(0 <= u < 1 for u in us)
    assert statistics.mean(us) == pytest.approx(0.5, abs=0.02)
    deciles = [sum(int(u * 10) == d for u in us) for d in range(10)]
    assert min(deciles) > 340 and max(deciles) < 460  # 400 each expected


def test_draw_thresholds():
    assert ref.draw(0, "job-01", 1, chance=1.0, reply_rate=0.0)[0] == "success"
    assert ref.draw(0, "job-01", 1, chance=0.0, reply_rate=1.0)[0] == "failure"
    assert ref.draw(0, "job-01", 1, chance=0.0, reply_rate=0.0)[0] == "ignored"


def test_draw_success_does_not_depend_on_reply_rate():
    for seed in range(200):
        a, da = ref.draw(seed, "job-01", 1, 0.3, 0.0)
        b, db = ref.draw(seed, "job-01", 1, 0.3, 1.0)
        assert (a == "success") == (b == "success")
        assert da["success_draw"] == db["success_draw"]
        assert da["success_key"] != da["reply_key"]


def test_draw_rates_match_chance():
    n = 5000
    wins = sum(ref.draw(s, "job-01", 1, 0.2, 0.5)[0] == "success" for s in range(n))
    assert wins / n == pytest.approx(0.2, abs=0.02)


def test_launch_upvotes_in_range():
    for seed in range(300):
        outcome, upvotes, d = ref.draw_launch(seed, "repo", 1, 0.5, FORUM)
        lo, hi = FORUM["upvotes_traction" if outcome == "traction" else "upvotes_quiet"]
        assert lo <= upvotes <= hi
        assert outcome == ("traction" if d["success_draw"] < 0.5 else "quiet")


def test_message_reply():
    assert ref.draw_message(0, "dad", 1, 1.0)[0] is True
    assert ref.draw_message(0, "dad", 1, 0.0)[0] is False
    assert ref.draw_message(3, "dad", 2, 0.5) == ref.draw_message(3, "dad", 2, 0.5)


def test_post_engagement():
    results = [ref.draw_post(s, 1, 0.0, FEED, followers=10)[0] for s in range(2000)]
    assert not any(r["breakout"] for r in results)
    assert all(1 <= r["luck"] <= FEED["luck_cap"] for r in results)
    assert all(r["likes"] >= 0 and r["new_followers"] >= 0 and r["replies"] >= 0 for r in results)
    # Stochastic rounding: an expected ~0.9 likes is sometimes 0, sometimes more, never always the same.
    assert len({r["likes"] for r in results}) > 2
    breakout = ref.draw_post(5, 1, 1.0, FEED, followers=10)[0]
    quiet = ref.draw_post(5, 1, 0.0, FEED, followers=10)[0]
    assert breakout["breakout"] and breakout["likes"] >= quiet["likes"]


def test_post_extra_reach_only_adds():
    base = ref.draw_post(9, 3, 0.1, FEED, followers=50)[0]
    boosted = ref.draw_post(9, 3, 0.1, FEED, followers=50, extra_reach=500)[0]
    assert boosted["likes"] >= base["likes"] and boosted["breakout"] == base["breakout"]
