#!/usr/bin/env python3
"""
Controls for stale_refs.py — the stale-reference monitor.

What this file is defending
---------------------------
A stale-reference scanner is unusually easy to ship broken, because its broken state and its
healthy state print the same sentence. "0 stale references, exit 0" is emitted both by a clean
tree and by a scanner that read nothing at all. So the headline case here is not "does it find
rot" — it is `test_empty_corpus_fails_rather_than_reporting_clean`, and that case is written so
that a naive scanner CANNOT pass it: it asserts the exact exit code 3, the verdict string, that
`counts.stale` is `null` rather than `0`, and that the word "clean" appears nowhere in the
output. A scanner that shrugged and said "0 stale references" fails every one of those.

Three git behaviours make that failure reachable, and all three are re-measured here rather
than assumed, because the whole defence rests on them (verified against git 2.43):
  * a valid repo with NO commits          -> `git ls-files` exits **0**, prints nothing
  * a pathspec matching nothing           -> exits **0**, prints nothing
  * a conflicted path mid-merge           -> listed **three times** (stages 1/2/3), exits 0
The first two mean exit status cannot guard the corpus. The third means a naive corpus
triple-counts and can mask a real shrink. `test_git_exit_zero_on_empty_is_real` asserts these
are still true, so if a future git changes them this file says so instead of silently resting
on a stale premise.

Everything else is ordinary two-sided verification: every positive control has a negative twin
that proves the check can fail.

Run: python3 tests/test_stale_refs.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SR = ROOT / "skills" / "dev-loop" / "scripts" / "stale_refs.py"
sys.path.insert(0, str(SR.parent))

FAILURES: list[str] = []
_TMP: list[Path] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


# ------------------------------------------------------------------------------- fixtures

def tmp_tree(files: dict[str, str], git: bool = True) -> Path:
    """A scratch tree under /tmp. The repo under test is never mutated by these controls."""
    d = Path(tempfile.mkdtemp(prefix="stale-refs-test-"))
    _TMP.append(d)
    for rel, body in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    if git:
        git_init(d)
        if files:
            run_git(d, "add", "-A")
            run_git(d, "commit", "-qm", "fixture")
    return d


def git_init(d: Path) -> None:
    run_git(d, "init", "-q", "-b", "main")
    run_git(d, "config", "user.email", "control@example.invalid")
    run_git(d, "config", "user.name", "control")
    run_git(d, "config", "commit.gpgsign", "false")


def run_git(d: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True)


def run_cli(root: Path, *args: str) -> tuple[int, dict, str]:
    """-> (exit code, parsed JSON report, stderr). The CLI is driven as a subprocess so the
    exit code under test is the real one a supervisor would see."""
    cp = subprocess.run([sys.executable, str(SR), "--root", str(root), *args],
                        capture_output=True, text=True, timeout=120)
    try:
        doc = json.loads(cp.stdout)
    except json.JSONDecodeError:
        doc = {"_stdout": cp.stdout[:2000]}
    return cp.returncode, doc, cp.stderr


# A tree with one resolvable citation per extractor, used as the clean baseline.
CLEAN_TREE = {
    "README.md": "# demo\n\nSee [the guide](docs/guide.md) and `src/app.py`.\n",
    "docs/guide.md": "Refs: src/app.py\n\nAnd the helper at `src/util/helper.py`.\n",
    "src/app.py": '"""App.\n\nRefs: docs/guide.md\n"""\nX = 1\n',
    "src/util/helper.py": '"""Helper.\n\nRefs: src/app.py\n"""\nY = 2\n',
}


# --------------------------------------------------------------------------- the premises

def test_git_exit_zero_on_empty_is_real() -> None:
    """The premise the whole empty-set defence rests on, re-measured rather than assumed.

    If git ever starts reporting a non-zero status for these, the defence could be simplified —
    and if this case ever fails, the comments in stale_refs.py are lying about why the census
    exists. Either way a human needs to know."""
    print("git's own behaviour (the premise):")
    d = tmp_tree({}, git=False)
    git_init(d)
    cp = run_git(d, "ls-files")
    check("an empty repo: git ls-files exits 0 with empty stdout",
          cp.returncode == 0 and cp.stdout.strip() == "",
          f"rc={cp.returncode} stdout={cp.stdout!r}")

    d2 = tmp_tree({"README.md": "`a/b.md`\n"})
    cp2 = run_git(d2, "ls-files", "--", "no/such/dir")
    check("a pathspec matching nothing: git ls-files exits 0 with empty stdout",
          cp2.returncode == 0 and cp2.stdout.strip() == "",
          f"rc={cp2.returncode} stdout={cp2.stdout!r}")

    d3 = tmp_tree({"README.md": "See `x/gone.md`\nbase\n"})
    run_git(d3, "checkout", "-qb", "other")
    (d3 / "README.md").write_text("See `x/gone.md`\nOTHER\n")
    run_git(d3, "commit", "-qam", "other")
    run_git(d3, "checkout", "-q", "main")
    (d3 / "README.md").write_text("See `x/gone.md`\nMAIN\n")
    run_git(d3, "commit", "-qam", "main")
    run_git(d3, "merge", "other")
    rows = [l for l in run_git(d3, "ls-files").stdout.splitlines() if "README.md" in l]
    check("a conflicted path mid-merge is listed three times by git ls-files",
          len(rows) == 3, f"{len(rows)} row(s)")


# ------------------------------------------------------------------- the five named cases

def test_planted_stale_reference_is_found() -> None:
    """POSITIVE CONTROL. A path cited in a header that resolves to nothing must be reported,
    by file, by line, and by the token as written."""
    print("a planted stale reference:")
    tree = dict(CLEAN_TREE)
    tree["src/rot.py"] = '"""Rot.\n\nRefs: docs/does-not-exist.md\n"""\nZ = 3\n'
    d = tmp_tree(tree)
    rc, rep, err = run_cli(d, "--no-ledger")
    check("exit code is 1 (the ordinary gate failure)", rc == 1, f"rc={rc}")
    check("verdict is 'regressed'", rep.get("verdict") == "regressed", str(rep.get("verdict")))
    hit = [f for f in rep.get("new", []) if f["ref"] == "docs/does-not-exist.md"]
    check("the planted reference is named in findings", len(hit) == 1,
          str([f["ref"] for f in rep.get("new", [])]))
    if hit:
        check("the finding carries the citing file and line",
              hit[0]["file"] == "src/rot.py" and hit[0]["line"] == 3,
              f"{hit[0]['file']}:{hit[0]['line']}")
    check("the resolvable citations were NOT reported",
          all(f["ref"] != "docs/guide.md" for f in rep.get("new", [])))
    check("the human summary reaches stderr", "src/rot.py" in err, err[:120])


def test_clean_corpus_reports_clean() -> None:
    """The baseline. A scanner that shouted on every tree would pass every negative case in
    this file while being useless, so the clean tree must read clean — and must still prove it
    looked, by carrying a non-trivial corpus and reference count."""
    print("a clean corpus:")
    d = tmp_tree(CLEAN_TREE)
    rc, rep, err = run_cli(d, "--no-ledger")
    check("exit code is 0", rc == 0, f"rc={rc} verdict={rep.get('verdict')}")
    check("verdict is 'clean'", rep.get("verdict") == "clean", str(rep.get("verdict")))
    check("zero stale", rep.get("counts", {}).get("stale") == 0, str(rep.get("counts")))
    check("it actually scanned something (corpus and references are non-trivial)",
          rep["corpus"]["scanned_files"] >= 4 and rep["counts"]["candidates"] >= 4,
          f"scanned={rep['corpus']['scanned_files']} refs={rep['counts']['candidates']}")
    check("the PASS line states the true scope, not just '0 stale'",
          "citations examined" in err and "resolved" in err, err[:160])


def test_empty_corpus_fails_rather_than_reporting_clean() -> None:
    """THE CASE THIS FILE EXISTS FOR.

    Five different ways to end up scanning nothing. Every one must exit 3 with verdict
    `could_not_run`, must name what was empty, must report `counts.stale` as null rather than
    0, and must never print the word "clean". A scanner with a broken corpus that printed
    "0 stale references, exit 0" fails all four assertions on all five shapes — which is the
    point: this case must not be satisfiable by the bug it is testing for.
    """
    print("an empty corpus (the headline case):")

    shapes: list[tuple[str, Path, tuple[str, ...], str]] = []

    not_a_repo = tmp_tree({"README.md": "See `a/b.md`\n"}, git=False)
    shapes.append(("not a git repository", not_a_repo, (), "git_unavailable"))

    empty_repo = tmp_tree({}, git=False)
    git_init(empty_repo)
    shapes.append(("valid repo, zero files (git exits 0)", empty_repo, (), "empty_corpus"))

    real = tmp_tree({"README.md": "See `docs/gone.md`\n"})
    shapes.append(("a path filter matching nothing (git exits 0)", real,
                   ("--include", "no/such/dir/**"), "empty_corpus"))
    shapes.append(("every file excluded by a filter", real, ("--exclude", "*"), "empty_corpus"))

    binary_only = tmp_tree({}, git=False)
    git_init(binary_only)
    (binary_only / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (binary_only / "blob.bin").write_bytes(b"\x00\x01\x02")
    run_git(binary_only, "add", "-A")
    run_git(binary_only, "commit", "-qm", "binaries")
    shapes.append(("corpus non-empty but nothing is text", binary_only, (), "empty_scan"))

    prose = tmp_tree({"README.md": "just prose, nothing is cited here at all\n"})
    shapes.append(("files scanned but zero citations extracted", prose, (),
                   "no_references_found"))

    for label, root, args, expected in shapes:
        rc, rep, err = run_cli(root, "--no-ledger", *args)
        blob = (json.dumps(rep) + err).lower()
        ok = (rc == 3
              and rep.get("verdict") == "could_not_run"
              and str(rep.get("verdict_reason", "")).startswith(expected)
              and rep.get("counts", {}).get("stale") is None
              and "clean" not in blob)
        check(f"{label} -> exit 3, could_not_run/{expected}, stale=null, never 'clean'", ok,
              f"rc={rc} verdict={rep.get('verdict')} "
              f"reason={str(rep.get('verdict_reason'))[:70]!r} "
              f"stale={rep.get('counts', {}).get('stale')!r} "
              f"says_clean={'clean' in blob}")

    # The assertion above must not be vacuously true: the SAME harness, on a tree that is
    # genuinely fine, has to produce a different verdict and a different exit code. Without
    # this, a scanner hardwired to exit 3 forever would pass every shape above.
    rc_ok, rep_ok, _ = run_cli(tmp_tree(CLEAN_TREE), "--no-ledger")
    check("control: the same harness on a healthy tree exits 0 and says 'clean'",
          rc_ok == 0 and rep_ok.get("verdict") == "clean",
          f"rc={rc_ok} verdict={rep_ok.get('verdict')}")


def test_runtime_prefix_path_is_not_reported() -> None:
    """Runtime paths legitimately do not exist in a source tree.

    The observed field bug was an exempt list holding /etc /var /tmp /proc /sys /run and NOT
    /usr, which turned every /usr citation into a false positive. Two things are asserted: the
    default (exempt every absolute path) cannot express that asymmetry at all, and the curated
    list — the shape that had the bug — carries /usr in its default. Both regimes must still
    report the ordinary in-tree rot sitting next to the runtime paths, otherwise the exemption
    has become a way of not looking.
    """
    print("runtime-prefix paths:")
    tree = dict(CLEAN_TREE)
    tree["src/runtime.py"] = (
        '"""Runtime.\n\n'
        "Refs: /etc/app/config.toml\n"
        "Refs: /var/log/app.log\n"
        "Refs: /proc/cpuinfo\n"
        "Refs: /usr/share/app/data.json\n"
        "Refs: docs/actually-gone.md\n"
        '"""\n'
    )
    d = tmp_tree(tree)

    rc, rep, err = run_cli(d, "--no-ledger")
    refs = [f["ref"] for f in rep.get("new", [])]
    check("default: no absolute runtime path is reported stale",
          not any(r.startswith("/") for r in refs), str(refs))
    check("default: /usr is exempt on the same footing as /etc and /var (no asymmetry)",
          rep["exempt"]["by_prefix"].get("/usr/") == 1
          and rep["exempt"]["by_prefix"].get("/etc/") == 1, str(rep["exempt"]["by_prefix"]))
    check("the exemption is DISCLOSED, not silent",
          rep["exempt"]["total"] == 4 and "were NOT checked" in err,
          f"total={rep['exempt']['total']}")
    check("in-tree rot beside the runtime paths is still reported",
          "docs/actually-gone.md" in refs, str(refs))

    rc2, rep2, _ = run_cli(d, "--no-ledger", "--no-exempt-absolute")
    refs2 = [f["ref"] for f in rep2.get("new", [])]
    check("curated-list mode: the default list includes /usr, so /usr is still not a finding",
          not any(r.startswith("/usr") for r in refs2), str(refs2))
    check("curated-list mode: in-tree rot is still reported",
          "docs/actually-gone.md" in refs2, str(refs2))

    # The negative twin: an exemption must be an opt-in decision, not an assumption. With
    # /usr/ mapped into the tree it is CHECKED, and a /usr path that is not mirrored becomes a
    # finding. Without this, "no /usr findings" would be indistinguishable from "not looking".
    rc3, rep3, _ = run_cli(d, "--no-ledger", "--root-map", "/usr/=usr/")
    refs3 = [f["ref"] for f in rep3.get("new", [])]
    check("root_map opts a prefix back IN: the /usr citation becomes checkable and fails",
          "usr/share/app/data.json" in refs3, str(refs3))


