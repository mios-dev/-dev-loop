#!/usr/bin/env python3
"""
artifacts.py — canonical autonomous-development artifacts (stdlib only).

  scaffold  [--root .] [--dry-run]        create any missing canonical files from assets/templates/ (never overwrites)
  bridges   [--root .]                    create thin pointer files (CLAUDE.md @AGENTS.md, GEMINI.md, .agents/rules, copilot, cursor, opencode)
  tasks     path     [--root .]           print the resolved task file (see "Task file resolution" below)
  tasks     render   [--root .]           task file -> TASKS.md (human view; grouped by epic; - [ ] boxes); a TASKS.md whose
                                          first line is not this renderer's '# TASKS' banner belongs to another renderer and is left alone
  tasks     validate [--root .]           ids unique, status vocabulary, depends_on resolvable, no cycles, done ⇒ evidence present
  tasks     set <id> <status> [--evidence TEXT] [--root .]
  tasks     add --id T-00N --title ... [--epic ID] [--goal ID] [--depends a,b] [--ac "..."] [--positive CMD --negative CMD --expect RE]
  tasks     next [--root .] [--limit N]   ids that are open with all depends_on done (what a fresh session should pick up)
  tasks     lane <id> [--root .]          print a lane object (v2 schema) for this task, ready to drop into lanes.json
  adr       new "<title>" [--root .]      next NNNN-title.md in docs/decisions from the MADR 4.0 template, status: proposed
  trailer   <id>                           print the commit trailer line for a task
  strip-frontmatter <SKILL.md>             keep only the six agentskills.io frontmatter keys (used when installing into non-Claude harnesses)

Every `tasks` op also takes --tasks FILE. Task file resolution (first match wins):
  1. --tasks FILE                         (relative to the current directory)
  2. $DEVLOOP_TASKS_FILE                  (relative to --root)
  3. <root>/tasks.jsonl                   when it is a file (a project keeping its canonical list at the root)
  4. <root>/.devloop/tasks.jsonl          the default; `scaffold` creates it when no task file resolves yet
Mutating ops (set, add, reconcile, archive-stale, fold-stale, recycle) hold an exclusive lock on '<task file>.lock'
around load-modify-save, so another tool taking the same lock never loses an update.

Vocabularies (also enforced by `tasks validate`):
  task.status  open | in_progress | blocked | done | cancelled      task.type  task | epic | bug
               A file is in the OpenAI plan-status dialect when any record says pending, completed or incomplete:
               those read as open, done and blocked, input accepts either dialect, and a save writes the file's own words.
  goal.status  active | at_risk | met | dropped                    adr.status proposed | accepted | deprecated | superseded
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TPL = HERE.parent / "assets" / "templates"
TASK_STATUS = ["open", "in_progress", "blocked", "done", "cancelled"]
# The OpenAI plan-status dialect: same five states, three spelled differently. Detected per file.
STATUS_ALIASES = {"pending": "open", "completed": "done", "incomplete": "blocked"}
STATUS_DIALECT_OUT = {v: k for k, v in STATUS_ALIASES.items()}
# A strict superset of the former ^[A-Z]+-\d+(?:(?:\.\.|-)\d+)?$ - ranges with a prefix (AGY-503..AGY-510), space-
# separated words (G-TASK 1) and a '#n' suffix for a second task that reused an id (T-031#2). fullmatch, never a
# trailing newline.
TASK_ID_RE = re.compile(r"[A-Z][A-Z0-9]*(?:[- ][A-Z0-9]+)*(?:\.\.(?:[A-Z][A-Z0-9]*-)?[0-9]+)?(?:#[0-9]+)?")
TASKS_FILE_ENV = "DEVLOOP_TASKS_FILE"
TASK_TYPE = ["task", "epic", "bug"]
CANON = {  # target path -> template
    "AGENTS.md": "AGENTS.md", "docs/GOALS.md": "GOALS.md", "docs/ROADMAP.md": "ROADMAP.md", "docs/DOD.md": "DOD.md",
    "CHECKLISTS.md": "CHECKLISTS.md", "CHANGELOG.md": "CHANGELOG.md", ".devloop/tasks.jsonl": "tasks.jsonl", ".devloop/LEDGER.md": "LEDGER.md",
}
BRIDGES = {
    "CLAUDE.md": "@AGENTS.md\n\n<!-- Claude-specific additions below; the constitution lives in AGENTS.md -->\n",
    "GEMINI.md": "Follow `AGENTS.md` (the project constitution). Gemini/Antigravity-specific additions below.\n",
    ".agents/rules/00-agents.md": "---\ntrigger: always_on\n---\nFollow `AGENTS.md` at the repository root; it is the project constitution. Run engineering work through the `dev-loop` skill.\n",
    ".github/copilot-instructions.md": "Follow `AGENTS.md` at the repository root (project constitution). Run engineering work through the `dev-loop` skill (`/dev-loop`).\n",
    ".cursor/rules/agents.mdc": "---\ndescription: Project constitution pointer\nalwaysApply: true\n---\nFollow `AGENTS.md` at the repository root. Run engineering work through the `dev-loop` skill.\n",
}


def die(m, c=1):
    print(m, file=sys.stderr); sys.exit(c)


def tasks_path(root, explicit=None) -> Path:
    """The project's task file: --tasks FILE, then $DEVLOOP_TASKS_FILE (relative to root), then <root>/tasks.jsonl
    when it is a file, then <root>/.devloop/tasks.jsonl. The result need not exist yet."""
    root = Path(root)
    if explicit: return Path(explicit).resolve()
    env = os.environ.get(TASKS_FILE_ENV, "").strip()
    if env:
        p = Path(env)
        return p if p.is_absolute() else root / p
    top = root / "tasks.jsonl"
    return top if top.is_file() else root / ".devloop" / "tasks.jsonl"


def _rel(root: Path, p: Path) -> str:
    try: return p.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError: return str(p)


def norm_status(s):
    return STATUS_ALIASES.get(s, s)


def read_task_file(p: Path) -> tuple[list[dict], str]:
    """(records with status normalised to the internal words, dialect) where dialect is 'openai' when any record
    uses pending/completed/incomplete and 'legacy' otherwise (also for an absent or empty file)."""
    if not p.exists(): return [], "legacy"
    out, dialect = [], "legacy"
    for n, line in enumerate(p.read_text("utf-8").splitlines(), 1):
        if line.strip():
            try: t = json.loads(line)
            except json.JSONDecodeError as e: die(f"{p.name} line {n}: {e}")
            if isinstance(t, dict) and t.get("status") in STATUS_ALIASES:
                dialect = "openai"; t["status"] = STATUS_ALIASES[t["status"]]
            out.append(t)
    return out, dialect


def load_tasks(root: Path, path=None) -> list[dict]:
    return read_task_file(Path(path) if path else tasks_path(root))[0]


def save_tasks(root: Path, tasks: list[dict], path=None) -> None:
    """Write back in the file's own dialect, read from the file as it is on disk (the caller holds the lock)."""
    p = Path(path) if path else tasks_path(root); p.parent.mkdir(parents=True, exist_ok=True)
    dialect = read_task_file(p)[1]
    def out(t):
        if dialect == "openai" and t.get("status") in STATUS_DIALECT_OUT: t = {**t, "status": STATUS_DIALECT_OUT[t["status"]]}
        return json.dumps(t, ensure_ascii=False) + "\n"
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text("".join(out(t) for t in tasks), "utf-8")
    tmp.replace(p)  # atomic


