#!/usr/bin/env python3
"""
agy_session.py — drive `agy` as a HELD, multi-turn stream-json session.

Why this exists
---------------
`agy -p "<prompt>"` is single-turn print mode: the turn ends when the model stops
speaking and the PROCESS EXITS. Anything the manager started that had not finished --
a native `invoke_subagent` lane, a backgrounded command -- dies with it, and the
manager cannot detect that, because from inside the turn the dispatch succeeded.
That is why `agy_host.sh --headless` forbids native subagents.

Measured on agy 1.2.6: `--input-format stream-json` reads one NDJSON message per line
from stdin and runs a turn for each, requiring `--output-format stream-json`. While the
caller holds stdin open the process stays alive ACROSS turns. So the constraint above is
a property of SINGLE-SHOT print mode, not of headless operation: a held session can
dispatch native lanes and then poll for them over further turns.

Wire protocol (all measured, see references/translation-layer.md 5.1a)
----------------------------------------------------------------------
  invoke : agy --input-format stream-json --output-format stream-json \
               --print-timeout 0 [--model M] [--effort E] -p=''
           Flag order is load-bearing: a BARE `-p` swallows the next token as its
           prompt, so the empty-valued `-p=''` form is required here.
  stdin  : {"event":"user","message":{"role":"user","content":"..."}}   one per line
  stdout : {"event":"init","conversation_id":...,"init":{cwd,tools[],permission_mode}}
           {"event":"step_update","step_update":{step_index,state,step_type,...}}
           {"event":"result","result":{...}}        ONE PER TURN, not only at the end

  `num_turns` and `duration_seconds` in a result are CUMULATIVE across the session,
  not per-turn. Do not sum them.

  An UNKNOWN input event only warns and is ignored -- a stream of them yields no result
  event at all, so "no terminal envelope" is its own outcome and is reported here as an
  error rather than as success. A MALFORMED KNOWN event is fatal instead.

Exit codes: 0 ok · 3 no terminal envelope / session produced nothing · 4 agy missing
            5 lane reports still missing when the poll budget ran out
            6 the manager left the base tree dirty outside every lane worktree
            7 --done-cmd still FAILS when the session ended (it ended without doing the work)
            8 not converging: the stop condition failed with IDENTICAL output on CONVERGE_LIMIT
              consecutive turn-ends -- repeating "continue" would only burn quota
            75 (EX_TEMPFAIL) as 7, and agy reported RESOURCE_EXHAUSTED: a quota, retry after reset

STATUS OF THE POLL LOOP: UNEXERCISED as of the first end-to-end run (2026-09-19). The manager
dispatched both native lanes, gated them and merged them inside a SINGLE turn, so `missing_reports`
was already empty at the first result event and no follow-up turn was ever sent. The loop's unit
behaviour is covered by tests/test_agy_dispatch_rule.py, but its reason for existing -- keeping the
process alive for a subagent that has NOT finished when the turn ends -- has not yet been observed.
Do not describe it as proven.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # for job.py

USER_EVENT = "user"


def ndjson_user(text: str) -> str:
    """One stdin line. `message` is TOP-LEVEL, not nested under `user` (measured:
    omitting it fails with 'stream input "user" message is missing the "message" field')."""
    return json.dumps({"event": USER_EVENT, "message": {"role": "user", "content": text}}) + "\n"


def missing_reports(native_dir: Path, lane_ids: list[str], jobs_dir: Path | None = None) -> list[str]:
    """Lane ids that have not finished. Empty lane_ids means nothing to wait for.

    THE PREDICATE MATTERS MORE THAN THE LOOP. This was `is_file()` over
    report-<id>.json -- a file the poll prompt explicitly asks the polled agent to create
    (see the prompt below). The thing being measured wrote the measurement, so an agent that
    wrote the file and did nothing else ended the wait. That is a self-certifying predicate
    (SKILL.md 7) sitting inside the one mitigation that was actually enforced in code.

    When a jobs directory is present the SHELL's receipt decides: a lane is finished only when
    job.py reports it terminal (done/lost/forged), which the agent cannot fabricate because the
    wrapper writes done.json before the receipt and status() cross-checks the pair. The report
    file remains the FALLBACK for native subagent lanes, which have no job of their own -- and
    that fallback is still agent-writable, which is stated here rather than hidden.
    """
    out = []
    for lid in lane_ids:
        if jobs_dir is not None and (jobs_dir / lid).is_dir():
            try:
                import job as _job
                if _job.status(jobs_dir, lid)["state"] in ("done", "lost", "forged"):
                    continue
                out.append(lid)
                continue
            except Exception:
                pass  # fall through to the report-file fallback
        if not (native_dir / f"report-{lid}.json").is_file():
            out.append(lid)
    return out


def scan_teamwork_state(agents_dir: Path, now: float) -> dict:
    """Scans .agents/ to monitor subagent progress, heartbeats, and terminal handoffs."""
    if not agents_dir.is_dir():
        return {"live": False, "agents": {}, "terminal_handoff": None}

    agents = {}
    terminal_candidates = []

    for sub in sorted(agents_dir.iterdir()):
        if not sub.is_dir() or sub.name.startswith("."):
            continue

        prog_file = sub / "progress.md"
        handoff_file = sub / "handoff.md"

        last_visited = 0.0
        status_text = "unknown"
        current_step = ""

        if prog_file.is_file():
            try:
                txt = prog_file.read_text(encoding="utf-8")
                m_time = re.search(r"Last visited\*{0,2}:\s*\[?(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\]\s\n]*)\]?", txt)
                if m_time:
                    ts_str = m_time.group(1).strip()
                    if ts_str.endswith("Z"):
                        ts_str = ts_str[:-1] + "+00:00"
                    dt = datetime.datetime.fromisoformat(ts_str)
                    last_visited = dt.timestamp()
                m_status = re.search(r"Status\*{0,2}:\s*(.+)", txt)
                if m_status:
                    status_text = m_status.group(1).strip().strip("*")
                m_step = re.search(r"Current Step\*{0,2}:\s*(.+)", txt)
                if m_step:
                    current_step = m_step.group(1).strip().strip("*")
            except Exception:
                pass

        has_handoff = handoff_file.is_file()
        age_s = max(0.0, now - last_visited) if last_visited > 0 else 999999.0
        agents[sub.name] = {
            "last_visited": last_visited,
            "age_s": age_s,
            "status": status_text,
            "current_step": current_step,
            "has_handoff": has_handoff
        }

        if has_handoff:
            name_lower = sub.name.lower()
            if (name_lower.startswith("auditor") or name_lower.startswith("orchestrator") or
                name_lower.startswith("sentinel") or name_lower.startswith("victory_auditor") or
                "auditor" in name_lower):
                try:
                    mtime = handoff_file.stat().st_mtime
                except Exception:
                    mtime = 0.0
                terminal_candidates.append((mtime, handoff_file))

    terminal_handoff = None
    if terminal_candidates:
        terminal_candidates.sort(key=lambda x: x[0], reverse=True)
        terminal_handoff = terminal_candidates[0][1]

    live = any(a["has_handoff"] is False and a["age_s"] < 300 for a in agents.values())
    return {
        "live": live,
        "agents": agents,
        "terminal_handoff": terminal_handoff
    }


def harvest_teamwork_receipt(run_root: str | Path, terminal_handoff: Path, prompt_file: Path | None = None) -> None:
    """Harvests teamwork conclusions and writes a Ralph-style entry to .devloop/LEDGER.md."""
    run_root = Path(run_root).resolve()
    handoff_text = terminal_handoff.read_text(encoding="utf-8")

    obj_text = ""
    if prompt_file and Path(prompt_file).is_file():
        try:
            raw = Path(prompt_file).read_text(encoding="utf-8")
            obj_text = raw.replace("/teamwork-preview", "").strip()
        except Exception:
            pass
    if not obj_text:
        orig_req = run_root / ".agents" / "ORIGINAL_REQUEST.md"
        if orig_req.is_file():
            try:
                m = re.findall(r"##\s*(?:[^\n]*\s*—\s*)?\d{4}-\d{2}-\d{2}[^\n]*\n+(.*?)(?=\n##|\Z)", orig_req.read_text("utf-8"), re.S)
                if m:
                    obj_text = m[-1].strip()
            except Exception:
                pass
    if not obj_text:
        obj_text = "Teamwork execution"

    conclusion = re.search(r"##\s*(?:4\.\s*)?Conclusion\s*\n(.*?)(?=\n##|\Z)", handoff_text, re.S)
    verif = re.search(r"##\s*(?:5\.\s*)?Verification Method\s*\n(.*?)(?=\n##|\Z)", handoff_text, re.S)
    caveats = re.search(r"##\s*(?:3\.\s*)?Caveats\s*\n(.*?)(?=\n##|\Z)", handoff_text, re.S)

    done_summary = conclusion.group(1).strip().replace("\n", " ")[:300] if conclusion else "Teamwork execution completed."
    blockers = caveats.group(1).strip().replace("\n", " ")[:200] if caveats else "-"
    unverified_summary = verif.group(1).strip().replace("\n", " ")[:200] if verif else "-"

    import adapters
    args = argparse.Namespace(
        root=str(run_root),
        status="teamwork-done",
        objective=obj_text[:80],
        done=done_summary,
        next="Review auditor handoff and sync task parity",
        blockers=blockers,
        unverified=unverified_summary,
    )
    adapters.cmd_ledger(args)


# The manager is not a lane, so nothing else in this file watches what IT writes.
# Measured 2026-09-19: a manager run with worktree_root set never created a worktree and
# edited the base tree directly, planting a negatives-suite fixture -- `echo
# "Root:<literal>" | chpasswd` -- into a shipped boot script and a 99999 ratchet into the
# SSOT. Every lane gate passed, because lane gates read WORKTREES. The dispatch prompt
# already said to use isolated workspaces; a rule with no measurement behind it is a check
# that cannot fail (SKILL.md 7), so this measures it.
BASE_TREE_ALWAYS_ALLOWED = (".devloop/", ".git/", "AGENTS.md", "TASKS.md", ".agents/")


def base_tree_state(root: Path) -> dict[str, str] | None:
    """`git status --porcelain` as {path: XY}, or None when git cannot answer.

    None is NOT "clean". A control that reports nothing to report when its instrument is
    missing is the Skip-as-Pass this whole guard exists to catch, so the caller says so out
    loud and turns the guard OFF rather than letting it pass vacuously.
    """
    try:
        p = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                           capture_output=True, text=True)
    except OSError:
        return None
    if p.returncode != 0:
        return None
    out: dict[str, str] = {}
    for ln in p.stdout.splitlines():
        if len(ln) < 4:
            continue
        path = ln[3:]
        # `R  old -> new` names two paths; the destination is the one that appeared.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        out[path.strip().strip('"')] = ln[:2]
    return out


def stray_base_edits(before: dict[str, str], now: dict[str, str] | None,
                     allowed: tuple[str, ...]) -> list[str]:
    """Paths whose base-tree status CHANGED since `before` and that no lane may own.

    Compared against a baseline rather than against clean, because a run that starts on a
    dirty tree would otherwise blame the manager for every path it inherited.
    """
    if now is None:
        return []
    return sorted(path for path, st in now.items()
                  if before.get(path) != st
                  and not any(path == a or (a.endswith("/") and path.startswith(a)) for a in allowed))


def worktree_root_of(lanes_path: Path) -> str:
    """The lane plan's worktree_root, normalised to a directory prefix."""
    try:
        doc = json.loads(lanes_path.read_text())
    except Exception:
        return ".worktrees/"
    root = str(doc.get("worktree_root") or ".worktrees").strip().lstrip("./")
    return (root.rstrip("/") or ".worktrees") + "/"


