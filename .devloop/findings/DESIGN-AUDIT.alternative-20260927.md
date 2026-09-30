## VERDICT
PARTLY_CONFIRMED - The loop-translation-layer design exhibits motivated reasoning by dressing up documentation inferences and analogies as empirical measurements, specifying verification controls that admit trivial or vacuous bypasses, and leaving explicit architectural scope refusals entirely unenforced in the repository.

## WHAT IS ACTUALLY TRUE

### (a) Claims Asserted as Measured That Were Inferences
The design documents claim in skills/dev-loop/references/translation-layer.md:31 that the seam inventory is "all first-party, all measured", yet multiple items are unmeasured inferences:

1. **`LocalOpenAIAgentConfig.base_url` as the sole AGY backend interface** (skills/dev-loop/references/translation-layer.md:36):
   - *Claim:* Marked as first-party measured seam and described as "the only way AGY consumes a backend".
   - *Measurement Reality:* In skills/dev-loop/references/translation-layer.md:426, the document explicitly confesses that `LocalOpenAIAgentConfig` is sourced from `*(docs + package metadata)*` of the closed Python wheel (`google-antigravity` PyPI 0.1.17). No command in this container probed it. Declaring it "measured" and universally inferring that it is "the only way AGY consumes a backend" without testing binary flags or config options is an inference wearing a measurement's label.

2. **Claude Code `claude -p --output-format stream-json`** (skills/dev-loop/references/translation-layer.md:39, skills/dev-loop/references/translation-layer.md:102):
   - *Claim:* Listed as a first-party measured seam ("caller drives", "yes — same shape") and specified as the exact lane execution command in line 102.
   - *Measurement Reality:* The document provides evidence only for `agy --output-format stream-json` and `claude -p --output-format json` (skills/dev-loop/references/translation-layer.md:122). There is zero trace or measurement that `claude -p` supports `--output-format stream-json` or holds an NDJSON session open on stdin. The author observed agy's streaming NDJSON behavior and assumed Claude Code possessed the identical seam by structural analogy.

3. **`agy remote-control` daemon subcommands** (skills/dev-loop/references/translation-layer.md:42, skills/dev-loop/references/translation-layer.md:382, docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:117):
   - *Claim:* Marked as "a real daemon (`start|status|stop`, measured)".
   - *Measurement Reality:* The actual Antigravity CLI daemon command is `agy remote-control serve` (which registers the host machine), as demonstrated in tests/test_agy_remote_control.py:24. The subcommands `start|status|stop` were inferred from standard daemon conventions rather than measured from the CLI's actual subcommands.

4. **`toolPermission` enum and `strict` mode** (skills/dev-loop/references/translation-layer.md:275):
   - *Claim:* "One more measured trap the mapper must encode: `toolPermission` takes exactly `always-proceed | request-review | strict`".
   - *Measurement Reality:* The actual key in Antigravity settings is `artifactReviewPolicy`, not `toolPermission` (see tests/test_agy_settings.py:6). Furthermore, the real enum values in the binary are `always-proceed`, `request-review`, `agent-decides` (and legacy `turbo`), never `strict`. The author conflated `artifactReviewPolicy` with Claude Code's `--permission-mode strict` and asserted the hallucinated configuration as a "measured trap".

5. **`read_file(/repo/**)` path-matching failure** (skills/dev-loop/references/translation-layer.md:244, skills/dev-loop/references/translation-layer.md:248):
   - *Claim:* Under "Measured asymmetry", states that `read_file(/repo/**)` is "accepted and matches nothing".
   - *Measurement Reality:* The author observed the 5 live action strings in the binary and deduced that path globbing syntax is absent from the grammar. No functional execution trace or probe command was run demonstrating an auto-denial for `/repo/**`.

6. **Headless subagent fan-out reachability** (skills/dev-loop/references/translation-layer.md:287):
   - *Claim:* "| AGY headless `-p` and held stream-json | `invoke_subagent` works (measured, 1.2.6) | native fan-out is reachable headlessly |".
   - *Measurement Reality:* The probe tested a trivial subagent that finished inside a single turn. In reality, single-turn `agy -p` terminates when the turn ends, destroying any ongoing subagent workers. Inferring general headless native fan-out from a synchronous single-turn toy subagent is motivated reasoning that conflates single-turn availability with lifecycle support.

