## VERDICT
PARTLY_CONFIRMED - The loop translation layer design exhibits motivated reasoning across all three audited axes: several claims asserted as measured are unmeasured inferences or conflations, multiple promised gates permit vacuous passes or specify invariant assertions instead of negative controls, and scope refusals are declared solely in prose with zero repository enforcement.

## WHAT IS ACTUALLY TRUE

### (a) CLAIMS ASSERTED AS MEASURED THAT WERE NOT
The design documents mark several capabilities and behaviors as `(measured)` or assert them as measured facts when they are actually unmeasured inferences, overclaims, or conflations:

1. **Claude Code stream-json seam asserted as measured**:
   In skills/dev-loop/references/translation-layer.md:31, the table heading asserts "Seam inventory (all first-party, all measured)". Line skills/dev-loop/references/translation-layer.md:39 lists `claude -p --output-format stream-json` as a caller-driven NDJSON stdio stream with "same shape" as AGY's stream-json.
   *Command to produce*: `claude -p --output-format stream-json`.
   *Reality*: Claude CLI does not provide a caller-driven NDJSON input session via `--output-format stream-json`. In the repository's own adapter at skills/dev-loop/scripts/adapters.py:253, Claude is invoked with `--output-format json`. In skills/dev-loop/references/translation-layer.md:136, the author notes `claude -p --output-format json` and in the mapping table at skills/dev-loop/references/translation-layer.md:151 notes "from Claude json". The assertion that `claude -p --output-format stream-json` is a measured, caller-driven NDJSON seam is an unmeasured inference.

2. **Accepted-and-matches-nothing globbing asserted as measured**:
   Line skills/dev-loop/references/translation-layer.md:244 introduces "Measured asymmetry. AGY's permission grammar has exactly five live actions...". Line skills/dev-loop/references/translation-layer.md:248 asserts: `read_file(*) is universal; read_file(/repo/**) is accepted and matches nothing.`
   *Command to produce*: An `agy` invocation with `read_file(/repo/**)` configured in settings.json attempting to read a workspace file.
   *Reality*: No command, probe, or test in the repository or document demonstrates evidence for this claim. The repository's settings manager at skills/dev-loop/scripts/env/agy_settings.py:45 hardcodes universal `read_file(*)`, and the claim that `/repo/**` is accepted and matches nothing is an unmeasured inference presented as measured behavior.

3. **`toolPermission` and `strict` enum asserted as a measured trap**:
   Lines skills/dev-loop/references/translation-layer.md:275 claim: `One more measured trap the mapper must encode: toolPermission takes exactly always-proceed | request-review | strict, and an unrecognised value voids the entire settings file`.
   *Command to produce*: Writing `toolPermission` to `settings.json` and running `agy`.
   *Reality*: The actual Antigravity CLI setting key is `artifactReviewPolicy` (measured in skills/dev-loop/scripts/env/agy_settings.py:14), NOT `toolPermission`. Furthermore, in `agy` 1.2.11 the accepted values are `always-proceed`, `request-review`, `agent-decides` (measured in skills/dev-loop/scripts/env/agy_settings.py:52), NOT `strict`. The author invented or conflated `toolPermission` with `strict` and labelled it a "measured trap" without running a functional test against that key.

4. **Native fan-out reachable headlessly asserted from single-turn probes**:
   In skills/dev-loop/references/translation-layer.md:287, the table asserts: `| AGY headless -p and held stream-json | invoke_subagent works (measured, 1.2.6) | native fan-out is reachable headlessly |`.
   *Command to produce*: An unattended multi-turn lane fan-out dispatched via headless `agy -p`.
   *Reality*: The probes described in lines 296-300 tested single-turn immediate subagent calls that finished before the dispatching turn ended. As codified in repository constitution AGENTS.md, native lanes require a manager whose process outlives a turn because headless `agy -p` kills backgrounded subagents at turn end. Extrapolating full headless native fan-out from synchronous single-turn probes is an inference wearing a measurement's label.

5. **ADR maintains unmeasured absolute claim despite design reference concession**:
   In docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:12, the ADR asserts: `Measurement says that component cannot be built as stated: neither harness serves an API to translate.`
   *Command to produce*: Comprehensive network socket and IPC inspection across all daemons and background services.
   *Reality*: Even though the design reference conceded that background daemons like `remote-control` and undocumented flags were left unprobed, the ADR continues to assert as a measured premise that "Measurement says... neither harness serves an API to translate."

---

### (b) GATES THAT CANNOT FAIL
The Confirmation table in the ADR and Section 9 in the design reference define controls that permit vacuous bypasses, test proxy properties, or lack negative controls entirely:

1. **Phase P6 ACP negative control is an assertion of invariance, not a negative control**:
   In skills/dev-loop/references/translation-layer.md:404, Phase P6 specifies the negative control under table column skills/dev-loop/references/translation-layer.md:397 ("Negative control (must fail, by name)") as: `envelope/status/permissions unchanged across transports`.
   *Vulnerability*: This is a positive invariance check, NOT a negative control that plants a defect and asserts failure by name. Under SKILL.md §7 (Empty-Set Pass / Assertion-Free Test), no failing scenario or mutation is defined. Any implementation passes unconditionally.

2. **Phase P2 / ADR Claim 2 tests a proxy keyword rather than worktree diffs**:
   In skills/dev-loop/references/translation-layer.md:400 and docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:130, the negative control is: `a lane whose worker is true returns vacuous — asserting delivered fails the suite`.
   *Vulnerability*: A lazy implementation checking `if lane.worker.cmd == "true": return "vacuous"` passes. Under SKILL.md §7 (Measuring the Wrong Property), testing a literal proxy command (`cmd == "true"`) fails to verify that diff-emptiness is actually evaluated via worktree diffs. Furthermore, tests/test_loop_envelope.py:87 tests `diff_bytes: 0` against a hardcoded in-memory dictionary, exemplifying Mock-Only Coverage rather than integration with git diff.

