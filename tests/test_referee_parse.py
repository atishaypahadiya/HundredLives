"""The referee's output is checked and clamped in code; the model never decides an outcome or an amount."""

import json

import pytest

from orchestrator import referee as ref
from orchestrator.world import load_world
from tests.harness import ROOT, persona

MAYA = {c["id"]: c for c in persona("maya.yaml")["contacts"]}
SELF = {c["id"]: c for c in persona("self.yaml")["contacts"]}
OPENINGS = {o["id"]: o for o in load_world(ROOT / "world/openings.yaml")["openings"]}
STUDENT = {o["id"]: o for o in load_world(ROOT / "world/student.yaml")["openings"]}


def j(**kw):
    return json.dumps(kw)


# --- applications ---------------------------------------------------------------------------

def test_estimate_passes_through():
    est, err = ref.parse_estimate(j(estimated_chance=0.12, decision_in_weeks=3, message_if_success="yes",
                                    message_if_failure="no", rationale="r"), 0.05)
    assert err is None and est["estimated_chance"] == 0.12 and est["decision_in_weeks"] == 3


@pytest.mark.parametrize("chance,weeks,want", [(1.7, 99, (1.0, 26)), (-0.3, -4, (0.0, 0)), ("0.4", "2", (0.4, 2))])
def test_estimate_clamped(chance, weeks, want):
    est, err = ref.parse_estimate(j(estimated_chance=chance, decision_in_weeks=weeks), 0.05)
    assert err is None and (est["estimated_chance"], est["decision_in_weeks"]) == want


@pytest.mark.parametrize("text", ["not json", "[0.5]", j(estimated_chance="high"), j(decision_in_weeks=None), "null"])
def test_unusable_estimate_falls_back_to_base_rate(text):
    est, err = ref.parse_estimate(text, 0.05)
    assert err and est["estimated_chance"] == 0.05


def test_estimate_ignores_fields_outside_the_schema():
    est, _ = ref.parse_estimate(j(estimated_chance=0.2, outcome="success", pay_weekly=10**6), 0.05)
    assert "outcome" not in est and "pay_weekly" not in est


def test_launch_comments_capped_and_stringified():
    out, err = ref.parse_launch(j(estimated_chance=2, comments_if_traction=[1, 2, 3, 4, 5], comments_if_quiet=None), 0.1)
    assert err is None and out["estimated_chance"] == 1.0
    assert out["comments_if_traction"] == ["1", "2", "3"] and out["comments_if_quiet"] == []


def test_post_replies_filtered():
    out, err = ref.parse_post(j(estimated_chance=0.5, replies_if_breakout=[
        {"handle": "a", "text": "nice"}, {"handle": "b", "text": "  "}, "junk", {"text": "x" * 1000}]), 0.02)
    assert err is None
    assert [r["handle"] for r in out["replies_if_breakout"]] == ["a", "someone"]
    assert len(out["replies_if_breakout"][1]["text"]) == 400


def test_judge_falls_back():
    out, err = ref.parse_judge("{", 0.1)
    assert err and out["estimated_chance"] == 0.1


# --- contacts -------------------------------------------------------------------------------

def contact(c, used=frozenset(), openings=OPENINGS, term=None, **kw):
    return ref.parse_contact(j(reply="hi", **kw), c, openings, set(used), term)


def test_no_offer():
    assert contact(MAYA["priya"], offer_kind="none") == ({"reply": "hi", "offer": None}, None)


def test_offer_not_on_the_list_is_dropped_but_reply_kept():
    out, problem = contact(MAYA["priya"], offer_kind="paid_pilot", offer_amount=900)
    assert out == {"reply": "hi", "offer": None} and "isn't on priya's list" in problem


def test_referral_only_to_listed_openings():
    assert contact(MAYA["priya"], offer_kind="referral", offer_opening_id="job-02")[0]["offer"] == \
        {"kind": "referral", "opening_id": "job-02"}
    out, problem = contact(MAYA["priya"], offer_kind="referral", offer_opening_id="job-01")
    assert out["offer"] is None and problem


