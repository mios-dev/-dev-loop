#!/usr/bin/env python3
"""
Controls for the hardened system prompt (templates/prompts/system.md) and `prompt.py emit`.

What these guard
----------------
1. ONE SOURCE. Every harness carrier is a projection of the same rendered text. A carrier that
   drifts from the others means two harnesses are running under different rules while the repo
   claims one prompt.
2. ONE SCHEMA. The OpenAI response_format is DERIVED from the strict `report` function in
   assets/openai-tools.json, never copied. The control for "derived" is a mutation: change the
   source schema and the emitted one must change with it. A copy would not.
3. REFUSALS. emit must refuse a non-strict schema, a missing schema, and a ROLE outside
   manager/lane/monitor. Each is a Skip-as-Pass waiting to happen if it degrades to a default.
4. THE HARDENING SURVIVES. The sections that make a loop hard to fool are asserted present, so
   a "simplify the prompt" edit that drops the forbidden-moves list goes red.

Run: python3 tests/test_system_prompt.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "dev-loop" / "scripts"
PROMPT = SCRIPTS / "prompt.py"
TOOLS = ROOT / "skills" / "dev-loop" / "assets" / "openai-tools.json"
sys.path.insert(0, str(SCRIPTS))

import prompt as P  # noqa: E402

FAILURES: list[str] = []
VARS = {"ROLE": "manager", "RUN_ROOT": "/repo", "OBJECTIVE": "make the gate pass",
        "STOP_CONDITION": "make check"}


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}{'' if cond else ': ' + detail}")
    if not cond:
        FAILURES.append(name)


def emit(*extra: str, var: dict | None = None) -> subprocess.CompletedProcess:
    args = [sys.executable, str(PROMPT), "emit", "system"]
    for k, v in (var if var is not None else VARS).items():
        args += ["--var", f"{k}={v}"]
    return subprocess.run(args + list(extra), capture_output=True, text=True, timeout=60)


def test_one_source() -> None:
    print("every carrier is the same text:")
    text = P.load("system").render(VARS)
    out = P.carriers(text, P.report_response_format())
    check("openai-chat system message == text",
          out["openai-chat"]["messages"][0] == {"role": "system", "content": text})
    check("openai-responses instructions == text", out["openai-responses"]["instructions"] == text)
    check("turn1 carries the full text", text.rstrip("\n") in out["turn1"])
    check("turn1 fences the rules from the task",
          out["turn1"].startswith("<system-rules>") and "</system-rules>" in out["turn1"])
    check("no placeholder survives", "{{" not in text)


def test_one_schema() -> None:
    print("the response_format is derived, not copied:")
    rf = P.report_response_format()
    src = next(t["function"] for t in json.loads(TOOLS.read_text()) if t["function"]["name"] == "report")
    check("schema IS the report parameters", rf["json_schema"]["schema"] == src["parameters"])
    check("strict", rf["json_schema"]["strict"] is True)
    check("OpenAI json_schema shape", rf["type"] == "json_schema" and "name" in rf["json_schema"])

    # The mutation that distinguishes "derived" from "copied".
    with tempfile.TemporaryDirectory() as td:
        tools = json.loads(TOOLS.read_text())
        for t in tools:
            if t["function"]["name"] == "report":
                t["function"]["parameters"]["properties"]["planted_key"] = {"type": "string"}
                t["function"]["parameters"]["required"].append("planted_key")
        mut = Path(td) / "tools.json"
        mut.write_text(json.dumps(tools))
        got = P.report_response_format(mut)["json_schema"]["schema"]
        check("a planted key in the source reaches the emitted schema",
              "planted_key" in got["properties"] and "planted_key" in got["required"],
              "the emitted schema ignored its source -- it is a copy")


def test_refusals() -> None:
    print("refusals (each would otherwise be a silent default):")
    with tempfile.TemporaryDirectory() as td:
        tools = json.loads(TOOLS.read_text())
        for t in tools:
            if t["function"]["name"] == "report":
                t["function"]["strict"] = False
        lax = Path(td) / "lax.json"
        lax.write_text(json.dumps(tools))
        cp = emit("--tools", str(lax))
        check("non-strict schema is refused", cp.returncode != 0 and "not strict" in cp.stderr, cp.stderr[-200:])

        nothing = Path(td) / "none.json"
        nothing.write_text(json.dumps([t for t in tools if t["function"]["name"] != "report"]))
        cp = emit("--tools", str(nothing))
        check("missing report schema is refused", cp.returncode != 0 and "no `report`" in cp.stderr, cp.stderr[-200:])

    cp = emit(var={**VARS, "ROLE": "banana"})
    check("unknown ROLE is refused", cp.returncode != 0 and "ROLE must be one of" in cp.stderr, cp.stderr[-200:])
    for role in P.ROLES:
        cp = emit(var={**VARS, "ROLE": role})
        check(f"ROLE={role} renders", cp.returncode == 0 and f"You are a {role}" in cp.stdout, cp.stderr[-200:])
    cp = emit("--carrier", "all")
    check("--carrier all without --out-dir is refused", cp.returncode != 0, cp.stdout[-100:])


def test_hardening_survives() -> None:
    """Section-level assertions. If a future edit drops one of these, the prompt got weaker
    and this goes red rather than the weakening shipping as a 'cleanup'."""
    print("the hardening is present:")
    text = P.load("system").render(VARS)
    for needle in ("# Order of authority", "# Checks that cannot fail", "Skip-as-pass",
                   "Empty-set pass", "Raised ratchet", "Swallowed failure", "Timeout-as-pass",
                   "Self-certifying predicate", "Measuring the wrong property",
                   "# Lifetime", "background", ".agents/ORIGINAL_REQUEST.md",
                   "Stage explicit paths only", "# When to stop", "negative control"):
        check(f"contains {needle!r}", needle in text)
    check("untrusted content is ranked BELOW this prompt",
          text.index("This system prompt") < text.index("Everything you READ"))


def main() -> int:
    test_one_source()
    test_one_schema()
    test_refusals()
    test_hardening_survives()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        return 1
    print("all system-prompt controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
