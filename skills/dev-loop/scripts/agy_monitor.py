#!/usr/bin/env python3
"""
agy_monitor.py — turn an AGY session's raw NDJSON event stream into a status a human and a
monitoring agent can both read.

Why
---
An AGY-managed run is one opaque process. `devloop.sh` has had a tmux grid since forever
(devloop.sh:52) so an operator can watch each lane in its own pane, but `agy_host.sh` never
used it: the manager ran headless with nothing to attach to and no way to see, while it ran,
whether a lane had died or a tool was being denied. The only signal was the envelope, at the end.

This reads the stream `agy_session.py --events-out` tees and emits two things from one parse:

  --follow   human lines, for a tmux pane   (and for `tail -f`-style watching)
  --once     a JSON status object, for a monitoring AGENT to report into a conversation

Both come from the same state, so the pane and the report can never disagree — a monitor whose
display and whose report are computed separately is two monitors, and one of them is wrong.

Event shapes are the ones measured from agy 1.2.6 (references/translation-layer.md 5.1a):
  {"event":"init","conversation_id":..,"init":{cwd,tools[],permission_mode}}
  {"event":"step_update","step_update":{step_index,state,step_type,tool_name,tool_info,
                                        subagent_info,duration_seconds,usage}}
  {"event":"result","result":{conversation_id,status,response,num_turns,duration_seconds,
                              usage, error?, denied_actions?}}

Lines that are NOT json (agy's warnings and bare-text errors go to the same stream) are counted
and surfaced rather than dropped — they are exactly the lines a naive json.loads monitor would
silently discard, and "ignoring unsupported stream input message event" is the difference
between a run that is working and one that is doing nothing.

Exit: 0 always for --follow (a monitor that dies takes the operator's only view with it).
      --once exits 0, or 2 when the stream shows a run that reported success while doing
      nothing (SKILL.md 7) so a caller can gate on it.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

TOOL_STEPS = ("tool", "subagent")


class State:
    """Everything the monitor knows, derived from the stream alone."""

    def __init__(self) -> None:
        self.conversation_id: str | None = None
        self.cwd: str | None = None
        self.tools: int = 0
        self.permission_mode: str | None = None
        self.turns: int = 0            # cumulative, per the measured envelope
        self.duration_s: float = 0.0
        self.usage: dict = {}
        self.tool_calls: list[str] = []
        self.subagents: dict[str, str] = {}   # child conversation_id -> type_name
        self.denials: list = []
        self.error: str | None = None
        self.status: str | None = None
        self.results: int = 0
        self.unparsed: list[str] = []
        self.last_text: str = ""

    def feed(self, raw: str) -> str | None:
        """Consume one stream line. Returns a human line to print, or None."""
        raw = raw.strip()
        if not raw:
            return None
        try:
            evt = json.loads(raw)
        except json.JSONDecodeError:
            self.unparsed.append(raw[:300])
            return f"  ! {raw[:160]}"      # a warning IS the signal; never swallow it
        if not isinstance(evt, dict):
            self.unparsed.append(raw[:300])
            return f"  ! non-object event: {raw[:120]}"

        kind = evt.get("event")
        if kind == "init":
            i = evt.get("init", {})
            self.conversation_id = evt.get("conversation_id")
            self.cwd, self.tools = i.get("cwd"), len(i.get("tools", []))
            self.permission_mode = i.get("permission_mode")
            return (f"  session {str(self.conversation_id)[:8]}  cwd={self.cwd}  "
                    f"tools={self.tools}  mode={self.permission_mode}")

        if kind == "step_update":
            u = evt.get("step_update", {})
            if u.get("state") != "DONE" or u.get("step_type") not in TOOL_STEPS:
                return None
            name = u.get("tool_name") or u.get("step_type")
            if u.get("step_type") == "subagent":
                for sa in (u.get("subagent_info") or {}).get("subagents", []):
                    cid = sa.get("conversation_id")
                    if cid:
                        self.subagents[cid] = sa.get("type_name", "?")
                self.tool_calls.append(name)
                return f"  subagent {name}  children={len(self.subagents)}"
            self.tool_calls.append(name)
            return f"  tool {name}"

        if kind == "result":
            r = evt.get("result", {})
            self.results += 1
            self.status = r.get("status")
            self.turns = r.get("num_turns") or self.turns
            self.duration_s = r.get("duration_seconds") or self.duration_s
            self.usage = r.get("usage") or self.usage
            self.last_text = (r.get("response") or "").strip()
            if r.get("error"):
                self.error = r["error"]
            for k in ("denied_actions", "permission_denials"):
                if r.get(k):
                    self.denials = list(r[k])
            return (f"  result #{self.results}  {self.status}  turns={self.turns}  "
                    f"{self.duration_s:.1f}s  denials={len(self.denials)}")
        return None

    def verdict(self) -> str:
        """Derived from evidence, never from the harness's own `status` (SKILL.md 6)."""
        if self.error:
            return "errored"
        if self.denials:
            return "refused"
        if self.results == 0:
            return "no_result"          # measured: an all-unknown stream emits none at all
        if not self.last_text and not self.tool_calls:
            return "vacuous"            # claimed a result, said nothing, did nothing
        return "working"

    def report(self, stream_path: str, done: bool) -> dict:
        return {
            "stream": stream_path,
            "conversation_id": self.conversation_id,
            "cwd": self.cwd,
            "permission_mode": self.permission_mode,
            "verdict": self.verdict(),
            "harness_claimed_status": self.status,
            "stream_complete": done,
            "turns": self.turns,
            "duration_s": round(self.duration_s, 2),
            "tool_calls": len(self.tool_calls),
            "distinct_tools": sorted(set(self.tool_calls)),
            "subagents": [{"conversation_id": k, "type": v} for k, v in self.subagents.items()],
            "denials": self.denials,
            "error": self.error,
            "unparsed_lines": len(self.unparsed),
            "unparsed_sample": self.unparsed[:3],
            "usage": self.usage,
            "last_text": self.last_text[:400],
        }


