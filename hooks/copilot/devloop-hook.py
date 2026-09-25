#!/usr/bin/env python3
"""GitHub Copilot CLI -> dev-loop hook adapter.

Copilot's stdin is camelCase (`toolName`, `toolArgs`) and its deny output is FLAT
-- `{"permissionDecision":"deny","permissionDecisionReason":...}` with no
`hookSpecificOutput` wrapper, unlike Claude Code. Its stop output, by contrast, is
`{"decision":"block","reason":...}`, which IS Claude's shape. The dev-loop scripts
in ../*.sh emit Claude's shapes only; this file translates in both directions.

Usage:  python3 devloop-hook.py <mode>   mode = pretool|format|stop-gate|pre-compact
"""
import json
import os
import subprocess
import sys

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = int(os.environ.get("DEVLOOP_HOOK_TIMEOUT", "20"))

CMD_PATHS = ("toolArgs.command", "toolArgs.cmd", "tool_input.command", "command")
PATH_PATHS = ("toolArgs.path", "toolArgs.filePath", "toolArgs.file_path",
              "tool_input.file_path", "filePath", "path")


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
                emit({"permissionDecision": "deny", "permissionDecisionReason": text})
                return
        if path:
            kind, text = classify(run("no-env.sh", {"tool_input": {"file_path": path}}))
            if kind == "deny":
                emit({"permissionDecision": "deny", "permissionDecisionReason": text})
                return
        return                                  # preToolUse is the ONLY event that can deny

    if mode == "format":
        path = first(payload, PATH_PATHS)
        if not path:
            return
        kind, text = classify(run("format.sh", {"tool_input": {"file_path": path}}))
        if kind == "block":
            # postToolUse cannot block; the failure is reported back as context.
            emit({"additionalContext": text})
        return

    if mode == "stop-gate":
        tp = first(payload, ("transcriptPath", "transcript_path", "transcriptFile"))
        if not tp:
            # Copilot's stop payload is not documented to carry a transcript path.
            # stop-gate.sh reads the transcript to decide, so without one it cannot
            # gate. Say so on stderr rather than exiting 0 and looking enforced.
            print("dev-loop: stop gate inert -- no transcript path in the Copilot stop payload",
                  file=sys.stderr)
            return
        kind, text = classify(run("stop-gate.sh", {"transcript_path": tp, "stop_hook_active": False}))
        if kind == "block":
            emit({"decision": "block", "reason": text})
        return

    if mode == "pre-compact":
        run("pre-compact.sh", payload)
        return

    print("usage: devloop-hook.py pretool|format|stop-gate|pre-compact", file=sys.stderr)
    sys.exit(64)


if __name__ == "__main__":
    main()
