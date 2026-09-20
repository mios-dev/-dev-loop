# The Global Reporting Monitor

One monitor, not one of many. `skills/dev-loop/scripts/global_monitor.py` runs on a **30-second
tick**, enumerates **agents from every harness**, and runs under **whichever harness spawned as
the manager**. Its subject is **staleness**: agents that have gone stale, and references that
have gone stale.

It is a **`monitor` worker** in `devloop_serverd.py`'s sense — a short periodic poller the
supervisor runs on an interval — and it contains no supervision loop of its own.

---

## 1. Registering it

```json
{"schema": "serverd.workers.v1", "workers": [
  {"id": "global", "kind": "monitor",
   "argv": ["python3", "skills/dev-loop/scripts/global_monitor.py",
            "--once", "--supervised", "--quiet",
            "--root", ".", "--report-out", ".devloop/global-monitor.json"],
   "cwd": ".", "interval_s": 30, "timeout_s": 25, "max_failures": 5}]}
```

`timeout_s` **must** be `<= interval_s` — the supervisor refuses otherwise, because monitors run
inside the tick and one allowed to outlast its own interval stalls the supervision of every
manager beside it. The monitor bounds its own work below that (`--deadline-s`, default 25s), so
the supervisor's kill is a backstop rather than the mechanism. Measured on this repository,
three runs each: **0.15s** with `--no-cli`, **1.57–1.80s** with every harness CLI probe enabled
(the spread is the probes, not the scan).

**Pass `--supervised`.** Without it a persistently stale fleet exits non-zero every tick, hits
`max_failures`, and is marked `failed_permanent` — killing the monitor that was doing its job,
and, if it is the only live worker, ending the supervisor with it. `--supervised` keeps findings
in the report and reserves the non-zero exit for `blind` alone.

Nothing in the registration names a harness. The monitor works identically whether the L0
manager is Antigravity, Claude Code, or anything else — and identically again when run standalone
by hand, which is the same single-tick program either way. `--once` is accepted and explicit:
one tick is the *only* mode, because the supervisor owns the interval and this program must
never grow a loop of its own.

### What "a 30-second tick" honestly means

The supervisor is single-threaded: `tick()` calls a **blocking** `subprocess.run(...,
timeout=timeout_s)` inline and sets `next_run_at = time.time() + interval_s` **after** the run
returns. There is no thread, pool or queue anywhere in it. Three consequences, all measured:

* runs **never overlap, are never queued and are never skipped** — the next one simply starts
  later;
* `interval_s` is a **gap after completion, not a wall-clock period**. A monitor sleeping 2s at
  `interval_s=3` started every **5.015s** (duration + interval), and the daemon's own
  `--interval` quantises that further. So 30s means *"at least 30s after the previous scan
  ended, plus up to one daemon tick"*. **Claiming an exact 30s cadence is an overclaim** and
  neither the code nor this page makes it.
* a slow monitor **stalls the supervision of everything beside it** for its duration — which is
  why the scan is bounded from the inside by `--deadline-s` rather than left to the kill.

The side the supervisor does *not* control — a human, a second supervisor, or a harness workflow
running this by hand at the same moment — is covered by publishing `--report-out` through a
**pid-unique** temporary name plus `rename(2)`, which is atomic on one filesystem. A reader sees
the old report or the new one, never a torn one. Six concurrent publishes to one path are a
control in the suite.

---

## 2. Three outcomes, three exit codes

`outcome` is the top-level answer and the first word of the headline. It is **three-valued on
purpose** — a two-valued field cannot distinguish a clean fleet from an unobserved one.

| `outcome` | Meaning | Exit |
|---|---|---|
| `CLEAN` | agents were enumerated, coverage complete, nothing stale, suspected or undetermined | **0** |
| `STALE` | observed, and something is stale — listed in `agents.stale_records` / `suspected_records` / `references` | **5** |
| `UNOBSERVABLE` | **could not observe** — nothing could enumerate agents, a source went blind, or an enumerated agent's state could not be determined | **3** |

`verdict` keeps the finer five-value lattice underneath, so collapsing to three loses nothing:

| Verdict | Meaning | → outcome |
|---|---|---|
| `blind` | **no source could enumerate agents** — the instrument is not measuring | `UNOBSERVABLE` |
| `stale` | ≥1 agent measured stale, or the reference scan found stale references | `STALE` |
| `partial` | ≥1 source blind, **or** ≥1 enumerated agent `unknown`: coverage incomplete | `UNOBSERVABLE` |
| `suspect` | full coverage, nothing measured-stale, ≥1 silence-based suspicion | `STALE` |
| `clean` | full coverage, no findings, nothing suspected, nothing undetermined | `CLEAN` |