def undispatched(subagent_steps: set, lane_ids: list[str]) -> int:
    """Antigravity lanes that have never been handed to a subagent.

    The dispatch prompt says to start every independent lane in the SAME turn, and
    nothing measured it. agy_host.sh already records the failure from an earlier run:
    the manager "provisioned all three worktrees, invoked the first native lane, and
    ended its turn saying it was waiting for the lane to report" -- three worktrees
    left at dirty=0. A serialised run is not a wrong answer, it is a run that spends
    its whole poll budget doing one lane at a time.

    Counted by distinct step_index, because a single subagent step reports ACTIVE and
    then DONE and would otherwise count twice.
    """
    return max(0, len(lane_ids) - len(subagent_steps))


def poll_message(native_dir, outstanding: list[str], subagent_steps: set,
                 lane_ids: list[str]) -> str:
    """What to say to a manager whose turn ended with lanes still unreported.

    "Do NOT start new work" used to be unconditional here, which told a manager that
    had dispatched one lane of four to sit and wait for it -- the run then serialises
    through the poll budget one lane at a time, or spends it. Not re-dispatching a
    RUNNING lane and not starting one that was never dispatched are opposite
    instructions, and only the first is a rule.
    """
    short = undispatched(subagent_steps, lane_ids)
    catch_up = (
        f"You have dispatched only {len(subagent_steps)} subagent(s) for {len(lane_ids)} "
        "antigravity lane(s), so at least one lane has never been started. Dispatch every "
        "lane that is not already running NOW, in this turn, all of them at once. "
    ) if short else "Do NOT start new work. "
    return ("Your native lanes have not all written "
            f"{native_dir}/report-<LANE_ID>.json yet. Still missing: {', '.join(outstanding)}. "
            + catch_up +
            "Never re-dispatch a lane that is already running. "
            "Wait for the outstanding subagents, collect each one's devloop_report into its "
            "report file with write_file, then reply DONE when every listed lane has a file.")


