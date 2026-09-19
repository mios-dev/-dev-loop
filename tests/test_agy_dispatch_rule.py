#!/usr/bin/env python3
"""
Two-sided controls for agy_host.sh's dispatch rule and agy_session.py's wire shape.

The rule these guard
--------------------
Which lanes a manager may run as NATIVE Antigravity subagents is decided by PROCESS
LIFETIME, not by whether a human is watching:

  interactive  -> native subagents allowed (a person waits for them)
  --headless   -> FORBIDDEN. `agy -p` is single-turn; the process exits when the turn
                  ends and an unfinished subagent dies with it. Not an availability
                  claim -- invoke_subagent works headlessly (measured) -- a lifetime one.
  --session    -> allowed. The held stream-json session outlives each turn, and
                  agy_session.py polls until every antigravity lane has reported.

Every assertion below fails loudly if those three collapse into each other, which is the
mutation this file exists to catch: if someone "simplifies" --session to reuse the
headless rule (or vice versa), the distinctness checks go red.

Run: python3 tests/test_agy_dispatch_rule.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = ROOT / "skills" / "dev-loop" / "scripts" / "agy_host.sh"
LANES = ROOT / "skills" / "dev-loop" / "assets" / "lanes.example.json"
sys.path.insert(0, str(ROOT / "skills" / "dev-loop" / "scripts"))

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def prompt_for(*flags: str) -> str:
    cp = subprocess.run(["sh", str(HOST), str(LANES), "--print-prompt", *flags],
                        capture_output=True, text=True, timeout=180)
    assert cp.returncode == 0, f"agy_host.sh --print-prompt {flags} exited {cp.returncode}: {cp.stderr[-400:]}"
    return cp.stdout


FORBID = "Do NOT use invoke_subagent"
NATIVE = "invoke_subagent with workspace: branch"


def test_rules() -> None:
    print("dispatch rules:")
    interactive, headless, session = prompt_for(), prompt_for("--headless"), prompt_for("--session")

    # Positive controls: each mode carries the rule its lifetime demands.
    check("interactive allows native subagents", NATIVE in interactive)
    check("interactive does not carry the ban", FORBID not in interactive)
    check("headless bans native subagents", FORBID in headless)
    check("headless routes the full plan through devloop.sh", "devloop.sh" in headless)
    check("session allows native subagents", NATIVE in session)
    check("session does not carry the ban", FORBID not in session)
    check("session announces the held lifetime", "HELD SESSION" in session)

    # The ban must be justified by LIFETIME, not by availability -- a future editor
    # rewriting it as "invoke_subagent is unavailable" would be reinstating a claim
    # three measurements refuted.
    check("headless ban is worded as a lifetime constraint, not availability",
          "it works" in headless and "process exits" in headless)

    # Negative controls: the three rules must stay DISTINCT. Collapsing any pair is the
    # regression this file is for; without these, copying one rule over another passes.
    check("headless != session rule", headless != session)
    check("headless != interactive rule", headless != interactive)
    check("session != interactive rule", session != interactive,
          "session must say more than interactive: it promises the host will poll")
    check("session tells the manager a turn end is not the run end",
          "Ending a turn does NOT end the run" in session)


def test_print_only_is_sticky() -> None:
    """A dry-run flag that executes is the worst kind of surprise. --print-prompt must
    win in EVERY flag order; previously `--print-prompt --headless` launched the run."""
    print("--print-prompt stickiness:")
    for flags in (("--headless",), ("--session",)):
        after = subprocess.run(["sh", str(HOST), str(LANES), "--print-prompt", *flags],
                               capture_output=True, text=True, timeout=180)
        before = subprocess.run(["sh", str(HOST), str(LANES), *flags, "--print-prompt"],
                                capture_output=True, text=True, timeout=180)
        check(f"--print-prompt before {flags[0]} previews", after.returncode == 0 and after.stdout.strip() != "")
        check(f"--print-prompt after {flags[0]} previews (order-independent)",
              before.returncode == 0 and before.stdout.strip() != "",
              f"rc={before.returncode} — the flag order decided whether the manager RAN")
        check(f"both orders produce the same prompt for {flags[0]}", after.stdout == before.stdout)


def test_session_wire_shape() -> None:
    """agy_session.py's NDJSON shape and argv, both measured against agy 1.2.6."""
    print("agy_session wire shape:")
    import agy_session as S

    line = S.ndjson_user("hello")
    doc = json.loads(line)
    check("input event is 'user'", doc.get("event") == "user")
    check("message is TOP-LEVEL, not nested under 'user'",
          "message" in doc and "user" not in {k for k in doc if k != "event"},
          "agy rejects a nested form: 'stream input \"user\" message is missing the \"message\" field'")
    check("message carries role+content", doc["message"] == {"role": "user", "content": "hello"})
    check("exactly one NDJSON line", line.endswith("\n") and line.count("\n") == 1)

    # The -p trap: a BARE -p swallows the next token as its prompt, so `-p` immediately
    # followed by a flag silently turns that flag into the prompt (measured: exit 2).
    src = (ROOT / "skills" / "dev-loop" / "scripts" / "agy_session.py").read_text()
    check("argv uses the attached-empty -p= form", '"-p="' in src)
    check("argv never emits a bare -p", '"-p"' not in src,
          "a bare -p would consume the following flag as the prompt")


def test_report_tracking() -> None:
    """missing_reports drives the poll loop; an Empty-Set Pass here would make the host
    declare every lane finished the moment no lane was listed."""
    print("report tracking:")
    import agy_session as S

    with tempfile.TemporaryDirectory() as td:
        native = Path(td) / ".devloop" / "native"
        native.mkdir(parents=True)
        check("unreported lane is listed", S.missing_reports(native, ["a", "b"]) == ["a", "b"])
        (native / "report-a.json").write_text("{}")
        check("reported lane drops out", S.missing_reports(native, ["a", "b"]) == ["b"])
        (native / "report-b.json").write_text("{}")
        check("all reported -> empty", S.missing_reports(native, ["a", "b"]) == [])

        lanes = Path(td) / "lanes.json"
        lanes.write_text(json.dumps({"lanes": [
            {"id": "n1", "worker": {"harness": "antigravity"}},
            {"id": "c1", "worker": {"harness": "claude-code"}},
            {"id": "n2", "worker": {"harness": "antigravity"}},
        ]}))
        ids = S.antigravity_lane_ids(lanes)
        check("only antigravity lanes are polled for", ids == ["n1", "n2"],
              f"got {ids}: a claude-code lane runs under devloop.sh and writes no native report")
        bad = Path(td) / "nope.json"
        bad.write_text("{not json")
        check("unparseable lane file yields no ids rather than raising",
              S.antigravity_lane_ids(bad) == [])


def main() -> int:
    for t in (test_rules, test_print_only_is_sticky, test_session_wire_shape, test_report_tracking):
        t()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("all dispatch-rule controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
