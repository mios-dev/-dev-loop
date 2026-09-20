---
name: gate-audit
description: Audit a repository's STANDING gates - a CI workflow, a Makefile/justfile recipe, a lint or gate script, a test directory - against the SKILL.md section 7 "Checks That Cannot Fail" taxonomy, then prove the survivors. `gate_audit.py` detects seven mechanically decidable rows (Skip-as-Pass, Swallowed Failure, Unanchored Allowlist, Count-Only/Raisable Ratchet, Timeout-as-Pass, Check-Without-Diff, Self-Comparison); six judgment rows are read by the agent, not the script. Every gate the audit CLEARS is then proved by planting the violation it claims to catch and requiring it to go red. Use before trusting a green pipeline, when inheriting a repo, or when a check has never failed.
argument-hint: "[ci-file|script|target|test-dir]"
allowed-tools: Read, Grep, Glob, Bash
---
# /gate-audit — is this gate capable of failing?

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use `<skills dir>/dev-loop/scripts/` (the shims in `shims/<harness>/` already do)._ Below, `$S` = that scripts directory.

A gate that cannot fail is worse than a missing one: everyone believes the rule is enforced. This
command audits the gate machinery **whether or not it changed** — the check that was already
vacuous before this branch existed.

**Not `/review`.** `/review` is staged oversight of a **diff**: what changed, its contracts,
security and suppression drift. `/gate-audit` ignores the diff and audits the **standing
machinery**. Different trigger, different output.

Read SKILL.md §7 before reporting — it is the taxonomy, and the row text is the source of truth.
The coverage map (detector vs judgment, with each detector's known limits) is
`$S/../references/gate-audit.md`.

## 1. Scope the target

`$ARGUMENTS` is a CI workflow file, a gate/lint script, a `Makefile`/`justfile` (with
`--target NAME` for one recipe), or a directory such as a test tree or a `.github/workflows/`.
No argument: list the repository's gates first (CI workflows, the project's own gate command,
pre-commit config, test runner) and say which you are auditing. **Audit what the pipeline
actually runs**, not what the README says it runs.

## 2. Run the detector half

```sh
python3 $S/gate_audit.py <target> [--target RECIPE] [--only RULE,...] [--json]
python3 $S/gate_audit.py --list-rules     # what is detected, and what is not
```

Exit codes — read them exactly:

- `0` — **no pattern matched.** This is not "the gate can fail". It means seven regex families
  found nothing; step 4 is still owed.
- `1` — vacuous-gate pattern(s) found. Each finding carries the §7 row, the line, why, and the
  row's remediation.
- `2` — **nothing was audited**: unreadable, unsupported, no scannable file, or no such recipe.
  Never report a `2` as clean. Re-scope and run again.

Findings are pattern matches, not verdicts. Open every one, read the surrounding gate, and say
whether it is real. A detector's limits are listed in the coverage map; cite the limit when you
dismiss a finding.

## 3. Read the six rows no script can decide

The script does **not** detect these and does not claim to. Work them by hand against §7:

- **Measuring the Wrong Property** — name the property the gate claims to enforce, then the one it
  measures. Keyword greps, filename checks and "does `eval` appear" are proxies.
- **Self-Certifying Predicate** — does the evidence include the subject's own name, filename, or
  text the subject was handed? Scope a detector to what was *generated*, never to its input.
- **Empty-Set Pass** — run the gate with an empty input set (no files matched, no tests
  collected). If it passes, nothing asserts the collection is non-empty.
- **Mock-Only Coverage** — which boundary is exercised for real? If every collaborator is mocked,
  the test asserts the mock.
- **Assertion-Free Test** — read the bodies the gate runs; executing code and asserting nothing is
  vacuous.
- **Snapshot Rubber-Stamp** — were goldens updated wholesale (`-u`) in the same commit as a
  behaviour change?

## 4. Plant and prove — this is what makes it more than a linter

**For every gate the audit CLEARS, plant the violation that gate claims to catch and require the
gate to go red.** A gate that stays green is reported **vacuous regardless of how it reads**.

1. State, in one line, what this gate claims to catch.
2. Plant exactly that violation, minimally, in a real input the gate consumes.
3. Run the gate unchanged. It must fail, and its output must **name the planted violation** — a
   failure for an unrelated reason proves nothing.
4. Restore the tree and confirm it is clean (`git status --porcelain` empty). Never `git add` or
   commit a plant.
5. Record the plant, the command, and the exact failing line.

Naming: prefer the tool's own error on a real mutation. Where nothing mutates naturally, plant
`DEVLOOP-PLANTED-<TARGET-ID>` — never a string that also appears in the fixture's own filename or
in the gate's prompt, which passes whether or not the plant landed (§7 Self-Certifying Predicate).

`$S/adapters.py gate` runs this positive/negative pair mechanically once you can express it as a
lane; `/verify` is the wrapper.

## 5. Blast radius before you arm anything

Close every run with §7's last paragraph. A repaired gate was **silently passing real
violations**, so repairing it makes the pipeline redder. Before arming a repair, estimate and tell
the operator: how many existing violations it will start catching, which files, and whether they
are pre-existing debt or fresh. Offer the order — land the repair red and fix forward, or fix the
backlog first. **A vacuous check often over-claims its scope; the repair is often to narrow the
claim, not widen the check** — state the true scope in the PASS line.

**Honest red beats green that lies.**

## 6. Report

Per gate: `path` · §7 row (or CLEARED) · one-line evidence · plant-and-prove receipt (plant,
command, failing line) or **VACUOUS: stayed green under its own violation** · remediation ·
blast-radius estimate. Then: what was **not** audited — targets out of scope, rows left to
judgment, detector limits you relied on. Do not let "no pattern matched" read as "verified".