def test_near_miss_suggestion_fires_on_slug_typo() -> None:
    """A doc cited by a guessed title, next to its real filename.

    This is the case that rules out `difflib` as the implementation: the true pair scores 0.746
    on SequenceMatcher, below any cutoff that keeps out junk. The suggester uses a shared
    leading id plus extension instead. Asserted here together with its negative twin — an
    unrelated missing file in the same directory must get NO suggestion, because a confident
    wrong suggestion is worse than none.
    """
    print("near-miss suggestion on a slug typo:")
    real = "0020-edge-mesh-binary-wire-protocol-and-dual-tier-sandboxing.md"
    cited = "0020-edge-node-mesh-protocol-and-dual-tier-execution.md"
    tree = dict(CLEAN_TREE)
    tree[f"docs/adr/{real}"] = "# adr 0020\n"
    tree["docs/adr/0019-something-entirely-different.md"] = "# adr 0019\n"
    tree["src/cite.py"] = (f'"""Cite.\n\nRefs: docs/adr/{cited}\n'
                           'Refs: docs/adr/completely-unrelated-thing.md\n"""\n')
    d = tmp_tree(tree)
    rc, rep, _ = run_cli(d, "--no-ledger")

    hit = next((f for f in rep.get("new", []) if f["ref"].endswith(cited)), None)
    check("the typo'd slug is reported stale", hit is not None)
    if hit:
        sug = hit.get("suggestion")
        check("a suggestion is offered", sug is not None)
        if sug:
            check("the suggestion is the real file", sug["path"] == f"docs/adr/{real}",
                  sug["path"])
            check("the suggestion carries its basis and confidence, labelled as a hypothesis",
                  "basis" in sug and 0 < sug["confidence"] <= 1.0, str(sug))

    import difflib
    ratio = difflib.SequenceMatcher(None, cited, real).ratio()
    check("negative twin: difflib alone would NOT find this pair at a safe cutoff",
          ratio < 0.8 and not difflib.get_close_matches(cited, [real], 1, 0.8),
          f"SequenceMatcher={ratio:.3f}")

    other = next((f for f in rep.get("new", [])
                  if f["ref"].endswith("completely-unrelated-thing.md")), None)
    check("negative twin: an unrelated missing file gets NO suggestion",
          other is not None and other.get("suggestion") is None,
          str(other.get("suggestion") if other else None))