7. **`agy plugin import` seam classification** (skills/dev-loop/references/translation-layer.md:31, skills/dev-loop/references/translation-layer.md:77, skills/dev-loop/references/translation-layer.md:79):
   - *Claim:* Included in the table of "all-first-party, all measured" seams at line 31.
   - *Measurement Reality:* In skills/dev-loop/references/translation-layer.md:79, the text admits that the absence of permission importing is an unverified proxy ("Treat it as unverified until an import is run end to end"). Stamping the seam table as "all measured" directly contradicts this admission.

### (b) Gates That Cannot Fail (Vacuous-Check Analysis)
The controls promised in the ADR Confirmation table (docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:129-134) and Reference Phase Table (skills/dev-loop/references/translation-layer.md:398-403) exhibit several SKILL.md §7 failure modes:

1. **Envelope Mutated Field Control (P0)** (docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:129, skills/dev-loop/references/translation-layer.md:398):
   - *Promise:* "a mutated field fails **by name**".
   - *Lazy Implementation:* A normalization function that parses fields using `.get()` without schema validation (exactly what skills/dev-loop/scripts/loop_envelope.py:121 implements). If a field contains invalid data (e.g. `num_turns: -5` or strings), it is passed through silently. The test suite in tests/test_loop_envelope.py:58 tests only happy-path hand-crafted dictionaries with zero mutation assertions, passing completely without ever testing field failure by name.

2. **Vacuous Worker Gate (P2)** (docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:130, skills/dev-loop/references/translation-layer.md:400):
   - *Promise:* "fixture lane whose worker is `true` must return `vacuous`; asserting `delivered` fails the suite".
   - *Lazy Implementation:* A unit test passing a synthetic dictionary `{..., "diff_bytes": 0}` directly to the in-memory Python helper `derive_status()` (as done in `tests/test_loop_envelope.py`). It never executes an actual lane or verifies git worktree diff inspection in `loopd`. If `loopd` fails to run `git diff` or swallows subprocess errors in actual worktrees, the mock test still passes (SKILL.md §7 Mock-Only Coverage).

3. **Permission Closed-Fail Gate (P3)** (docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:131, skills/dev-loop/references/translation-layer.md:401):
   - *Promise:* "fixture lane whose grants map to `widens`/`none` must be rejected at validate time".
   - *Lazy Implementation:* A validator that unconditionally rejects all lanes containing permissions, or rejects based on fixed fixture IDs (`if lane["id"] == "fixture_widens"`). In the ADR table, no positive control is defined alongside this negative check, allowing a reject-all implementation to pass.

4. **Server Isolation Ownership Gate** (docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:132):
   - *Promise:* "a lane declaring harness-native worktree isolation while the server also isolates is rejected".
   - *Lazy Implementation:* A syntactic check `assert "worktree" not in lane.get("isolation")`. This checks only a config string rejection proxy. It never verifies that the server creates isolated worktrees, isolates git HEAD, or detects index collisions.

5. **Depth Flattening Gate** (docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:133):
   - *Promise:* "a headless AGY lane declaring `max_depth > 0` is rejected at validate".
   - *Lazy Implementation:* A static validation check `assert lane.get("max_depth", 0) == 0`. It checks only schema input and does not prevent headless agents from dispatching subagents dynamically at runtime.

6. **No Smuggled Model Gateway Route Table Gate** (docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:134):
   - *Promise:* "A gate that inspects `loopd`'s registered route table at import time and fails if an Anthropic-Messages path is bound while `[surfaces].messages` is off".
   - *Lazy Implementation:* If routes are bound dynamically inside a factory function (`create_app()`), registered during an ASGI lifecycle hook, or handled through catch-all wildcard dispatch (`/{path:path}`), an import-time check on `loopd.ROUTES` sees an empty table and passes. Planting a dummy key in a dictionary satisfies the negative control without testing network request handling.

