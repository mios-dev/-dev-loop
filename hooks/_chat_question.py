#!/usr/bin/env python3
"""Did the final turn ask the operator a question in chat prose instead of the native UI?

SKILL.md §5: operator questions go through the harness's question UI (Claude Code's
AskUserQuestion), never as a sentence ending in "?" in a reply, and a question still open is
re-asked EVERY turn. Exit 1 when the last turn never called the question tool and either its reply
asks in prose (prints "chat: <line>") or its devloop_report is blocked on the operator (prints
"open: <item>"); exit 0 otherwise, including on any transcript it cannot read (a hook must not
wedge a session)."""
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


def _open_operator_items(text: str) -> list[str]:
    """blocked_on items that name the operator, from the reply's devloop_report block."""
    for block in reversed(re.findall(r"```(?:json)?[ \t]*\n(.*?)```", text, flags=re.S)):
        if "devloop_report" not in block:
            continue
        try:
            rep = json.loads(block).get("devloop_report") or {}
        except ValueError:
            return []
        if rep.get("status") != "blocked":
            return []
        return [str(i) for i in rep.get("blocked_on") or [] if "operator" in str(i).lower()]
    return []


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
            print("chat: " + ln.strip()[:200])
            return 1
    items = _open_operator_items(reply)
    if items:
        print("open: " + items[0][:200])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) > 1 else 0)
