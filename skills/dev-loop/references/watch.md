# `/watch` — Observing a Run Specification

`/watch` answers one question and refuses the rest: **what is the state of this run, right now,
according to the artefacts on disk?** It is read-only. It never dispatches a lane, never merges,
never kills a process. The run-directory contract it reads is `references/run-directory.md`.

---

## 1. Why the command exists

Between dispatch and the final envelope a multi-lane run is opaque. Without `/watch` the options
are `ls .devloop/run-*/` by hand or waiting for the envelope. Two consequences follow, and both
have been measured here:

1. **Nothing re-attaches to a run whose launching turn already ended.** Harnesses are turn-based;
   the agent that dispatched the lanes is gone. The run, however, is on disk, and `job.py` was
   built precisely so the work outlives the turn. `/watch` is the reader for that state.
2. **Step-level monitoring existed but had one consumer.** `agy_monitor.py` was written to close
   this gap and was then wired only into `agy_host.sh`'s tmux pane, so any host that is not
   Antigravity has no view at all.

---

## 2. The claim / receipt / evidence separation

Three things are reported per lane and never collapsed into one verdict:

| | Source | Authority |
|---|---|---|
| **Claim** | `report-<id>.json` `.status` | what the *model* says happened |
| **Receipt** | `worker-<id>.exit` | what the *shell* recorded: the lane command returned, with this code |
| **Evidence** | `worker-<id>.log`, `pos-<id>.log`, `neg-<id>.log` | what the commands actually printed |

**The core rule: never call a lane done from `report-<id>.json` when `worker-<id>.exit` is absent
or non-zero.** Completion is an artefact the shell writes, never a sentence the model says. This is
`job.py`'s founding doctrine, adopted after four incidents at three altitudes — a manager that
dispatched lanes and ended its turn "waiting"; a manager that backgrounded the launcher and killed
the lane tree with itself; a worker that announced three times it would wait for a background
command and measured nothing; and a report claiming success for a lane the orchestrator had
already recorded as partial.

A report that says `done` while the receipt is absent is not an edge case to smooth over. It is
*the* finding, and `/watch` exists to surface it.

Receipt vocabulary: `0` clean · `124` outer timeout · `125` never started / no receipt recovered ·
absent = nothing has returned yet (unknown, not running and not done).

---

## 3. Liveness, stated in the tool's own words

```sh
python3 <skills dir>/dev-loop/scripts/job.py status --root <RUN>/jobs --json
```

States: `absent | running | done | lost | forged`. Exit `0` ok · `1` usage/spawn error ·
`2` job failed or is not done · `3` lost/forged. Report the state literally — paraphrasing `lost`
as "probably finished" is how the original incidents happened.

- **`lost`** deserves its own line in the output: no receipt, pid gone — SIGKILLed wrapper or a
  rebooted box — and **live grandchildren are possible**. Cleanup is by *session id*, never by
  process group: `kill -- -<pid>` has reported "No such process" while three descendants were
  alive, because `timeout` had moved them into a new process group sharing the session id.
  `/watch` reports this; it does not kill.
- **`forged`** means a receipt the wrapper did not write, or pid reuse. Untrusted; not done.

---

## 4. Waiting is bounded or it does not happen

Only when the operator asks:

```sh
python3 <skills dir>/dev-loop/scripts/job.py wait --root <RUN>/jobs --id <id> --budget 300 --interval 5
```

`--id` takes a single job id; wait on the lane that gates the rest, or repeat per lane. Never
invent a poll loop, and never wait without a budget. **An exhausted budget is `partial`, never
`done`** (SKILL §§11–12): report the exact remaining work instead of trying one more thing.

---

## 5. The AGY-only branch

`agy_monitor.py`'s own argparse says its input is an *"NDJSON file written by `agy_session.py
--events-out`"*. Only an Antigravity-hosted run produces one (default
`.devloop/native/session-events.ndjson`, or `$AGY_HOST_EVENTS`). When it exists:

```sh
python3 <skills dir>/dev-loop/scripts/agy_monitor.py <stream> --once
```

It prints a JSON status and exits `2` on verdicts `vacuous`, `no_result` or `stalled` — a run that
claimed a result while doing nothing, or that announced a background wait whose work died with the
turn. `in_progress` is **not** a failure. Do not re-derive the verdict — but do not gate on the exit
code alone either: **`--once` also exits `2` with verdict `no_stream` when the file does not exist**
(measured; an absent stream is deliberately not reported as a clean empty run). Check the file
exists first, and read the printed `verdict` alongside the code.

For a lane or host running under any other harness there is no stream and therefore no step-level
detail. Say so. A description promising step-level visibility for every harness would be an
overclaim — and in this repo an overclaiming description is itself a defect, not a rounding error.

---

## 6. Output shape

```
LANE   report      receipt  job      age    evidence
L1     done        0        done     14m    pos ok / neg failed-as-expected
L2     done        (none)   running  14m    still executing — NOT done
L3     (no report) 125      lost     14m    never started; check for live grandchildren
```

Then the anomalies, named individually:

- reports claiming `done` without a clean receipt (the contradiction above);
- `lost` and `forged` jobs;
- lanes with no report (their diff is parked at `lane-<id>.patch`);
- stalls, and the AGY verdict when a stream existed.

Close with the single next action — wait on a named lane, read a named log, or escalate — and stop.

---

## 7. Two-sided verification still governs what "done" means

A lane passes only with a positive control **and** a negative control that proves the check can
fail (SKILL §6). When `/watch` calls a lane healthy it must cite both: `pos-<id>.log` showing the
suite pass, and `neg-<id>.log` showing the seeded defect caught with the expected signature. A
missing `neg-` log, or one showing a pass, means the lane's checks have never been shown capable
of failing — report it as **unverified**, whatever the report and the receipt say together.
