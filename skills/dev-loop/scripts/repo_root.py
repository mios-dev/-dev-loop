#!/usr/bin/env python3
"""
scripts/repo_root.py
The one repo-root and template-dir resolver shared by goal.py, research.py, review.py,
ship.py and triage.py. Each of those still runs standalone by path: it puts its own
directory on sys.path and imports this module from next to itself.

Two rules, both fail-closed:
  * find_repo_root() never guesses. Outside a git work tree it raises RepoRootError instead
    of silently treating the current directory as the repository.
  * Templates come from ONE directory: the skill's shipped assets/templates, or the
    directory the caller passes explicitly (--template-dir). The target repository is never
    searched implicitly -- a `reference/templates` (or any other) directory in a foreign repo
    is read only when it is named.
"""
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]

# assets/templates of the skill these scripts ship in -- the default --template-dir.
DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"


class RepoRootError(RuntimeError):
    """No git work tree contains the start directory."""


def find_repo_root(start: Optional[PathLike] = None) -> Path:
    """Top of the git work tree containing `start` (default: the current directory).

    `git rev-parse --show-toplevel` first (quietly: no 'fatal: not a git repository' on
    stderr). When git is missing or refuses (e.g. safe.directory), walk upward for a `.git`
    entry -- a directory in a primary checkout, a pointer FILE in a linked worktree. When
    neither finds one, raise RepoRootError; never fall back to `start` itself.
    """
    cur = Path(start).resolve() if start is not None else Path.cwd().resolve()
    try:
        res = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(cur),
                             capture_output=True, text=True, timeout=30)
        out = res.stdout.strip()
        if res.returncode == 0 and out:
            return Path(out).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    for parent in [cur] + list(cur.parents):
        if (parent / ".git").exists():
            return parent
    raise RepoRootError(f"not inside a git repository: {cur}")


def cli_repo_root(start: Optional[PathLike] = None) -> Path:
    """find_repo_root() for a script's main(): a clean one-line error and exit 2, no traceback."""
    try:
        return find_repo_root(start)
    except RepoRootError as e:
        print(f"error: {e} (run from inside the repository to operate on)", file=sys.stderr)
        sys.exit(2)


def template_source(name: str, template_dir: Optional[PathLike] = None) -> Path:
    """Path of template `name` in `template_dir` (default DEFAULT_TEMPLATE_DIR).

    Exactly one directory is consulted. A missing template is an error the caller reports;
    there is no second place to look.
    """
    base = Path(template_dir).expanduser().resolve() if template_dir else DEFAULT_TEMPLATE_DIR
    src = base / name
    if not src.is_file():
        raise FileNotFoundError(f"template {name!r} not found in {base}")
    return src