Worst axis wins. **`clean` is reachable only from complete coverage with zero findings**, and an
unrecognised verdict maps to `UNOBSERVABLE` — degrading pessimistically, never into `CLEAN`.

An agent that was **enumerated but not determined** (`state: "unknown"`) caps the verdict at
`partial`. Counting it as "not stale" would let `CLEAN` mean *"I found five agents and can tell
you nothing about any of them"* — the headline failure in miniature.

### The exit code under a supervisor is deliberately different

`--supervised` returns **0 for `CLEAN` and `STALE` alike** and keeps **3** for `blind` only.
Findings must not ride the exit code there: a monitor that exits non-zero for *noticing a stale
agent* is one the supervisor marks `failing` and, after `max_failures` ticks,
`failed_permanent` — so a fleet that stays stale would kill the monitor reporting it. `blind` is
the exception because escalating an instrument that has enumerated nothing for `max_failures`
consecutive ticks is the correct outcome. A gate that wants one code for "anything but clean"
uses `--strict` (exit 4).

The headline is designed for a **truncated** reader: the supervisor keeps only
`_tail(stdout, 400)` of a monitor run (measured: 5000 chars in, 415 out), so the first line puts
the outcome and every count *before* the prose, and `--quiet` prints it plus the path to the
full report.

### "Clean" and "could not observe" are different values

This is the property the whole file is built around. A naive monitor whose run directory is
missing emits *"0 stale agents, all healthy"* — a sentence indistinguishable from a genuinely
clean fleet. So:

* every source reports `observed | blind | not_applicable` **with a reason**, and blind sources
  are listed by name in `coverage.blind_sources`;
* a missing `.devloop` directory is **blind**, never an empty fleet — you cannot tell "no runs
  ever happened" from "you were pointed at the wrong root";
