#!/usr/bin/env python3
"""
stale_refs.py — a stale-reference monitor for any repository, in any language.

A STALE REFERENCE is a path cited in a comment, a docstring, a file header or a doc that does
not resolve to anything in the tree. They rot silently: the citation still reads as
authoritative long after the file moved, was renamed, or was never built. Nothing fails, so
nobody learns.

This is a GLOBAL check: it knows nothing about any particular project. The corpus is whatever
git tracks, the comment syntax comes from a table keyed by extension, and every per-repo
judgement (which absolute prefixes are real, which prose paths are intentional) is
configuration with a printed count, never a hardcoded assumption.


THE FAILURE THIS IS DESIGNED AGAINST
------------------------------------
An **Empty-Set Pass** (SKILL.md §7): the corpus comes back empty — git refuses, a path filter
is wrong, the glob matched nothing — and a naive scanner reports "0 stale references" and exits
0, which reads *identically* to a clean tree. Three measured ways git produces exactly that,
all verified against git 2.43:

  1. outside a repository .............. rc 128, "fatal: not a git repository"  (the only
                                         case git tells you about)
  2. a valid repo with no commits ...... rc **0**, empty stdout
  3. a pathspec matching nothing ....... rc **0**, empty stdout
     (`git ls-files -- no/such/dir`)

Cases 2 and 3 are byte-identical to "a repo with no files". **Exit status is therefore not a
usable corpus guard.** The guard is a census, in three layers:

  LAYER 1  hard floor .... corpus_files, scanned_files, scanned_bytes, candidate_refs all >= 1.
           `candidates >= 1` is in there deliberately: a tree whose files read fine but
           produced zero path-shaped tokens is a broken extractor, not a clean repo.
  LAYER 2  census ratchet . this run's scanned_files and candidate_refs must each be >= 70% of
           the last accepted run's. A hard floor of "1" happily passes a run that scanned 4
           files out of 3,000; this is what catches that. The floor is `--census-floor`.
  LAYER 3  config fingerprint . the resolved config is hashed into the ledger. Change the
           exemptions and the run REFUSES until a human re-accepts. Without this, the cheapest
           way to make the gate green is to widen an exemption — which is the observed bug in
           reverse, and it would be invisible.

Any layer failing produces verdict `could_not_run`, **exit 3**, and a human line on stderr that
prints the numbers that failed next to the numbers they failed against, echoes the exact command
that built the corpus, and never contains the word "clean". On `could_not_run` every member of
`counts` is `null`, not `0`, so a dashboard cannot average a zero that was never measured.

A fourth refusal has the same shape and the same measured justification: **a repository
mid-rebase or mid-merge**. `git ls-files` prints a conflicted path THREE times (stages 1/2/3)
and exits 0, so a naive corpus triple-counts it — inflating the census and masking a real
shrink — while the working-tree copy is full of conflict markers that manufacture junk tokens.
The corpus always de-duplicates, and an in-progress rebase/merge/cherry-pick/bisect is
`could_not_run`: this does not report a verdict on a tree that is halfway between two trees.


WHAT IT DOES NOT DO
-------------------
It does not resolve imports (a module graph is not a filesystem, and pretending otherwise
produces confident nonsense). It does not follow references into sibling repositories. It does
not rewrite anything: suggestions are hypotheses, labelled with their basis and confidence, and
are never applied. It never runs `git add` and writes nothing outside `--json-out` and the
ledger it is explicitly pointed at. Default extraction is DELIMITED — tokens inside backticks,
markdown links, and explicit citation markers — so a reference written in bare prose is missed.
That is a stated recall limit, not a completeness claim.


SURFACES
--------
  scan(root, config, ledger=None) -> Report    pure; no printing, no exit. The importable one.
  gate(root, config, ledger_path) -> Report    scan + ratchet comparison.
  main(argv) -> int                            CLI: JSON to stdout, human lines to stderr.

Exit codes (the supervisor contract — serverd's `_tick_monitor` treats rc 0 as ok and anything
else as a failure counting toward `max_failures`):
  0  clean
  1  regressed — NEW stale references (the ordinary gate failure)
  2  drained  — the ledger names findings the tree no longer has; run --accept.
                In `--monitor` mode this is rc 0 with verdict "drained" instead: a supervisor
                would trip `failed_permanent` on a bookkeeping lapse, and a monitor that has
                been switched off measures nothing. The gate enforces; the monitor observes.
  3  could_not_run — any census layer tripped, git refused, repo mid-rebase, config changed.
  4  bad usage / internal error.

Supervisor registration (serverd worker schema, ready to paste):
  {"id": "stale-refs", "kind": "monitor", "interval_s": 300, "timeout_s": 120,
   "argv": ["python3", "skills/dev-loop/scripts/stale_refs.py",
            "--monitor", "--json-out", ".devloop/stale-refs.json"]}
`timeout_s <= interval_s` is the supervisor's own rule; the scan is set-based rather than a
stat() per token precisely so it stays inside it.

Run `stale_refs.py --self-test` for the two-sided control: a synthetic tree with a planted
stale reference must exit 1, the same tree repaired must exit 0, and an empty one must exit 3.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

SCHEMA = "devloop.stale_refs/1"
BASELINE_SCHEMA = "devloop.stale_refs.baseline/1"
TOOL_VERSION = "1"

DEFAULT_LEDGER = ".devloop/stale-refs.baseline.json"
CONFIG_CANDIDATES = (".devloop/stale-refs.json", ".devloop/stale-refs.toml")

# --------------------------------------------------------------------------- sibling modules

def _load_git_lock():
    """git_lock.run_git_safe retries through a lane holding index.lock. Concurrent lanes hold
    it by design here, and a raw subprocess would read that contention as a phantom empty
    corpus — the exact Empty-Set Pass this tool exists to refuse. Optional so the scanner still
    runs when vendored into a repo that has no dev-loop scripts beside it."""
    try:
        import git_lock  # type: ignore
        return git_lock
    except ImportError:
        pass
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import git_lock  # type: ignore
        return git_lock
    except ImportError:
        return None


_GIT_LOCK = _load_git_lock()

# --------------------------------------------------------------------------- lexical tables

DOC_EXTENSIONS = frozenset({".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".asciidoc"})

_HASH = (("#",), ())
_SLASH = (("//",), (("/*", "*/"),))
_DASH = (("--",), ())
_SEMI = ((";",), ())
_XML = ((), (("<!--", "-->"),))

# extension -> (line-comment tokens, block (open, close) pairs)
COMMENT_SYNTAX: dict[str, tuple] = {
    ".py": (("#",), (('"""', '"""'), ("'''", "'''"))),
    ".pyi": (("#",), (('"""', '"""'), ("'''", "'''"))),
    ".sh": _HASH, ".bash": _HASH, ".zsh": _HASH, ".ksh": _HASH, ".fish": _HASH,
    ".rb": _HASH, ".pl": _HASH, ".pm": _HASH, ".r": _HASH, ".nu": _HASH,
    ".toml": _HASH, ".yaml": _HASH, ".yml": _HASH, ".ini": _HASH, ".cfg": _HASH,
    ".conf": _HASH, ".properties": _HASH, ".env": _HASH, ".just": _HASH,
    ".mk": _HASH, ".make": _HASH, ".dockerfile": _HASH, ".rules": _HASH,
    ".service": _HASH, ".timer": _HASH, ".socket": _HASH, ".target": _HASH,
    ".mount": _HASH, ".path": _HASH, ".slice": _HASH, ".container": _HASH,
    ".volume": _HASH, ".network": _HASH, ".kube": _HASH, ".pod": _HASH,
    ".ps1": (("#",), (("<#", "#>"),)),
    ".psm1": (("#",), (("<#", "#>"),)),
    ".rs": _SLASH, ".go": _SLASH, ".c": _SLASH, ".h": _SLASH, ".cc": _SLASH,
    ".cpp": _SLASH, ".hpp": _SLASH, ".java": _SLASH, ".cs": _SLASH, ".kt": _SLASH,
    ".swift": _SLASH, ".scala": _SLASH, ".js": _SLASH, ".jsx": _SLASH, ".ts": _SLASH,
    ".tsx": _SLASH, ".mjs": _SLASH, ".cjs": _SLASH, ".css": ((), (("/*", "*/"),)),
    ".scss": _SLASH, ".php": _SLASH, ".dart": _SLASH, ".zig": _SLASH,
    ".sql": (("--",), (("/*", "*/"),)),
    ".lua": (("--",), (("--[[", "]]"),)),
    ".hs": _DASH, ".elm": _DASH, ".ada": _DASH,
    ".el": _SEMI, ".lisp": _SEMI, ".clj": _SEMI, ".scm": _SEMI, ".asm": _SEMI,
    ".tex": (("%",), ()), ".erl": (("%",), ()), ".m": (("%",), ()),
    ".html": _XML, ".htm": _XML, ".xml": _XML, ".xsl": _XML, ".svg": _XML,
    ".vue": _XML, ".svelte": _XML,
}

# Extensionless files that are nonetheless text with a known comment syntax.
BASENAME_SYNTAX: dict[str, tuple] = {
    "makefile": _HASH, "gnumakefile": _HASH, "dockerfile": _HASH, "containerfile": _HASH,
    "justfile": _HASH, "vagrantfile": _HASH, "rakefile": _HASH, "brewfile": _HASH,
    "readme": ((), ()), "license": ((), ()), "notice": ((), ()), "authors": ((), ()),
    "changelog": ((), ()), "codeowners": _HASH, "gitignore": _HASH, "gitattributes": _HASH,
    "agents": ((), ()),
}

# .json/.jsonc/.patch/.diff are deliberately ABSENT: a path inside a JSON value or a diff
# hunk is data being carried, not a claim about the tree, and harvesting it is how a marker
# regex starts reporting patch context as stale references.
DEFAULT_TEXT_EXTENSIONS: tuple[str, ...] = tuple(sorted(set(COMMENT_SYNTAX) | set(DOC_EXTENSIONS)))

# Citation markers. Deliberately generic — a repo's own convention goes in config.
DEFAULT_MARKERS: tuple[str, ...] = ("Refs:", "Ref:", "See-also:", "See also:", "Related:",
                                    "Doc:", "Docs:", "Spec:", "Source:", "Defined-in:")

# Directories never worth walking when git is unavailable.
WALK_PRUNE = frozenset({".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
                        ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "target",
                        "dist", "build", ".worktrees", ".next", ".gradle", "vendor"})

# Consulted ONLY when exempt_absolute is false. /usr is present on purpose: the observed
# field bug was a list holding /etc /var /tmp /proc /sys /run and NOT /usr, which made every
# /usr citation a false positive. Trailing separators are mandatory so /etcetera/foo is not
# swallowed by /etc (the Unanchored Allowlist defect, SKILL.md §7).
DEFAULT_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/proc/", "/sys/", "/dev/", "/run/", "/tmp/", "/var/", "/etc/", "/usr/", "/opt/",
    "/srv/", "/boot/", "/mnt/", "/media/", "/lib/", "/lib64/", "/bin/", "/sbin/",
    "/root/", "/home/", "~/",
)

URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")
WIN_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
EXT_TAIL_RE = re.compile(r"\.[A-Za-z][A-Za-z0-9_+\-]{0,7}$")
# An angle bracket or brace ANYWHERE disqualifies a token. `<name>` is a placeholder; a bare
# trailing `dir>` or `NAME}}` is the right-hand half of one that an extractor split on
# whitespace, and such a fragment resolves to nothing and reads as rot. Measured on this
# repository these two fragment shapes were the largest junk class in bare extraction,
# together 89 of the 137 findings bare mode added (137 -> 48). No real path carries those.
INTERP_RE = re.compile(r"[$<>{}]|%[A-Za-z_][A-Za-z0-9_]*%")
# `[timestamp]`, `[NNN]`, `[feature]` are placeholders. `[ch]` and `[0-9]` are real character
# classes: a placeholder is 3+ characters and starts with a letter or underscore.
PLACEHOLDER_RE = re.compile(r"\[[A-Za-z_][A-Za-z0-9_ .-]{2,}\]")
BACKTICK_RE = re.compile(r"`([^`\n]{1,256})`")
QUOTED_RE = re.compile(r"[\"']([^\"'\n]{1,256})[\"']")
MD_INLINE_RE = re.compile(r"\[[^\]\n]*\]\(\s*<?([^)>\s]{1,256})\s*(?:\"[^\"]*\")?>?\s*\)")
MD_REFDEF_RE = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*<?([^\s>]{1,256})>?")
# Only whitespace and comment-opening punctuation may precede a marker. Measured effect of
# this gate elsewhere: it dropped ~210 marker lines that were markers embedded inside JSON
# string values and .patch hunks, and collapsed the "exotic path syntax" categories by ~96%
# — almost all of which had been extraction failure, not exotic syntax.
MARKER_LEAD_RE = re.compile(r"^[\s\-*#/;<!%\"'>|=+.)\]]*$")
TOKEN_SPLIT_RE = re.compile(r"[,\s;]+")
SLUG_SPLIT_RE = re.compile(r"[^A-Za-z0-9]+")
LEADING_ID_RE = re.compile(r"^([A-Za-z]{0,6}-?\d{2,6})\b")

MAX_TOKEN_BYTES = 256
MAX_SUGGESTION_FINDINGS = 400     # suggestions are the expensive part; bound them explicitly
CENSUS_MIN_SAMPLE = 20            # below this the shrink ratio is noise; see the census check


class ScanError(Exception):
    """A refusal that must never be reported as a verdict about the tree."""

    def __init__(self, reason: str, detail: str, extra: dict | None = None) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.extra = extra or {}


# --------------------------------------------------------------------------------- config

@dataclass(frozen=True)
class Config:
    include_globs: tuple[str, ...] = ()
    exclude_globs: tuple[str, ...] = ()
    text_extensions: tuple[str, ...] = DEFAULT_TEXT_EXTENSIONS
    extraction: str = "delimited"          # "delimited" | "bare"
    markers: tuple[str, ...] = DEFAULT_MARKERS
    scan_quoted: bool = True
    exempt_absolute: bool = True
    exempt_prefixes: tuple[str, ...] = DEFAULT_EXEMPT_PREFIXES
    root_map: tuple[tuple[str, str], ...] = ()
    exempt_globs: tuple[str, ...] = ()
    search_roots: tuple[str, ...] = ()
    suggest: bool = True
    census_floor: float = 0.70
    use_git: bool = True
    allow_untracked: bool = True

    def fingerprint_payload(self) -> dict:
        """Everything that changes WHAT IS CHECKED. Hashed into the ledger so widening an
        exemption cannot silently turn a gate green."""
        return {
            "include_globs": sorted(self.include_globs),
            "exclude_globs": sorted(self.exclude_globs),
            "text_extensions": sorted(self.text_extensions),
            "extraction": self.extraction,
            "markers": sorted(self.markers),
            "scan_quoted": self.scan_quoted,
            "exempt_absolute": self.exempt_absolute,
            "exempt_prefixes": sorted(self.exempt_prefixes),
            "root_map": sorted([list(p) for p in self.root_map]),
            "exempt_globs": sorted(self.exempt_globs),
            "search_roots": sorted(self.search_roots),
            "use_git": self.use_git,
            "allow_untracked": self.allow_untracked,
        }

    def sha256(self) -> str:
        blob = json.dumps(self.fingerprint_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        d = self.fingerprint_payload()
        d["suggest"] = self.suggest
        d["census_floor"] = self.census_floor
        return d


def load_config(root: Path, explicit: Path | None) -> tuple[Config, list[str]]:
    """--config FILE, else .devloop/stale-refs.{json,toml}, else built-in defaults."""
    warnings: list[str] = []
    path = explicit
    if path is None:
        for cand in CONFIG_CANDIDATES:
            p = root / cand
            if p.is_file():
                path = p
                break
    if path is None:
        return Config(), warnings
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise ScanError("config_unreadable", f"--config {path}: {e}") from None
    if path.suffix == ".toml":
        try:
            import tomllib
        except ImportError:
            raise ScanError("config_unreadable",
                            f"{path} is TOML but this interpreter has no tomllib "
                            f"(needs Python 3.11+); use a .json config instead") from None
        try:
            data = tomllib.loads(raw.decode("utf-8"))
        except Exception as e:
            raise ScanError("config_unreadable", f"{path}: {e}") from None
    else:
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise ScanError("config_unreadable", f"{path}: {e}") from None
    if not isinstance(data, dict):
        raise ScanError("config_unreadable", f"{path}: top level must be an object")
    warnings.append(f"config loaded from {path.name}")
    return config_from_dict(data), warnings


def config_from_dict(data: dict, base: Config | None = None) -> Config:
    b = base or Config()

    def tup(key, default):
        v = data.get(key)
        if v is None:
            return default
        if isinstance(v, str):
            return (v,)
        return tuple(str(x) for x in v)

    rm = data.get("root_map")
    root_map = b.root_map
    if isinstance(rm, dict):
        root_map = tuple(sorted((str(k), str(v)) for k, v in rm.items()))
    elif isinstance(rm, list):
        root_map = tuple(sorted((str(a), str(c)) for a, c in rm))
    extraction = str(data.get("extraction", b.extraction))
    if extraction not in ("delimited", "bare"):
        raise ScanError("bad_config", f"extraction must be 'delimited' or 'bare', got {extraction!r}")
    floor = float(data.get("census_floor", b.census_floor))
    if not 0.0 < floor <= 1.0:
        raise ScanError("bad_config", f"census_floor must be in (0,1], got {floor}")
    return Config(
        include_globs=tup("include_globs", b.include_globs),
        exclude_globs=tup("exclude_globs", b.exclude_globs),
        text_extensions=tup("text_extensions", b.text_extensions),
        extraction=extraction,
        markers=tup("markers", b.markers),
        scan_quoted=bool(data.get("scan_quoted", b.scan_quoted)),
        exempt_absolute=bool(data.get("exempt_absolute", b.exempt_absolute)),
        exempt_prefixes=tup("exempt_prefixes", b.exempt_prefixes),
        root_map=root_map,
        exempt_globs=tup("exempt_globs", b.exempt_globs),
        search_roots=tup("search_roots", b.search_roots),
        suggest=bool(data.get("suggest", b.suggest)),
        census_floor=floor,
        use_git=bool(data.get("use_git", b.use_git)),
        allow_untracked=bool(data.get("allow_untracked", b.allow_untracked)),
    )


# --------------------------------------------------------------------------------- corpus

@dataclass
class Corpus:
    root: Path
    files: tuple[str, ...]
    index: frozenset[str]
    by_basename: dict[str, tuple[str, ...]]
    by_dirname: dict[str, tuple[str, ...]]
    lower_index: dict[str, str]
    source: str
    built_by: str
    warnings: list[str] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    skipped_by_extension: int = 0


IN_PROGRESS_MARKERS = (("rebase-merge", "rebase"), ("rebase-apply", "rebase"),
                       ("MERGE_HEAD", "merge"), ("CHERRY_PICK_HEAD", "cherry-pick"),
                       ("REVERT_HEAD", "revert"), ("BISECT_LOG", "bisect"))


def _git_dir(root: Path) -> Path | None:
    """Quiet probe first. git_lock.resolve_git_dir() leaks 'fatal: not a git repository' onto
    our stderr when there is no repo, and a monitor's stderr is read by a human."""
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None
    gd = Path(p.stdout.strip())
    return gd if gd.is_absolute() else (root / gd)


