#!/usr/bin/env python3
"""Gemini CLI -> dev-loop hook adapter.

Gemini's event names are its own (`BeforeTool`, `AfterTool`, `PreCompress`) and so
is its output contract: a tool call is denied with a flat
`{"decision":"deny","reason":...}`, and session context is injected with
`{"hookSpecificOutput":{"additionalContext":...}}`. The dev-loop scripts in ../*.sh
speak Claude Code's contract only. This file is the translation.

Note also that Gemini's hook `timeout` is in MILLISECONDS, unlike every other
harness here -- that is handled in ../gemini/hooks.fragment.json, not in this file.

Usage:  python3 devloop-hook.py <mode>   mode = pretool|format|session-start|pre-compact
"""
import json
import os
import subprocess
import sys

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = int(os.environ.get("DEVLOOP_HOOK_TIMEOUT", "20"))

# Gemini's per-event stdin FIELD NAMES are not pinned down by the published
# reference, so look under every plausible spelling rather than committing to one.
CMD_PATHS = ("tool_input.command", "toolArgs.command", "tool_args.command",
             "args.command", "command", "tool_input.cmd")
PATH_PATHS = ("tool_input.file_path", "tool_input.filePath", "tool_input.absolute_path",
              "tool_input.path", "toolArgs.file_path", "tool_args.file_path",
              "args.file_path", "args.absolute_path", "file_path", "absolute_path")


def dig(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur if cur not in (None, "", {}, []) else None


def first(obj, paths):
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


def classify(out):
    out = (out or "").strip()
    if not out:
        return ("none", "")
    try:
        d = json.loads(out)
    except Exception:
        return ("context", out)
    if not isinstance(d, dict):
        return ("none", "")
    if dig(d, "hookSpecificOutput.permissionDecision") == "deny":
        return ("deny", dig(d, "hookSpecificOutput.permissionDecisionReason") or "denied by dev-loop")
    if d.get("decision") == "block":
        return ("block", d.get("reason") or "blocked by dev-loop")
    ctx = dig(d, "hookSpecificOutput.additionalContext")
    if ctx:
        return ("context", ctx)
    return ("none", "")


def emit(obj):
    json.dump(obj, sys.stdout)
    sys.stdout.write("\n")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    if mode == "pretool":
        cmd = flatten(first(payload, CMD_PATHS))
        path = first(payload, PATH_PATHS)
        if cmd:
            kind, text = classify(run("guard.sh", {"tool_input": {"command": cmd}}))
            if kind == "deny":
                emit({"decision": "deny", "reason": text})
                return
        if path:
            kind, text = classify(run("no-env.sh", {"tool_input": {"file_path": path}}))
            if kind == "deny":
                emit({"decision": "deny", "reason": text})
                return
        return                                   # silence == no objection

    if mode == "format":
        path = first(payload, PATH_PATHS)
        if not path:
            return
        kind, text = classify(run("format.sh", {"tool_input": {"file_path": path}}))
        if kind == "block":
            # AfterTool has no deny; surface the parse/truncation failure as a reason.
            emit({"decision": "deny", "reason": text})
        return

    if mode == "session-start":
        kind, text = classify(run("session-start.sh", payload))
        if text:
            emit({"hookSpecificOutput": {"additionalContext": text}})
        return

    if mode == "pre-compact":
        run("pre-compact.sh", payload)           # writes a ledger entry; no output contract
        return

    print("usage: devloop-hook.py pretool|format|session-start|pre-compact", file=sys.stderr)
    sys.exit(64)


if __name__ == "__main__":
    main()
