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
            "--root", ".", "--quiet", "--report-out", ".devloop/global-monitor.json"],
   "cwd": ".", "interval_s": 30, "timeout_s": 25, "max_failures": 5}]}
```

`timeout_s` **must** be `<= interval_s` — the supervisor refuses otherwise, because monitors run
inside the tick and one allowed to outlast its own interval stalls the supervision of every
manager beside it. The monitor bounds its own work below that (`--deadline-s`, default 25s), so
the supervisor's kill is a backstop rather than the mechanism. Measured: **1.3s** with
`--no-cli`, **2.9s** with every harness CLI probe enabled, against a tree with three run
directories.

Nothing in the registration names a harness. The monitor works identically whether the L0
manager is Antigravity, Claude Code, or anything else.

---

## 2. Verdicts

| Verdict | Meaning | Exit |
|---|---|---|
| `blind` | **no source could enumerate agents** — the instrument is not measuring | **3** |
| `stale` | ≥1 agent measured stale, or the reference scan found stale references | 0 |
| `partial` | ≥1 source is blind: coverage is incomplete, so `clean` cannot be claimed | 0 |
| `suspect` | full coverage, nothing measured-stale, ≥1 silence-based suspicion | 0 |
| `clean` | full coverage, no findings, nothing suspected | 0 |

Worst axis wins. **`clean` is reachable only from complete coverage with zero findings.**

Findings live in the report, not in the exit code: a monitor that exits non-zero for *noticing a
stale agent* is one the supervisor marks `failing` and eventually kills for doing its job. Exit
**3** is reserved for `blind`, where escalation is correct — a monitor blind for `max_failures`
consecutive ticks genuinely is failed. Gates opt in with `--fail-on-stale` or `--strict`
(exit 4).

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

---

## 6. Controls

`tests/test_global_monitor.py` — every control is two-sided (a positive case, and a negative
case proving the same check *can* fail). Two mutation probes confirmed the suite is live:

1. making `blind` unreachable → 4 controls fail, including the headline one;
2. removing the 128-second rule so a live pid goes stale on silence → 4 controls fail.

The suite also exercises the registration contract for real: it registers the monitor with
`devloop_serverd.py` at `interval_s: 30, timeout_s: 25`, asserts the supervisor records it `ok`
with `rc 0` inside the tick, and asserts that `timeout_s > interval_s` is **refused** — so the
tick budget is a constraint, not a comment.