# ----------------------------------------------------------------- ratchet and resolution

def test_ratchet_is_itemised_not_a_count() -> None:
    """A count-only ratchet passes when one violation is swapped for another (SKILL.md §7).

    So: adopt a baseline, then repair one stale reference and introduce a different one in the
    same commit. The TOTAL is unchanged. An itemised ratchet must still fail, because the new
    citation has a fingerprint nobody accepted.
    """
    print("the ratchet is itemised, not a count:")
    tree = dict(CLEAN_TREE)
    tree["src/a.py"] = '"""A.\n\nRefs: docs/gone-one.md\n"""\n'
    d = tmp_tree(tree)

    rc, _, err = run_cli(d, "--adopt", "--reason", "initial adoption")
    check("--adopt writes a baseline and exits 0", rc == 0, f"rc={rc} {err[:120]}")
    check("the baseline file was created",
          (d / ".devloop" / "stale-refs.baseline.json").is_file())

    rc2, rep2, _ = run_cli(d)
    check("an adopted repo is green immediately", rc2 == 0 and rep2["verdict"] == "clean",
          f"rc={rc2} verdict={rep2.get('verdict')}")
    check("the accepted debt is still reported, not hidden",
          rep2["counts"]["stale"] == 1 and rep2["debt"]["distinct"] == 1, str(rep2["debt"]))

    # the swap: one repaired, one introduced, total unchanged
    (d / "src/a.py").write_text('"""A.\n\nRefs: docs/gone-two.md\n"""\n')
    run_git(d, "add", "-A")
    run_git(d, "commit", "-qm", "swap")
    rc3, rep3, _ = run_cli(d)
    check("a swap that keeps the count identical still FAILS", rc3 == 1,
          f"rc={rc3} verdict={rep3.get('verdict')}")
    check("the stale TOTAL really is unchanged (so a count ratchet would have passed)",
          rep3["counts"]["stale"] == 1, str(rep3["counts"]))
    check("the newly introduced citation is the one named",
          [f["ref"] for f in rep3["new"]] == ["docs/gone-two.md"],
          str([f["ref"] for f in rep3["new"]]))


