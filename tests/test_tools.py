"""Tool argument validation, which tools a world offers, and the no-sandbox workspace."""

import os

import pytest

from orchestrator import tools as T
from orchestrator.tools import ToolError, Workspace


def test_validate_accepts_a_good_call():
    T.validate("apply", {"opening_id": "job-01", "details": "hi"})
    T.validate("wait", {"idea": "x"})
    T.validate("gig", {})


@pytest.mark.parametrize("name,args,says", [
    ("bogus", {}, "there is no tool 'bogus'"),
    ("apply", {}, "missing opening_id, details"),
    ("apply", {"opening_id": "", "details": "x"}, "missing opening_id"),
    ("files", {"action": "delete"}, "action must be one of list, read, write, append"),
    ("wait", {"idea": "x", "command": "ls"}, "unexpected command (those are arguments of shell)"),
    ("gig", {"hours": 3}, "unexpected hours"),
])
def test_validate_says_what_is_wrong(name, args, says):
    with pytest.raises(ToolError, match=None) as e:
        T.validate(name, args)
    assert says in str(e.value)
    if name != "bogus":
        assert "Its arguments:" in str(e.value)


def names(**kw):
    return {t["name"] for t in T.tools_for(**kw)}


def test_maya_without_a_sandbox():
    got = names(sandbox=False)
    assert {"files", "apply", "message", "spend", "gig", "leave", "wait"} <= got
    assert not got & {"shell", "launch", "submit", "deploy", "post", "train", "invest_personal"}


def test_each_world_key_switches_on_only_its_tools():
    base = names(sandbox=True)
    assert names(sandbox=True, feed=True) - base == {"post"}
    assert names(sandbox=True, training=True) - base == {"train"}
    assert names(sandbox=True, venture=True) - base == set(T.VENTURE_TOOLS)
    assert names(sandbox=True, mockweb_domain="mockweb.local") - base == {"deploy"}
    assert "deploy" not in names(sandbox=False, mockweb_domain="mockweb.local")  # a site needs a repo
    assert "message" not in names(sandbox=True, contacts=False)


def test_hidden_streak_train_tool_never_mentions_the_streak():
    shown = next(t for t in T.tools_for(sandbox=False, training=True) if t["name"] == "train")
    hidden = next(t for t in T.tools_for(sandbox=False, training=True, show_streak=False) if t["name"] == "train")
    assert "streak" in shown["description"].lower() and "streak" not in hidden["description"].lower()


def test_deploy_description_names_the_domain():
    deploy = next(t for t in T.tools_for(sandbox=True, mockweb_domain="example.test") if t["name"] == "deploy")
    assert "example.test" in deploy["description"] and "{domain}" not in deploy["description"]


# --- workspace -------------------------------------------------------------------------------

@pytest.fixture
def ws(tmp_path):
    return Workspace(tmp_path / "ws")


def test_write_read_append_list(ws):
    assert ws.run("list") == "(empty)"
    ws.run("write", "app/main.py", "print(1)\n")
    ws.run("append", "app/main.py", "print(2)\n")
    assert ws.run("read", "app/main.py") == "print(1)\nprint(2)\n"
    assert "app/main.py (18 bytes)" in ws.run("list")


@pytest.mark.parametrize("path", ["../escape.txt", "/etc/passwd", "a/../../b", "", "."])
def test_paths_stay_inside(ws, path):
    with pytest.raises(ToolError):
        ws.run("write", path, "x")
    assert not (ws.root.parent / "escape.txt").exists()


def test_file_size_and_quota(ws):
    with pytest.raises(ToolError, match="limit"):
        ws.run("write", "big.txt", "x" * (ws.MAX_FILE_BYTES + 1))
    for i in range(ws.MAX_TOTAL_BYTES // ws.MAX_FILE_BYTES):
        ws.run("write", f"f{i}.txt", "x" * ws.MAX_FILE_BYTES)
    with pytest.raises(ToolError, match="quota"):
        ws.run("write", "one-more.txt", "x" * ws.MAX_FILE_BYTES)
    ws.run("write", "f0.txt", "small")  # rewriting a file counts its old size out first


def test_append_counts_toward_the_file_limit(ws):
    ws.run("write", "log.txt", "x" * (ws.MAX_FILE_BYTES - 10))
    with pytest.raises(ToolError, match="limit"):
        ws.run("append", "log.txt", "y" * 11)


def test_symlinks_are_never_followed(ws, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("host secret")
    os.symlink(secret, ws.root / "link.txt")
    os.mkdir(tmp_path / "outside")
    os.symlink(tmp_path / "outside", ws.root / "dir")
    with pytest.raises(ToolError, match="symbolic link"):
        ws.run("read", "link.txt")
    with pytest.raises(ToolError, match="symbolic link"):
        ws.run("write", "link.txt", "overwritten")
    with pytest.raises(ToolError):
        ws.run("write", "dir/planted.txt", "x")
    assert secret.read_text() == "host secret"
    assert not (tmp_path / "outside" / "planted.txt").exists()
    assert "link.txt" not in ws.run("list") and ws.run("list") == "(empty)"


def test_git_internals_are_not_listed(ws):
    ws.run("write", ".git/config", "[core]")
    ws.run("write", "README.md", "hi")
    assert ws.run("list") == "- README.md (2 bytes)"


def test_reading_a_missing_file(ws):
    with pytest.raises(ToolError, match="does not exist"):
        ws.run("read", "nope.md")


def test_reading_a_directory_is_a_tool_error(ws):
    ws.run("write", "app/main.py", "x")
    with pytest.raises(ToolError, match="not a file"):
        ws.run("read", "app")