def session_lane_ids(lanes_path: Path) -> list[str]:
    """All lane ids declared in the plan, regardless of harness, so polling covers
    claude-code, antigravity, and external worker lanes (MON-003)."""
    try:
        doc = json.loads(lanes_path.read_text())
    except Exception:
        return []
    out = []
    for lane in doc.get("lanes", []):
        if lane.get("id"):
            out.append(lane["id"])
    return out


def antigravity_lane_ids(lanes_path: Path) -> list[str]:
    try:
        doc = json.loads(lanes_path.read_text())
    except Exception:
        return []
    out = []
    for lane in doc.get("lanes", []):
        if (lane.get("worker") or {}).get("harness") == "antigravity" and lane.get("id"):
            out.append(lane["id"])
    return out


CONTINUE_MESSAGE = (
    "Continue autonomously. Anything you drafted or proposed is APPROVED: do not ask for "
    "confirmation, do not wait for a reply -- nobody is watching this turn. Take the next step "
    "yourself (dispatch, implement, gate, report). If you are genuinely blocked, state exactly "
    "on what, write it to your results file, and stop.")


class RelayWatch:
    """Points the manager back at the monitor's relay file when, and only when, it changed.

    A monitor that relays findings by editing a file has no channel into a running session:
    the manager read the relay once, in turn 1, and every later turn is text this driver
    injects. Without this the relay is read only if the manager happens to remember it.
    Change is decided by CONTENT (sha256), not mtime: a touched-but-unchanged file is not
    news, and an edit inside the same mtime tick still is."""

    def __init__(self, path: str | None):
        self.path = Path(path) if path else None
        self.seen = self._digest()   # turn 1's prompt already points at it

    def _digest(self) -> str | None:
        if self.path is None:
            return None
        try:
            import hashlib
            return hashlib.sha256(self.path.read_bytes()).hexdigest()
        except OSError:
            return None               # absent: its later creation is a change

    def note(self) -> str:
        now = self._digest()
        if self.path is None or now is None or now == self.seen:
            return ""
        self.seen = now
        return (f" The monitor relay {self.path} CHANGED since your last turn. Re-read it now, "
                "before anything else, and act on its open items.")


