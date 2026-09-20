#!/usr/bin/env python3
"""Cursor Agent -> dev-loop hook adapter.

Cursor's stdin is snake_case and, usefully, `transcript_path` is on EVERY hook
payload -- which is what `stop-gate.sh` needs to decide anything. Its output
contract is its own: permission events answer
`{"permission":"allow|deny|ask", "agent_message":...}`, `sessionStart` answers
`{"additional_context":...}`, and `stop` answers ONLY `{"followup_message":...}`.
The dev-loop scripts in ../*.sh emit Claude Code's shapes; this file translates.

Read the `stop` mapping carefully: Cursor's stop hook has no documented way to
refuse a stop. The dev-loop gate therefore degrades from enforcement to ADVICE
here, and the README says so rather than letting the manifest imply otherwise.

Usage:  python3 devloop-hook.py <mode>
        mode = shell|pretool|format|session-start|pre-compact|stop-gate
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

    if mode == "shell":                          # beforeShellExecution: {command, cwd, sandbox}
        cmd = flatten(first(payload, "command", "tool_input.command"))
        kind, text = classify(run("guard.sh", {"tool_input": {"command": cmd}}))
        # Stay silent on the allow path. Answering {"permission":"allow"} on every
        # command would strip the operator's own approval prompts.
        if kind == "deny":
            emit({"permission": "deny", "agent_message": text, "user_message": text})
        return

    if mode == "pretool":                        # preToolUse: {tool_name, tool_input}
        cmd = flatten(first(payload, "tool_input.command"))
        path = first(payload, "tool_input.file_path", "tool_input.path", "tool_input.filePath")
        if cmd:
            kind, text = classify(run("guard.sh", {"tool_input": {"command": cmd}}))
            if kind == "deny":
                emit({"permission": "deny", "agent_message": text, "user_message": text})
                return
        if path:
            kind, text = classify(run("no-env.sh", {"tool_input": {"file_path": path}}))
            if kind == "deny":
                emit({"permission": "deny", "agent_message": text, "user_message": text})
                return
        return

    if mode == "format":                         # postToolUse: {additional_context}
        path = first(payload, "tool_input.file_path", "tool_input.path", "file_path")
        if not path:
            return
        kind, text = classify(run("format.sh", {"tool_input": {"file_path": path}}))
        if kind == "block":
            emit({"additional_context": text})
        return

    if mode == "session-start":
        kind, text = classify(run("session-start.sh", payload))
        if text:
            emit({"additional_context": text})
        return

    if mode == "pre-compact":
        run("pre-compact.sh", payload)
        return

    if mode == "stop-gate":
        tp = first(payload, "transcript_path")
        if not tp:
            print("dev-loop: stop gate inert -- no transcript_path in the Cursor stop payload",
                  file=sys.stderr)
            return
        if payload.get("status") in ("aborted", "error"):
            return                               # the operator stopped it; do not nag
        kind, text = classify(run("stop-gate.sh", {"transcript_path": tp, "stop_hook_active": False}))
        if kind == "block":
            # ADVISORY ONLY. Cursor's stop hook has no documented refusal; the most
            # it accepts is a followup message. This does NOT re-arm the loop the way
            # Claude Code's {"decision":"block"} or Antigravity's
            # {"decision":"continue"} do.
            emit({"followup_message": text})
        return

    print("usage: devloop-hook.py shell|pretool|format|session-start|pre-compact|stop-gate",
          file=sys.stderr)
    sys.exit(64)


if __name__ == "__main__":
    main()
