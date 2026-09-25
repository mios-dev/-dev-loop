# Reply skeleton

Fill every field from this run. Replace each `<...>` with what was actually observed, and delete
nothing: write `none` where a list is empty. Section 3 follows the contract's own report order
and fields. When the contract defines that order, it replaces the placeholder list shown here.

```text
## Capability preflight
| | Capability | Probe (exact URL or command) | Result (exact output or error) |
|---|---|---|---|
| A | HTTPS fetch | <url> | <status, sha field line> |
| B | Offline code runner | <command; in place or pasted> | <SELF-TEST line, python version> |
| C | Byte-exact transfer | <contents API url -> bytes_proof.py> | <PASS/FAIL line> |
| D | Output delivery | <attach or save target> | <what the user can see> |
Skill files found at: <where>. Fetched bytes reached the runner by: <path>.

## Fetch paths tried
| URL | Tool | Result | Content type | Bytes | Blob proof |
|---|---|---|---|---|---|
| <url> | <direct fetch / browser / runner> | <200 / exact error> | <type> | <n> | <match / mismatch / n.a.> |

## Definition of Done
- Objective: <...>
- Revisions: <repository @ commit, evidence line>
- Deliverables: <names and formats from the contract>
- Positive controls: <the contract's checks, in order>
- Negative controls: <one plant per validator; sentinel DEVLOOP-PLANTED-<RUN-ID>>
- No-op decision: <rule applied, evidence compared>
- Stop conditions: <the contract's verdict words and when each applies>

## <The contract's report, in the contract's order>
<revisions and evidence lines>
<fetched files with their digests>
<no-op decision>
<bundle or output names with bytes and sha256 of each delivered file>
<each check: result and the two-sided evidence line>
<for every failure: the exact remediation>

## Not verified
- <each point this run could not prove, or none>

## Phantoms dismissed
- <failure investigated, evidence that it was an artefact, or none>

## Questions
- <contradiction or ambiguity; options; the reading this run took, or none>

<the contract's verdict line, exactly, as the last line>
```

Rules the skeleton cannot show:

- Nothing follows the verdict line: no signature, no note, no blank-line summary.
- Nothing inside the skeleton may carry a secret, token, email address or account identifier.
  Scan a saved copy of the reply draft with `scripts/secret_scan.py` before sending.
- The machine-readable report is whatever file the contract defines. Do not add a second JSON
  block to the reply.