def _run_git(args: list[str], root: Path) -> subprocess.CompletedProcess:
    if _GIT_LOCK is not None:
        return _GIT_LOCK.run_git_safe(args, cwd=root)
    env = {**os.environ, "CI": "1", "GIT_TERMINAL_PROMPT": "0", "NO_COLOR": "1"}
    return subprocess.run(["git", "-C", str(root)] + args, capture_output=True, text=True, env=env)


def _wanted(rel: str, cfg: Config) -> bool:
    if cfg.exclude_globs and any(fnmatch.fnmatch(rel, g) for g in cfg.exclude_globs):
        return False
    if cfg.include_globs and not any(fnmatch.fnmatch(rel, g) for g in cfg.include_globs):
        return False
    return True


def _is_text(rel: str, cfg: Config) -> bool:
    name = rel.rsplit("/", 1)[-1]
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    if ext and ext in cfg.text_extensions:
        return True
    return name.lower().lstrip(".") in BASENAME_SYNTAX


def enumerate_corpus(root: Path, cfg: Config) -> Corpus:
    """The tracked tree, once, as a frozen record. Raises ScanError rather than returning an
    empty corpus for any condition that means "I could not look"."""
    warnings: list[str] = []
    if cfg.use_git:
        gd = _git_dir(root)
        if gd is None:
            raise ScanError("git_unavailable",
                            f"{root} is not a git repository (git rev-parse --git-dir failed). "
                            "Pass --no-git to walk the filesystem instead; it is opt-in "
                            "because a silent fallback would report a broken git as a "
                            "healthy tree.")
        for marker, what in IN_PROGRESS_MARKERS:
            if (gd / marker).exists():
                raise ScanError("repo_in_progress",
                                f"{gd / marker} exists: this tree is mid-{what}. git ls-files "
                                "lists a conflicted path three times (stages 1/2/3) and still "
                                "exits 0, and the working copy carries conflict markers. No "
                                "verdict is reported on a tree halfway between two trees.")
        unmerged = _run_git(["ls-files", "-u"], root)
        if unmerged.returncode == 0 and unmerged.stdout.strip():
            n = len(set(unmerged.stdout.splitlines()))
            raise ScanError("repo_in_progress",
                            f"git ls-files -u reports {n} unmerged path record(s): the tree has "
                            "conflicts. No verdict is reported on a tree halfway between two trees.")
        args = ["ls-files", "-z", "--cached"]
        if cfg.allow_untracked:
            args += ["--others", "--exclude-standard"]
        if cfg.include_globs:
            args += ["--"] + list(cfg.include_globs)
        built_by = "git " + " ".join(args)
        proc = _run_git(args, root)
        if proc.returncode != 0:
            raise ScanError("git_refused",
                            f"`{built_by}` exited {proc.returncode}: "
                            f"{(proc.stderr or '').strip()[:400]}")
        # NUL-delimited on purpose: paths with spaces and newlines are ordinary, and a
        # newline-split enumerator truncates the corpus without saying so. De-duplicated on
        # purpose: see repo_in_progress above.
        raw = [p for p in proc.stdout.split("\0") if p]
        rels = sorted(set(raw))
        if len(raw) != len(rels):
            warnings.append(f"git listed {len(raw)} rows for {len(rels)} distinct paths "
                            "(duplicates collapsed)")
        source = "git"
    else:
        built_by = f"os.walk({root}) with prune set"
        rels = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in WALK_PRUNE]
            for fn in filenames:
                full = Path(dirpath) / fn
                try:
                    rel = full.relative_to(root).as_posix()
                except ValueError:
                    continue
                rels.append(rel)
        rels = sorted(set(rels))
        source = "walk"
        warnings.append("corpus built by filesystem walk, not git: ignored and generated files "
                        "may be present and can satisfy a citation that git would not")

    rels = [r for r in rels if _wanted(r, cfg)]

    index: set[str] = set()
    by_basename: dict[str, list[str]] = {}
    dirs: set[str] = set()
    for rel in rels:
        index.add(rel)
        by_basename.setdefault(rel.rsplit("/", 1)[-1], []).append(rel)
        parts = rel.split("/")
        for i in range(1, len(parts)):
            d = "/".join(parts[:i])
            index.add(d)
            index.add(d + "/")
            dirs.add(d)
    # A directory is a legitimate citation target that a FILE list can never contain, so the
    # implied directories are synthesised and indexed by basename too. Without this, `scripts/`
    # -- a directory that exists at exactly one place in the tree -- is reported stale.
    by_dirname: dict[str, list[str]] = {}
    for d in dirs:
        by_dirname.setdefault(d.rsplit("/", 1)[-1], []).append(d)
    lower_index = {}
    for p in index:
        lower_index.setdefault(p.lower(), p)

    return Corpus(root=root, files=tuple(rels), index=frozenset(index),
                  by_basename={k: tuple(sorted(v)) for k, v in by_basename.items()},
                  by_dirname={k: tuple(sorted(v)) for k, v in by_dirname.items()},
                  lower_index=lower_index, source=source, built_by=built_by,
                  warnings=warnings)