7. **Single-Shot State Loss Control (P1)** (skills/dev-loop/references/translation-layer.md:399):
   - *Promise:* "the same lane through a single-shot adapter must fail at turn 2, with turn 1 having succeeded and the failure naming the lost state".
   - *Lazy Implementation:* An adapter mock that tracks invocation count and raises `StateLostError("lost state")` on turn 2 without executing CLI processes.

8. **Façade Live-Lane Disambiguation (P4)** (skills/dev-loop/references/translation-layer.md:402):
   - *Promise:* "with no backing lane the façade errors while the same request against a live lane succeeds in the same test run".
   - *Lazy Implementation:* A handler that switches response status code based on a synthetic request parameter or query flag rather than verifying backing lane existence.

### (c) Scope Refusals That Are Stated But Not Enforced
Section 2 of skills/dev-loop/references/translation-layer.md explicitly refuses model-wire translation ("Do not build"), and Section 6.3 (skills/dev-loop/references/translation-layer.md:355) states:
"Ship only if the operator prefers one process over two, and gate it behind `[surfaces].messages` so `validate.sh` can assert it is absent by default".

In reality, this refusal is **pure prose**:
1. Inspection of skills/dev-loop/scripts/validate.sh:3, skills/dev-loop/scripts/validate.sh:25, and skills/dev-loop/scripts/validate.sh:71 reveals checks for skill frontmatter, plugin manifests, hooks syntax, schema assets, and python tests. There is **zero code** in `validate.sh` checking `[surfaces].messages`, route definitions, or model gateway behavior.
2. A search across the repository finds that `[surfaces].messages` does not exist in any configuration file or validator.
3. No lint rule, test double, or static analysis prevents a model gateway from being added to the repository; `validate.sh` would pass without warning.

## NUMBERS
- 7 claims labeled or categorized as measured that are actually inferences, documentation readings, or analogies.
- 8 verification gate promises vulnerable to lazy-but-passing or mock-only bypasses.
- 0 enforcing mechanisms in `validate.sh` or elsewhere in the repo for the model gateway refusal.
- 100% of the Anthropic Messages scope refusal exists strictly in prose.

## PROPOSED FIX
1. **Accurate Provenance Labeling:**
   - Remove `(measured)` from `LocalOpenAIAgentConfig`, `claude -p --output-format stream-json`, `read_file(/repo/**)`, and `agy remote-control {start,status,stop}` in skills/dev-loop/references/translation-layer.md.
   - Replace the fictional `toolPermission: strict` claim with `artifactReviewPolicy` and the actual binary-extracted values (`always-proceed`, `request-review`, `agent-decides`).
   - Narrow the subagent claim from "native fan-out is reachable headlessly" to "single-turn subagent execution succeeds headlessly".
2. **Defensible Gate Specifications:**
   - Require real mutation testing (schema type & constraint mutations) in P0 to assert that invalid fields fail by field name.
   - Require P2's vacuous control to execute an actual worker in a real git worktree rather than passing mock dictionaries to unit functions.
   - Mandate live HTTP functional dispatch checks rather than module-level import-time dictionary inspection in the model gateway gate.
3. **Automated Scope Enforcement:**
   - Add an explicit assertion to `skills/dev-loop/scripts/validate.sh` that scans `loopd` (when implemented) for unregistered routes and fails if any Anthropic Messages routes exist when `[surfaces].messages` is absent or false.

## FILES TO CHANGE
- skills/dev-loop/references/translation-layer.md
- docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md
- skills/dev-loop/scripts/validate.sh

## NEGATIVE CONTROL
The negative control script plants a non-resolvable citation to the sentinel `DEVLOOP-PLANTED-DESIGN-AUDIT` and asserts that `check_finding.py` fails naming that sentinel.

## UNVERIFIED
- We have not executed a full live test of `agy plugin import` against Claude Code plugin manifests to exhaustively catalog which specific keys are dropped beyond `settings.json` permissions.
- We have not probed `claude` CLI on a Linux container in this specific turn to check if any undocumented streaming flags exist.