def test_drained_entry_is_not_left_as_a_trap() -> None:
    """A repaired citation must be forced out of the ledger.

    If `src/a.py -> docs/gone.md` stays accepted after being fixed, re-introducing that exact
    citation later matches a pre-accepted fingerprint and passes silently. So a drain is a
    non-zero gate result (it wants a commit), rc 0 under --monitor (a supervisor counts any
    non-zero toward max_failures, and a monitor that has been switched off measures nothing),
    and after --accept the entry is gone and the citation is catchable again.
    """
    print("a drained entry is not left as a trap:")
    tree = dict(CLEAN_TREE)
    tree["src/a.py"] = '"""A.\n\nRefs: docs/gone-one.md\n"""\n'
    d = tmp_tree(tree)
    run_cli(d, "--adopt", "--reason", "initial adoption")

    (d / "src/a.py").write_text('"""A.\n\nRefs: docs/guide.md\n"""\n')
    run_git(d, "add", "-A")
    run_git(d, "commit", "-qm", "repair")

    rc, rep, _ = run_cli(d)
    check("gate mode: a drain is a non-zero result (exit 2) and says so",
          rc == 2 and rep["verdict"] == "drained", f"rc={rc} verdict={rep.get('verdict')}")
    rc_m, rep_m, _ = run_cli(d, "--monitor")
    check("monitor mode: the same drain exits 0 with the verdict still recorded",
          rc_m == 0 and rep_m["verdict"] == "drained",
          f"rc={rc_m} verdict={rep_m.get('verdict')}")

    rc_a, _, err_a = run_cli(d, "--accept", "--reason", "repaired the citation")
    check("--accept exits 0 and reports what it dropped",
          rc_a == 0 and "-1 dropped as repaired" in err_a, err_a[:160])
    doc = json.loads((d / ".devloop" / "stale-refs.baseline.json").read_text())
    check("the repaired entry is GONE from the ledger", doc["entries"] == [],
          str(doc["entries"]))

    (d / "src/a.py").write_text('"""A.\n\nRefs: docs/gone-one.md\n"""\n')
    run_git(d, "add", "-A")
    run_git(d, "commit", "-qm", "regress")
    rc_r, rep_r, _ = run_cli(d)
    check("re-introducing the once-accepted citation now FAILS (the trap is disarmed)",
          rc_r == 1 and [f["ref"] for f in rep_r["new"]] == ["docs/gone-one.md"],
          f"rc={rc_r} new={[f['ref'] for f in rep_r.get('new', [])]}")