# ----------------------------------------------------------------------------- extraction

def comment_regions(lines: Sequence[str], rel: str, cfg: Config) -> list[tuple[int, str]]:
    """(line_number, text) for every region a path citation can legitimately live in.

    Docs are read whole. Source files contribute only comment and docstring text: a path in
    live code is an argument being passed, not a claim about the tree, and scanning it is what
    turns `git add`, `origin/main` and `a/b` ratios into "stale references".

    A line-1 shebang is skipped outright — it cites an interpreter, not an artifact.
    """
    name = rel.rsplit("/", 1)[-1]
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    if ext in DOC_EXTENSIONS or name.lower().lstrip(".") in ("readme", "license", "notice",
                                                             "changelog", "authors", "agents"):
        return [(i + 1, ln) for i, ln in enumerate(lines)]

    syntax = COMMENT_SYNTAX.get(ext)
    if syntax is None:
        syntax = BASENAME_SYNTAX.get(name.lower().lstrip("."), _HASH)
    line_toks, blocks = syntax
    out: list[tuple[int, str]] = []
    open_block: tuple[str, str] | None = None

    for i, line in enumerate(lines):
        if i == 0 and line.startswith("#!"):
            continue
        pos = 0
        n = len(line)
        while pos < n:
            if open_block is not None:
                close = open_block[1]
                j = line.find(close, pos)
                if j < 0:
                    out.append((i + 1, line[pos:]))
                    pos = n
                else:
                    out.append((i + 1, line[pos:j]))
                    pos = j + len(close)
                    open_block = None
                continue
            best = n
            best_kind: tuple | None = None
            for tok in line_toks:
                j = line.find(tok, pos)
                if 0 <= j < best:
                    best, best_kind = j, ("line", tok)
            for pair in blocks:
                j = line.find(pair[0], pos)
                if 0 <= j < best:
                    best, best_kind = j, ("block", pair)
            if best_kind is None:
                break
            if best_kind[0] == "line":
                out.append((i + 1, line[best + len(best_kind[1]):]))
                pos = n
            else:
                pair = best_kind[1]
                pos = best + len(pair[0])
                open_block = pair
    return out


def _span_pieces(span: str) -> list[str]:
    """A delimited span, plus each whitespace-separated word inside it.

    Measured on this repository: 444 discarded tokens contained a slash, and the largest class
    was a command line whose ARGUMENT is a real path (`sh skills/dev-loop/scripts/validate.sh`)
    -- rejected whole because the shape filter forbids whitespace. Splitting is safe HERE and
    not in prose because the delimiter already established a code context; the shape filter
    still has to accept each piece. Effect measured below in the docstring's recall note.
    """
    span = span.strip()
    if not span:
        return []
    out = [span]
    if any(c.isspace() for c in span) and not INTERP_RE.search(span):
        # The interpolation guard is load-bearing and was added from measurement, not caution:
        # splitting an angle-bracket placeholder followed by a path yields a fragment that
        # no longer carries the sigil marking it uninterpretable, and it is duly reported
        # stale. That one pattern manufactured 79 of
        # the 83 findings the split added on this repository. Interpolation is a property of
        # the WHOLE span, so it must be tested before the span is taken apart.
        out.extend(w for w in span.split() if "/" in w)
    return out


