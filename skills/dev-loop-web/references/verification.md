# Verification for web-only runs

How a run without a shell still proves its checks, which is the dev-loop rule that a check counts
only after it has been seen to fail. Every value below that belongs to a project (key sets,
counts, names, the schema) is a placeholder. Take the real value from the contract fetched on
the run.

## The two-sided protocol

For each validator:

1. **Choose the sentinel.** `DEVLOOP-PLANTED-` plus the run's bundle or run name, uppercased,
   with each run of non-alphanumerics replaced by one hyphen. Example: a bundle called
   `nightly-set-20260925-abc123` gives `DEVLOOP-PLANTED-NIGHTLY-SET-20260925-ABC123`. Use one
   sentinel per run, and confirm it occurs nowhere in the inputs. The scripts refuse a sentinel
   that is already present, because a failure that names it would prove nothing.
2. **Plant.** Run the validator on a copy that carries the sentinel in a form the check must
   reject. It must exit non-zero, and its message must contain the sentinel.
3. **Real.** Run the validator on the real artifact. It must exit 0, and report a non-zero count.
4. **Record** both lines verbatim as the evidence for that check.

`--two-sided SENTINEL` does steps 2 and 3 in one call and prints one line: `PASS two-sided
<tool>: plant <S> -> FAIL naming it (<the failure line>); real -> PASS (<count>)`. The exit code
is 0 only when both sides hold. Anything else starts `FAIL two-sided`, and says which side broke.

A plant the validator does not catch is the most important result a run can produce: it means
the check is vacuous. That check fails, whatever the real run printed.

## The scripts

All scripts are offline, use only the Python 3 standard library, and print one evidence line.
Exit codes: 0 pass, 1 check failed, 2 usage error. Each has `--self-test`, which builds a tiny
fixture, runs both sides, and prints `SELF-TEST PASS <script> (python X.Y.Z): ...`. That is the
capability probe for "can this runtime run bundled code at all".

### bytes_proof.py: exact bytes

```text
python3 scripts/bytes_proof.py --contents-json contents.json --out contract.md
python3 scripts/bytes_proof.py --file raw.bin --blob-sha BLOB_SHA --size N
python3 scripts/bytes_proof.py --contents-json contents.json --two-sided SENTINEL
```

- Input for `--contents-json`: the GitHub contents API (or git blobs API) response, saved
  unchanged.
- It recomputes the git blob SHA-1 and compares it with `sha` and `size`. `--out` writes the
  decoded bytes only when the proof passes.
- Plant: the sentinel appended to the bytes. Named by "bytes beyond the expected size".

### jsonl_check.py: records

```text
python3 scripts/jsonl_check.py records.jsonl --keys KEY1,KEY2 --min N \
    --shape openai-chat|openai-preference --split-hex-prefixes P,Q --against other.jsonl \
    --two-sided SENTINEL
```

- `--keys` is the contract's exact top-level key set. It is required, and extra and missing keys
  both fail.
- `--shape openai-chat`: the last message is a non-empty assistant message, and a system message
  may appear only first.
- `--shape openai-preference`: the input ends with a user turn, each output is exactly one
  non-empty assistant message, and the two outputs differ.
- `--split-hex-prefixes`: the contract's split rule, when it is "sha256 of the line starts with".
  By default the line is hashed without its newline; `--split-with-newline` hashes it with the
  newline. Use whichever the contract states, and say which. Both splits must be non-empty.
- `--against`: fails on a line that is identical to a line in another file.
- Plant: an extra record whose extra key is the sentinel. Named by `key set mismatch: extra
  ['SENTINEL']`.

### oci_closure.py: OCI image layout tar

```text
python3 scripts/oci_closure.py build --out layout.tar --layer-root PREFIX/ --ref-name NAME \
    --revision COMMIT FILE1 FILE2
python3 scripts/oci_closure.py check layout.tar --ref-name NAME --revision COMMIT \
    --layer-contains PREFIX/FILE1 --two-sided SENTINEL
```