def test_widening_the_config_refuses_until_reaccepted() -> None:
    """The cheapest way to make this gate green is to widen an exemption. Changing the config
    must therefore refuse, not quietly pass with fewer things checked."""
    print("a changed config refuses:")
    tree = dict(CLEAN_TREE)
    tree["src/a.py"] = '"""A.\n\nRefs: docs/gone-one.md\n"""\n'
    d = tmp_tree(tree)
    run_cli(d, "--adopt", "--reason", "initial adoption")
    rc0, _, _ = run_cli(d)
    check("green before the config changes", rc0 == 0, f"rc={rc0}")

    rc, rep, _ = run_cli(d, "--exempt-glob", "docs/**")
    check("widening an exemption exits 3, not 0", rc == 3, f"rc={rc}")
    check("and says the config changed rather than reporting a tree verdict",
          rep["verdict"] == "could_not_run"
          and rep["verdict_reason"].startswith("config_changed"),
          str(rep.get("verdict_reason"))[:90])


def test_resolution_ladder_and_globs() -> None:
    """Resolution rungs that were measured to matter, each with the false positive it prevents.

    `../x` from a subdirectory, a bare directory citation, and a glob. The glob cases are
    separated deliberately: "the pattern matched nothing" and "that file is gone" are different
    repairs, so a glob with no matches gets its own reason plus `parent_exists`, which is the
    fact that tells the two apart.
    """
    print("the resolution ladder:")
    tree = {
        "README.md": "Dirs: `src/` and `docs/`\n",
        "hooks/register.sh": "#!/bin/sh\necho hi\n",
        "hooks/sub/README.md": "Parent script: `../register.sh`\n",
        "docs/adr/0001-first.md": "# a\n",
        "docs/adr/0002-second.md": "# b\n",
        "src/app.py": ('"""App.\n\n'
                       "Refs: docs/adr/*.md\n"
                       "Refs: docs/adr/ADR-*.md\n"
                       "Refs: nowhere/at/all/*.md\n"
                       '"""\n'),
    }
    d = tmp_tree(tree)
    rc, rep, _ = run_cli(d, "--no-ledger")
    refs = {f["ref"]: f for f in rep.get("new", [])}

    check("a `../x` citation resolves against the citing file, not the repo root",
          "../register.sh" not in refs, str(list(refs)))
    check("a bare directory citation resolves by unique suffix",
          "src/" not in refs and "docs/" not in refs, str(list(refs)))
    check("a glob with matches resolves", "docs/adr/*.md" not in refs, str(list(refs)))
    g1 = refs.get("docs/adr/ADR-*.md")
    check("a glob with NO matches gets its own reason, not 'missing'",
          g1 is not None and g1["reason"] == "glob_no_match",
          str(g1.get("reason") if g1 else None))
    check("...and says the parent DOES exist, so the pattern is what is wrong",
          g1 is not None and g1["parent_exists"] is True,
          str(g1.get("parent_exists") if g1 else None))
    g2 = refs.get("nowhere/at/all/*.md")
    check("a glob whose parent is also gone is distinguishable by parent_exists=false",
          g2 is not None and g2["reason"] == "glob_no_match" and g2["parent_exists"] is False,
          str(g2))