@dataclass
class Candidate:
    file: str
    line: int
    raw: str
    extractor: str


def extract_candidates(rel: str, lines: Sequence[str], cfg: Config) -> list[Candidate]:
    """Delimited by default: backticks, markdown link targets, quoted strings, and explicit
    citation-marker payloads.

    Measured elsewhere on a 3,147-file tree: bare-token extraction produced 54,205 raw
    candidates against 14,709 for delimited, and the extra half was visibly junk — an
    interpolation whose sigil had been stripped, bare command names, tool lists. `--extraction
    bare` exists and is off.
    """
    out: list[Candidate] = []
    for lineno, text in comment_regions(lines, rel, cfg):
        if not text or "/" not in text:
            if not any(m in text for m in cfg.markers):
                continue
        for m in MD_INLINE_RE.finditer(text):
            out.append(Candidate(rel, lineno, m.group(1), "md_link"))
        m = MD_REFDEF_RE.match(text)
        if m:
            out.append(Candidate(rel, lineno, m.group(1), "md_link"))
        for m in BACKTICK_RE.finditer(text):
            for piece in _span_pieces(m.group(1)):
                out.append(Candidate(rel, lineno, piece, "code_span"))
        if cfg.scan_quoted:
            for m in QUOTED_RE.finditer(text):
                for piece in _span_pieces(m.group(1)):
                    out.append(Candidate(rel, lineno, piece, "quoted"))
        for marker in cfg.markers:
            idx = text.find(marker)
            if idx < 0:
                continue
            if not MARKER_LEAD_RE.match(text[:idx]):
                continue      # the comment-context gate; see MARKER_LEAD_RE
            payload = text[idx + len(marker):]
            # Bound the payload. Without this a marker inside an embedded script swallows the
            # rest of the body as one "path": measured elsewhere, bounding cut raw marker
            # tokens from 24,097 to 10,552 — more than half were runaway payload.
            for stop in ("-->", "*/", "\\n", "  #", "#>"):
                k = payload.find(stop)
                if k >= 0:
                    payload = payload[:k]
            for tok in TOKEN_SPLIT_RE.split(payload):
                tok = tok.strip("`'\"<>()[]")
                if tok:
                    out.append(Candidate(rel, lineno, tok, "marker"))
        if cfg.extraction == "bare":
            for tok in TOKEN_SPLIT_RE.split(text):
                tok = tok.strip("`'\"<>()[]")
                if tok and "/" in tok:
                    out.append(Candidate(rel, lineno, tok, "bare"))
    return out


# ------------------------------------------------------------------------- classification

def normalize_token(raw: str) -> str:
    t = raw.strip().strip("`\"'")
    t = t.lstrip("([{")
    t = t.strip("`\"'")
    t = t.rstrip(".,:;!?")
    t = t.rstrip(")]}>")
    for cut in ("#", "?"):
        k = t.find(cut)
        if k > 0:
            t = t[:k]
    return t


def collapse(path: str) -> str | None:
    """Lexical collapse of . and .. — never Path.resolve(). A symlinked directory would rewrite
    the cited path into its target mid-walk, and the citation as written is what a reader
    follows. Returns None when the path escapes the root."""
    parts: list[str] = []
    for seg in path.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts)


def classify(token: str, cfg: Config) -> tuple[str, str]:
    """-> (class, token). class is one of: url, interpolated, absolute, glob, path, not_a_path."""
    if not token or len(token.encode("utf-8", "replace")) > MAX_TOKEN_BYTES:
        return "not_a_path", token
    if any(c.isspace() for c in token):
        return "not_a_path", token
    if URL_RE.match(token) or token.startswith(("mailto:", "git@", "ssh://")) or "://" in token:
        return "url", token
    if INTERP_RE.search(token):
        return "interpolated", token
    if token.startswith(("/", "~", "\\\\")) or WIN_ABS_RE.match(token):
        for pre, sub in cfg.root_map:
            if token.startswith(pre):
                return classify(sub + token[len(pre):], cfg)
        return "absolute", token
    t = token.replace("\\", "/")
    if "/" not in t:
        return "not_a_path", t
    tail = t.rstrip("/").rsplit("/", 1)[-1]
    if not (t.endswith("/") or EXT_TAIL_RE.search(tail)):
        return "not_a_path", t
    if not re.search(r"[A-Za-z]", t):
        return "not_a_path", t          # 38431/39903, 3/5/10, T-1046/T-1048
    if PLACEHOLDER_RE.search(t):
        return "interpolated", t
    if any(c in t for c in "*?[]"):
        return "glob", t
    return "path", t


# ---------------------------------------------------------------------------- resolution

def _glob_re(pattern: str) -> re.Pattern:
    """fnmatch's `*` matches `/`, which makes every glob far too greedy. `**` spans separators;
    `*` and `?` do not."""
    out, i, n = [], 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < n and pattern[i] == "/":
                    i += 1
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "[":
            j = pattern.find("]", i + 1)
            if j < 0:
                out.append(re.escape(c))
            else:
                out.append("[" + pattern[i + 1:j].replace("\\", "\\\\") + "]")
                i = j + 1
                continue
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def suffix_matches(token: str, corpus: Corpus, is_dir: bool = False) -> tuple[str, ...]:
    """Tracked paths ending with `token` on a `/` boundary. A trailing slash in the citation
    means a directory and nothing else; otherwise files are searched, then directories."""
    t = token.rstrip("/")
    if not t:
        return ()
    base = t.rsplit("/", 1)[-1]
    cands = list(corpus.by_dirname.get(base, ())) if is_dir else (
        list(corpus.by_basename.get(base, ())) + list(corpus.by_dirname.get(base, ())))
    return tuple(p for p in cands if p == t or p.endswith("/" + t))


@dataclass
class Resolution:
    status: str          # resolved | stale
    rung: str | None
    reason: str | None
    target: str | None = None
    candidates: tuple[str, ...] = ()
    parent_exists: bool | None = None


def resolve(token: str, kind: str, citing: str, corpus: Corpus, cfg: Config) -> Resolution:
    """A ladder. The rung that fired is recorded: "resolved" and "resolved only by guessing the
    anchor" are different facts, and a resolution whose provenance is unknown cannot be
    reviewed."""
    citing_dir = citing.rsplit("/", 1)[0] if "/" in citing else ""
    anchors = [token]
    if citing_dir:
        anchors.append(citing_dir + "/" + token)
    for sr in cfg.search_roots:
        anchors.append(sr.rstrip("/") + "/" + token)
    rungs = ["root", "sibling"] + ["search_root"] * len(cfg.search_roots)

    if kind == "glob":
        for anchor, rung in zip(anchors, rungs):
            c = collapse(anchor)
            if c is None:
                continue
            rx = _glob_re(c)
            if any(rx.match(p) for p in corpus.index):
                return Resolution("resolved", f"glob_{rung}", None, target=c)
        c0 = collapse(token) or token
        parent = c0.rsplit("/", 1)[0] if "/" in c0 else ""
        # Two different repairs hide behind one reason string: parent_exists:false says the
        # directory is gone (fix the directory), parent_exists:true says the pattern is wrong
        # (fix the pattern). The observed field case had neither.
        return Resolution("stale", None, "glob_no_match",
                          parent_exists=bool(parent and parent in corpus.index))

    # `../x` cited from a subdirectory escapes the ROOT anchor and resolves against the
    # SIBLING one. Letting the first anchor decide reported every such citation as
    # escapes_root; measured on this repository that was 9 findings, all false, all of them
    # files that are tracked one level up. escapes_root is only true when NO anchor collapses.
    collapsed: list[str] = []
    for anchor, rung in zip(anchors, rungs):
        c = collapse(anchor)
        if c is None:
            continue
        collapsed.append(c)
        if c in corpus.index or (c.rstrip("/") in corpus.index and c.endswith("/")):
            return Resolution("resolved", rung, None, target=c)

    if not collapsed:
        return Resolution("stale", None, "escapes_root")
    c0 = collapse(token) or collapsed[0]

    # The single highest-value rung. Resolving only at the repo root reports every doc that
    # cites a path relative to its own subtree as stale; measured on this repository, that was
    # 49 of 110 apparent findings (44%), all false.
    sm = suffix_matches(c0, corpus, is_dir=token.endswith("/"))
    if len(sm) == 1:
        return Resolution("resolved", "suffix_unique", None, target=sm[0])
    if len(sm) > 1:
        return Resolution("resolved", "suffix_ambiguous", None, candidates=sm[:8])

    lower = corpus.lower_index.get(c0.lower())
    if lower is not None:
        # Resolved, and flagged: it works on a case-insensitive filesystem and breaks in CI.
        # Reporting it as ok hides a portability bug; reporting it as missing misdescribes it.
        return Resolution("resolved", "case_mismatch", "case_mismatch", target=lower)

    if cfg.allow_untracked and corpus.source == "git":
        try:
            if (corpus.root / c0).exists():
                return Resolution("resolved", "untracked_present", None, target=c0)
        except OSError:
            # Measured: a malformed 4KB token raised ENAMETOOLONG here. An unhandled OSError
            # kills the monitor, and a dead monitor reports nothing.
            pass

    parent = c0.rsplit("/", 1)[0] if "/" in c0 else ""
    return Resolution("stale", None, "unresolved",
                      parent_exists=bool(parent and parent in corpus.index))