def _exclude_lock_file(lock: Path) -> None:
    """A lock file this tool just created must not dirty `git status` (a dirty base tree stops the orchestrator).
    Add one anchored line for it to the repository's info/exclude unless something already ignores it."""
    try:
        d = lock.parent
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=d, capture_output=True, text=True)
        if top.returncode: return
        rel = lock.resolve().relative_to(Path(top.stdout.strip()).resolve()).as_posix()
        if subprocess.run(["git", "check-ignore", "-q", "--", rel], cwd=top.stdout.strip(), capture_output=True).returncode == 0: return
        ex = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=top.stdout.strip(), capture_output=True, text=True)
        if ex.returncode: return
        exf = Path(ex.stdout.strip()); exf = exf if exf.is_absolute() else Path(top.stdout.strip()) / exf
        exf.parent.mkdir(parents=True, exist_ok=True)
        cur = exf.read_text("utf-8") if exf.exists() else ""
        line = "/" + rel
        if line not in cur.splitlines():
            exf.write_text(cur + ("" if not cur or cur.endswith("\n") else "\n") + line + "\n", "utf-8")
    except (OSError, ValueError):
        pass


@contextlib.contextmanager
def task_lock(p: Path):
    """Exclusive lock on '<task file>.lock' for a load-modify-save. Any other tool that rewrites the same file must take
    the same lock (flock on POSIX, a byte-range lock on Windows)."""
    lock = p.with_name(p.name + ".lock"); lock.parent.mkdir(parents=True, exist_ok=True)
    fresh = not lock.exists()
    f = open(lock, "a+")
    try:
        if fresh: _exclude_lock_file(lock)
        try:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        except ImportError:  # Windows
            import msvcrt
            f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        yield
    finally:
        f.close()  # closing the descriptor releases either lock


_HEAD_COMMIT_CACHE: dict = {}
_COMMIT_COUNT_CACHE: dict = {}
_IS_GIT_CACHE: dict = {}


def get_git_head_commit(root: Path) -> str:
    root_str = str(root)
    if root_str in _HEAD_COMMIT_CACHE:
        return _HEAD_COMMIT_CACHE[root_str]
    try:
        import subprocess
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
        sha = res.stdout.strip()
        _HEAD_COMMIT_CACHE[root_str] = sha
        return sha
    except Exception:
        return "HEAD"


