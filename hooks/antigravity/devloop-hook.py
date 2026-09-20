#!/usr/bin/env python3
"""Antigravity (`agy`) -> dev-loop hook adapter.

The scripts in ../*.sh speak ONE contract: Claude Code's (snake_case stdin,
`hookSpecificOutput.permissionDecision` / `{"decision":"block"}` stdout).
Antigravity speaks a different one: camelCase protojson in, `{"decision":
"allow|deny|ask|force_ask"}` out for PreToolUse, `{"injectSteps":[...]}` out for
PreInvocation, `{"decision":"continue"}` out for Stop. This file is the only
place that translation lives.

Source of the agy contract: the vendor's own "# Lifecycle Hooks (hooks.json)"
reference, which ships EMBEDDED in the agy binary (recoverable with `strings`).
That is primary-source. What is NOT established is runtime behaviour: no agy
hook has been observed to fire here (the CLI is unauthenticated in this
container), so treat firing as unverified until you measure it.

Usage:  python3 devloop-hook.py <mode>        mode = guard|no-env|invocation|stop-gate
Reads the agy payload on stdin, writes an agy result object on stdout.
"""
import json
import os
import subprocess
import sys

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../hooks
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


def as_command(v):
    """agy passes run_command args as {"CommandLine": "..."}; be tolerant of a list."""
    if isinstance(v, list):
        return " ".join(str(x) for x in v)
    return v if isinstance(v, str) else ""


def looks_like_path(s):
    return isinstance(s, str) and s and ("/" in s or "." in s) and "\n" not in s and len(s) < 4096


def run(script, payload):
    """Run a dev-loop hook script with a Claude-shaped payload; return its stdout."""
    path = os.path.join(HOOKS, script)
    if not os.path.exists(path):
        print("dev-loop: missing hook script %s" % path, file=sys.stderr)
        return ""
    try:
        p = subprocess.run(["sh", path], input=json.dumps(payload), capture_output=True,
                           text=True, timeout=TIMEOUT)
    except Exception as e:  # never let the adapter wedge the agent loop
        print("dev-loop: %s failed: %s" % (script, e), file=sys.stderr)
        return ""
    if p.stderr:
        sys.stderr.write(p.stderr)
    return p.stdout


def classify(out):
    """Normalise a dev-loop script's Claude-shaped stdout to (kind, text)."""
    out = (out or "").strip()
    if not out:
        return ("none", "")
    try:
        d = json.loads(out)
    except Exception:
        return ("context", out)          # session-start.sh prints bare text
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

    if mode == "guard":
        cmd = as_command(first(payload, "toolCall.args.CommandLine", "toolCall.args.command"))
        kind, text = classify(run("guard.sh", {"tool_input": {"command": cmd}}))
        # NOTE: on the allow path we emit {} rather than {"decision":"allow"}.
        # Returning "allow" would auto-approve EVERY command and silently strip the
        # operator's own permission prompts -- a far worse failure than a missing
        # override. {} is the no-override shape; the vendor doc calls `decision`
        # required, so this specific fallthrough is the one unverified assumption here.
        emit({"decision": "deny", "reason": text} if kind == "deny" else {})

    elif mode == "no-env":
        args = dig(payload, "toolCall.args") or {}
        path = ""
        if isinstance(args, dict):
            # The args key carrying a file path is NOT documented for agy's write
            # steps (only run_command's CommandLine is). Take the first path-shaped
            # string value rather than guessing a key name that may not exist.
            for k in ("file_path", "filePath", "TargetFile", "path", "AbsolutePath"):
                if looks_like_path(args.get(k)):
                    path = args[k]
                    break
            else:
                for v in args.values():
                    if looks_like_path(v):
                        path = v
                        break
        kind, text = classify(run("no-env.sh", {"tool_input": {"file_path": path}}))
        emit({"decision": "deny", "reason": text} if kind == "deny" else {})

    elif mode == "invocation":
        # agy has no SessionStart event. PreInvocation carries invocationNum, so the
        # session preamble goes in on the first invocation and the in-progress task
        # goes in on every one.
        steps = []
        if int(payload.get("invocationNum") or 0) <= 1:
            k, t = classify(run("session-start.sh", payload))
            if t:
                steps.append({"ephemeralMessage": t})
        k, t = classify(run("prompt-context.sh", payload))
        if t:
            steps.append({"ephemeralMessage": t})
        emit({"injectSteps": steps} if steps else {})

    elif mode == "stop-gate":
        tp = first(payload, "transcriptPath", "transcript_path")
        if not tp:
            # Loud, not silent: a stop gate with no transcript cannot gate anything.
            print("dev-loop: stop gate inert -- no transcriptPath in the agy Stop payload",
                  file=sys.stderr)
            emit({})
            return
        kind, text = classify(run("stop-gate.sh", {"transcript_path": tp, "stop_hook_active": False}))
        # agy: decision "continue" BLOCKS the stop and re-enters the loop. stop-gate.sh
        # bounds itself with DEVLOOP_STOP_CAP / DEVLOOP_LOOP_CAP, which is what keeps
        # this from being an unbounded spend.
        emit({"decision": "continue", "reason": text} if kind == "block" else {})

    else:
        print("usage: devloop-hook.py guard|no-env|invocation|stop-gate", file=sys.stderr)
        sys.exit(64)


if __name__ == "__main__":
    main()