# --------------------------------------------------------------------------- suggestions

def _shared_tail(cited_segs: list[str], candidate: str) -> int:
    """How many trailing path segments the citation and the candidate agree on."""
    cand = candidate.strip("/").split("/")
    n = 0
    for a, b in zip(reversed(cited_segs), reversed(cand)):
        if a != b:
            break
        n += 1
    return n


def suggest(token: str, corpus: Corpus) -> dict | None:
    """Three ranked signals. Plain difflib is rejected by measurement, not by taste: on the
    real observed case — a doc cited by a guessed title — SequenceMatcher scores the TRUE pair
    at 0.746 while scoring false pairs HIGHER (hardware.md~hardware.rs 0.818,
    cluster.md~user.md 0.824). No global character-similarity cutoff separates them, so a
    threshold tuned to admit the real match admits every wrong one."""
    c0 = collapse(token) or token
    base = c0.rsplit("/", 1)[-1]
    ext = ("." + base.rsplit(".", 1)[-1]) if "." in base else ""
    directory = c0.rsplit("/", 1)[0] if "/" in c0 else ""

    same_name = corpus.by_basename.get(base, ()) or corpus.by_dirname.get(base, ())
    if same_name:
        # Rank by SHARED TRAILING PATH SEGMENTS, not by sort order. Measured on this
        # repository, taking the first match suggested `skills/backlog/SKILL.md` for a
        # citation to `<harness>/skills/dev-loop/SKILL.md` -- confidently, and wrong, when
        # `skills/dev-loop/SKILL.md` was right there sharing two more segments. Confidence
        # scales with the evidence: a basename alone is a weak hypothesis, not a 0.95 one.
        cited_segs = c0.strip("/").split("/")
        ranked = sorted(same_name, key=lambda p: (-_shared_tail(cited_segs, p), p))
        depth = _shared_tail(cited_segs, ranked[0])
        conf = {1: 0.60, 2: 0.80}.get(depth, 0.95 if depth >= 3 else 0.60)
        return {"path": ranked[0], "confidence": conf,
                "basis": f"exact_basename(shared_tail_segments={depth})",
                "alternatives": list(ranked[1:4])}

    siblings = [p for p in corpus.files
                if (p.rsplit("/", 1)[0] if "/" in p else "") == directory and p != c0]
    if not siblings and directory:
        anc = directory
        while "/" in anc and anc not in corpus.index:
            anc = anc.rsplit("/", 1)[0]
        if anc in corpus.index:
            siblings = [p for p in corpus.files
                        if (p.rsplit("/", 1)[0] if "/" in p else "") == anc]
    siblings = [p for p in siblings if p.endswith(ext)] if ext else siblings
    if not siblings:
        return None

    cited_id = LEADING_ID_RE.match(base)
    cited_tokens = {t for t in SLUG_SPLIT_RE.split(base.lower()) if t}

    best = None
    for p in siblings:
        pb = p.rsplit("/", 1)[-1]
        pid = LEADING_ID_RE.match(pb)
        if cited_id and pid and cited_id.group(1).lower() == pid.group(1).lower():
            return {"path": p, "confidence": 0.85, "basis": "shared_id+extension",
                    "alternatives": []}
        toks = {t for t in SLUG_SPLIT_RE.split(pb.lower()) if t}
        if not toks or not cited_tokens:
            continue
        j = len(cited_tokens & toks) / len(cited_tokens | toks)
        if best is None or j > best[1]:
            best = (p, j)
    if best and best[1] >= 0.55:
        return {"path": best[0], "confidence": round(0.60 + 0.20 * best[1], 3),
                "basis": f"token_overlap(jaccard={best[1]:.3f})", "alternatives": []}
    return None


# -------------------------------------------------------------------------------- report

def fingerprint(file: str, ref: str, reason: str) -> str:
    h = hashlib.sha256(f"{file}\0{ref}\0{reason}".encode("utf-8")).hexdigest()
    return h[:16]


@dataclass
class Report:
    root: str
    verdict: str
    verdict_reason: str
    exit_code: int
    corpus: dict
    census_baseline: dict | None
    config_sha256: str
    config: dict
    counts: dict
    exempt: dict
    extractor_yield: dict
    new: list
    drained: list
    debt: dict
    warnings: list
    generated_at: str
    duration_s: float

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA, "tool_version": TOOL_VERSION,
            "generated_at": self.generated_at, "root": self.root,
            "verdict": self.verdict, "verdict_reason": self.verdict_reason,
            "exit_code": self.exit_code, "duration_s": self.duration_s,
            "corpus": self.corpus, "census_baseline": self.census_baseline,
            "config_sha256": self.config_sha256, "config": self.config,
            "counts": self.counts, "exempt": self.exempt,
            "extractor_yield": self.extractor_yield,
            "new": self.new, "drained": self.drained, "debt": self.debt,
            "warnings": self.warnings,
        }

    def human(self) -> str:
        if self.verdict == "could_not_run":
            lines = [f"stale_refs: COULD NOT RUN (exit {self.exit_code}) -- {self.verdict_reason}"]
            for k, v in (self.corpus.get("census_detail") or {}).items():
                lines.append(f"    {k}")
            lines.append(f"    corpus built by: {self.corpus.get('built_by')}")
            lines.append("    This run examined almost nothing. It is NOT reporting a healthy tree.")
            lines.append('    Fix the filter, or re-accept with: '
                         'stale_refs.py --accept --reason "<why the tree changed>"')
            return "\n".join(lines)
        c = self.counts
        head = {"clean": "ok", "regressed": "REGRESSED", "drained": "DRAINED"}[self.verdict]
        lines = [
            f"stale_refs: {head} -- {c['candidates']} path citations examined in "
            f"{self.corpus['scanned_files']} of {self.corpus['corpus_files']} files "
            f"({self.corpus['lines']} lines); {c['resolved']} resolved, {c['stale']} stale, "
            f"{c['new']} new, {c['drained']} drained."
        ]
        ex = self.exempt
        if ex.get("total"):
            lines.append(f"    {ex['total']} references were NOT checked "
                         f"(absolute/interpolated paths; set root_map to check them): "
                         + ", ".join(f"{k}={v}" for k, v in
                                     sorted(ex.get("by_prefix", {}).items(),
                                            key=lambda kv: -kv[1])[:6]))
        for f in self.new[:20]:
            sug = f.get("suggestion")
            tail = f"  -> {sug['path']} ({sug['basis']}, {sug['confidence']})" if sug else ""
            lines.append(f"    {f['file']}:{f['line']}: {f['ref']} [{f['reason']}]{tail}")
        if len(self.new) > 20:
            lines.append(f"    ... and {len(self.new) - 20} more new")
        for d in self.drained[:10]:
            lines.append(f"    drained: {d['file']}: {d['ref']} (accepted {d.get('first_seen')})")
        if self.debt.get("distinct"):
            lines.append(f"    debt: {self.debt['total']} accepted citation(s) over "
                         f"{self.debt['distinct']} distinct references; oldest "
                         f"{self.debt.get('oldest_first_seen')}")
        for w in self.warnings:
            lines.append(f"    note: {w}")
        return "\n".join(lines)


NULL_COUNTS = {k: None for k in ("candidates", "resolved", "exempt", "not_a_path", "stale",
                                 "new", "baselined", "drained", "ambiguous", "glob_no_match",
                                 "untracked_present", "case_mismatch")}


def _refusal(root: Path, cfg: Config, reason: str, detail: str, extra: dict,
             started: float, warnings: list[str]) -> Report:
    corpus = {"corpus_files": None, "scanned_files": None, "scanned_bytes": None,
              "lines": None, "source": None, "built_by": extra.get("built_by"),
              "unreadable": extra.get("unreadable", []),
              "skipped_by_extension": None,
              "census_detail": extra.get("census_detail", {})}
    return Report(root=str(root), verdict="could_not_run",
                  verdict_reason=f"{reason}: {detail}", exit_code=3, corpus=corpus,
                  census_baseline=extra.get("census_baseline"),
                  config_sha256=cfg.sha256(), config=cfg.to_dict(),
                  counts=dict(NULL_COUNTS), exempt={"total": None}, extractor_yield={},
                  new=[], drained=[], debt={}, warnings=warnings,
                  generated_at=_iso(), duration_s=round(time.time() - started, 3))


def _iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ------------------------------------------------------------------------------- the scan

