#!/usr/bin/env python3
"""Did the final turn ask the operator a question in chat prose instead of the native UI?

SKILL.md §5: operator questions go through the harness's question UI (Claude Code's
AskUserQuestion), never as a sentence ending in "?" in a reply. Exit 1 and print the offending
line when the last turn's reply asks one and the turn never called the question tool; exit 0
otherwise, including on any transcript it cannot read (a hook must not wedge a session)."""
from __future__ import annotations

import json
import re
import sys

ASK_TOOLS = {"AskUserQuestion"}
# a "?" that ends a sentence: after a word or closing mark, before whitespace, markup or the end.
# URL queries ("?a=1") and code are not sentences.
QUESTION = re.compile(r"[\w)\]\"'*`]\?(?=[\s*_)\"']|$)")


def _genuine_prompt(row: dict) -> bool:
    if row.get("type") != "user" or row.get("isMeta"):
        return False
    c = (row.get("message") or {}).get("content")
    if isinstance(c, str):
        return True
    return isinstance(c, list) and not any(b.get("type") == "tool_result" for b in c)


def _prose(text: str) -> list[str]:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    return [ln for ln in text.splitlines() if not ln.lstrip().startswith(">")]


def main(path: str) -> int:
    rows = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return 0
    start = max((i for i, r in enumerate(rows) if _genuine_prompt(r)), default=-1) + 1
    asked, reply = False, ""
    for r in rows[start:]:
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("name") in ASK_TOOLS:
                asked = True
            elif b.get("type") == "text" and b.get("text", "").strip():
                reply = b["text"]
    if asked:
        return 0
    for ln in _prose(reply):
        if QUESTION.search(ln):
            print(ln.strip()[:200])
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) > 1 else 0)