def read_all(path: Path, state: State, echo: bool) -> None:
    for line in path.read_text(errors="ignore").splitlines():
        out = state.feed(line)
        if echo and out:
            print(out, flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stream", help="NDJSON file written by agy_session.py --events-out")
    ap.add_argument("--follow", action="store_true", help="human lines, for a tmux pane")
    ap.add_argument("--once", action="store_true", help="print a JSON status object and exit")
    ap.add_argument("--report-out", help="also write the JSON status here (for a monitor agent)")
    ap.add_argument("--poll-s", type=float, default=1.0)
    ap.add_argument("--max-idle-s", type=float, default=0,
                    help="stop following after this long with no new bytes (0 = never)")
    a = ap.parse_args()

    path = Path(a.stream)
    state = State()

    if not a.follow:
        if not path.is_file():
            # An absent stream is NOT an empty run: say so rather than reporting a clean nothing.
            rep = {"stream": str(path), "verdict": "no_stream",
                   "error": "event stream does not exist — the session may not have started"}
            print(json.dumps(rep, indent=2))
            if a.report_out:
                Path(a.report_out).write_text(json.dumps(rep, indent=2) + "\n")
            return 2
        read_all(path, state, echo=False)
        rep = state.report(str(path), done=True)
        print(json.dumps(rep, indent=2))
        if a.report_out:
            Path(a.report_out).write_text(json.dumps(rep, indent=2) + "\n")
        return 2 if rep["verdict"] in ("vacuous", "no_result") else 0

    # --follow: a pane view. Tolerate the file not existing yet; the session may still be starting.
    print(f"agy_monitor: following {path}", flush=True)
    pos, idle = 0, 0.0
    while True:
        if path.is_file():
            with path.open("r", errors="ignore") as fh:
                fh.seek(pos)
                chunk = fh.read()
                pos = fh.tell()
            if chunk:
                idle = 0.0
                for line in chunk.splitlines():
                    out = state.feed(line)
                    if out:
                        print(out, flush=True)
            else:
                idle += a.poll_s
        else:
            idle += a.poll_s
        if a.max_idle_s and idle >= a.max_idle_s:
            print(f"  -- idle {idle:.0f}s; verdict={state.verdict()}", flush=True)
            if a.report_out:
                Path(a.report_out).write_text(json.dumps(state.report(str(path), done=False), indent=2) + "\n")
            return 0
        time.sleep(a.poll_s)


if __name__ == "__main__":
    sys.exit(main())