def scan(root: Path, cfg: Config | None = None, ledger: dict | None = None,
         monitor: bool = False) -> Report:
    """The importable entrypoint. Pure: reads the tree, returns a Report, prints nothing and
    never calls sys.exit."""
    started = time.time()
    cfg = cfg or Config()
    root = Path(root).resolve()
    warnings: list[str] = []

    try:
        corpus = enumerate_corpus(root, cfg)
    except ScanError as e:
        return _refusal(root, cfg, e.reason, e.detail, e.extra, started, warnings)
    warnings.extend(corpus.warnings)

    scanned: list[str] = []
    scanned_bytes = 0
    total_lines = 0
    candidates: list[Candidate] = []
    unreadable: list[str] = []
    skipped_ext = 0

    for rel in corpus.files:
        if not _is_text(rel, cfg):
            skipped_ext += 1
            continue
        p = corpus.root / rel
        try:
            data = p.read_bytes()
        except OSError as e:
            # "I did not read the whole corpus" is the honest statement, and a missed file is
            # silently a missed reference.
            unreadable.append(f"{rel}: {type(e).__name__}")
            continue
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines()
        scanned.append(rel)
        scanned_bytes += len(data)
        total_lines += len(lines)
        candidates.extend(extract_candidates(rel, lines, cfg))

    corpus_info = {
        "corpus_files": len(corpus.files), "scanned_files": len(scanned),
        "scanned_bytes": scanned_bytes, "lines": total_lines,
        "skipped_by_extension": skipped_ext, "unreadable": unreadable,
        "source": corpus.source, "built_by": corpus.built_by,
    }

    if unreadable:
        return _refusal(root, cfg, "corpus_unreadable",
                        f"{len(unreadable)} tracked text file(s) could not be read: "
                        f"{', '.join(unreadable[:5])}",
                        {"built_by": corpus.built_by, "unreadable": unreadable},
                        started, warnings)

    # ---- classification ----------------------------------------------------------------
    exempt_by_prefix: dict[str, int] = {}
    exempt_absolute = exempt_interp = 0
    not_a_path = 0
    path_cands: list[tuple[Candidate, str, str]] = []
    yields: dict[str, int] = {}

    for cand in candidates:
        tok = normalize_token(cand.raw)
        kind, tok = classify(tok, cfg)
        if kind in ("not_a_path", "url"):
            not_a_path += 1
            continue
        if kind == "interpolated":
            exempt_interp += 1
            continue
        if kind == "absolute":
            pre = "/" + tok.lstrip("/~\\").split("/", 1)[0] + "/" if len(tok) > 1 else tok
            if not cfg.exempt_absolute:
                hit = next((p for p in cfg.exempt_prefixes if tok.startswith(p)), None)
                if hit is None:
                    # exempt_absolute is off and no configured prefix claims it: check it as a
                    # repo-root-relative path.
                    kind, tok = "path", tok.lstrip("/")
                    path_cands.append((cand, tok, kind))
                    yields[cand.extractor] = yields.get(cand.extractor, 0) + 1
                    continue
                pre = hit
            exempt_absolute += 1
            exempt_by_prefix[pre] = exempt_by_prefix.get(pre, 0) + 1
            continue
        if cfg.exempt_globs and any(fnmatch.fnmatch(tok, g) for g in cfg.exempt_globs):
            exempt_by_prefix["<exempt_globs>"] = exempt_by_prefix.get("<exempt_globs>", 0) + 1
            exempt_absolute += 1
            continue
        path_cands.append((cand, tok, kind))
        yields[cand.extractor] = yields.get(cand.extractor, 0) + 1

    n_candidates = len(path_cands)

    # ---- LAYER 1: the hard floor ---------------------------------------------------------
    floor_fail = None
    if corpus_info["corpus_files"] < 1:
        floor_fail = ("empty_corpus", "the corpus holds 0 files")
    elif corpus_info["scanned_files"] < 1:
        floor_fail = ("empty_scan", f"0 of {corpus_info['corpus_files']} corpus files were "
                                    "scanned: every one was excluded by a filter or by the "
                                    "text-extension list")
    elif corpus_info["scanned_bytes"] < 1:
        floor_fail = ("empty_scan", "scanned 0 bytes")
    elif n_candidates < 1:
        floor_fail = ("no_references_found",
                      f"{corpus_info['scanned_files']} file(s) scanned but 0 path-shaped "
                      f"citations were extracted (extraction={cfg.extraction}); that is a "
                      "broken extractor or a filtered corpus, not a healthy tree")
    if floor_fail:
        detail = {
            "built_by": corpus.built_by,
            "census_detail": {
                f"corpus_files   {corpus_info['corpus_files']}": "",
                f"scanned_files  {corpus_info['scanned_files']}": "",
                f"scanned_bytes  {corpus_info['scanned_bytes']}": "",
                f"candidate_refs {n_candidates}": "",
                "hard floor for each: >= 1": "",
            },
        }
        return _refusal(root, cfg, floor_fail[0], floor_fail[1], detail, started, warnings)

    # ---- LAYER 3: config fingerprint -----------------------------------------------------
    baseline_census = (ledger or {}).get("census")
    if ledger is not None:
        recorded = ledger.get("config_sha256")
        if recorded and recorded != cfg.sha256():
            return _refusal(root, cfg, "config_changed",
                            f"the resolved config hashes to {cfg.sha256()[:12]} but the ledger "
                            f"was accepted against {str(recorded)[:12]}. Widening an exemption "
                            "is the cheapest way to make this gate green, so it refuses until "
                            'a human runs --accept --reason "<why>".',
                            {"built_by": corpus.built_by, "census_baseline": baseline_census},
                            started, warnings)

    # ---- LAYER 2: the census ratchet -----------------------------------------------------
    if baseline_census:
        checks = []
        for key, now in (("scanned_files", corpus_info["scanned_files"]),
                         ("candidate_refs", n_candidates)):
            was = baseline_census.get(key)
            if not was:
                continue
            if was < CENSUS_MIN_SAMPLE:
                # A ratio guard is noise at small N. Measured on a 3-file fixture: repairing
                # ONE of three references is a 33% drop and tripped `corpus_shrank`, which
                # masked the `drained` verdict the run should have reported. The guard exists
                # to catch a corpus COLLAPSE, so below the sample floor it is switched off and
                # SAID to be off rather than applied to numbers too small to mean anything.
                warnings.append(f"census check for {key} is inactive: baseline {was} is below "
                                f"the minimum sample of {CENSUS_MIN_SAMPLE}; only the hard "
                                f"floor (>= 1) guards this run")
                continue
            checks.append((key, now, was, now / was))
        bad = [c for c in checks if c[3] < cfg.census_floor]
        if bad:
            detail = {
                "built_by": corpus.built_by, "census_baseline": baseline_census,
                "census_detail": {
                    f"{k:<15}{now:<8} baseline {was:<8} "
                    f"({pct * 100:.1f}% of baseline, floor {cfg.census_floor * 100:.0f}%)": ""
                    for k, now, was, pct in checks},
            }
            return _refusal(root, cfg, "corpus_shrank",
                            "; ".join(f"{k} fell to {pct * 100:.1f}% of baseline ({now} vs {was})"
                                      for k, now, was, pct in bad),
                            detail, started, warnings)
    elif ledger is not None:
        warnings.append("ledger carries no census; this run cannot detect a shrunken corpus")
    else:
        warnings.append("no ledger: every stale reference is reported as new, and this run "
                        "cannot detect a shrunken corpus")

    # ---- resolution ----------------------------------------------------------------------
    resolved = ambiguous = untracked = case_mismatch = glob_no_match = 0
    stale_map: dict[str, dict] = {}

    for cand, tok, kind in path_cands:
        r = resolve(tok, kind, cand.file, corpus, cfg)
        if r.status == "resolved":
            resolved += 1
            if r.rung == "suffix_ambiguous":
                ambiguous += 1
            elif r.rung == "untracked_present":
                untracked += 1
            elif r.rung == "case_mismatch":
                case_mismatch += 1
            continue
        if r.reason == "glob_no_match":
            glob_no_match += 1
        fp = fingerprint(cand.file, tok, r.reason or "unresolved")
        ent = stale_map.get(fp)
        if ent is None:
            stale_map[fp] = {
                "fingerprint": fp, "file": cand.file, "line": cand.line, "ref": tok,
                "raw": cand.raw, "extractor": cand.extractor, "reason": r.reason,
                "parent_exists": r.parent_exists, "count": 1, "seen_lines": [cand.line],
            }
        else:
            ent["count"] += 1
            if cand.line not in ent["seen_lines"]:
                ent["seen_lines"].append(cand.line)

    stale_total = sum(e["count"] for e in stale_map.values())

    # ---- ratchet -------------------------------------------------------------------------
    led_entries = {e["fingerprint"]: e for e in (ledger or {}).get("entries", [])}
    new_list: list[dict] = []
    drained_list: list[dict] = []
    baselined = 0

    for fp, ent in sorted(stale_map.items(), key=lambda kv: (kv[1]["file"], kv[1]["line"])):
        prev = led_entries.get(fp)
        if prev is None:
            new_list.append(ent)
        elif ent["count"] > int(prev.get("count", 1)):
            e2 = dict(ent)
            e2["reason"] = f"{ent['reason']} (count rose {prev.get('count')} -> {ent['count']})"
            new_list.append(e2)
            baselined += int(prev.get("count", 1))
        else:
            baselined += ent["count"]
            if ent["count"] < int(prev.get("count", 1)):
                drained_list.append({**prev, "note": f"count fell "
                                                     f"{prev.get('count')} -> {ent['count']}"})
    for fp, prev in led_entries.items():
        if fp not in stale_map:
            drained_list.append(dict(prev))

    if cfg.suggest and new_list:
        for ent in new_list[:MAX_SUGGESTION_FINDINGS]:
            if ent["reason"] in ("unresolved", "glob_no_match"):
                ent["suggestion"] = suggest(ent["ref"], corpus)
        if len(new_list) > MAX_SUGGESTION_FINDINGS:
            warnings.append(f"suggestions computed for the first {MAX_SUGGESTION_FINDINGS} of "
                            f"{len(new_list)} new findings (bounded for monitor latency)")

    # ---- debt ----------------------------------------------------------------------------
    debt = {"total": 0, "distinct": 0, "oldest_first_seen": None,
            "age_days_p50": None, "age_days_max": None}
    if led_entries:
        ages = []
        now = time.time()
        for e in led_entries.values():
            fs = e.get("first_seen")
            if fs:
                try:
                    t = time.mktime(time.strptime(fs[:10], "%Y-%m-%d"))
                    ages.append(int((now - t) // 86400))
                except ValueError:
                    pass
        ages.sort()
        debt = {
            "total": sum(int(e.get("count", 1)) for e in led_entries.values()),
            "distinct": len(led_entries),
            "oldest_first_seen": min((e.get("first_seen") for e in led_entries.values()
                                      if e.get("first_seen")), default=None),
            "age_days_p50": ages[len(ages) // 2] if ages else None,
            "age_days_max": ages[-1] if ages else None,
        }

    # ---- verdict -------------------------------------------------------------------------
    if new_list:
        verdict, rc = "regressed", 1
        vr = (f"{len(new_list)} new stale reference(s) not present in the baseline"
              if ledger is not None else
              f"{len(new_list)} stale reference(s); no baseline ledger to compare against")
    elif drained_list:
        verdict = "drained"
        rc = 0 if monitor else 2
        vr = (f"{len(drained_list)} baseline entr(y/ies) no longer reproduce. A dead ledger "
              "entry is a loaded trap: re-introducing that exact citation would be "
              'pre-accepted and pass silently. Run --accept --reason "<why>".')
    else:
        verdict, rc = "clean", 0
        vr = (f"no new stale references; {baselined} accepted citation(s) unchanged"
              if led_entries else "no stale references found")

    counts = {
        "candidates": n_candidates, "resolved": resolved,
        "exempt": exempt_absolute + exempt_interp, "not_a_path": not_a_path,
        "stale": stale_total, "new": len(new_list), "baselined": baselined,
        "drained": len(drained_list), "ambiguous": ambiguous,
        "glob_no_match": glob_no_match, "untracked_present": untracked,
        "case_mismatch": case_mismatch,
    }
    return Report(
        root=str(root), verdict=verdict, verdict_reason=vr, exit_code=rc,
        corpus=corpus_info, census_baseline=baseline_census,
        config_sha256=cfg.sha256(), config=cfg.to_dict(), counts=counts,
        exempt={"total": exempt_absolute + exempt_interp, "absolute": exempt_absolute,
                "interpolated": exempt_interp, "by_prefix": exempt_by_prefix},
        extractor_yield=yields, new=new_list, drained=drained_list, debt=debt,
        warnings=warnings, generated_at=_iso(), duration_s=round(time.time() - started, 3))


def gate(root: Path, cfg: Config, ledger_path: Path | None, monitor: bool = False) -> Report:
    """scan + ratchet. A missing ledger is not an error: every stale reference is new, which is
    the correct reading of a repo that has never adopted."""
    ledger = None
    if ledger_path and ledger_path.is_file():
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            return _refusal(Path(root).resolve(), cfg, "ledger_unreadable",
                            f"{ledger_path}: {e}", {}, time.time(), [])
        if not isinstance(ledger, dict) or "entries" not in ledger:
            return _refusal(Path(root).resolve(), cfg, "ledger_unreadable",
                            f"{ledger_path}: not a baseline document", {}, time.time(), [])
    return scan(Path(root), cfg, ledger, monitor=monitor)


# ------------------------------------------------------------------------------ ledger I/O

def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def build_ledger(rep: Report, cfg: Config, reason: str,
                 previous: dict | None) -> tuple[dict, int, int]:
    """The new ledger is EXACTLY what reproduces right now, with `first_seen` carried over.

    It is built from a ledger-free scan, so `rep.new` is the whole current stale set. Nothing
    is unioned with the old file: an entry that no longer reproduces is DROPPED, which is the
    entire point of the ratchet. A dead entry is a loaded trap -- re-introducing that exact
    citation later would match a pre-accepted fingerprint and pass silently -- and a union
    would preserve every trap forever. Returns (document, added, dropped) so the operator is
    told the size of the change rather than discovering it in a diff.
    """
    prev = {e["fingerprint"]: e for e in (previous or {}).get("entries", [])}
    entries = []
    today = _iso()
    for ent in rep.new:
        old = prev.get(ent["fingerprint"])
        entries.append({
            "fingerprint": ent["fingerprint"], "file": ent["file"], "ref": ent["ref"],
            "reason": str(ent["reason"]).split(" (")[0], "count": ent["count"],
            "seen_lines": ent["seen_lines"],
            "first_seen": (old or {}).get("first_seen", today),
        })
    entries.sort(key=lambda e: (e["file"], e["ref"]))
    now_fps = {e["fingerprint"] for e in entries}
    added = len(now_fps - set(prev))
    dropped = len(set(prev) - now_fps)
    return {
        "schema": BASELINE_SCHEMA, "version": 1, "adopted_at": today, "reason": reason,
        "config_sha256": cfg.sha256(),
        "census": {"corpus_files": rep.corpus["corpus_files"],
                   "scanned_files": rep.corpus["scanned_files"],
                   "candidate_refs": rep.counts["candidates"],
                   "floor": cfg.census_floor},
        "entries": entries,
    }, added, dropped


# --------------------------------------------------------------------------- propose tool

def propose_root_map(root: Path, cfg: Config) -> str:
    """Measure, then recommend. Never auto-apply: deriving the exemption set from the same
    corpus it judges is a Self-Certifying Predicate — if every citation under one prefix rots
    at once, its resolution rate collapses, the derivation flips to "exempt", and the scanner
    hides the rot it exists to find. A human ratifies the block into the config."""
    open_cfg = config_from_dict({"exempt_absolute": False, "exempt_prefixes": []}, cfg)
    corpus = enumerate_corpus(root, open_cfg)
    hits: dict[str, list[int]] = {}
    for rel in corpus.files:
        if not _is_text(rel, open_cfg):
            continue
        try:
            lines = (corpus.root / rel).read_bytes().decode("utf-8", "replace").splitlines()
        except OSError:
            continue
        for cand in extract_candidates(rel, lines, open_cfg):
            tok = normalize_token(cand.raw)
            if not tok.startswith("/"):
                continue
            kind, t2 = classify(tok, Config(exempt_absolute=True))
            if kind != "absolute":
                continue
            pre = "/" + t2.lstrip("/").split("/", 1)[0] + "/"
            rec = hits.setdefault(pre, [0, 0])
            rec[0] += 1
            stripped = collapse(t2.lstrip("/"))
            if stripped and (stripped in corpus.index or len(suffix_matches(stripped, corpus)) == 1):
                rec[1] += 1
    out = ["# Measured absolute-path prefixes. Paste the root_map entries you ratify into",
           "# .devloop/stale-refs.json. Nothing was written.", "{", '  "root_map": {']
    rows = []
    for pre, (n, ok) in sorted(hits.items(), key=lambda kv: -kv[1][0]):
        rate = ok / n if n else 0.0
        verdict = "MIRRORED in-tree: map it" if rate >= 0.5 else "runtime-only: leave exempt"
        rows.append(f'    "{pre}": "{pre.lstrip("/")}"'
                    f'   // {n} citation(s), {rate * 100:.0f}% resolve in-tree -- {verdict}')
    out += rows or ["    // no absolute-path citations found"]
    out += ["  }", "}"]
    return "\n".join(out)


# ----------------------------------------------------------------------------- self-test

SELF_TEST_TREE = {
    "README.md": "# demo\n\nSee [the guide](docs/guide.md) and `src/app.py`.\n",
    "docs/guide.md": "Refs: src/app.py\n\nAlso `docs/0020-edge-mesh-binary-wire-protocol.md`.\n",
    "docs/0020-edge-mesh-binary-wire-protocol.md": "# adr\n\nbody\n",
    "src/app.py": '"""App.\n\nRefs: docs/guide.md\n"""\nX = 1\n',
}
SELF_TEST_STALE = ('src/rot.py',
                   '"""Rot.\n\nRefs: docs/does-not-exist.md\n"""\nY = 2\n')


def self_test() -> int:
    """The two-sided control, runnable in production. A check that cannot fail is worse than a
    missing one, so this proves the scanner distinguishes three states it must never conflate."""
    ok = True

    def emit(name: str, good: bool, detail: str = "") -> None:
        nonlocal ok
        print(f"  {'ok  ' if good else 'FAIL'} {name}{': ' + detail if detail else ''}")
        ok = ok and good

    d = Path(tempfile.mkdtemp(prefix="stale-refs-selftest-"))
    try:
        cfg = Config(use_git=False, allow_untracked=False)
        for rel, body in SELF_TEST_TREE.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body)

        r = scan(d, cfg)
        emit("positive: clean tree is clean",
             r.verdict == "clean" and r.exit_code == 0 and r.counts["candidates"] >= 3,
             f"{r.verdict}/{r.exit_code} candidates={r.counts['candidates']}")

        (d / SELF_TEST_STALE[0]).write_text(SELF_TEST_STALE[1])
        r2 = scan(d, cfg)
        emit("negative: a planted stale reference is found and fails",
             r2.verdict == "regressed" and r2.exit_code == 1
             and any(f["ref"] == "docs/does-not-exist.md" for f in r2.new),
             f"{r2.verdict}/{r2.exit_code} new={[f['ref'] for f in r2.new]}")

        empty = Path(tempfile.mkdtemp(prefix="stale-refs-empty-"))
        r3 = scan(empty, cfg)
        emit("empty-set: an empty tree REFUSES rather than reporting clean",
             r3.verdict == "could_not_run" and r3.exit_code == 3
             and r3.counts["stale"] is None,
             f"{r3.verdict}/{r3.exit_code}")
        shutil.rmtree(empty, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("stale_refs --self-test: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ------------------------------------------------------------------------------------ CLI

class _Parser(argparse.ArgumentParser):
    def error(self, message):      # usage errors must not collide with `drained` (rc 2)
        self.print_usage(sys.stderr)
        sys.stderr.write(f"stale_refs: {message}\n")
        sys.exit(4)


def build_parser() -> argparse.ArgumentParser:
    p = _Parser(prog="stale_refs.py", description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=".", help="repository root (default: cwd)")
    p.add_argument("--config", help="config file (.json or .toml); default: "
                                    ".devloop/stale-refs.json|.toml if present")
    p.add_argument("--ledger", default=DEFAULT_LEDGER,
                   help=f"baseline ledger path (default: {DEFAULT_LEDGER})")
    p.add_argument("--monitor", action="store_true",
                   help="supervisor mode: `drained` exits 0 with the verdict recorded, because "
                        "a supervisor trips failed_permanent on a bookkeeping lapse and a "
                        "monitor that has been switched off measures nothing")
    p.add_argument("--no-ledger", action="store_true", help="ignore the ledger entirely")
    p.add_argument("--adopt", action="store_true",
                   help="write the current findings as the baseline (day-one adoption)")
    p.add_argument("--accept", action="store_true",
                   help="re-record the baseline after a drain or a config change")
    p.add_argument("--reason", help="required with --adopt/--accept: why this baseline is ok")
    p.add_argument("--json-out", help="also write the JSON report here (atomic tmp+replace)")
    p.add_argument("--format", choices=("json", "text", "both"), default="both",
                   help="both (default): JSON on stdout, human summary on stderr")
    p.add_argument("--include", action="append", default=[], metavar="GLOB")
    p.add_argument("--exclude", action="append", default=[], metavar="GLOB")
    p.add_argument("--search-root", action="append", default=[], metavar="DIR",
                   help="extra anchor a citation may be relative to (never inferred)")
    p.add_argument("--root-map", action="append", default=[], metavar="/pre/=sub/",
                   help="check an absolute prefix as a subtree instead of exempting it")
    p.add_argument("--exempt-glob", action="append", default=[], metavar="GLOB")
    p.add_argument("--no-exempt-absolute", action="store_true",
                   help="stop exempting every absolute path; the configured exempt_prefixes "
                        "list then applies (its default INCLUDES /usr — the observed field bug "
                        "was a list holding /etc /var /tmp /proc /sys /run and not /usr, which "
                        "made every /usr citation a false positive)")
    p.add_argument("--extraction", choices=("delimited", "bare"), default=None,
                   help="delimited (default) = backticks, markdown links and citation-marker "
                        "payloads. bare also scans unquoted comment prose; it is opt-in "
                        "because it is noisier: measured on this repository it raised "
                        "candidates 548 -> 1214 and findings by 48, whose largest remaining "
                        "class is placeholder conventions written without a sigil (RUNDIR/x)")
    p.add_argument("--no-git", action="store_true",
                   help="walk the filesystem instead of asking git (opt-in: a silent "
                        "fallback would report a broken git as a healthy tree)")
    p.add_argument("--census-floor", type=float, default=None, metavar="F")
    p.add_argument("--no-suggest", action="store_true")
    p.add_argument("--propose-root-map", action="store_true",
                   help="measure absolute-path prefixes and print a candidate root_map; "
                        "writes nothing")
    p.add_argument("--self-test", action="store_true",
                   help="two-sided control: planted stale ref must fail, clean tree must pass, "
                        "empty tree must refuse")
    return p


def config_from_args(root: Path, a: argparse.Namespace) -> tuple[Config, list[str]]:
    cfg, warns = load_config(root, Path(a.config) if a.config else None)
    over: dict = {}
    if a.include:
        over["include_globs"] = a.include
    if a.exclude:
        over["exclude_globs"] = a.exclude
    if a.search_root:
        over["search_roots"] = a.search_root
    if a.exempt_glob:
        over["exempt_globs"] = a.exempt_glob
    if a.root_map:
        rm = dict(cfg.root_map)
        for spec in a.root_map:
            if "=" not in spec:
                raise ScanError("bad_config", f"--root-map {spec!r} must be PREFIX=SUBTREE")
            k, v = spec.split("=", 1)
            rm[k] = v
        over["root_map"] = rm
    if a.no_exempt_absolute:
        over["exempt_absolute"] = False
    if a.extraction:
        over["extraction"] = a.extraction
    if a.no_git:
        over["use_git"] = False
    if a.census_floor is not None:
        over["census_floor"] = a.census_floor
    if a.no_suggest:
        over["suggest"] = False
    return (config_from_dict(over, cfg) if over else cfg), warns


def main(argv: Sequence[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if a.self_test:
        return self_test()

    root = Path(a.root).resolve()
    try:
        cfg, warns = config_from_args(root, a)
    except ScanError as e:
        sys.stderr.write(f"stale_refs: bad config -- {e.detail}\n")
        return 4

    if a.propose_root_map:
        try:
            print(propose_root_map(root, cfg))
        except ScanError as e:
            sys.stderr.write(f"stale_refs: {e.reason}: {e.detail}\n")
            return 3
        return 0

    ledger_path = None if a.no_ledger else (root / a.ledger if not os.path.isabs(a.ledger)
                                            else Path(a.ledger))
    previous = None
    if ledger_path and ledger_path.is_file():
        try:
            previous = json.loads(ledger_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None

    if a.adopt or a.accept:
        if not a.reason:
            sys.stderr.write("stale_refs: --adopt/--accept require --reason \"<why>\"\n")
            return 4
        if a.adopt and previous is not None:
            sys.stderr.write(f"stale_refs: {ledger_path} already exists; use --accept to "
                             "re-record it\n")
            return 4
        rep = scan(root, cfg, None)          # adopt against the raw findings, never the ledger
        if rep.verdict == "could_not_run":
            sys.stderr.write(rep.human() + "\n")
            return 3
        doc, added, dropped = build_ledger(rep, cfg, a.reason, previous)
        write_atomic(ledger_path, json.dumps(doc, indent=2, sort_keys=False) + "\n")
        sys.stderr.write(f"stale_refs: baseline written to {ledger_path} -- "
                         f"{len(doc['entries'])} accepted entr(y/ies) "
                         f"(+{added} newly accepted, -{dropped} dropped as repaired), census "
                         f"scanned_files={doc['census']['scanned_files']} "
                         f"candidate_refs={doc['census']['candidate_refs']}. "
                         "Commit it: adoption is a reviewed change, not a side effect.\n")
        return 0

    rep = gate(root, cfg, ledger_path, monitor=a.monitor)
    rep.warnings = list(warns) + rep.warnings

    payload = json.dumps(rep.to_dict(), indent=2)
    if a.format in ("json", "both"):
        print(payload)
    if a.format == "text":
        print(rep.human())
    elif a.format in ("both",):
        sys.stderr.write(rep.human() + "\n")
    if a.json_out:
        try:
            write_atomic(Path(a.json_out), payload + "\n")
        except OSError as e:
            sys.stderr.write(f"stale_refs: could not write --json-out: {e}\n")
            return 4
    return rep.exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ScanError as _e:            # refusals that escaped the report path
        sys.stderr.write(f"stale_refs: COULD NOT RUN (exit 3) -- {_e.reason}: {_e.detail}\n")
        sys.exit(3)
    except KeyboardInterrupt:
        sys.exit(4)
