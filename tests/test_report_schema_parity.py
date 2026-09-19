#!/usr/bin/env python3
"""
Control: the report example in SKILL.md 13 must validate against the `report` tool
in assets/openai-tools.json, because 13 says it does.

The tool is declared `strict: true` with `additionalProperties: false` and
`required == properties`. Under OpenAI strict mode an unknown property is a hard
validation failure, not a warning -- so a harness that enforces the schema natively
(`claude --json-schema`, `codex --output-schema`) REJECTS a report carrying a key the
schema does not list. Every lane, in every harness, is told to end its output with
that block, so a key in the example but not the schema breaks the one artifact the
whole orchestrator consumes.

That is exactly what had happened. The example emitted 13 keys and the schema listed
12: `commits` was documented, never declared, and nothing read it -- the host takes
commits from git ground truth, never from a lane's self-report, which is the point of
"`status` is the single field a host trusts". validate.sh already asserted the schema
was internally strict, so the schema was self-consistent and the DOC drifted away from
it undetected. Strictness of a schema says nothing about whether the documentation
agrees with it.

Only one direction is enforced: doc keys must be a SUBSET of schema properties. The
example is free to omit properties it does not need to illustrate.

Run: python3 tests/test_report_schema_parity.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills/dev-loop/SKILL.md"
TOOLS = ROOT / "skills/dev-loop/assets/openai-tools.json"

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def report_tool_properties() -> tuple[set[str], bool]:
    """(properties, strict) for the `report` tool."""
    for tool in json.loads(TOOLS.read_text(encoding="utf-8")):
        fn = tool.get("function", tool)
        if fn.get("name") != "report":
            continue
        params = fn.get("parameters", {})
        strict = (
            fn.get("strict") is True
            and params.get("additionalProperties") is False
            and set(params.get("required") or []) == set(params.get("properties") or {})
        )
        return set(params.get("properties") or {}), strict
    return set(), False


def example_keys() -> set[str]:
    """Top-level keys of the devloop_report object in SKILL.md 13.

    Parsed as JSON rather than grepped, so a malformed example fails here too: the
    block is published as the shape a lane emits, and a lane cannot emit something
    that does not parse.
    """
    text = SKILL.read_text(encoding="utf-8")
    m = re.search(r'```json\n(\{"devloop_report".*?\}\})\n```', text, re.S)
    if not m:
        return set()
    try:
        obj = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        check("the section 13 example parses as JSON", False, str(exc))
        return set()
    body = obj.get("devloop_report")
    return set(body) if isinstance(body, dict) else set()


def main() -> int:
    print("report doc/schema parity:")
    props, strict = report_tool_properties()
    keys = example_keys()

    # Assert the collection is non-empty BEFORE asserting about its members: a regex
    # that stopped matching would otherwise make this whole file pass over nothing.
    check("the report tool was found and declares properties", bool(props))
    check("the section 13 example was found and yielded keys", bool(keys))
    if not props or not keys:
        print("report doc/schema parity: FAILED (nothing was compared)")
        return 1

    check(
        "the report tool is strict, so an undeclared key is fatal rather than ignored",
        strict,
        "additionalProperties is not false, or required != properties",
    )
    extra = sorted(keys - props)
    check(
        "every key in the section 13 example is a declared property",
        not extra,
        "documented but not declared: " + ", ".join(extra) if extra else "",
    )

    if FAILURES:
        print(f"report doc/schema parity: FAILED ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print(f"report doc/schema parity: PASS ({len(keys)} documented key(s) vs {len(props)} declared)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