def test_referral_once_per_opening():
    out, problem = contact(MAYA["priya"], used={("referral", "job-02")}, offer_kind="referral", offer_opening_id="job-02")
    assert out["offer"] is None and "already" in problem


@pytest.mark.parametrize("amount,want,capped", [(900, 900, False), (5000, 1500, True)])
def test_paid_pilot_capped(amount, want, capped):
    out, problem = contact(MAYA["parents"], offer_kind="paid_pilot", offer_amount=amount)
    assert out["offer"] == {"kind": "paid_pilot", "amount": want}
    assert bool(problem) == capped


@pytest.mark.parametrize("amount", [0, -50, "lots"])
def test_paid_pilot_needs_an_amount(amount):
    out, problem = contact(MAYA["parents"], offer_kind="paid_pilot", offer_amount=amount)
    assert out["offer"] is None and "no amount" in problem


def test_paid_pilot_once():
    out, _ = contact(MAYA["parents"], used={("paid_pilot", None)}, offer_kind="paid_pilot", offer_amount=100)
    assert out["offer"] is None


def test_money_once_a_semester():
    fall, spring = "Fall semester (year 1)", "Spring semester (year 1)"
    used = {("money", fall)}
    assert contact(SELF["family"], used, STUDENT, fall, offer_kind="money", offer_amount=200)[0]["offer"] is None
    assert contact(SELF["family"], used, STUDENT, spring, offer_kind="money", offer_amount=200)[0]["offer"] == \
        {"kind": "money", "amount": 200}
    out, problem = contact(SELF["family"], set(), STUDENT, spring, offer_kind="money", offer_amount=9000)
    assert out["offer"]["amount"] == 500 and "capped" in problem


def test_teammate_only_for_listed_hackathons():
    ok = contact(SELF["kabir"], set(), STUDENT, offer_kind="teammate", offer_opening_id="hk-01")[0]["offer"]
    assert ok == {"kind": "teammate", "opening_id": "hk-01"}
    assert contact(SELF["kabir"], set(), STUDENT, offer_kind="teammate", offer_opening_id="hk-02")[0]["offer"] is None
    assert contact(SELF["kabir"], {("teammate", "hk-01")}, STUDENT, offer_kind="teammate",
                   offer_opening_id="hk-01")[0]["offer"] is None


def test_boost_uses_the_contacts_numbers_not_the_models():
    out, _ = contact(SELF["tomas"], set(), STUDENT, offer_kind="boost", offer_amount=10**6)
    assert out["offer"] == {"kind": "boost", "reach": 400, "community": SELF["tomas"]["offers"][0]["community"]}
    assert contact(SELF["tomas"], {("boost", None)}, STUDENT, offer_kind="boost")[0]["offer"] is None


@pytest.mark.parametrize("text", ["nope", "[]", "null"])
def test_unusable_contact_output(text):
    out, problem = ref.parse_contact(text, MAYA["priya"], OPENINGS, set())
    assert out == {"reply": "", "offer": None} and problem


@pytest.mark.xfail(strict=True, reason="bug: a non-string offer_kind is used as a dict key and raises TypeError, "
                                       "which ends the run with reason 'error'")
@pytest.mark.parametrize("kind", [["referral"], {"kind": "referral"}])
def test_malformed_offer_kind_is_dropped(kind):
    out, problem = ref.parse_contact(j(reply="hi", offer_kind=kind), MAYA["priya"], OPENINGS, set())
    assert out == {"reply": "hi", "offer": None} and problem


def test_describe_offers_leaves_out_used_ones():
    text = ref.describe_offers(MAYA["dana"], OPENINGS, {("referral", "job-01")})
    assert "angel-01" in text and "job-01" not in text
    assert ref.describe_offers(MAYA["priya"], OPENINGS, {("referral", "job-02")}) == "(none)"