def done_check(cmd: str | None, cwd: str) -> tuple[bool, str]:
    """The EXTERNAL stop signal for --auto-continue, plus WHY it failed. A shell command, run by
    the driver, never by the model: the model saying it is finished is a claim; this exiting 0 is
    the fact. The output tail is what the next turn is told, because a manager that is only told
    "continue" can do nothing but repeat "done" (measured 2026-09-24: 30 turns, quota burnt)."""
    if not cmd:
        return False, ""
    try:
        cp = subprocess.run(["sh", "-c", cmd], cwd=cwd, capture_output=True, text=True,
                            timeout=1800)
    except subprocess.TimeoutExpired:
        return False, "the stop condition timed out after 1800 s"
    except OSError as e:
        return False, f"the stop condition could not run: {e}"
    out = ((cp.stdout or "") + (cp.stderr or "")).strip()
    return cp.returncode == 0, out[-1500:] if out else f"(no output; exit {cp.returncode})"


def done_by(cmd: str | None, cwd: str) -> bool:
    return done_check(cmd, cwd)[0]


# The same failure output this many turn-ends in a row means the manager is not converging
# (SKILL §12). Continuing past it only spends quota.
CONVERGE_LIMIT = 3


_RESET_RE = re.compile(r"Resets in\s+((?:\d+h)?(?:\d+m)?(?:\d+s)?)")


def reset_seconds(text: str | None) -> int | None:
    """Seconds until a quota resets, from agy's "Resets in 3h4m58s." text; None if absent."""
    m = _RESET_RE.search(text or "")
    if not m or not m.group(1):
        return None
    part = lambda u: int(re.search(r"(\d+)" + u, m.group(1)).group(1)) if re.search(r"(\d+)" + u, m.group(1)) else 0
    return part("h") * 3600 + part("m") * 60 + part("s")


def quota_in_result(result: dict | None) -> str | None:
    """The quota text when agy reports it INSIDE a result (status ERROR) rather than as a bare
    RESOURCE_EXHAUSTED line -- measured both ways, depending on whether stderr was merged."""
    r = result or {}
    err = str(r.get("error") or "")
    if r.get("status") == "ERROR" and ("RESOURCE_EXHAUSTED" in err or "quota" in err.lower()):
        return err[:400]
    return None


def fatal_result(result: dict | None, quota: str | None, wait_max_s: float = 300) -> str | None:
    """A turn-end that no "continue" can fix: a quota that resets later than wait_max_s, or an
    invocation agy refused outright (status ERROR with zero turns -- measured: an --effort the
    model does not support). A quota that resets within wait_max_s is NOT fatal: the driver waits
    it out and continues (operator, 2026-09-25: a manager kept doing real work across 31
    turn-ends that each said "Resets in 16s")."""
    if quota:
        rs = reset_seconds(quota)
        if rs is not None and rs <= wait_max_s:
            return None
        return "agy hit its quota" + (f" (resets in {rs}s)" if rs is not None else "")
    r = result or {}
    if r.get("status") == "ERROR" and not r.get("num_turns"):
        return "agy refused the invocation: " + str(r.get("error", ""))[:300]
    return None