def test_mid_merge_tree_refuses() -> None:
    """git triple-lists a conflicted path and still exits 0. No verdict is reported on a tree
    that is halfway between two trees."""
    print("a tree mid-merge:")
    d = tmp_tree({"README.md": "See `docs/gone.md`\nbase\n", "docs/keep.md": "k\n"})
    run_git(d, "checkout", "-qb", "other")
    (d / "README.md").write_text("See `docs/gone.md`\nOTHER\n")
    run_git(d, "commit", "-qam", "other")
    run_git(d, "checkout", "-q", "main")
    (d / "README.md").write_text("See `docs/gone.md`\nMAIN\n")
    run_git(d, "commit", "-qam", "main")
    run_git(d, "merge", "other")
    rc, rep, err = run_cli(d, "--no-ledger")
    check("exit 3, not a verdict about the tree", rc == 3, f"rc={rc}")
    check("the reason names the in-progress operation",
          str(rep.get("verdict_reason", "")).startswith("repo_in_progress"),
          str(rep.get("verdict_reason"))[:90])
    check("'clean' appears nowhere", "clean" not in (json.dumps(rep) + err).lower())


# ----------------------------------------------------------------------- hosting surfaces

def test_importable_entrypoint_is_pure() -> None:
    """A supervisor must be able to host this without shelling out, so scan() returns a
    structured result and does not print or exit."""
    print("the importable entrypoint:")
    import io
    import contextlib
    import stale_refs

    tree = dict(CLEAN_TREE)
    tree["src/rot.py"] = '"""Rot.\n\nRefs: docs/does-not-exist.md\n"""\n'
    d = tmp_tree(tree)

    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            rep = stale_refs.scan(d, stale_refs.Config())
    except SystemExit as e:
        check("scan() does not call sys.exit", False, f"SystemExit({e.code})")
        return
    check("scan() returns a Report without exiting", rep.verdict == "regressed", rep.verdict)
    check("scan() prints nothing to stdout or stderr",
          buf_out.getvalue() == "" and buf_err.getvalue() == "",
          repr(buf_out.getvalue()[:80] + buf_err.getvalue()[:80]))
    check("the Report exposes exit_code and to_dict()",
          rep.exit_code == 1 and isinstance(rep.to_dict(), dict) and rep.to_dict()["schema"],
          str(rep.exit_code))
    d2 = tmp_tree({}, git=False)
    git_init(d2)
    rep2 = stale_refs.scan(d2, stale_refs.Config())
    check("an empty tree returns could_not_run through the library surface too",
          rep2.verdict == "could_not_run" and rep2.exit_code == 3
          and rep2.counts["stale"] is None, rep2.verdict)


