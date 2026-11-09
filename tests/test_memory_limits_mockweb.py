"""Memory condensing, the blocked_by_world detectors, and the mock web's visitor view."""

import pytest

from orchestrator import limits, mockweb
from orchestrator.memory import COMPRESS_EVERY, Memory, WeekRecord


# --- memory ----------------------------------------------------------------------------------

def test_current_quarter_in_full_older_quarters_condensed():
    m = Memory()
    for w in range(1, 30):
        m.add(WeekRecord(w, f"[w{w}] week {w}", key=[f"applied to job-{w:02d}"] if w in (3, 14) else [],
                         gig=w in (5, 6), broke=w == 6))
    text = m.records(29)
    assert text.splitlines()[0] == ("Weeks 1–13: [w3] applied to job-03; took gigs in 2 of 13 weeks; "
                                    "couldn't cover expenses in 1 weeks")
    assert text.splitlines()[1] == "Weeks 14–26: [w14] applied to job-14"
    assert text.splitlines()[2:] == ["[w27] week 27", "[w28] week 28", "[w29] week 29"]
    assert "[w3] week 3" not in text  # the full digest of an old week is gone


def test_first_week_and_quiet_quarters():
    m = Memory()
    assert m.records(1) == "(this is your first week)"
    for w in range(1, 14):
        m.add(WeekRecord(w, f"[w{w}] nothing"))
    assert m.records(14) == "Weeks 1–13: nothing of note"


def test_reflection_is_due_every_quarter_and_rendered():
    m = Memory()
    assert [w for w in range(1, 53) if m.due(w)] == [13, 26, 39, 52] and COMPRESS_EVERY == 13
    assert "(none yet)" in m.render(1)
    m.set_reflection("  Ship the demo.  ", 13)
    assert "(written in week 13)\nShip the demo." in m.render(14)


def test_reflection_prompt_states_the_week_only_when_asked():
    m = Memory()
    assert "It is the end of week 26" in m.reflection_prompt("Self", 26, state_week=True)[1]
    assert "week 26" not in m.reflection_prompt("Maya", 26)[1]  # Maya's prompt is unchanged


# --- blocked_by_world detectors --------------------------------------------------------------

@pytest.mark.parametrize("command,output,kinds", [
    ("npx vercel --prod", "", ["external_hosting"]),
    ("git push origin gh-pages", "", ["external_hosting"]),
    ("pip install requests", "WARNING: Retrying ... Failed to establish a new connection", ["internet"]),
    ("curl https://example.com", "curl: (6) Could not resolve host: example.com", ["internet"]),
    ("git push", "fatal: unable to access 'http://gitea:3000/x.git': Could not resolve host: gitea", []),
    ("ls -la", "total 0", []),
])
def test_shell_limits(command, output, kinds):
    assert [k for k, _ in limits.from_shell(command, output)] == kinds


@pytest.mark.parametrize("text,hit", [
    ("see http://gitea:3000/self/app", True), ("running on localhost:8000", True), ("http://127.0.0.1:5000", True),
    ("https://conscious.mockweb.local", False), ("my site is live", False),
])
def test_internal_links(text, hit):
    assert bool(limits.internal_link(text)) == hit


@pytest.mark.parametrize("text,what", [
    ("uvicorn main:app --reload", "runs a server"),
    ("python3 -m http.server 8000", "runs a server"),
    ("from flask import Flask\napp = Flask(__name__)", "server code"),
    ("const express = require('express')", "server code"),
    ("fetch('/api/plan', {method: 'POST'})", "calls a backend"),
    ("fetch('https://localhost:8000/x')", "calls a backend"),
    ("const x = 1; document.title = 'hi'", None),
])
def test_backend_evidence(text, what):
    got = limits.backend(text)
    assert (got.split(":")[0] if got else None) == what


# --- mock web --------------------------------------------------------------------------------

def test_site_names():
    assert mockweb.site_name("My_Cool App!") == "my-cool-app"
    assert mockweb.site_name("___") == "site"
    assert len(mockweb.site_name("a" * 100)) == 63


def test_find_urls_in_order_once():
    text = ("try https://conscious.mockweb.local and https://planner.mockweb.local/about "
            "and again https://CONSCIOUS.mockweb.local, not https://evil.com/x.mockweb.local")
    assert mockweb.find_urls(text, "mockweb.local") == ["conscious", "planner"]


def test_site_root_first_match_wins():
    assert mockweb.site_root(["README.md", "docs/index.html", "index.html"]) == ""
    assert mockweb.site_root(["src/app.py", "dist/index.html", "docs/index.html"]) == "docs/"
    assert mockweb.site_root(["app.py"]) is None


FILES = {
    "docs/index.html": ("<html><head><title>Planner</title><script src='app.js'></script></head><body>"
                        "<h1>Plan your week</h1><a href='about.html'>About</a><a href='../secret.html'>x</a>"
                        "<a href='https://elsewhere.com'>out</a><form><input name='email' placeholder='you@x.edu'>"
                        "<button>Join</button></form></body></html>"),
    "docs/about.html": "<p>Built in a dorm.</p>",
    "docs/app.js": "function plan(){return 42}",
    "secret.html": "<p>should never be shown</p>",
}


def test_visitor_view_shows_what_a_visitor_sees():
    served = ["docs/index.html", "docs/about.html", "docs/app.js"]
    view = mockweb.visitor_view("https://planner.mockweb.local", "docs/", served, FILES)
    assert view.startswith("https://planner.mockweb.local serves 3 files: index.html, about.html, app.js")
    for want in ("(title: Planner)", "Plan your week", "--- page /about.html", "Built in a dorm.",
                 "function plan(){return 42}", "Join", "About -> about.html"):
        assert want in view, want
    assert "should never be shown" not in view  # a link out of the site root is not followed


def test_resolve_stays_inside_the_site():
    assert mockweb._resolve("docs/index.html", "about.html", "docs/") == "docs/about.html"
    assert mockweb._resolve("docs/index.html", "/about.html", "docs/") == "docs/about.html"
    assert mockweb._resolve("docs/index.html", "../secret.html", "docs/") is None
    assert mockweb._resolve("docs/index.html", "https://x.com/a.html", "docs/") is None
    assert mockweb._resolve("docs/index.html", "#top", "docs/") is None
    assert mockweb._resolve("docs/a/b.html", "./", "docs/") == "docs/a/index.html"


def test_visitor_view_is_capped():
    big = {"index.html": "<p>" + "word " * 50_000 + "</p>"}
    view = mockweb.visitor_view("https://x.mockweb.local", "", ["index.html"], big)
    assert len(view) <= mockweb.VIEW_CHARS