def hold_open(proc, events, on_result, stop_file: Path, max_s: float,
              poll_s: float = 5.0) -> str:
    """Keep a finished session ALIVE and streaming, so a remote operator can drive it.

    Why this is not just "don't exit": the local driver's work ends when the manager stops
    speaking, but `--remote-control` ties the remote connection to the PROCESS. Exit and the
    CLI logs "Deleted session instance <id>-v2" -- the session vanishes from the Remote
    Control list mid-run. Holding stdin open keeps the conversation attachable, and every
    turn a remote operator drives arrives on THIS stdout, so the events file keeps growing
    and the monitor keeps seeing it.

    Costs NOTHING while idle: no follow-up turns are sent. Select-with-timeout, not a read
    loop, so the stop file is noticed within `poll_s` even when the model says nothing.

    Ends on, and REPORTS WHICH: the stop file appearing (an OPERATOR control -- it is not
    evidence that any work is correct, and nothing here treats it as such), the wall-clock
    budget expiring, or the process dying on its own (EOF).
    """
    deadline = time.monotonic() + max_s
    while True:
        if stop_file.exists():
            return "stopped"
        if time.monotonic() >= deadline:
            return "budget"
        if proc.poll() is not None:
            return "exited"
        try:
            ready, _, _ = select.select([proc.stdout], [], [], poll_s)
        except (OSError, ValueError):
            return "exited"
        if not ready:
            continue
        line = proc.stdout.readline()
        if not line:              # EOF: the CLI is gone, holding stdin open cannot revive it
            return "exited"
        line = line.strip()
        if not line:
            continue
        if events:
            events.write(line + "\n")
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            print(line, file=sys.stderr)
            continue
        if evt.get("event") == "result":
            # A remotely driven turn. Newest wins, so the envelope reflects the real end.
            on_result(evt.get("result", {}))
            print("agy_session: remote-driven turn completed", file=sys.stderr)


def write_status(events_out: str | None, **fields) -> None:
    """The run marker a monitor reads to tell "thinking" from "gone".

    agy_host.sh writes this for runs it launches, which left every DIRECT caller of this
    driver invisible: the global monitor reported `BLIND native_marker: .devloop/native
    exists but session.status does not` for exactly that reason -- a session was hosted
    here and its state was unknowable. The driver owns the session, so the driver writes
    the marker; the host's copy still agrees with it.

    Staleness alone cannot stand in for this: a manager inside a long run_command is
    silent for minutes (measured: 128s) and reads as dead without it.
    """
    if not events_out:
        return
    try:
        path = Path(events_out).parent / "session.status"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"events": events_out, **fields}) + "\n")
    except Exception:
        pass        # a marker that cannot be written must not take the run down with it


