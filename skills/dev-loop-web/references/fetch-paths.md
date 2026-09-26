# Fetch paths for a public GitHub file

How a run without a checkout reads a file from a public GitHub repository, and proves which
bytes it read. OWNER, REPO, BRANCH, PATH and SHA are placeholders: take them from the task
text and from the commit the run resolves.

## Resolve, then pin

1. **Resolve** the branch head:
   `GET https://api.github.com/repos/OWNER/REPO/commits/BRANCH`.
   - Read the top-level `sha` field. It must be exactly 40 lowercase hexadecimal characters.
   - Quote the line as evidence, for example `"sha": "0123...cdef"`.
2. **Pin** the file to that commit:
   `GET https://raw.githubusercontent.com/OWNER/REPO/SHA/PATH`.
   - Each commit is a distinct URL, and a commit's content never changes, so no cache can serve
     an older copy.
3. **Prove** the bytes:
   `GET https://api.github.com/repos/OWNER/REPO/contents/PATH?ref=SHA`.
   - The response carries `content` (base64 of the exact bytes), `size`, and `sha` (the git blob
     SHA-1 of those bytes).
   - `python3 scripts/bytes_proof.py --contents-json FILE` recomputes the blob SHA offline.
   - A match proves the bytes, however they reached the runner.
   - Bytes from step 2 are proven the same way: `--file FILE --blob-sha SHA --size N`.
4. **Report** one line per file: `REPO@COMMIT PATH blob BLOB_SHA N bytes sha256 HEX`.

The pair of commit and blob SHA can be checked by anyone later. The command
`git ls-tree COMMIT PATH` prints the blob SHA.

### Large files

- For files over 1 MB, the contents API returns no inline content (its `encoding` is not base64).
- Use `GET https://api.github.com/repos/OWNER/REPO/git/blobs/BLOB_SHA` instead. It returns the
  same `content`, `encoding`, `sha` and `size` fields, for blobs up to 100 MB.
- Take the blob SHA from the contents API entry or a tree listing.

### Rate limits

- Unauthenticated GitHub REST calls are limited to about 60 an hour for each source address. A
  hosted agent may share its egress address with other users, so the budget can already be
  spent.
- A full run should need only a handful of API calls: one resolve per repository, plus one
  contents call per file that needs a proof.
- A 403 or 429 is recorded verbatim, with the `x-ratelimit-*` headers if the tool shows them.
  Retry at most once, after a pause. Never retry in a loop.
- Raw-host fetches do not count against the API budget.

## Every tool, before the next URL

A runtime can hold more than one fetch tool, and they fail differently. Measured on Gemini Spark:
the direct fetch tool answers `FETCH_ERROR: No canonical URL found` for every GitHub URL, while
the browser tool resolves `api.github.com` (the raw and blob hosts were refused there). So try each
URL with every fetch tool before moving to the next URL, and record each tool's result. When a
contents API response arrives as rendered JSON, copy its `content` field exactly into the runner,
decode it there, and prove it with `bytes_proof.py` against the `sha` field.

## Fallback order for the contract file

Use this list only when a form fails with a fetch error. A safety or security block is recorded
and never routed around.

| Order | Form | Byte-exact? | Notes |
|---|---|---|---|
| 1 | `https://raw.githubusercontent.com/OWNER/REPO/SHA/PATH` | yes, when proven | pinned raw file |
| 2 | the URL written in the task text, for example the raw branch URL | yes, when proven | the user's own pointer; up to about 5 minutes stale at the edge |
| 3 | `https://api.github.com/repos/OWNER/REPO/contents/PATH?ref=SHA` | yes (base64 plus blob SHA) | JSON; decode it in the runner |
| 4 | `https://cdn.jsdelivr.net/gh/OWNER/REPO@SHA/PATH` | yes, when proven | a separate CDN; served as `text/markdown` for `.md` files; never use a branch alias here, which is cached for hours |
| 5 | `https://github.com/OWNER/REPO/blob/SHA/PATH` and the same URL with `?plain=1` | **no** | a rendered HTML page; readable text, not the file's bytes |

- A form that is not byte-exact may be read to learn what the contract says. Every digest the
  contract asks for must still come from a byte-exact form.
- If no byte-exact form works, every check that needs a digest fails. The report says so.
- Where the contract fixes a URL form for the files it names, only that form satisfies it.
  Other forms are diagnostics, reported but never substituted.

## Known failures (UNVERIFIED causes)

- **Observed on one earlier scheduled run.** Fetching a raw branch URL for a contract file
  failed twice in one run:
  - the direct fetch reported "No canonical URL found";
  - retrieval through the web agent reported a block by a security filter.
- The same URL returned HTTP 200 `text/plain` to an ordinary HTTP client at the time.
- **Likely causes.** These are inferences from public vendor documentation, not established
  facts:
  - The direct fetcher may read from a search-index cache first, with no live fallback for an
    unindexed raw file.
  - The security block may come from a prompt-injection classifier. That classifier reacts to
    fetched text that addresses the agent, for example text asserting the reader's identity or
    claiming precedence over the user's task.
- **Consequence for the run.** Changing the host is unlikely to help if the content is the
  trigger. The fix belongs in how the contract is written: as a declarative specification that
  the user's task invokes, not as instructions to its reader.
  - A run cannot make that change. It reports the failure, with the exact error text, under the
    task text's rule for an unfetchable contract.
- **Model-built URLs.** Constructed URLs (a SHA substituted into a template) may be treated
  differently from URLs that appear literally in the user's task. Whether this runtime does so is
  unknown.

## What the first live run should record

A table with one row for each form tried. It has these columns:

- the URL;
- the tool used (direct fetch, browser, code runner);
- the result (HTTP status, or the exact error text);
- the content type, if shown;
- the byte count;
- whether `bytes_proof.py` matched.

These rows settle "which URL forms this runtime can read". Until a run records them, that
question is open, and no report may state an answer.
