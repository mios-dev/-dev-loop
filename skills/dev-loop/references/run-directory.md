# The Run Directory — on-disk contract of a dev-loop run

Until now this layout existed only in `scripts/devloop.sh` source. It is the contract every
observer depends on: `/watch` reads it, `/postmortem`-style analysis reads it, and the merge gate
writes it. Nothing here is optional decoration — each file is a *receipt*, written by the shell,
that lets a later reader decide what actually happened without trusting a model's prose.

---

## 1. Location and naming

```
<repo>/.devloop/run-<YYYYmmdd-HHMMSS>/
```

Created by `devloop.sh:29` (`RUN="$ROOT/.devloop/run-$(date +%Y%m%d-%H%M%S)"`). The launcher adds
`.devloop/run-*/` and the worktree root to `.git/info/exclude`, so run artefacts are never staged.
The *newest* run is `ls -1d .devloop/run-* | tail -1` — the timestamped name sorts lexically.

---

## 2. Files

| Path | Written by | Meaning |
|---|---|---|
| `lanes.normalized.json` | `adapters.py validate` | the whole plan after schema validation — the authoritative lane list |
| `waves.txt` | `adapters.py waves` | dependency-ordered execution waves, one wave per line |
| `lane-<id>.json` | `adapters.py lane` | one lane's contract: id, objective, `owned_paths`, harness, `positive_cmd`, `negative_control_cmd`, `negative_expect`, `full_gate_cmd`, `depends_on`, caps |
| `report-<id>.json` | **the lane's model** | the `devloop_report` envelope (SKILL §13). `.status` ∈ `done · partial · blocked · converged_stuck · budget · halted`. **A claim, not evidence.** |
| `worker-<id>.exit` | **the shell** | the receipt. `devloop.sh:62` appends `; echo $? > worker-<id>.exit` to the lane command |
| `worker-<id>.log` | the lane's harness | combined stdout/stderr of the lane worker; job `out`/`err` are appended on reap |
| `pos-<id>.log` | `adapters.py gate` | positive control output |
| `neg-<id>.log` | `adapters.py gate` | negative control output — must show the seeded defect **caught** |
| `mut-<id>.log` | `adapters.py gate` | mutation / tree-restore probe output |
| `full-<id>.log` | `adapters.py gate` | full gate suite output |
| `lane-<id>.patch` | `devloop.sh` / gate | the lane's diff, parked when it has no report or fails the gate — nothing is lost on rejection |
| `base-tree-before.json` | `devloop.sh:46` | base-tree snapshot taken before any merge |
| `jobs/<id>/` | `job.py` | the durable job directory (§4) |
| `status` | `devloop.sh:210` | the run's rolling exit status |

The launcher refuses to start when `git status --porcelain` is non-empty (`devloop.sh:45`): a
dirty base makes the before/after snapshot meaningless.

---

## 3. Exit-code vocabulary of `worker-<id>.exit`

| Value | Meaning |
|---|---|
| `0` | the lane command returned cleanly |
| non-zero, general | the lane command failed with that code |
| `124` | **timeout** — the outer wall-clock `timeout` fired; `devloop.sh:140` writes it when a job is done but left no receipt of its own |
| `125` | **never started / no receipt recovered** — written at `devloop.sh:72`, `:94`, `:127` and `:148` when dispatch failed, the wait fell through, or the lane ended with no receipt at all |
| *absent* | **nothing has returned yet.** Not "running" and not "done" — the only honest reading is "unknown"; check job liveness (§4) |

**The rule that follows from this table:** a lane is done only when `worker-<id>.exit` is `0`.
`report-<id>.json` saying `done` with no receipt, or a non-zero one, is a contradiction, and the
receipt wins. Completion is an artefact the shell writes, never a sentence the model says.

---

## 4. `jobs/<id>/` — work that survives a turn boundary

`devloop.sh:31` puts the job root at `<RUN>/jobs`. Each job directory holds:

| File | Meaning |
|---|---|
| `meta.json` | what was spawned, and when |
| `pid`, `pidstart` | the wrapper's pid and its start time, for pid-reuse detection |
| `out`, `err` | the job's streams (appended into `worker-<id>.log` when the lane is reaped) |
| `done.json` | `{"rc":…,"finished_at":…,"pid":…}` — written **before** `exit` |
| `exit` | the receipt |

**Ordering is the whole contract:** `done.json` is renamed into place *before* `exit` is, and both
are tmp+rename on one filesystem. So the existence of `exit` implies every other artefact is
complete, and a reader never sees a partial receipt.

Query it, never guess:

```sh
python3 <skills dir>/dev-loop/scripts/job.py status --root <RUN>/jobs --json
python3 <skills dir>/dev-loop/scripts/job.py wait   --root <RUN>/jobs --id <id> --budget 300 --interval 5
```

States: `absent | running | done | lost | forged`.
Exit codes: `0` ok · `1` usage/spawn error · `2` job failed or is not done · `3` lost/forged.

- **`lost`** — no receipt and the pid is gone: the wrapper was hard-killed, or the box rebooted.
  **Live grandchildren may remain.** Cleanup goes by *session id*, never by process group: after a
  wrapper died, `kill -- -<pid>` reported "No such process" while three descendants were alive,
  because `timeout` had put them in a new process group that still shared the session id.
- **`forged`** — a receipt the wrapper did not write, or pid reuse was detected. Untrusted; not done.

---

## 5. Antigravity-native runs (this section applies to AGY only)

`agy_host.sh` tees the manager session's raw NDJSON to
`${AGY_HOST_EVENTS:-<repo>/.devloop/native/session-events.ndjson}`, beside which it writes
`session.status` (`{"state":"running"|"finished"|"failed",…}`), `session.rc`, and, on completion,
`transcript.html`, `monitor-report.json` and `tasks.json`.

`agy_monitor.py <stream> --once` parses that stream into a JSON status whose `verdict` is one of
`working · in_progress · refused · vacuous · no_result · stalled · errored · no_stream`, and exits
`2` on `vacuous`, `no_result` or `stalled` — a run that claimed a result while doing nothing, or
that announced a background wait whose work died with the turn. `in_progress` is not a failure.
It **also** exits `2` with verdict `no_stream` when the file does not exist (measured: an absent
stream is not an empty run), so a caller must read the printed `verdict`, not the exit code alone.

**No other harness writes this stream.** A Claude Code, Codex, Copilot, Cursor or OpenCode lane
leaves only the files in §2, so step-level visibility is an AGY-only capability. Any description
promising per-step detail for every harness is an overclaim.

---

## 6. Reading a run correctly (the short version)

1. Lanes come from `lane-*.json`, not from memory of what was dispatched.
2. For each lane hold three things apart: the **claim** (`report-<id>.json`), the **receipt**
   (`worker-<id>.exit`), the **evidence** (`worker-<id>.log`, `pos-`/`neg-<id>.log`).
3. A lane is verified only if the positive control passed **and** the negative control shows the
   seeded defect caught with the expected signature (SKILL §6). A `neg-<id>.log` that is missing,
   or that shows a pass, means the check cannot fail — unverified, not done.
4. Waiting is always bounded. An exhausted budget is **partial** (SKILL §12), never done.