def session_argv(model: str | None = None, effort: str | None = None,
                 yolo: bool = False, remote_control: bool = False) -> list[str]:
    """The held-session command line. Factored out so both sides can be asserted:
    a flag that is always present is not a flag, it is a constant.

    `--remote-control` ("Create a remote connection for the CLI session on start up")
    is what puts THIS session in the Remote Control list at antigravity.google.com.
    Measured 2026-09-20, agy 1.2.6, two probes differing only in this flag:
      with    -> server.go:3565 "Remote control enabled, starting connection",
                 remote_control_v2.go:2037 "Connection status: Connected",
                 and on exit server.go:3650 "Deleted session instance <id>-v2"
      without -> server.go:3768 "[RemoteControl] Session toggle is off, staying
                 disconnected" and an EMPTY proxyServerURL
    The connection lives exactly as long as the process, which is the second half of
    why a single-turn `agy -p` run is invisible: it is never registered, and it would
    have exited anyway. The `remote-control serve` DAEMON is a different object -- it
    registers the MACHINE (an instance name), not the sessions running on it, so a
    healthy daemon is not evidence that any session can be seen or driven.
    """
    argv = ["agy", "--input-format", "stream-json", "--output-format", "stream-json",
            "--print-timeout", "0"]
    if model:
        argv += ["--model", model]
    if effort:
        argv += ["--effort", effort]
    if yolo:
        argv.append("--dangerously-skip-permissions")
    if remote_control:
        argv.append("--remote-control")
    argv.append("-p=")  # MUST be the attached-empty form; a bare -p eats the next flag
    return argv


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt-file", required=True, help="file holding the manager prompt (turn 1)")
    ap.add_argument("--lanes", help="lanes.json; all lane ids are what we poll for")
    ap.add_argument("--run-root", default=".", help="repo root holding .devloop/native/")
    ap.add_argument("--jobs-root", help="job.py root; when set, a lane is finished when its "
                                        "SHELL-written receipt says so, not when a report file appears")
    ap.add_argument("--model")
    ap.add_argument("--effort")
    ap.add_argument("--poll-max", type=int, default=8, help="follow-up turns allowed after turn 1")
    ap.add_argument("--envelope-out", help="write the final result object here")
    ap.add_argument("--events-out", help="tee every raw NDJSON event here for monitors "
                                        "(agy_monitor.py tails this; a tmux pane watches it)")
    ap.add_argument("--yolo", action="store_true")
    ap.add_argument("--hold-file", help="after the local work ends, keep the session alive and "
                                       "streaming until THIS path exists. Operator stop control; "
                                       "it ends the process, it does not certify the work")
    ap.add_argument("--hold-max-s", type=float, default=3600.0,
                    help="wall-clock ceiling on --hold-file, so a stop file nobody writes cannot "
                         "hold a session open forever")
    ap.add_argument("--auto-continue", type=int, default=0,
                    help="answer up to N turn-ends with a pre-approved continue message. "
                         "A manager that ends its turn with a question otherwise stalls "
                         "forever in an unattended run (measured: /teamwork-preview stops "
                         "to ask for draft approval)")
    ap.add_argument("--done-cmd", help="shell command checked after every turn; exit 0 ends "
                    "--auto-continue. Run by the driver, never by the model")
    ap.add_argument("--remote-control", action="store_true",
                    help="register this session with Antigravity Remote Control so it can be "
                         "watched and driven from antigravity.google.com; the connection lasts "
                         "exactly as long as this process")
    ap.add_argument("--teamwork", action="store_true",
                    help="supervise an Antigravity /teamwork-preview multi-agent session")
    ap.add_argument("--quota-wait-max-s", type=float, default=300.0,
                    help="a quota that resets within this many seconds is waited out and the "
                         "session continues; a later reset ends it with rc 75 (default 300)")
    ap.add_argument("--relay-file", help="the monitor's relay file; when its content changes, the "
                    "next injected turn tells the manager to re-read it")
    a = ap.parse_args()

    argv = session_argv(a.model, a.effort, a.yolo, a.remote_control)

    native_dir = Path(a.run_root) / ".devloop" / "native"
    jobs_dir = Path(a.jobs_root) if a.jobs_root else None
    lane_ids = session_lane_ids(Path(a.lanes)) if a.lanes else []
    # WHAT THE STRAY GUARD ACTUALLY ASKS: did the manager edit the base tree INSTEAD OF a
    # lane worktree? That question presupposes worktrees. A lane-less session (one manager
    # doing the work itself, e.g. an AGY teamwork run) has none, so "outside every lane
    # worktree" is true of every edit it makes by construction -- including the edits that
    # ARE the run. Failing closed there measures the wrong property (SKILL.md 7) and kills
    # every such run at its first real change.
    #
    # This is a SCOPE, not an off switch: nothing at runtime can set it, it follows from the
    # lane file, and the lane-less path stays LOUD -- every base edit is still computed and
    # named on every turn, prefixed UNGATED, so a monitor and an operator see the tree moving.
    # What is lost is real and is not papered over: a lane-less run has no worktree gate, and
    # its changes must be reviewed before they are trusted.
    guard_gates = bool(lane_ids) or bool(a.teamwork)

    # Baseline BEFORE turn 1, so inherited dirt is never attributed to the manager.
    allowed = BASE_TREE_ALWAYS_ALLOWED + (
        (worktree_root_of(Path(a.lanes)),) if a.lanes else (".worktrees/",))
    # No off switch: a guard that can be turned off is turned off by whatever is failing it.
    base_before = base_tree_state(Path(a.run_root))
    if base_before is None:
        print("agy_session: base-tree guard OFF -- git could not read %s, so a manager editing "
              "the base tree instead of a lane worktree will NOT be detected" % a.run_root,
              file=sys.stderr)
    strays: list[str] = []
    stray_warned: set[str] = set()
    subagent_steps: set = set()

    events = None
    if a.events_out:
        Path(a.events_out).parent.mkdir(parents=True, exist_ok=True)
        # line-buffered: a monitor tailing this must see each event as it happens, not at exit
        events = open(a.events_out, "w", buffering=1)

    try:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1,
                                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except FileNotFoundError:
        print("agy_session: agy not installed", file=sys.stderr)
        return 4

    write_status(a.events_out, state="running", pid=proc.pid, started_at=time.time(),
                 remote_control=bool(a.remote_control), cwd=str(Path(a.run_root).resolve()))

    last_result: dict | None = None
    turns_sent = 1
    auto_left = max(0, a.auto_continue)
    relay = RelayWatch(a.relay_file)
    quota = None   # agy's RESOURCE_EXHAUSTED line, kept verbatim: it carries the reset time
    stuck = None   # set when the stop condition fails identically CONVERGE_LIMIT times running
    last_why, same_why = None, 0
    ended_why = None   # why auto-continue stopped, for the pre-hold line
    teamwork_harvested = False
    try:
        proc.stdin.write(ndjson_user(Path(a.prompt_file).read_text()))
        proc.stdin.flush()

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            if events:
                # tee BEFORE parsing: a monitor must see the warnings and bare-text errors
                # too, which are exactly the lines json.loads throws away
                events.write(line + "\n")
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                print(line, file=sys.stderr)  # warnings/errors arrive as bare text
                if "RESOURCE_EXHAUSTED" in line and quota is None:
                    quota = line[:400]
                continue

            kind = evt.get("event")
            if kind == "init":
                init = evt.get("init", {})
                print(f"agy_session: init conversation={evt.get('conversation_id')} "
                      f"cwd={init.get('cwd')} "
                      f"tools={len(init.get('tools', []))} mode={init.get('permission_mode')}"
                      f"{' remote-control=on' if a.remote_control else ''}",
                      file=sys.stderr)
                continue
            if kind == "step_update":
                u = evt.get("step_update", {})
                if u.get("step_type") == "subagent" and u.get("step_index") is not None:
                    subagent_steps.add(u["step_index"])
                if u.get("state") == "DONE" and u.get("step_type") in ("tool", "subagent"):
                    print(f"agy_session: {u.get('step_type')} {u.get('tool_name')}", file=sys.stderr)
                continue
            if kind != "result":
                continue

            last_result = evt.get("result", {})
            if quota is None:
                quota = quota_in_result(last_result)
            if base_before is not None:
                strays = stray_base_edits(base_before, base_tree_state(Path(a.run_root)), allowed)
            fresh = [x for x in strays if x not in stray_warned]
            outstanding = missing_reports(native_dir, lane_ids, jobs_dir)
            if fresh:
                stray_warned.update(fresh)
                if guard_gates:
                    print("agy_session: BASE TREE EDITED outside any lane worktree: %s -- failing closed"
                          % ", ".join(fresh), file=sys.stderr)
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except Exception:
                        proc.kill()
                    return 6
                print("agy_session: UNGATED base-tree change (%d lane(s), so no worktree gate "
                      "applies): %s -- review before trusting this run"
                      % (len(lane_ids), ", ".join(fresh)), file=sys.stderr)

            if getattr(a, "teamwork", False):
                import adapters
                violations = adapters.validate_agents_metadata_layout(Path(a.run_root))
                if violations:
                    print("agy_session: BASE TREE LEAKAGE: unauthorized source/executable files planted in .agents/: %s"
                          % ", ".join(violations), file=sys.stderr)
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except Exception:
                        proc.kill()
                    return 6
                tw_state = scan_teamwork_state(Path(a.run_root) / ".agents", time.time())
                if tw_state["terminal_handoff"]:
                    print(f"agy_session: terminal teamwork handoff detected: {tw_state['terminal_handoff']}", file=sys.stderr)
                    harvest_teamwork_receipt(a.run_root, tw_state["terminal_handoff"], Path(a.prompt_file))
                    teamwork_harvested = True
                    break
                if not tw_state["live"]:
                    # NOTHING LIVE is not the same as FINISHED. /teamwork-preview's first turn
                    # ends by asking "does this draft look good to run?" -- before any agent is
                    # live. Breaking here ended every unattended teamwork run at that question
                    # (measured: 1 invoke_subagent in 100 turns). Fall through to the
                    # auto-continue decision below, which answers it and still stops on the
                    # EXTERNAL done-cmd or an exhausted budget.
                    pass
                elif turns_sent > a.poll_max:
                    break
                else:
                    print(f"agy_session: teamwork in progress ({len(tw_state['agents'])} agent(s)) — polling turn {turns_sent}", file=sys.stderr)
                    proc.stdin.write(ndjson_user(
                        f"Teamwork subagents are still in progress. Active agents: {', '.join(tw_state['agents'].keys())}. "
                        "Continue monitoring until auditor handoff is produced, then report DONE."
                        + relay.note()))
                    proc.stdin.flush()
                    turns_sent += 1
                    continue

            if not outstanding:
                ok, why = done_check(a.done_cmd, a.run_root)
                if auto_left > 0 and not (a.hold_file and Path(a.hold_file).exists()) and not ok:
                    fatal = fatal_result(last_result, quota, a.quota_wait_max_s)
                    if fatal:
                        print(f"agy_session: turn {turns_sent} ended on something no continue can "
                              f"fix ({fatal}); not auto-continuing", file=sys.stderr)
                        ended_why = fatal
                        break
                    same_why = same_why + 1 if (a.done_cmd and why == last_why) else 1
                    last_why = why
                    if same_why >= CONVERGE_LIMIT:
                        stuck = why
                        print(f"agy_session: NOT CONVERGING -- the stop condition failed with the "
                              f"same output {same_why} turn-ends in a row; stopping instead of "
                              f"spending more turns", file=sys.stderr)
                        ended_why = "not converging"
                        break
                    if quota:
                        wait_s = (reset_seconds(quota) or 0) + 2
                        print(f"agy_session: turn {turns_sent} hit a short quota ({quota[:160]}); "
                              f"waiting {wait_s}s, then continuing", file=sys.stderr)
                        time.sleep(wait_s)
                        quota = None   # waited out: a later turn's quota is judged on its own
                    auto_left -= 1
                    print(f"agy_session: turn {turns_sent} ended with work outstanding by "
                          f"{'--done-cmd' if a.done_cmd else 'default'}; auto-continue "
                          f"({auto_left} left)", file=sys.stderr)
                    feedback = (f"\n\nYour stop condition still FAILS. It is `{a.done_cmd}`, run by "
                                f"the driver, and it printed:\n{why}\nClose exactly these gaps. "
                                f"Saying the work is done does not change the check."
                                if a.done_cmd else "")
                    proc.stdin.write(ndjson_user(CONTINUE_MESSAGE + feedback + relay.note()))
                    proc.stdin.flush()
                    turns_sent += 1
                    continue
                break
            if turns_sent > a.poll_max:
                break
            # The manager's turn ended but native lanes have not reported. In a held
            # session the process is still alive, so ask it to wait rather than
            # accepting a turn-end as the run's end.
            print(f"agy_session: turn {turns_sent} ended, {len(outstanding)} lane(s) "
                  f"unreported {outstanding} — polling", file=sys.stderr)
            short = undispatched(subagent_steps, lane_ids)
            if short:
                print(f"agy_session: {len(subagent_steps)} subagent(s) dispatched for "
                      f"{len(lane_ids)} lane(s) — {short} never started", file=sys.stderr)
            proc.stdin.write(ndjson_user(
                poll_message(native_dir, outstanding, subagent_steps, lane_ids) + relay.note()))
            proc.stdin.flush()
            turns_sent += 1

        if a.hold_file:
            # Say which of the two states this is. "local work done" used to be printed
            # unconditionally, so an agy that died on a quota 429 after two turns was announced
            # as finished (measured 2026-09-24: 11 nested instances, 0 deliverables, rc 0).
            met = (not a.done_cmd) or done_by(a.done_cmd, a.run_root)
            state = ("local work done" if met else
                     "stop condition NOT met (%s)" % (ended_why or
                                                      ("agy exited" if proc.poll() is not None
                                                       else "turn budget spent")))
            print(f"agy_session: {state} after {turns_sent} turn(s); HOLDING the session "
                  f"open (stop file: {a.hold_file}, ceiling {a.hold_max_s:.0f}s). "
                  f"{'It is attachable from Remote Control.' if a.remote_control else 'NOT registered with Remote Control -- pass --remote-control for that.'}",
                  file=sys.stderr)

            def _newest(r: dict) -> None:
                nonlocal last_result
                last_result = r

            why = hold_open(proc, events, _newest, Path(a.hold_file), a.hold_max_s)
            print(f"agy_session: hold ended ({why})", file=sys.stderr)
    finally:
        if events:
            try:
                events.close()
            except Exception:
                pass
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=60)
        except Exception:
            proc.kill()
        write_status(a.events_out, state="finished", pid=proc.pid, ended_at=time.time(),
                     remote_control=bool(a.remote_control))

    if last_result is None:
        # No terminal envelope at all. Measured: a stream whose events are all unknown
        # produces exactly this. Never report it as success.
        print("agy_session: the session produced NO result event — nothing ran", file=sys.stderr)
        return 3

    text = json.dumps(last_result)
    if a.envelope_out:
        Path(a.envelope_out).write_text(text + "\n")
    print(text)

    # The EXTERNAL stop condition decides the exit code, whatever ended the session. Without
    # this a lane-less run that produced any result event returned 0 -- dead reported as done.
    if a.done_cmd and not done_by(a.done_cmd, a.run_root):
        if quota:
            print("agy_session: --done-cmd still FAILS and agy hit its quota -- retry after the "
                  "reset: %s" % quota, file=sys.stderr)
            return 75
        if stuck is not None:
            print("agy_session: --done-cmd still FAILS and the run stopped converging; last "
                  "output: %s" % stuck[-400:], file=sys.stderr)
            return 8
        print("agy_session: --done-cmd still FAILS -- the session ended without doing the work",
              file=sys.stderr)
        return 7

    if base_before is not None:
        strays = stray_base_edits(base_before, base_tree_state(Path(a.run_root)), allowed)
        if strays:
            print("agy_session: run ended with the BASE TREE dirty outside every lane "
                  "worktree: %s -- these were never gated, because lane gates read "
                  "worktrees. Review and revert them before trusting this run."
                  % ", ".join(strays), file=sys.stderr)
            if guard_gates:
                return 6
            # Lane-less: these edits are the run's output, not a stray. Still named above --
            # reported, never swallowed -- but they are not an error on their own.
            print("agy_session: (lane-less run: the changes above are its OUTPUT, and carry no "
                  "worktree gate. The repo's own gates are what must accept them.)",
                  file=sys.stderr)

    if getattr(a, "teamwork", False):
        import adapters
        violations = adapters.validate_agents_metadata_layout(Path(a.run_root))
        if violations:
            print("agy_session: BASE TREE LEAKAGE: unauthorized source/executable files planted in .agents/: %s"
                  % ", ".join(violations), file=sys.stderr)
            return 6
        tw_state = scan_teamwork_state(Path(a.run_root) / ".agents", time.time())
        if not tw_state["terminal_handoff"]:
            print("agy_session: poll budget spent; teamwork finished without terminal handoff", file=sys.stderr)
            return 5
        if not teamwork_harvested:
            harvest_teamwork_receipt(a.run_root, tw_state["terminal_handoff"], Path(a.prompt_file))
        return 0

    still = missing_reports(native_dir, lane_ids, jobs_dir)
    if still:
        print(f"agy_session: poll budget spent; still unreported: {', '.join(still)}", file=sys.stderr)
        return 5
    return 0


if __name__ == "__main__":
    rc = main()
    # Record the real exit status beside the stream. Under --tmux this process is a pane and
    # its exit code is not observable by the launching shell, which previously fabricated one.
    try:
        import argparse as _a
        _p = _a.ArgumentParser(add_help=False)
        _p.add_argument("--events-out")
        _known, _ = _p.parse_known_args()
        if _known.events_out:
            Path(_known.events_out).parent.joinpath("session.rc").write_text(f"{rc}\n")
    except Exception:
        pass
    sys.exit(rc)