def get_commit_distance(root: Path, last_commit: str) -> int:
    root_str = str(root)
    if root_str not in _IS_GIT_CACHE:
        try:
            import subprocess
            r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True)
            _IS_GIT_CACHE[root_str] = (r.returncode == 0)
        except Exception:
            _IS_GIT_CACHE[root_str] = False
    if not _IS_GIT_CACHE[root_str]:
        return 0

    key = (root_str, last_commit)
    if key in _COMMIT_COUNT_CACHE:
        return _COMMIT_COUNT_CACHE[key]

    try:
        import subprocess
        res = subprocess.run(
            ["git", "rev-list", "--count", f"{last_commit}..HEAD"],
            cwd=root, capture_output=True, text=True
        )
        if res.returncode == 0:
            c = int(res.stdout.strip())
            _COMMIT_COUNT_CACHE[key] = c
            return c
    except Exception:
        pass
    _COMMIT_COUNT_CACHE[key] = 0
    return 0


def compute_task_staleness(root: Path, t: dict) -> dict:
    """Compute task half-life decay staleness score S in [0.0, 1.0]."""
    hl = t.get("half_life") or {}
    h_commits = float(hl.get("half_life_horizon_commits") or 50)
    h_days = float(hl.get("half_life_horizon_days") or 90)

    # Days elapsed
    dt_days = 0
    updated_str = t.get("updated") or t.get("created")
    if updated_str:
        try:
            import datetime
            up_dt = datetime.datetime.strptime(updated_str[:10], "%Y-%m-%d")
            dt_days = max(0, (datetime.datetime.now() - up_dt).days)
        except Exception:
            dt_days = 0

    # Commit distance
    dc_commits = 0
    last_commit = hl.get("last_reconciled_commit") or hl.get("created_commit")
    if last_commit and last_commit != "legacy-import":
        dc_commits = get_commit_distance(root, last_commit)

    # Check anchors
    anchors = hl.get("anchors") or t.get("links") or []
    broken_anchors = []
    for anc in anchors:
        if isinstance(anc, str) and ("/" in anc or "." in anc) and not anc.startswith("http"):
            clean_p = anc.lstrip("/")
            if not (root / clean_p).exists():
                broken_anchors.append(anc)

    # Decay math: P_fresh = 2^(-dc / H_c) * 2^(-dt / H_t)
    p_commit = 2.0 ** (-dc_commits / h_commits) if h_commits > 0 else 1.0
    p_time = 2.0 ** (-dt_days / h_days) if h_days > 0 else 1.0
    p_fresh = p_commit * p_time
    
    anchor_penalty = 0.35 if broken_anchors else 0.0
    staleness = min(1.0, (1.0 - p_fresh) + anchor_penalty)

    return {
        "staleness": round(staleness, 3),
        "p_fresh": round(p_fresh, 3),
        "days_elapsed": dt_days,
        "commits_elapsed": dc_commits,
        "broken_anchors": broken_anchors,
        "expired": staleness >= 0.5,
    }


# ---------------------------------------------------------------- scaffold / bridges
def cmd_scaffold(a):
    root = Path(a.root).resolve(); made = []
    for rel, tpl in CANON.items():
        dst = root / rel
        if dst.exists(): continue
        if rel == ".devloop/tasks.jsonl" and tasks_path(root).is_file(): continue  # the project already keeps its task file elsewhere
        made.append(rel)
        if not a.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True); dst.write_text((TPL / tpl).read_text("utf-8"), "utf-8")
    (root / "docs" / "decisions").mkdir(parents=True, exist_ok=True) if not a.dry_run else None
    (root / "docs" / "runbooks").mkdir(parents=True, exist_ok=True) if not a.dry_run else None
    print(("would create: " if a.dry_run else "created: ") + (", ".join(made) or "nothing (all present)"))
    if made and not a.dry_run: print("fill the <placeholders> in AGENTS.md / GOALS.md before relying on them; then `artifacts.py tasks render`.")


def cmd_bridges(a):
    root = Path(a.root).resolve(); made = []
    for rel, body in BRIDGES.items():
        dst = root / rel
        if dst.exists():
            if rel == "CLAUDE.md" and "@AGENTS.md" not in dst.read_text("utf-8"):
                print("CLAUDE.md exists without `@AGENTS.md` — add it as the first line so the constitution is imported.")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True); dst.write_text(body, "utf-8"); made.append(rel)
    print("bridges created: " + (", ".join(made) or "none (all present)"))


