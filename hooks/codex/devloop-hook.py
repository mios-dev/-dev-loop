#!/usr/bin/env python3
"""Codex -> dev-loop hook adapter.

Codex's documented hook contract is shaped like Claude Code's: snake_case stdin
(`tool_name`, `tool_input`, `transcript_path`, ...) and `hookSpecificOutput` /
`{"decision":"block"}` on stdout. So this adapter is mostly a pass-through. It
exists for two reasons that are NOT cosmetic:

 1. Codex's tool names are not documented, so the manifest cannot use a tool-name
    matcher without guessing. It matches everything and this adapter routes on the
    SHAPE of `tool_input` instead -- a command-ish field goes to guard.sh, a
    path-ish field goes to no-env.sh. A guessed matcher that never matches is the
    worst outcome available: it looks installed and does nothing.
 2. A shell tool's command may arrive as a LIST (`["bash","-lc","..."]`). Handed to
    guard.sh unchanged, its word-boundary patterns miss, because the command is
    preceded by a quote rather than whitespace. This flattens it first.

Usage:  python3 devloop-hook.py <mode>   mode = pretool|format|stop-gate|session-start|prompt-context|pre-compact
"""
import json
import os
import subprocess
import sys

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = int(os.environ.get("DEVLOOP_HOOK_TIMEOUT", "20"))


def dig(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur if cur not in (None, "", {}, []) else None


def first(obj, *paths):
    for p in paths:
        v = dig(obj, p)
        if v is not None:
            return v
    return None


def flatten(v):
    if isinstance(v, list):
        return " ".join(str(x) for x in v)
    return v if isinstance(v, str) else ""


def run(script, payload):
    path = os.path.join(HOOKS, script)
    if not os.path.exists(path):
        print("dev-loop: missing hook script %s" % path, file=sys.stderr)
        return ""
    try:
        p = subprocess.run(["sh", path], input=json.dumps(payload), capture_output=True,
                           text=True, timeout=TIMEOUT)
    except Exception as e:
        print("dev-loop: %s failed: %s" % (script, e), file=sys.stderr)
        return ""
    if p.stderr:
        sys.stderr.write(p.stderr)
    return p.stdout


def is_deny(out):
    try:
        d = json.loads(out)
    except Exception:
        return False
    return isinstance(d, dict) and dig(d, "hookSpecificOutput.permissionDecision") == "deny"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    if mode == "pretool":
        cmd = flatten(first(payload, "tool_input.command", "tool_input.cmd", "command"))
        path = first(payload, "tool_input.file_path", "tool_input.path", "tool_input.filePath")
        agent = payload.get("agent_type") or payload.get("subagent_type") or ""
        if cmd:
            out = run("guard.sh", {"tool_input": {"command": cmd}})
            if is_deny(out):
                sys.stdout.write(out)          # Codex reads Claude's deny shape verbatim
                return
        if path:
            out = run("no-env.sh", {"tool_input": {"file_path": path}, "agent_type": agent})
            if is_deny(out):
                sys.stdout.write(out)
                return
        return                                  # no output == no objection

    if mode == "format":
        path = first(payload, "tool_input.file_path", "tool_input.path", "tool_input.filePath")
        if not path:
            return
        sys.stdout.write(run("format.sh", {"tool_input": {"file_path": path}}))
        return

    if mode == "stop-gate":
        tp = first(payload, "transcript_path", "transcriptPath")
        if not tp:
            print("dev-loop: stop gate inert -- no transcript_path in the Codex Stop payload",
                  file=sys.stderr)
            return
        sys.stdout.write(run("stop-gate.sh", {
            "transcript_path": tp,
            "stop_hook_active": payload.get("stop_hook_active", False),
        }))
        return

    if mode in ("session-start", "prompt-context", "pre-compact"):
        sys.stdout.write(run(mode + ".sh", payload))
        return

    print("usage: devloop-hook.py pretool|format|stop-gate|session-start|prompt-context|pre-compact",
          file=sys.stderr)
    sys.exit(64)


if __name__ == "__main__":
    main()