- `check` fails on:
  - a compressed tar;
  - a missing or wrong `oci-layout`;
  - `index.json` whose schemaVersion is not 2, or that has no manifests;
  - a descriptor whose blob is missing, has the wrong size, or has the wrong sha256, anywhere in
    index, manifest, config and layers;
  - config `rootfs.diff_ids` that differ from the layer digests;
  - a missing ref name or revision annotation;
  - a required file absent from every layer.
- It reports a nested image index as unsupported rather than passing it.
- `build` makes one uncompressed layer and a byte-reproducible tar.
- Plant: an extra index descriptor whose ref name is the sentinel and whose blob is absent. Named
  by `index.manifests[1] ref=SENTINEL: blob ... missing`.

### schema_check.py: JSON against an OpenAI strict schema

```text
python3 scripts/schema_check.py --schema schema.json manifest.json --two-sided SENTINEL
```

- `schema.json` is the contract's schema block, copied byte for byte from the fetched contract
  bytes, not rewritten. The accepted shapes are a bare schema, `{name, strict, schema}`, or a
  whole `response_format` object.
- When the schema is strict, it is also linted: every object must set `additionalProperties:
  false` and require every property.
- An unsupported keyword is an error, never skipped.
- Plant: an extra top-level property named the sentinel. Named by `additional property
  'SENTINEL' not allowed`. If the schema allows extra properties, the plant is not caught, and
  the check is reported as vacuous.

### secret_scan.py: credentials and personal data

```text
python3 scripts/secret_scan.py out1.jsonl out2.jsonl layout.tar reply-draft.txt --two-sided SENTINEL
```

- It opens tar archives and nested tar layers, and scans every line.
- A finding prints the location and the kind, never the matched text.
- `--allow VALUE` skips a match only when the whole match equals VALUE.
- Scan the artifacts and a saved copy of the reply draft. Never scan the contract, which
  mentions secret patterns by design.
- Plant: a line with the sentinel and an address at `example.invalid`. Named by `(planted:
  SENTINEL)`.
- Scope: the patterns in the script. The PASS line states how many patterns ran. An identifier
  type they do not cover is not detected, so say so under Not verified if the contract names one.

### digest.py: attached bytes and determinism

```text
python3 scripts/digest.py out1.jsonl layout.tar manifest.json
python3 scripts/digest.py --compare build1 build2 --two-sided SENTINEL
```

- The first form prints `{"bytes", "name", "sha256"}` per file. Take the manifest's byte counts
  and digests from these lines, computed on the final files.
- `--compare` fails on any file present in only one build, or differing between them.
- Plant: the sentinel appended to one file of the second build. Named by `differs at byte K:
  second build has '...SENTINEL'`.

## Checks with no script

- Grounding (each record traces to a fetched file) and near-duplicates are judgment checks.
- Evidence for them: how many records were traced, to which files, and one sampled record per
  source file.
- Plant: add one record grounded in nothing (for example a claim about a file that was not
  fetched) to a copy. Confirm the procedure flags it before running it on the real set.

## One example per "cannot fail" row

| Row | What it looks like on a web-only run | Correct handling |
|---|---|---|
| Skip-as-pass | The code runner was unavailable, so the digest check "passed by inspection" | The check fails; `CAPABILITY_MISSING: B` |
| Empty-set pass | `jsonl_check` on a file that decoded to nothing | 0 records is a failure (the script enforces it) |
| Self-comparison | The manifest's sha256 copied from an earlier note, not from the attached bytes | Recompute with `digest.py` on the final files |
| Self-certifying predicate | The secret scan run on the contract text, which lists secret patterns | Scan the outputs and the reply draft only |
| Timeout-as-pass | A fetch that timed out, recorded as "fetched" | Record the timeout and apply the contract's rule for a failed fetch |
| Loosening to pass | The minimum record count lowered because the build came up short | Report the shortfall; the check fails |
| Measuring the wrong property | The tar "checked" by listing member names without hashing blobs | `oci_closure.py check` hashes every descriptor |