# ---------------------------------------------------------------- tasks
def validate(tasks: list[dict]) -> list[str]:
    errs = []; ids = [t.get("id") for t in tasks]
    if len(ids) != len(set(ids)): errs.append("duplicate ids")
    for t in tasks:
        i = t.get("id", "?")
        if not (isinstance(i, str) and TASK_ID_RE.fullmatch(i)): errs.append(f"{i!r}: id must look like T-001, AGY-106..122, AGY-503..AGY-510, G-TASK 1 or T-031#2")
        if t.get("status") not in TASK_STATUS: errs.append(f"{i}: status {t.get('status')!r} not in {TASK_STATUS}")
        if t.get("type", "task") not in TASK_TYPE: errs.append(f"{i}: type {t.get('type')!r} not in {TASK_TYPE}")
        for d in t.get("depends_on", []):
            if d not in ids: errs.append(f"{i}: depends_on unknown {d}")
        if t.get("epic") and t["epic"] not in ids: errs.append(f"{i}: epic unknown {t['epic']}")
        if t.get("status") == "done" and not t.get("verification_evidence"):
            errs.append(f"{i}: done without verification_evidence (SKILL §6 — 'done' needs both controls cited)")
    # cycles
    deps = {t["id"]: set(t.get("depends_on", [])) for t in tasks if "id" in t}; done = set()
    while deps:
        ready = [k for k, v in deps.items() if v <= done]
        if not ready: errs.append(f"depends_on cycle among {sorted(deps)}"); break
        done |= set(ready); [deps.pop(k) for k in ready]
    return errs


MUTATING_TASK_OPS = ("set", "add", "reconcile", "archive-stale", "fold-stale", "recycle")
RENDER_BANNER = "# TASKS"


def cmd_tasks(a):
    root = Path(a.root).resolve(); path = tasks_path(root, getattr(a, "tasks", None))
    if a.op == "path":
        print(path); return
    with (task_lock(path) if a.op in MUTATING_TASK_OPS else contextlib.nullcontext()):
        _cmd_tasks(a, root, path)