* an empty fleet under complete coverage says so explicitly ("the fleet is EMPTY — every source
  answered and found no agent, which is not the same as having failed to look");
* `blind` is judged on **enumerating sources only** (`devloop_runs`, `serverd`,
  `native_marker`, `harness_cli`). `process_scan` reads `/proc` and therefore answers on any
  Linux box whatever the tree looks like; counting it as an observation made `blind` almost
  unreachable. The first version of the rule did exactly that and the controls refused it.

---

## 3. Staleness: silence is not evidence of death

`agy_monitor.py` carries a measured finding this monitor must not regress: on a real multi-lane
run a manager went **128 seconds silent while a gate executed**, and a time-based staleness
heuristic flipped the verdict to stalled on a perfectly healthy process.

So **a live pid is never stale, for any duration of silence.** The explicit marker preferred
over silence is *liveness* — `job.py`'s `/proc`-based, zombie-aware, pid-reuse-guarded predicate
— plus the shell-written receipt. Staleness is asserted only from a positive fact:

| Basis | The fact that proves it | Confidence |
|---|---|---|
| `receipt` | `worker-<id>.exit` = **125** (never started / no receipt recovered), or `job.py` reports `forged` | measured |
| `liveness` | `job.py` reports `lost`: no receipt **and** the pid is gone | measured |
| `marker` | a run marker says `running` while the pid it names is dead | measured |
| `budget` | the process is alive but has outlived **its own declared** budget | measured |
| `supervisor` | the supervisor recorded the worker failed | measured |
| `silence` | nothing written for `--silence-after-s` — **only where liveness cannot be measured at all** | **weak** |

Silence-based findings are counted separately as `suspected_stale` and produce the distinct
verdict **`suspect`**, never `stale`. They cannot fire for a lane whose liveness *is* measurable.
`--count-silence` promotes them for a caller that wants it.

The default `--silence-after-s` is **900s** — an order of magnitude above the measured 128s quiet
period, and used only where there is no pid left to ask.

`worker-<id>.exit` = **124** (the outer wall-clock timeout fired) is **finished, not stale**: the
lane terminated. That is a failure, and a different one.

---

## 4. What is actually observable, per harness (measured)

The **harness-agnostic backbone** is the dev loop's own run layout
(`references/run-directory.md`), which exists regardless of which harness ran the lane:
`.devloop/run-*/lane-<id>.json` names the lane **and its harness**, `worker-<id>.exit` is the
receipt the shell writes, `jobs/<id>/` is the durable job record, `report-<id>.json` is the
lane's own claim. Per-harness CLI queries are **optional enrichment**; each degrades on its own
and none is required.

| Harness | CLI | Live-agent query | Confidence |
|---|---|---|---|
| Claude Code | `claude` | **`claude agents --json`** — active interactive *and* background sessions as JSON (`pid`, `cwd`, `kind`, `startedAt`, `sessionId`, `status`); explicitly does not require a TTY | **verified** |
| OpenCode | `opencode` | **`opencode session list`** — runs headlessly. A session *listing*, not a liveness probe | **verified** |
| Codex | `codex` | **none usable.** `codex agents` browses sessions on the shared local app-server daemon but is a TUI: run non-interactively it prints `ERROR: stdin is not a terminal` | **verified** |
| Copilot | `copilot` | **none.** `copilot sessions` has exactly one subcommand, `import`; `copilot sessions list` → `unrecognized subcommand` | **verified** |
| Antigravity | `agy` | **none via CLI.** No session/conversation listing subcommand (`agents` lists agent *types*). Its state dir holds conversation artifacts, not liveness — a `presence/*.lock` tested **free** under a non-blocking `flock` with no process holding it, so the file's existence is not liveness. The dev loop's **run marker** is the signal instead | **verified** |
| Gemini CLI | `gemini` | `--list-sessions` exists but refuses before listing without a configured auth method, so it is not a dependable probe. Whether it lists *live* or only *saved* sessions is **unmeasured** | **unverified** |
| Cursor | `agent` | not installed here | **verified** |

**Four of six installed harnesses expose no usable live-agent query.** That is a legitimate
answer and the monitor reports it as *not observable* — it is never silently rendered as "no
agents". Any description promising per-harness live visibility across the board is an overclaim.

A cheap cross-check, `process_scan`, reads `/proc` for live harness binaries. It **cannot**
attribute a process to a dev-loop lane and never claims to; its job is to make "a harness is
running something this monitor cannot account for" visible instead of invisible.

---

## 5. The reference half

Delegated to `stale_refs.py`, which this monitor does not own and does not reimplement.

* scanner absent → `references.status = blind`, `stale_refs = null`, **never 0**;
* scanner reports its own `could_not_run` → **blind**, and its `counts.stale = 0` is *not*
  adopted as a clean answer;
* unparseable report → **blind**. A monitor that cannot parse a report has not measured a clean
  one.

"No stale references" is a lie when you did not scan. Override the invocation with `--refs-cmd`.

The default invocation is `stale_refs.py --root <root> --monitor --format json`. `--monitor` is
that scanner's own supervisor mode; **it writes nothing** — measured, by checksumming every path
and mtime in a fixture tree before and after a tick (unchanged). Ledger writes are `--adopt` /
`--accept`, which the monitor never passes. Verified against the real scanner in both
directions: its `could_not_run` verdict read as **blind** (not as zero), and a tree with two
genuinely stale citations read as `STALE` with `refs=2`.

---

## 6. Controls

`tests/test_global_monitor.py` — **193 controls**, every one two-sided (a positive case, and a
negative case proving the same check *can* fail). The brief's five cases exist under their own
names: `test_a_stale_agent_is_detected`, `test_a_healthy_fleet_reports_clean`,
`test_an_unobservable_environment_reports_unobservable_and_not_clean`,
`test_a_128_second_silent_agent_is_not_reported_stale`,
`test_reference_scan_absent_reports_unavailable_not_none_found`.

**Four mutation probes** confirmed the suite is live — each was applied to the monitor, the
suite was run, and the file was restored:

| Mutation | Controls that failed |
|---|---|
| `blind` made unreachable (`if not enum_observed:` → `if False:`) | **5** |
| the receipt rule removed, so a `125` reads as a normal return | **15** |
| the 128-second rule removed, so a live pid goes stale on silence | **10** |
| an unscanned reference axis reported as a clean `0` | **3** |

Mutation 2 also exposed a defect **in the controls themselves**: the file raised `IndexError` on
the very failure it exists to catch, aborting the run and reporting one crash instead of ninety
results. Indexing is now defensive and `main()` records a raising control as a failure rather
than letting it silence the rest.

A **flaky control** was caught the same way and fixed: `test_a_live_pid_is_never_stale` slept a
fixed 2s for a detached job to start, and under the load of a full `validate.sh` pass the
wrapper had not yet written `pid`/`pidstart` — so `job.status` read `absent`, the lane fell
through to the silence branch, and the control accused a healthy agent. It now polls until the
job is genuinely `running`. Afterwards: four consecutive `validate.sh` passes and four
concurrent suite runs, all green.

The suite also exercises the registration contract for real: it registers the monitor with
`devloop_serverd.py` at `interval_s: 30, timeout_s: 25`, asserts the supervisor records it `ok`
with `rc 0` inside the tick, asserts that the **same tick without `--supervised` exits non-zero**
(so the flag is load-bearing rather than decorative), and asserts that `timeout_s > interval_s`
is **refused** — so the tick budget is a constraint, not a comment.