def test_report_is_machine_readable_and_stable() -> None:
    """A supervisor diffs two reports, and a ratchet keys off the fingerprints, so an
    unchanged tree must produce an unchanged document apart from its timestamps."""
    print("the report document:")
    tree = dict(CLEAN_TREE)
    tree["src/rot.py"] = '"""Rot.\n\nRefs: docs/does-not-exist.md\n"""\n'
    d = tmp_tree(tree)
    _, r1, _ = run_cli(d, "--no-ledger")
    _, r2, _ = run_cli(d, "--no-ledger")
    for r in (r1, r2):
        r.pop("generated_at", None)
        r.pop("duration_s", None)
        r.pop("root", None)
    check("two runs over an unchanged tree produce an identical document", r1 == r2)
    check("every counter is present on a passing run",
          set(r1["counts"]) >= {"candidates", "resolved", "stale", "new", "exempt"},
          str(sorted(r1["counts"])))
    check("findings are content-addressed for the ratchet",
          all(len(f["fingerprint"]) == 16 for f in r1["new"]))

    out = Path(tempfile.mkdtemp(prefix="stale-refs-out-")) / "report.json"
    _TMP.append(out.parent)
    rc, _, _ = run_cli(d, "--no-ledger", "--json-out", str(out))
    check("--json-out writes a parseable document",
          out.is_file() and json.loads(out.read_text())["schema"] == "devloop.stale_refs/1")


def test_self_test_flag_is_two_sided() -> None:
    """--self-test is the control that ships with the tool. It must pass here, and it must be
    genuinely two-sided rather than a check that cannot fail."""
    print("the shipped --self-test:")
    cp = subprocess.run([sys.executable, str(SR), "--self-test"],
                        capture_output=True, text=True, timeout=120)
    check("--self-test exits 0", cp.returncode == 0, cp.stdout[-300:] + cp.stderr[-300:])
    for needed in ("positive", "negative", "empty-set"):
        check(f"--self-test covers the {needed} control", needed in cp.stdout,
              cp.stdout[:200])


def main() -> int:
    if shutil.which("git") is None:
        # A missing tracked prerequisite must fail, never print PASS on a skip path.
        print("  FAIL git is not installed; these controls cannot run")
        return 1
    for fn in (test_git_exit_zero_on_empty_is_real,
               test_planted_stale_reference_is_found,
               test_clean_corpus_reports_clean,
               test_empty_corpus_fails_rather_than_reporting_clean,
               test_runtime_prefix_path_is_not_reported,
               test_near_miss_suggestion_fires_on_slug_typo,
               test_ratchet_is_itemised_not_a_count,
               test_drained_entry_is_not_left_as_a_trap,
               test_widening_the_config_refuses_until_reaccepted,
               test_resolution_ladder_and_globs,
               test_mid_merge_tree_refuses,
               test_importable_entrypoint_is_pure,
               test_report_is_machine_readable_and_stable,
               test_self_test_flag_is_two_sided):
        fn()
    for d in _TMP:
        shutil.rmtree(d, ignore_errors=True)
    if FAILURES:
        print(f"\ntest_stale_refs: FAIL ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("\ntest_stale_refs: all controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