def _cmd_tasks(a, root: Path, path: Path):
    tasks, dialect = read_task_file(path); name = path.name
    shown = (lambda st: STATUS_DIALECT_OUT.get(st, st)) if dialect == "openai" else (lambda st: st)
    if a.op == "validate":
        errs = validate(tasks)
        die(f"{name} invalid:\n  " + "\n  ".join(errs)) if errs else print(f"{name} ok: {len(tasks)} tasks")
    elif a.op == "render":
        md = root / "TASKS.md"
        if md.exists():
            with open(md, encoding="utf-8", errors="replace") as fh: first = fh.readline().rstrip("\r\n")
            if first != RENDER_BANNER:
                print("TASKS.md owned by another renderer; skipped"); return
        errs = validate(tasks)
        if errs: die(f"refusing to render invalid {name}:\n  " + "\n  ".join(errs))
        box = {"done": "x", "cancelled": "-"}; src = _rel(root, path)
        lines = [RENDER_BANNER, "", f"_Rendered from `{src}` — edit the JSONL (or `artifacts.py tasks set/add`), then `artifacts.py tasks render`. Do not hand-edit this file._", ""]
        epics = [t for t in tasks if t.get("type") == "epic"]; by_epic = {}
        for t in tasks:
            if t.get("type") != "epic": by_epic.setdefault(t.get("epic") or "_none", []).append(t)
        def line(t):
            b = box.get(t["status"], " "); dep = f" ← {', '.join(t['depends_on'])}" if t.get("depends_on") else ""
            own = f" @{t['owner']}" if t.get("owner") else ""; st = "" if t["status"] in ("open", "done") else f" **[{shown(t['status'])}]**"
            return f"- [{b}] **{t['id']}** {t['title']}{st}{own}{dep}"
        for e in epics:
            lines += [f"## {e['id']} · {e['title']} · `{shown(e['status'])}`" + (f" · goal {e['goal']}" if e.get("goal") else ""), ""]
            lines += [line(t) for t in by_epic.get(e["id"], [])] + [""]
        if by_epic.get("_none"):
            lines += ["## Unassigned", ""] + [line(t) for t in by_epic["_none"]] + [""]
        n_done = sum(t["status"] == "done" for t in tasks); lines += [f"_{n_done}/{len(tasks)} {shown('done')} · {time.strftime('%Y-%m-%d')}_", ""]
        (root / "TASKS.md").write_text("\n".join(lines), "utf-8"); print(f"TASKS.md rendered ({len(tasks)} tasks)")
    elif a.op == "set":
        t = next((t for t in tasks if t["id"] == a.id), None) or die(f"no task {a.id}")
        a.status = norm_status(a.status)
        if a.status not in TASK_STATUS: die(f"status must be one of {TASK_STATUS} (or {sorted(STATUS_ALIASES)})")
        if a.status == "done" and not (a.evidence or t.get("verification_evidence")): die("done requires --evidence (both controls, exact commands)")
        t["status"] = a.status
        if a.evidence: t["verification_evidence"] = a.evidence
        t["updated"] = time.strftime("%Y-%m-%d")
        save_tasks(root, tasks, path); print(f"{a.id} -> {shown(a.status)}")
    elif a.op == "add":
        if any(t["id"] == a.id for t in tasks): die(f"{a.id} exists")
        t = {"id": a.id, "type": a.type, "title": a.title, "status": "open", "owner": a.owner or "", "epic": a.epic or "", "goal": a.goal or "",
             "depends_on": [d for d in (a.depends or "").split(",") if d], "acceptance_criteria": a.ac or [],
             "verification": {k: v for k, v in (("positive_cmd", a.positive), ("negative_control_cmd", a.negative), ("negative_expect", a.expect)) if v},
             "verification_evidence": "", "links": [], "notes": "", "created": time.strftime("%Y-%m-%d")}
        tasks.append(t); errs = validate(tasks)
        if errs: die(f"would make {name} invalid:\n  " + "\n  ".join(errs))
        save_tasks(root, tasks, path); print(f"added {a.id}")
    elif a.op == "next":
        done = {t["id"] for t in tasks if t["status"] in ("done", "cancelled")}
        ready = [t for t in tasks if t["status"] == "open" and t.get("type") != "epic" and set(t.get("depends_on", [])) <= done]
        lim = a.limit if a.limit is not None and a.limit >= 0 else None
        shown_ready = ready if lim is None else ready[:lim]
        out = [f"{t['id']}  {t['title']}" for t in shown_ready]
        if len(ready) > len(shown_ready): out.append(f"(+{len(ready) - len(shown_ready)} more)")
        print("\n".join(out) or "(nothing ready — check blocked/in_progress tasks and the ledger)")
    elif a.op == "lane":
        t = next((t for t in tasks if t["id"] == a.id), None) or die(f"no task {a.id}")
        v = t.get("verification", {})
        lane = {"id": re.sub(r"[^a-z0-9_-]", "-", t["id"].lower()), "task_id": t["id"], "objective": t["title"] + ("\nAcceptance: " + "; ".join(t["acceptance_criteria"]) if t.get("acceptance_criteria") else ""),
                "owned_paths": ["<fill: exclusive globs>"], "positive_cmd": v.get("positive_cmd", "<fill>"),
                "negative_control_cmd": v.get("negative_control_cmd", "<fill>"), "negative_expect": v.get("negative_expect", "<fill>"),
                "depends_on": [re.sub(r"[^a-z0-9_-]", "-", d.lower()) for d in t.get("depends_on", [])]}
        print(json.dumps(lane, indent=2))
    elif a.op == "staleness":
        thresh = getattr(a, "threshold", 0.5) or 0.5
        rows = []
        for t in tasks:
            st = compute_task_staleness(root, t)
            flag = " [EXPIRED]" if st["expired"] else ""
            rows.append((t["id"], t["status"], f"{st['staleness']:.2f}", f"{st['days_elapsed']}d", f"{st['commits_elapsed']}c", f"{len(st['broken_anchors'])} broken", flag, t["title"][:50]))
        print(f"TASK STALENESS & HALF-LIFE MONITOR (threshold >= {thresh:.2f})")
        print(f"{'ID':<12} {'STATUS':<12} {'STALE':<7} {'AGE':<6} {'COMMITS':<9} {'ANCHORS':<10} {'TITLE'}")
        print("-" * 80)
        for r in rows:
            print(f"{r[0]:<12} {r[1]:<12} {r[2]:<7} {r[3]:<6} {r[4]:<9} {r[5]:<10} {r[7]}{r[6]}")
        expired_count = sum(1 for r in rows if r[6])
        print(f"\n{expired_count}/{len(tasks)} tasks exceeded half-life horizon.")
    elif a.op == "reconcile":
        t = next((t for t in tasks if t["id"] == a.id), None) or die(f"no task {a.id}")
        head_sha = get_git_head_commit(root)
        hl = t.setdefault("half_life", {})
        hl["last_reconciled_commit"] = head_sha
        hl["staleness_score"] = 0.0
        t["updated"] = time.strftime("%Y-%m-%d")
        save_tasks(root, tasks, path)
        print(f"{a.id} reconciled to HEAD ({head_sha[:8]}); staleness reset to 0.0")
    elif a.op in ("archive-stale", "fold-stale"):
        thresh = getattr(a, "threshold", 0.5) or 0.5
        surviving = []
        archived = []
        archive_jsonl = root / ".devloop" / "backlog_archive.jsonl"
        historical_md = root / ".devloop" / "HISTORICAL_BACKLOG.md"
        archive_jsonl.parent.mkdir(parents=True, exist_ok=True)
        head_sha = get_git_head_commit(root)
        
        for t in tasks:
            st = compute_task_staleness(root, t)
            if st["staleness"] >= thresh and t.get("status") not in ("done", "cancelled"):
                t["folded_at"] = time.strftime("%Y-%m-%d %H:%M:%SZ")
                t["folded_commit"] = head_sha
                t["status_at_fold"] = t.get("status", "open")
                t["folded_status"] = "folded"
                t["review_state"] = "re-research_pending"
                t["recycle_after_commits"] = 25
                t["archive_staleness"] = st
                archived.append(t)
            else:
                surviving.append(t)
        
        if archived:
            with open(archive_jsonl, "a", encoding="utf-8") as af:
                for t in archived:
                    af.write(json.dumps(t, ensure_ascii=False) + "\n")
            
            # Append markdown record
            md_entries = [f"\n## [FOLDED] [{t['id']}] {t['title']} (Folded {t['folded_at']} @ {t['folded_commit'][:8]})\n"
                          f"- **Status at Fold:** `{t['status_at_fold']}` (legacy: `{t.get('legacy_status', 'N/A')}`)\n"
                          f"- **Staleness Score:** {t['archive_staleness']['staleness']} (age: {t['archive_staleness']['days_elapsed']} days, commits: {t['archive_staleness']['commits_elapsed']})\n"
                          f"- **Recycle Policy:** Every 25-50 commits for review / re-research\n"
                          f"- **Review State:** `{t['review_state']}`\n"
                          f"- **Broken Anchors:** {', '.join(t['archive_staleness']['broken_anchors']) or 'none'}\n"
                          f"- **Acceptance Criteria:** {'; '.join(t.get('acceptance_criteria', [])) or 'none'}\n"
                          f"- **Notes & Historical Context:**\n\n```\n{t.get('notes', '')}\n```\n"
                          for t in archived]
            if not historical_md.exists():
                historical_md.write_text("# HISTORICAL BACKLOG & KNOWLEDGE ARCHIVE\n\n_Rolling append-only record of tasks that exceeded half-life horizon, preserved wholly with complete reasoning context and recycled every 25-50 commits._\n\n", "utf-8")
            with open(historical_md, "a", encoding="utf-8") as hf:
                hf.write("".join(md_entries))
            
            archived_ids = {t["id"] for t in archived}
            for t in surviving:
                broken = [d for d in t.get("depends_on", []) if d in archived_ids]
                if broken:
                    t["depends_on"] = [d for d in t["depends_on"] if d not in archived_ids]
                    arch_deps = t.setdefault("archived_dependencies", [])
                    for b in broken:
                        if b not in arch_deps:
                            arch_deps.append(b)

            save_tasks(root, surviving, path)
            print(f"Folded {len(archived)} tasks wholly to {archive_jsonl} and {historical_md}. Remaining active tasks: {len(surviving)}")
        else:
            print(f"No tasks exceeded staleness threshold {thresh}. None folded.")
    elif a.op == "recycle":
        archive_jsonl = root / ".devloop" / "backlog_archive.jsonl"
        if not archive_jsonl.exists():
            print("No archived tasks found to recycle.")
            return
        archived_tasks = [json.loads(l) for l in archive_jsonl.read_text("utf-8").splitlines() if l.strip()]
        cadence = getattr(a, "cadence", 25) or 25
        head_sha = get_git_head_commit(root)
        target_id = a.id or getattr(a, "id_flag", None)
        re_research = getattr(a, "re_research", False)
        reactivate = getattr(a, "reactivate", False)

        if target_id and reactivate:
            target_task = next((t for t in archived_tasks if t["id"] == target_id), None)
            if not target_task:
                die(f"Task {target_id} not found in archive")
            target_task["status"] = "open"
            target_task["updated"] = time.strftime("%Y-%m-%d")
            hl = target_task.setdefault("half_life", {})
            hl["last_reconciled_commit"] = head_sha
            hl["staleness_score"] = 0.0
            target_task.pop("folded_status", None)
            target_task["review_state"] = "reactivated"
            active = load_tasks(root, path)
            active.append(target_task)
            save_tasks(root, active, path)
            for t in archived_tasks:
                if t["id"] == target_id:
                    t["review_state"] = "reactivated"
                    t["reactivated_at"] = time.strftime("%Y-%m-%d %H:%M:%SZ")
            archive_jsonl.write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in archived_tasks), "utf-8")
            print(f"Task {target_id} reactivated to active {name} at HEAD ({head_sha[:8]})")
            return

        if target_id and re_research:
            target_task = next((t for t in archived_tasks if t["id"] == target_id), None)
            if not target_task:
                die(f"Task {target_id} not found in archive")
            spike_dir = root / "docs" / "research"
            spike_dir.mkdir(parents=True, exist_ok=True)
            spike_file = spike_dir / f"spike-{target_id.lower()}.md"
            spike_lines = [
                f"# Research Spike: {target_id} — {target_task['title']}",
                "",
                f"- **Date**: {time.strftime('%Y-%m-%d')}",
                f"- **Source**: Recycled from historical backlog (folded at {target_task.get('folded_at', 'N/A')})",
                f"- **Status**: proposed",
                "",
                "## 1. Context & Motivation",
                f"Task `{target_id}` was folded wholly after exceeding half-life expectancies.",
                f"Recycled for periodic re-research (25-50 commit cadence).",
                "",
                "### Original Acceptance Criteria",
            ] + [f"- {ac}" for ac in target_task.get("acceptance_criteria", [])] + [
                "",
                "### Historical Notes & Rationale",
                "```",
                target_task.get("notes", ""),
                "```",
                "",
                "## 2. Upstream Tech & Substrate Delta",
                "What has changed in the codebase or upstream dependencies since this task was created?",
                "",
                "## 3. Implementation Recommendation",
                "- [ ] Reactivate as active task (`python3 artifacts.py tasks recycle " + target_id + " --reactivate`)",
                "- [ ] Supercede with new ADR / Milestone",
                "- [ ] Keep folded for future review cycle",
            ]
            spike_file.write_text("\n".join(spike_lines), "utf-8")
            for t in archived_tasks:
                if t["id"] == target_id:
                    t["review_state"] = "re-researched"
                    t["spike_file"] = str(spike_file.relative_to(root))
            archive_jsonl.write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in archived_tasks), "utf-8")
            print(f"Generated research spike for {target_id} at {spike_file}")
            return

        candidates = []
        import subprocess
        for t in archived_tasks:
            if t.get("review_state") == "reactivated":
                continue
            folded_c = t.get("folded_commit")
            dc = 0
            if folded_c and folded_c != "HEAD":
                dc = get_commit_distance(root, folded_c)
            is_candidate = (dc >= cadence) or (t.get("review_state") == "re-research_pending")
            candidates.append((t["id"], t.get("folded_at", "N/A")[:10], f"{dc}c", t.get("review_state", "pending"), is_candidate, t["title"][:45]))

        print(f"RECYCLED TASK REVIEW CANDIDATES (cadence: >= {cadence} commits)")
        print(f"{'ID':<12} {'FOLDED':<12} {'DISTANCE':<10} {'STATE':<22} {'TITLE'}")
        print("-" * 80)
        for c in candidates:
            flag = " [DUE FOR REVIEW]" if c[4] else ""
            print(f"{c[0]:<12} {c[1]:<12} {c[2]:<10} {c[3]:<22} {c[5]}{flag}")
        due_n = sum(1 for c in candidates if c[4])
        print(f"\n{due_n}/{len(candidates)} folded tasks due for review/re-research.")
        print("Action: run `artifacts.py tasks recycle <id> --re-research` or `--reactivate`")
    elif a.op == "distill":
        archive_jsonl = root / ".devloop" / "backlog_archive.jsonl"
        if not archive_jsonl.exists():
            print(f"No archive file found at {archive_jsonl} to distill.")
            return
        archived_tasks = [json.loads(line) for line in archive_jsonl.read_text("utf-8").splitlines() if line.strip()]
        distill_dir = root / "docs" / "distilled"
        distill_dir.mkdir(parents=True, exist_ok=True)
        distill_out = distill_dir / "knowledge_distillation.md"
        
        lines = [
            "# DISTILLED KNOWLEDGE & HISTORICAL TASK ANALYSIS",
            "",
            f"_Synthesized on {time.strftime('%Y-%m-%d %H:%M:%SZ')} from {len(archived_tasks)} archived task records._",
            "",
            "## 1. Executive Summary & Recurrent Themes",
            "",
        ]
        domains = {}
        for t in archived_tasks:
            dom = t.get("goal") or "General"
            domains.setdefault(dom, []).append(t)
            
        for dom, dtasks in sorted(domains.items()):
            lines.append(f"### Domain: {dom} ({len(dtasks)} tasks)")
            for t in dtasks:
                lines.append(f"- **{t['id']}**: {t['title']}")
                if t.get("acceptance_criteria"):
                    lines.append(f"  - *Acceptance:* {'; '.join(t['acceptance_criteria'])}")
                if t.get("knowledge", {}).get("why"):
                    lines.append(f"  - *Why:* {t['knowledge']['why']}")
            lines.append("")
            
        lines.append("## 2. Invariants & Lessons Learned")
        lines.append("- Task half-lives decay exponentially with commit drift and calendar days.")
        lines.append("- Broken file anchors are the strongest leading indicator of task obsolescence.")
        lines.append("- Historical reasoning is preserved losslessly for future architectural synthesis.")
        
        distill_out.write_text("\n".join(lines), "utf-8")
        print(f"Distilled {len(archived_tasks)} archived tasks into {distill_out}")
    elif a.op == "export-openai":
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "DevLoopTask",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "id", "type", "title", "status", "legacy_status", "owner", "epic", "goal",
                "depends_on", "acceptance_criteria", "verification",
                "verification_evidence", "links", "notes", "created"
            ],
            "properties": {
                "id": {"type": "string", "pattern": "^" + TASK_ID_RE.pattern + "$"},
                "type": {"type": "string", "enum": ["task", "epic", "bug"]},
                "title": {"type": "string"},
                "status": {"type": "string", "enum": ["open", "in_progress", "blocked", "done", "cancelled"]},
                "legacy_status": {"type": ["string", "null"]},
                "owner": {"type": "string"},
                "epic": {"type": "string"},
                "goal": {"type": "string"},
                "depends_on": {"type": "array", "items": {"type": "string"}},
                "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                "verification": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["positive_cmd", "negative_control_cmd", "negative_expect"],
                    "properties": {
                        "positive_cmd": {"type": "string"},
                        "negative_control_cmd": {"type": "string"},
                        "negative_expect": {"type": "string"}
                    }
                },
                "verification_evidence": {"type": "string"},
                "links": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
                "created": {"type": "string"}
            }
        }
        tool_definition = {
            "type": "function",
            "function": {
                "name": "manage_devloop_task",
                "description": "Manage and manipulate dev-loop canonical tasks adhering strictly to OpenAI standards.",
                "strict": True,
                "parameters": schema
            }
        }
        print(json.dumps(tool_definition, indent=2))