3. **ADR Claim 4 isolation gate lacks a positive control and permits blanket rejection**:
   In docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:132, Claim 4 states: `a lane declaring harness-native worktree isolation while the server also isolates is rejected as a second source of truth`.
   *Vulnerability*: A validator that unconditionally rejects any lane with `isolation: worktree` or rejects whenever the `isolation` key is present satisfies this gate. Without a positive control in the ADR Confirmation table showing that non-conflicting isolation declarations succeed, an unconditional rejection or crash satisfies the gate.

4. **ADR Claim 5 depth gate lacks positive controls**:
   In docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:133, Claim 5 states: `a headless AGY lane declaring max_depth > 0 is rejected at validate`.
   *Vulnerability*: A validator that unconditionally rejects `max_depth > 0` across all harnesses and modes (blocking valid configurations in interactive AGY or Claude Code) satisfies this gate. Without a positive control ensuring that valid lane depths pass, an over-broad rejection passes the gate.

5. **Phase P0 / ADR Claim 1 promised mutated-field negative control is absent from test suite**:
   In skills/dev-loop/references/translation-layer.md:398 and docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:129, Claim 1 promises: `tests/test_loop_envelope.py — recorded real envelopes (incl. the stream-json line above) normalise to loop.v1; a mutated field fails by name`.
   *Vulnerability*: In skills/dev-loop/scripts/loop_envelope.py:120, `normalize()` extracts fields via `.get()` without schema validation. Malformed or mutated fields simply default to `None`. In tests/test_loop_envelope.py:1-184, not a single test mutates an envelope field to assert that it fails by name. The suite exits 0 and reports all green despite the promised negative control being completely absent (Check-Without-Diff / Empty-Set Pass).

6. **Phase P5 xlate controls specify unachievable or vacuous round-tripping**:
   In skills/dev-loop/references/translation-layer.md:403, Phase P5 specifies: `round-trip a plugin; structure preserved` / `the permission block is refused, not translated; a silent translation fails the suite`.
   *Vulnerability*: A lazy implementation that implements `xlate` as an identity function and crashes on encountering `"permissions"` passes. Because Section 3.2 admits that AGY plugin import is "one-way and lossy", preserving structure in a round trip between `.claude-plugin/` and `.agents/` is structurally impossible without synthetic mappings. The requirement "structure preserved" is too vague to forbid identity stubs.

---

### (c) SCOPE REFUSALS THAT ARE STATED BUT NOT ENFORCED
1. **Model-wire translation refusal exists only in prose**:
   In skills/dev-loop/references/translation-layer.md:46, Section 2 states: "Model-wire translation (Anthropic Messages ↔ OpenAI/Gemini) ... Do not build." and "Claude Code delegates a task to agy ... Do not build."
   *Enforcement analysis*: There is zero enforcement code in the repository. No AST linter, import checker, or structural validator verifies that wire translation or delegation logic is absent.

2. **Smuggled model gateway gate is entirely aspirational prose**:
   In skills/dev-loop/references/translation-layer.md:355, Section 6.3 states: "gate it behind [surfaces].messages so validate.sh can assert it is absent by default". In docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:134, Claim 6 promises: "A gate that inspects loopd's registered route table at import time and fails if an Anthropic-Messages path is bound while [surfaces].messages is off."
   *Enforcement analysis*:
   - skills/dev-loop/scripts/validate.sh:4 and skills/dev-loop/scripts/validate.sh:78 contain zero checks for `loopd`, zero route table inspections, zero mentions of `[surfaces]`, and zero checks for Anthropic routes.
   - `loopd` does not exist in the codebase.
   - No tests in `tests/` inspect route tables or verify that bound routes fail.
   The entire anti-smuggling gate is aspirational prose. A smuggled route would pass `validate.sh` and CI completely undetected.

## NUMBERS
- 5 claims asserted as measured that are unmeasured inferences, overclaims, or conflations.
- 6 gates identified in the ADR Confirmation table and Reference Section 9 phase table that permit vacuous bypasses, proxy checks, mock-only coverage, or lack negative controls.
- 0 actual enforcement mechanisms in `validate.sh` or CI for the stated scope refusals.

## PROPOSED FIX
1. Remove `(measured)` labels from inferred claims (or execute and document real functional probes for `claude` stream-json, `/repo/**` permission globbing, and `artifactReviewPolicy`).
2. Replace proxy controls (such as `cmd == "true"` in P2) with explicit worktree diff evaluations; replace the positive invariance assertion in P6 with a true negative control; implement field-level schema validation and mutated-field tests in `loop_envelope.py` and `test_loop_envelope.py`.
3. Add structural checks in `skills/dev-loop/scripts/validate.sh` (or a dedicated architectural linter) that inspect route tables and module imports to mechanically enforce the model-wire and Anthropic gateway refusals.

## FILES TO CHANGE
- skills/dev-loop/references/translation-layer.md
- docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md
- skills/dev-loop/scripts/validate.sh
- skills/dev-loop/scripts/loop_envelope.py
- tests/test_loop_envelope.py

## NEGATIVE CONTROL
Run the contract negative control command. The script appends an unresolvable planted citation and verifies that check_finding fails with exit code 1 naming the lane's planted sentinel (named in .devloop/lanes.research.json).

## UNVERIFIED
1. We have not checked whether undocumented flags or future versions of `agy` or `claude` expose wire listeners.
2. We have not verified whether `jiridanek/agy-acp` can be automated without interactive OAuth.