def cmd_adr(a):
    root = Path(a.root).resolve(); d = root / "docs" / "decisions"; d.mkdir(parents=True, exist_ok=True)
    nums = [int(m.group(1)) for p in d.glob("*.md") if (m := re.match(r"^(\d{4})-", p.name))]
    n = max(nums, default=0) + 1; slug = re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")[:60]
    dst = d / f"{n:04d}-{slug}.md"
    dst.write_text((TPL / "adr.md").read_text("utf-8").replace("{date}", time.strftime("%Y-%m-%d")).replace("{title}", a.title), "utf-8")
    print(f"{dst}  (status: proposed — a human flips it to accepted; agents never self-accept)")


SPEC_KEYS = ("name", "description", "license", "compatibility", "metadata", "allowed-tools")


def cmd_strip(a):
    """Reduce a SKILL.md's frontmatter to the six agentskills.io keys (Claude Code extensions such as context/agent/argument-hint are dropped)."""
    p = Path(a.path); s = p.read_text("utf-8")
    if not s.startswith("---"): die(f"{p}: no frontmatter")
    head, _, body = s[3:].partition("\n---")
    keep, cur, dropped = [], None, []
    for line in head.splitlines():
        if line and not line[0].isspace() and ":" in line:
            cur = line.split(":", 1)[0].strip(); (keep if cur in SPEC_KEYS else dropped).append(line)
        elif cur in SPEC_KEYS: keep.append(line)
    p.write_text("---\n" + "\n".join(k for k in keep if k.strip()) + "\n---" + body, "utf-8")
    print(f"{p}: dropped {[d.split(':')[0] for d in dropped if d.strip()]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("scaffold"); p.add_argument("--root", default="."); p.add_argument("--dry-run", action="store_true"); p.set_defaults(f=cmd_scaffold)
    p = sp.add_parser("bridges"); p.add_argument("--root", default="."); p.set_defaults(f=cmd_bridges)
    p = sp.add_parser("tasks"); p.add_argument("op", choices=["path", "render", "validate", "set", "add", "next", "lane", "staleness", "reconcile", "archive-stale", "fold-stale", "recycle", "distill", "export-openai"]); p.add_argument("id", nargs="?"); p.add_argument("status", nargs="?")
    p.add_argument("--root", default="."); p.add_argument("--evidence"); p.add_argument("--id", dest="id_flag"); p.add_argument("--title"); p.add_argument("--type", default="task", choices=TASK_TYPE)
    p.add_argument("--owner"); p.add_argument("--epic"); p.add_argument("--goal"); p.add_argument("--depends"); p.add_argument("--ac", action="append")
    p.add_argument("--positive"); p.add_argument("--negative"); p.add_argument("--expect"); p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--cadence", type=int, default=25); p.add_argument("--re-research", action="store_true"); p.add_argument("--reactivate", action="store_true")
    p.add_argument("--tasks", help="task file (overrides $DEVLOOP_TASKS_FILE and discovery)"); p.add_argument("--limit", type=int, help="next: print at most N tasks (default: all)")
    p.set_defaults(f=cmd_tasks)
    p = sp.add_parser("adr"); p.add_argument("op", choices=["new"]); p.add_argument("title"); p.add_argument("--root", default="."); p.set_defaults(f=cmd_adr)
    p = sp.add_parser("trailer"); p.add_argument("id"); p.set_defaults(f=lambda a: print(f"Task-Id: {a.id}"))
    p = sp.add_parser("strip-frontmatter"); p.add_argument("path"); p.set_defaults(f=cmd_strip)
    a = ap.parse_args()
    if a.cmd == "tasks":
        if a.op == "add": a.id = a.id_flag or a.id or die("--id required")
        if a.op in ("set", "lane") and not a.id: die("task id required")
        if a.op == "set" and not a.status: die("status required")
        if a.op == "add" and not a.title: die("--title required")
    a.f(a)


if __name__ == "__main__":
    main()
