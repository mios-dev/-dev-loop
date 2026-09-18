# Symphony-CC Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python daemon that polls GitHub Issues and runs Claude Code CLI against each issue in isolated git worktrees.

**Architecture:** Single-process asyncio daemon. Orchestrator owns the poll loop and dispatches workers as asyncio tasks. Workers spawn `claude` CLI as subprocesses. State is in-memory with JSON file persistence for the `status` command.

**Tech Stack:** Python 3.11+, click, pyyaml, jinja2, watchfiles, asyncio, subprocess

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `symphony/__init__.py`
- Create: `symphony/cli.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "symphony-cc"
version = "0.1.0"
description = "Autonomous coding agent orchestrator for GitHub Issues + Claude Code"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "pyyaml>=6.0",
    "jinja2>=3.1",
    "watchfiles>=0.20",
]

[project.scripts]
symphony = "symphony.cli:main"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]
```

**Step 2: Create symphony/__init__.py**

```python
"""Symphony-CC: Autonomous coding agent orchestrator."""
__version__ = "0.1.0"
```

**Step 3: Create minimal CLI entry point**

```python
"""symphony/cli.py"""
import click


@click.group()
@click.version_option()
def main():
    """Symphony-CC — autonomous coding agent orchestrator."""
    pass


@main.command()
def start():
    """Start the Symphony orchestrator."""
    click.echo("Symphony starting... (not implemented)")


@main.command()
def status():
    """Show current orchestrator status."""
    click.echo("Status: not implemented")


@main.command()
def stop():
    """Stop the running orchestrator."""
    click.echo("Stop: not implemented")
```

**Step 4: Install in dev mode and verify**

Run: `cd /Users/hackerman/Developer/agents-stuff/autonomous-agents && pip install -e ".[dev]"`
Run: `symphony --version`
Expected: `symphony-cc, version 0.1.0`

**Step 5: Commit**

```bash
git init
git add pyproject.toml symphony/
git commit -m "scaffold: project setup with CLI entry point"
```

---

### Task 2: Config Layer (WORKFLOW.md Parser)

**Files:**
- Create: `symphony/config.py`
- Create: `tests/test_config.py`
- Create: `tests/fixtures/sample_workflow.md`

**Step 1: Create test fixture**

```markdown
---
tracker:
  kind: github
  labels:
    - agent
  exclude_labels:
    - blocked
  assignee: "@me"

polling:
  interval_ms: 15000

agent:
  max_concurrent: 2
  max_turns: 3
  max_retry_backoff_ms: 60000
  command: claude
  permission_mode: acceptEdits
  skills:
    - code-reviewer
  mcp_servers:
    - name: playwright
      command: npx @playwright/mcp@latest

hooks:
  after_create: |
    npm install
  before_run: |
    git fetch origin main
  timeout_ms: 30000
---

You are working on issue #{{ issue.number }}: {{ issue.title }}

{{ issue.body }}

When done, commit, push, and create a PR.
```

**Step 2: Write failing tests**

```python
"""tests/test_config.py"""
import os
import pytest
from symphony.config import load_workflow, WorkflowConfig, ConfigError

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_load_valid_workflow():
    wf = load_workflow(os.path.join(FIXTURES, "sample_workflow.md"))
    assert wf.tracker_kind == "github"
    assert wf.tracker_labels == ["agent"]
    assert wf.tracker_exclude_labels == ["blocked"]
    assert wf.tracker_assignee == "@me"
    assert wf.poll_interval_ms == 15000
    assert wf.max_concurrent == 2
    assert wf.max_turns == 3
    assert wf.agent_command == "claude"
    assert wf.permission_mode == "acceptEdits"
    assert "issue.number" in wf.prompt_template
    assert len(wf.mcp_servers) == 1
    assert wf.mcp_servers[0]["name"] == "playwright"
    assert wf.hook_after_create.strip() == "npm install"
    assert wf.hook_timeout_ms == 30000


def test_load_missing_file():
    with pytest.raises(ConfigError, match="missing_workflow_file"):
        load_workflow("/nonexistent/WORKFLOW.md")


def test_load_no_front_matter():
    """File with no YAML front matter uses all defaults."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("Just a prompt template with {{ issue.title }}")
        f.flush()
        wf = load_workflow(f.name)
        assert wf.tracker_kind == "github"
        assert wf.max_concurrent == 3
        assert wf.prompt_template == "Just a prompt template with {{ issue.title }}"
    os.unlink(f.name)


def test_load_invalid_yaml():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("---\n[not: valid: yaml\n---\nPrompt")
        f.flush()
        with pytest.raises(ConfigError, match="workflow_parse_error"):
            load_workflow(f.name)
    os.unlink(f.name)


def test_load_non_map_front_matter():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("---\n- just\n- a\n- list\n---\nPrompt")
        f.flush()
        with pytest.raises(ConfigError, match="workflow_front_matter_not_a_map"):
            load_workflow(f.name)
    os.unlink(f.name)


def test_defaults_applied():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("---\ntracker:\n  kind: github\n---\nPrompt")
        f.flush()
        wf = load_workflow(f.name)
        assert wf.poll_interval_ms == 30000
        assert wf.max_concurrent == 3
        assert wf.max_turns == 5
        assert wf.max_retry_backoff_ms == 300000
        assert wf.agent_command == "claude"
        assert wf.permission_mode == "acceptEdits"
        assert wf.hook_timeout_ms == 60000
        assert wf.tracker_labels == []
        assert wf.tracker_exclude_labels == []
        assert wf.tracker_assignee is None
        assert wf.mcp_servers == []
        assert wf.skills == []
    os.unlink(f.name)
```

**Step 3: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'symphony.config'`

**Step 4: Implement config.py**

```python
"""symphony/config.py — WORKFLOW.md parser and typed config."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml


class ConfigError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class WorkflowConfig:
    # Tracker
    tracker_kind: str = "github"
    tracker_labels: list[str] = field(default_factory=list)
    tracker_exclude_labels: list[str] = field(default_factory=list)
    tracker_assignee: str | None = None

    # Polling
    poll_interval_ms: int = 30000

    # Agent
    max_concurrent: int = 3
    max_turns: int = 5
    max_retry_backoff_ms: int = 300000
    agent_command: str = "claude"
    permission_mode: str = "acceptEdits"
    skills: list[str] = field(default_factory=list)
    mcp_servers: list[dict[str, Any]] = field(default_factory=list)

    # Hooks
    hook_after_create: str | None = None
    hook_before_run: str | None = None
    hook_after_run: str | None = None
    hook_before_remove: str | None = None
    hook_timeout_ms: int = 60000

    # Prompt
    prompt_template: str = ""


def _get(d: dict, *keys: str, default: Any = None) -> Any:
    """Nested dict get."""
    current = d
    for k in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(k)
        if current is None:
            return default
    return current


def _parse_front_matter(content: str) -> tuple[dict[str, Any], str]:
    """Split WORKFLOW.md into YAML front matter dict and prompt body."""
    if not content.startswith("---"):
        return {}, content.strip()

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content.strip()

    yaml_str = parts[1]
    body = parts[2].strip()

    try:
        parsed = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise ConfigError("workflow_parse_error", str(e))

    if parsed is None:
        return {}, body

    if not isinstance(parsed, dict):
        raise ConfigError(
            "workflow_front_matter_not_a_map",
            f"Expected a mapping, got {type(parsed).__name__}",
        )

    return parsed, body


def load_workflow(path: str) -> WorkflowConfig:
    """Load and parse a WORKFLOW.md file into a typed config."""
    if not os.path.isfile(path):
        raise ConfigError("missing_workflow_file", f"File not found: {path}")

    try:
        with open(path) as f:
            content = f.read()
    except OSError as e:
        raise ConfigError("missing_workflow_file", str(e))

    fm, prompt = _parse_front_matter(content)

    def _int(val: Any, default: int) -> int:
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    return WorkflowConfig(
        tracker_kind=_get(fm, "tracker", "kind", default="github"),
        tracker_labels=_get(fm, "tracker", "labels", default=[]),
        tracker_exclude_labels=_get(fm, "tracker", "exclude_labels", default=[]),
        tracker_assignee=_get(fm, "tracker", "assignee"),
        poll_interval_ms=_int(_get(fm, "polling", "interval_ms"), 30000),
        max_concurrent=_int(_get(fm, "agent", "max_concurrent"), 3),
        max_turns=_int(_get(fm, "agent", "max_turns"), 5),
        max_retry_backoff_ms=_int(_get(fm, "agent", "max_retry_backoff_ms"), 300000),
        agent_command=_get(fm, "agent", "command", default="claude"),
        permission_mode=_get(fm, "agent", "permission_mode", default="acceptEdits"),
        skills=_get(fm, "agent", "skills", default=[]),
        mcp_servers=_get(fm, "agent", "mcp_servers", default=[]),
        hook_after_create=_get(fm, "hooks", "after_create"),
        hook_before_run=_get(fm, "hooks", "before_run"),
        hook_after_run=_get(fm, "hooks", "after_run"),
        hook_before_remove=_get(fm, "hooks", "before_remove"),
        hook_timeout_ms=_int(_get(fm, "hooks", "timeout_ms"), 60000),
        prompt_template=prompt,
    )
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add symphony/config.py tests/test_config.py tests/fixtures/sample_workflow.md
git commit -m "feat: WORKFLOW.md parser with typed config and defaults"
```

---

### Task 3: GitHub Issue Tracker Client

**Files:**
- Create: `symphony/tracker.py`
- Create: `tests/test_tracker.py`

**Step 1: Write failing tests**

```python
"""tests/test_tracker.py"""
import json
import pytest
from unittest.mock import patch, AsyncMock
from symphony.tracker import GitHubTracker, Issue, TrackerError


@pytest.fixture
def tracker():
    return GitHubTracker(
        labels=["agent"],
        exclude_labels=["blocked"],
        assignee=None,
    )


def _make_gh_issue(number=42, title="Fix bug", state="open", labels=None, body="Issue body"):
    return {
        "number": number,
        "title": title,
        "state": state.upper(),
        "labels": [{"name": l} for l in (labels or [])],
        "body": body,
        "url": f"https://github.com/owner/repo/issues/{number}",
        "createdAt": "2026-03-16T10:00:00Z",
        "updatedAt": "2026-03-16T12:00:00Z",
        "assignees": [],
    }


@pytest.mark.asyncio
async def test_fetch_candidates(tracker):
    gh_output = json.dumps([
        _make_gh_issue(42, "Fix bug", "open", ["agent"]),
        _make_gh_issue(43, "Add feature", "open", ["agent"]),
    ])
    with patch("symphony.tracker.run_gh", new_callable=AsyncMock, return_value=gh_output):
        issues = await tracker.fetch_candidates()
        assert len(issues) == 2
        assert issues[0].number == 42
        assert issues[0].title == "Fix bug"
        assert issues[0].state == "open"


@pytest.mark.asyncio
async def test_fetch_candidates_filters_excluded(tracker):
    gh_output = json.dumps([
        _make_gh_issue(42, "Fix bug", "open", ["agent"]),
        _make_gh_issue(43, "Blocked", "open", ["agent", "blocked"]),
    ])
    with patch("symphony.tracker.run_gh", new_callable=AsyncMock, return_value=gh_output):
        issues = await tracker.fetch_candidates()
        assert len(issues) == 1
        assert issues[0].number == 42


@pytest.mark.asyncio
async def test_fetch_issue_state(tracker):
    gh_output = json.dumps({"number": 42, "state": "CLOSED"})
    with patch("symphony.tracker.run_gh", new_callable=AsyncMock, return_value=gh_output):
        state = await tracker.fetch_issue_state(42)
        assert state == "closed"


@pytest.mark.asyncio
async def test_issue_normalization():
    raw = _make_gh_issue(42, "Fix bug", "OPEN", ["agent", "Bug"], body="Fix the login")
    issue = Issue.from_gh(raw)
    assert issue.number == 42
    assert issue.title == "Fix bug"
    assert issue.state == "open"
    assert issue.labels == ["agent", "bug"]
    assert issue.body == "Fix the login"


@pytest.mark.asyncio
async def test_parse_issue_skills():
    from symphony.tracker import parse_issue_skills
    body = """## Description
Fix the login page

## Skills
- playwright
- accessibility-checker

## Acceptance Criteria
- Login works
"""
    skills = parse_issue_skills(body)
    assert skills == ["playwright", "accessibility-checker"]


@pytest.mark.asyncio
async def test_parse_issue_skills_no_section():
    from symphony.tracker import parse_issue_skills
    assert parse_issue_skills("Just a plain issue body") == []
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tracker.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement tracker.py**

```python
"""symphony/tracker.py — GitHub Issues client via gh CLI."""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime


class TrackerError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class Issue:
    number: int
    title: str
    state: str
    body: str
    url: str
    labels: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def identifier(self) -> str:
        return str(self.number)

    @classmethod
    def from_gh(cls, raw: dict) -> Issue:
        labels = [l["name"].lower() for l in raw.get("labels", [])]
        assignees = [a.get("login", "") for a in raw.get("assignees", [])]
        created_at = None
        if raw.get("createdAt"):
            try:
                created_at = datetime.fromisoformat(raw["createdAt"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        updated_at = None
        if raw.get("updatedAt"):
            try:
                updated_at = datetime.fromisoformat(raw["updatedAt"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        return cls(
            number=raw["number"],
            title=raw["title"],
            state=raw["state"].lower(),
            body=raw.get("body") or "",
            url=raw.get("url", ""),
            labels=labels,
            assignees=assignees,
            created_at=created_at,
            updated_at=updated_at,
        )


async def run_gh(args: list[str]) -> str:
    """Run a gh CLI command and return stdout."""
    proc = await asyncio.create_subprocess_exec(
        "gh", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise TrackerError(
            "gh_command_failed",
            f"gh {' '.join(args)} failed (rc={proc.returncode}): {stderr.decode().strip()}",
        )
    return stdout.decode()


def parse_issue_skills(body: str) -> list[str]:
    """Extract skill names from a ## Skills section in the issue body."""
    if not body:
        return []
    match = re.search(r"##\s*Skills\s*\n((?:\s*-\s*.+\n?)+)", body, re.IGNORECASE)
    if not match:
        return []
    lines = match.group(1).strip().split("\n")
    skills = []
    for line in lines:
        line = line.strip()
        if line.startswith("- "):
            skill = line[2:].strip()
            # Take only the skill name, ignore parenthetical descriptions
            skill = re.split(r"\s*\(", skill)[0].strip()
            if skill:
                skills.append(skill)
    return skills


class GitHubTracker:
    def __init__(
        self,
        labels: list[str] | None = None,
        exclude_labels: list[str] | None = None,
        assignee: str | None = None,
    ):
        self.labels = labels or []
        self.exclude_labels = [l.lower() for l in (exclude_labels or [])]
        self.assignee = assignee

    async def fetch_candidates(self) -> list[Issue]:
        """Fetch open issues matching configured filters."""
        args = [
            "issue", "list",
            "--state", "open",
            "--json", "number,title,state,labels,body,url,createdAt,updatedAt,assignees",
            "--limit", "100",
        ]
        for label in self.labels:
            args.extend(["--label", label])
        if self.assignee:
            args.extend(["--assignee", self.assignee])

        output = await run_gh(args)
        raw_issues = json.loads(output)

        issues = [Issue.from_gh(r) for r in raw_issues]

        # Apply exclude filter
        if self.exclude_labels:
            issues = [
                i for i in issues
                if not any(el in i.labels for el in self.exclude_labels)
            ]

        # Sort: created_at ascending (oldest first)
        issues.sort(key=lambda i: i.created_at or datetime.min)
        return issues

    async def fetch_issue_state(self, number: int) -> str:
        """Fetch current state of a single issue."""
        output = await run_gh([
            "issue", "view", str(number),
            "--json", "number,state",
        ])
        raw = json.loads(output)
        return raw["state"].lower()

    async def fetch_issue_states(self, numbers: list[int]) -> dict[int, str]:
        """Fetch current states for multiple issues."""
        results = {}
        for number in numbers:
            try:
                results[number] = await self.fetch_issue_state(number)
            except TrackerError:
                pass
        return results
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tracker.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add symphony/tracker.py tests/test_tracker.py
git commit -m "feat: GitHub Issues tracker client with skill parsing"
```

---

### Task 4: Workspace Manager (Git Worktrees)

**Files:**
- Create: `symphony/workspace.py`
- Create: `tests/test_workspace.py`
- Create: `symphony/hooks.py`

**Step 1: Write failing tests**

```python
"""tests/test_workspace.py"""
import os
import pytest
from unittest.mock import patch, AsyncMock
from symphony.workspace import WorkspaceManager, WorkspaceError


@pytest.fixture
def tmp_workspace(tmp_path):
    return WorkspaceManager(
        project_root=str(tmp_path / "project"),
        symphony_dir=str(tmp_path / "project" / ".symphony"),
    )


@pytest.mark.asyncio
async def test_worktree_path(tmp_workspace):
    path = tmp_workspace.worktree_path(42)
    assert path.endswith(".symphony/worktrees/42")


@pytest.mark.asyncio
async def test_worktree_path_sanitized(tmp_workspace):
    path = tmp_workspace.worktree_path(42)
    dirname = os.path.basename(path)
    assert all(c.isalnum() or c in "._-" for c in dirname)


@pytest.mark.asyncio
async def test_create_worktree_new(tmp_workspace):
    with patch("symphony.workspace.run_cmd", new_callable=AsyncMock, return_value=""):
        result = await tmp_workspace.ensure_worktree(42)
        assert result.path.endswith("42")
        assert result.created_now is True


@pytest.mark.asyncio
async def test_reuse_existing_worktree(tmp_workspace):
    wt_path = tmp_workspace.worktree_path(42)
    os.makedirs(wt_path, exist_ok=True)
    result = await tmp_workspace.ensure_worktree(42)
    assert result.created_now is False


@pytest.mark.asyncio
async def test_cleanup_worktree(tmp_workspace):
    wt_path = tmp_workspace.worktree_path(42)
    os.makedirs(wt_path, exist_ok=True)
    with patch("symphony.workspace.run_cmd", new_callable=AsyncMock, return_value=""):
        await tmp_workspace.cleanup_worktree(42)
        assert not os.path.exists(wt_path)


@pytest.mark.asyncio
async def test_worktree_path_inside_root(tmp_workspace):
    path = tmp_workspace.worktree_path(42)
    assert path.startswith(tmp_workspace.symphony_dir)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_workspace.py -v`
Expected: FAIL

**Step 3: Implement hooks.py**

```python
"""symphony/hooks.py — Shell hook executor with timeout."""
from __future__ import annotations

import asyncio
import logging

log = logging.getLogger("symphony")


async def run_hook(
    name: str,
    script: str | None,
    cwd: str,
    timeout_ms: int = 60000,
) -> bool:
    """Run a shell hook script. Returns True on success, False on failure."""
    if not script or not script.strip():
        return True

    log.info(f"hook:{name} starting in {cwd}")
    try:
        proc = await asyncio.create_subprocess_exec(
            "bash", "-lc", script,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        timeout_s = max(timeout_ms / 1000, 1)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)

        if proc.returncode != 0:
            log.error(f"hook:{name} failed (rc={proc.returncode}): {stderr.decode()[:500]}")
            return False

        log.info(f"hook:{name} completed")
        return True

    except asyncio.TimeoutError:
        log.error(f"hook:{name} timed out after {timeout_ms}ms")
        proc.kill()
        return False
    except Exception as e:
        log.error(f"hook:{name} error: {e}")
        return False
```

**Step 4: Implement workspace.py**

```python
"""symphony/workspace.py — Git worktree lifecycle manager."""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass

log = logging.getLogger("symphony")


class WorkspaceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class WorktreeResult:
    path: str
    created_now: bool


async def run_cmd(args: list[str], cwd: str | None = None) -> str:
    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise WorkspaceError(
            "command_failed",
            f"{' '.join(args)} failed (rc={proc.returncode}): {stderr.decode().strip()}",
        )
    return stdout.decode()


class WorkspaceManager:
    def __init__(self, project_root: str, symphony_dir: str | None = None):
        self.project_root = os.path.abspath(project_root)
        self.symphony_dir = symphony_dir or os.path.join(self.project_root, ".symphony")
        self.worktrees_dir = os.path.join(self.symphony_dir, "worktrees")

    def worktree_path(self, issue_number: int) -> str:
        sanitized = str(issue_number)
        path = os.path.join(self.worktrees_dir, sanitized)
        # Safety: must be under symphony_dir
        abs_path = os.path.abspath(path)
        if not abs_path.startswith(os.path.abspath(self.symphony_dir)):
            raise WorkspaceError("path_escape", f"Worktree path {abs_path} escapes symphony dir")
        return abs_path

    async def ensure_worktree(self, issue_number: int) -> WorktreeResult:
        path = self.worktree_path(issue_number)

        if os.path.isdir(path):
            log.info(f"workspace: reusing worktree at {path}")
            return WorktreeResult(path=path, created_now=False)

        os.makedirs(self.worktrees_dir, exist_ok=True)
        branch = f"symphony/issue-{issue_number}"

        try:
            await run_cmd(
                ["git", "worktree", "add", "-b", branch, path, "HEAD"],
                cwd=self.project_root,
            )
        except WorkspaceError:
            # Branch may already exist from a previous run
            try:
                await run_cmd(
                    ["git", "worktree", "add", path, branch],
                    cwd=self.project_root,
                )
            except WorkspaceError as e:
                raise WorkspaceError("worktree_create_failed", str(e))

        log.info(f"workspace: created worktree at {path}")
        return WorktreeResult(path=path, created_now=True)

    async def cleanup_worktree(self, issue_number: int) -> None:
        path = self.worktree_path(issue_number)
        if not os.path.exists(path):
            return

        try:
            await run_cmd(
                ["git", "worktree", "remove", "--force", path],
                cwd=self.project_root,
            )
        except WorkspaceError:
            # Fallback: manual removal
            shutil.rmtree(path, ignore_errors=True)

        log.info(f"workspace: cleaned up worktree at {path}")
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_workspace.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add symphony/workspace.py symphony/hooks.py tests/test_workspace.py
git commit -m "feat: git worktree workspace manager with hooks"
```

---

### Task 5: Prompt Renderer

**Files:**
- Create: `symphony/prompt.py`
- Create: `tests/test_prompt.py`

**Step 1: Write failing tests**

```python
"""tests/test_prompt.py"""
import pytest
from symphony.prompt import render_prompt, PromptError
from symphony.tracker import Issue


@pytest.fixture
def issue():
    return Issue(
        number=42,
        title="Fix login redirect",
        state="open",
        body="The login page redirects to 404",
        url="https://github.com/owner/repo/issues/42",
        labels=["bug", "urgent"],
    )


def test_render_basic(issue):
    template = "Fix issue #{{ issue.number }}: {{ issue.title }}\n\n{{ issue.body }}"
    result = render_prompt(template, issue, attempt=None)
    assert "Fix issue #42" in result
    assert "Fix login redirect" in result
    assert "redirects to 404" in result


def test_render_with_attempt(issue):
    template = "{% if attempt %}Retry #{{ attempt }}{% endif %} {{ issue.title }}"
    result = render_prompt(template, issue, attempt=3)
    assert "Retry #3" in result


def test_render_no_attempt(issue):
    template = "{% if attempt %}Retry{% else %}First run{% endif %}"
    result = render_prompt(template, issue, attempt=None)
    assert "First run" in result


def test_render_labels(issue):
    template = "{% if 'bug' in issue.labels %}This is a bug{% endif %}"
    result = render_prompt(template, issue)
    assert "This is a bug" in result


def test_render_unknown_variable(issue):
    template = "{{ unknown_var }}"
    with pytest.raises(PromptError, match="template_render_error"):
        render_prompt(template, issue)


def test_render_empty_template(issue):
    result = render_prompt("", issue)
    assert result == ""
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_prompt.py -v`
Expected: FAIL

**Step 3: Implement prompt.py**

```python
"""symphony/prompt.py — Jinja2 prompt template renderer."""
from __future__ import annotations

from dataclasses import asdict

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError

from symphony.tracker import Issue


class PromptError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


_env = Environment(undefined=StrictUndefined)


def render_prompt(
    template_str: str,
    issue: Issue,
    attempt: int | None = None,
) -> str:
    """Render a prompt template with issue context."""
    if not template_str:
        return ""

    try:
        template = _env.from_string(template_str)
    except TemplateSyntaxError as e:
        raise PromptError("template_parse_error", str(e))

    try:
        return template.render(
            issue=asdict(issue),
            attempt=attempt,
        )
    except UndefinedError as e:
        raise PromptError("template_render_error", str(e))
```

**Step 4: Run tests**

Run: `pytest tests/test_prompt.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add symphony/prompt.py tests/test_prompt.py
git commit -m "feat: Jinja2 prompt renderer with strict variable checking"
```

---

### Task 6: Worker (Claude Code Subprocess Runner)

**Files:**
- Create: `symphony/worker.py`
- Create: `tests/test_worker.py`

**Step 1: Write failing tests**

```python
"""tests/test_worker.py"""
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from symphony.worker import Worker, WorkerResult, WorkerError
from symphony.config import WorkflowConfig
from symphony.tracker import Issue


@pytest.fixture
def config():
    return WorkflowConfig(
        agent_command="claude",
        permission_mode="acceptEdits",
        mcp_servers=[],
        skills=[],
    )


@pytest.fixture
def issue():
    return Issue(
        number=42,
        title="Fix bug",
        state="open",
        body="Fix the login",
        url="https://github.com/owner/repo/issues/42",
        labels=["bug"],
    )


def test_build_claude_args(config, issue):
    worker = Worker(config)
    args = worker._build_claude_args(
        prompt="Fix the bug",
        cwd="/path/to/worktree",
        issue_skills=[],
    )
    assert args[0] == "claude"
    assert "-p" in args
    assert "--output-format" in args
    assert "json" in args
    assert "--cwd" not in args  # cwd is set via subprocess, not flag


def test_build_claude_args_with_mcp(config, issue):
    config.mcp_servers = [{"name": "playwright", "command": "npx @playwright/mcp@latest"}]
    worker = Worker(config)
    args = worker._build_claude_args(
        prompt="Fix the bug",
        cwd="/path/to/worktree",
        issue_skills=[],
    )
    assert "--mcp-config" in args or any("playwright" in str(a) for a in args)


@pytest.mark.asyncio
async def test_run_turn_success(config, issue):
    worker = Worker(config)
    mock_result = json.dumps({
        "result": "I fixed the bug and created a PR",
        "is_error": False,
    })
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(mock_result.encode(), b""))
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await worker.run_turn(
            prompt="Fix the bug",
            cwd="/path/to/worktree",
            issue_skills=[],
            timeout_ms=60000,
        )
        assert result.success is True
        assert "fixed the bug" in result.output


@pytest.mark.asyncio
async def test_run_turn_failure(config, issue):
    worker = Worker(config)
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"", b"Error occurred"))
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await worker.run_turn(
            prompt="Fix the bug",
            cwd="/path/to/worktree",
            issue_skills=[],
            timeout_ms=60000,
        )
        assert result.success is False
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_worker.py -v`
Expected: FAIL

**Step 3: Implement worker.py**

```python
"""symphony/worker.py — Claude Code CLI subprocess runner."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass

from symphony.config import WorkflowConfig

log = logging.getLogger("symphony")


class WorkerError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class WorkerResult:
    success: bool
    output: str
    error: str | None = None
    exit_code: int = 0


class Worker:
    def __init__(self, config: WorkflowConfig):
        self.config = config

    def _build_mcp_config(self, issue_skills: list[str]) -> dict | None:
        """Build MCP config dict from workflow config and issue skills."""
        servers = {}
        for mcp in self.config.mcp_servers:
            name = mcp.get("name", "")
            command = mcp.get("command", "")
            if name and command:
                parts = command.split()
                servers[name] = {
                    "command": parts[0],
                    "args": parts[1:] if len(parts) > 1 else [],
                }
                if mcp.get("env"):
                    servers[name]["env"] = mcp["env"]
        if not servers:
            return None
        return {"mcpServers": servers}

    def _build_claude_args(
        self,
        prompt: str,
        cwd: str,
        issue_skills: list[str],
    ) -> list[str]:
        """Build the claude CLI argument list."""
        args = [
            self.config.agent_command,
            "-p", prompt,
            "--output-format", "json",
        ]

        if self.config.permission_mode:
            # Map our permission modes to claude CLI flags
            mode = self.config.permission_mode
            if mode == "acceptEdits":
                args.extend(["--permission-mode", "acceptEdits"])
            elif mode == "bypassPermissions":
                args.extend(["--dangerously-skip-permissions"])

        return args

    async def run_turn(
        self,
        prompt: str,
        cwd: str,
        issue_skills: list[str] | None = None,
        timeout_ms: int = 3600000,
    ) -> WorkerResult:
        """Run a single Claude Code turn."""
        issue_skills = issue_skills or []
        args = self._build_claude_args(prompt, cwd, issue_skills)

        # Write MCP config to temp file if needed
        mcp_config = self._build_mcp_config(issue_skills)
        mcp_config_path = None
        if mcp_config:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, prefix="symphony_mcp_"
            )
            json.dump(mcp_config, tmp)
            tmp.close()
            mcp_config_path = tmp.name
            args.extend(["--mcp-config", mcp_config_path])

        log.info(f"worker: launching {' '.join(args[:4])}... in {cwd}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            timeout_s = max(timeout_ms / 1000, 1)
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_s
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return WorkerResult(
                    success=False,
                    output="",
                    error=f"Turn timed out after {timeout_ms}ms",
                    exit_code=-1,
                )

            stdout_str = stdout.decode()
            stderr_str = stderr.decode()

            # Try to parse JSON output
            output_text = stdout_str
            try:
                parsed = json.loads(stdout_str)
                if isinstance(parsed, dict):
                    output_text = parsed.get("result", stdout_str)
                    if parsed.get("is_error"):
                        return WorkerResult(
                            success=False,
                            output=output_text,
                            error=output_text,
                            exit_code=proc.returncode or 1,
                        )
            except (json.JSONDecodeError, ValueError):
                pass

            if proc.returncode != 0:
                return WorkerResult(
                    success=False,
                    output=output_text,
                    error=stderr_str or f"Exit code {proc.returncode}",
                    exit_code=proc.returncode,
                )

            return WorkerResult(
                success=True,
                output=output_text,
                exit_code=0,
            )

        except FileNotFoundError:
            return WorkerResult(
                success=False,
                output="",
                error=f"Command not found: {self.config.agent_command}",
                exit_code=-1,
            )
        finally:
            if mcp_config_path:
                try:
                    os.unlink(mcp_config_path)
                except OSError:
                    pass
```

**Step 4: Run tests**

Run: `pytest tests/test_worker.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add symphony/worker.py tests/test_worker.py
git commit -m "feat: Claude Code CLI subprocess worker with MCP support"
```

---

### Task 7: State Manager

**Files:**
- Create: `symphony/state.py`
- Create: `tests/test_state.py`

**Step 1: Write failing tests**

```python
"""tests/test_state.py"""
import json
import os
import pytest
from symphony.state import OrchestratorState, IssueState


def test_initial_state():
    state = OrchestratorState()
    assert len(state.running) == 0
    assert len(state.claimed) == 0
    assert len(state.retry_queue) == 0


def test_claim_issue():
    state = OrchestratorState()
    state.claim(42)
    assert 42 in state.claimed
    assert state.is_claimed(42)


def test_release_issue():
    state = OrchestratorState()
    state.claim(42)
    state.release(42)
    assert 42 not in state.claimed


def test_add_running():
    state = OrchestratorState()
    state.add_running(42, IssueState(
        issue_number=42,
        identifier="42",
        title="Fix bug",
        state="open",
        turn=1,
        max_turns=5,
    ))
    assert 42 in state.running
    assert state.running_count == 1


def test_available_slots():
    state = OrchestratorState(max_concurrent=2)
    assert state.available_slots == 2
    state.add_running(42, IssueState(
        issue_number=42, identifier="42", title="Fix", state="open", turn=1, max_turns=5,
    ))
    assert state.available_slots == 1


def test_persist_and_load(tmp_path):
    state = OrchestratorState()
    state.claim(42)
    state.add_running(42, IssueState(
        issue_number=42, identifier="42", title="Fix bug", state="open", turn=1, max_turns=5,
    ))
    path = str(tmp_path / "state.json")
    state.persist(path)
    assert os.path.exists(path)

    loaded = json.loads(open(path).read())
    assert loaded["running"][0]["issue_number"] == 42


def test_schedule_retry():
    state = OrchestratorState()
    state.claim(42)
    state.schedule_retry(42, attempt=1, error="test failure", delay_ms=1000)
    assert 42 in state.retry_queue
    assert state.retry_queue[42].attempt == 1
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state.py -v`
Expected: FAIL

**Step 3: Implement state.py**

```python
"""symphony/state.py — In-memory orchestrator state with JSON persistence."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field


@dataclass
class IssueState:
    issue_number: int
    identifier: str
    title: str
    state: str
    turn: int
    max_turns: int
    started_at: float = field(default_factory=time.time)
    last_event: str | None = None
    last_event_at: float | None = None
    error: str | None = None


@dataclass
class RetryEntry:
    issue_number: int
    identifier: str
    attempt: int
    due_at: float
    error: str | None = None


class OrchestratorState:
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.running: dict[int, IssueState] = {}
        self.claimed: set[int] = set()
        self.retry_queue: dict[int, RetryEntry] = {}
        self.completed: set[int] = set()

    @property
    def running_count(self) -> int:
        return len(self.running)

    @property
    def available_slots(self) -> int:
        return max(self.max_concurrent - self.running_count, 0)

    def is_claimed(self, issue_number: int) -> bool:
        return issue_number in self.claimed

    def claim(self, issue_number: int) -> None:
        self.claimed.add(issue_number)

    def release(self, issue_number: int) -> None:
        self.claimed.discard(issue_number)
        self.running.pop(issue_number, None)
        self.retry_queue.pop(issue_number, None)

    def add_running(self, issue_number: int, state: IssueState) -> None:
        self.running[issue_number] = state
        self.claimed.add(issue_number)
        self.retry_queue.pop(issue_number, None)

    def remove_running(self, issue_number: int) -> IssueState | None:
        return self.running.pop(issue_number, None)

    def schedule_retry(
        self,
        issue_number: int,
        attempt: int,
        error: str | None = None,
        delay_ms: int = 1000,
    ) -> None:
        self.retry_queue[issue_number] = RetryEntry(
            issue_number=issue_number,
            identifier=str(issue_number),
            attempt=attempt,
            due_at=time.time() + delay_ms / 1000,
            error=error,
        )

    def due_retries(self) -> list[RetryEntry]:
        now = time.time()
        return [r for r in self.retry_queue.values() if r.due_at <= now]

    def persist(self, path: str) -> None:
        data = {
            "running": [
                {
                    "issue_number": s.issue_number,
                    "identifier": s.identifier,
                    "title": s.title,
                    "state": s.state,
                    "turn": s.turn,
                    "max_turns": s.max_turns,
                    "started_at": s.started_at,
                    "last_event": s.last_event,
                    "error": s.error,
                }
                for s in self.running.values()
            ],
            "retrying": [
                {
                    "issue_number": r.issue_number,
                    "identifier": r.identifier,
                    "attempt": r.attempt,
                    "due_at": r.due_at,
                    "error": r.error,
                }
                for r in self.retry_queue.values()
            ],
            "claimed": list(self.claimed),
            "completed_count": len(self.completed),
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
```

**Step 4: Run tests**

Run: `pytest tests/test_state.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add symphony/state.py tests/test_state.py
git commit -m "feat: orchestrator state manager with JSON persistence"
```

---

### Task 8: Orchestrator (Main Event Loop)

**Files:**
- Create: `symphony/orchestrator.py`
- Create: `tests/test_orchestrator.py`

**Step 1: Write failing tests**

```python
"""tests/test_orchestrator.py"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from symphony.orchestrator import Orchestrator
from symphony.config import WorkflowConfig
from symphony.tracker import Issue
from symphony.state import OrchestratorState


@pytest.fixture
def config():
    return WorkflowConfig(
        max_concurrent=2,
        max_turns=3,
        prompt_template="Fix #{{ issue.number }}: {{ issue.title }}",
    )


@pytest.fixture
def orchestrator(config, tmp_path):
    return Orchestrator(
        config=config,
        project_root=str(tmp_path),
        state_path=str(tmp_path / ".symphony" / "state.json"),
    )


def _make_issue(number=42, title="Fix bug", state="open"):
    return Issue(
        number=number, title=title, state=state,
        body="Fix it", url="", labels=["agent"],
    )


@pytest.mark.asyncio
async def test_should_dispatch_eligible(orchestrator):
    issue = _make_issue(42)
    assert orchestrator._should_dispatch(issue) is True


@pytest.mark.asyncio
async def test_should_not_dispatch_claimed(orchestrator):
    issue = _make_issue(42)
    orchestrator.state.claim(42)
    assert orchestrator._should_dispatch(issue) is False


@pytest.mark.asyncio
async def test_should_not_dispatch_no_slots(orchestrator):
    orchestrator.state.max_concurrent = 0
    issue = _make_issue(42)
    assert orchestrator._should_dispatch(issue) is False


@pytest.mark.asyncio
async def test_dispatch_creates_worker(orchestrator):
    issue = _make_issue(42)
    with patch.object(orchestrator, "_run_worker", new_callable=AsyncMock):
        await orchestrator._dispatch(issue)
        assert orchestrator.state.is_claimed(42)
        assert 42 in orchestrator.state.running


@pytest.mark.asyncio
async def test_reconcile_terminal_issue(orchestrator):
    issue = _make_issue(42)
    from symphony.state import IssueState
    orchestrator.state.add_running(42, IssueState(
        issue_number=42, identifier="42", title="Fix",
        state="open", turn=1, max_turns=3,
    ))
    with patch.object(orchestrator.tracker, "fetch_issue_states", new_callable=AsyncMock, return_value={42: "closed"}):
        with patch.object(orchestrator.workspace, "cleanup_worktree", new_callable=AsyncMock):
            await orchestrator._reconcile()
            assert 42 not in orchestrator.state.running
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL

**Step 3: Implement orchestrator.py**

```python
"""symphony/orchestrator.py — Main event loop: poll, dispatch, reconcile."""
from __future__ import annotations

import asyncio
import logging
import time

from symphony.config import WorkflowConfig, load_workflow
from symphony.hooks import run_hook
from symphony.prompt import render_prompt
from symphony.state import IssueState, OrchestratorState
from symphony.tracker import GitHubTracker, Issue, parse_issue_skills
from symphony.worker import Worker
from symphony.workspace import WorkspaceManager

log = logging.getLogger("symphony")


class Orchestrator:
    def __init__(
        self,
        config: WorkflowConfig,
        project_root: str,
        state_path: str,
        workflow_path: str | None = None,
    ):
        self.config = config
        self.project_root = project_root
        self.state_path = state_path
        self.workflow_path = workflow_path
        self.state = OrchestratorState(max_concurrent=config.max_concurrent)
        self.tracker = GitHubTracker(
            labels=config.tracker_labels,
            exclude_labels=config.tracker_exclude_labels,
            assignee=config.tracker_assignee,
        )
        self.workspace = WorkspaceManager(project_root=project_root)
        self.worker = Worker(config)
        self._running_tasks: dict[int, asyncio.Task] = {}
        self._stop_event = asyncio.Event()

    def _should_dispatch(self, issue: Issue) -> bool:
        if self.state.is_claimed(issue.number):
            return False
        if self.state.available_slots <= 0:
            return False
        return True

    async def _dispatch(self, issue: Issue) -> None:
        self.state.add_running(issue.number, IssueState(
            issue_number=issue.number,
            identifier=str(issue.number),
            title=issue.title,
            state=issue.state,
            turn=1,
            max_turns=self.config.max_turns,
        ))

        task = asyncio.create_task(self._run_worker(issue))
        self._running_tasks[issue.number] = task
        task.add_done_callback(lambda t: self._on_worker_done(issue.number, t))

        log.info(f"START #{issue.number} \"{issue.title}\"")

    def _on_worker_done(self, issue_number: int, task: asyncio.Task) -> None:
        self._running_tasks.pop(issue_number, None)
        entry = self.state.remove_running(issue_number)

        try:
            exc = task.exception()
        except asyncio.CancelledError:
            exc = None

        if exc:
            log.error(f"FAIL #{issue_number}: {exc}")
            attempt = entry.turn if entry else 1
            delay = self._backoff_delay(attempt)
            self.state.schedule_retry(
                issue_number, attempt=attempt,
                error=str(exc), delay_ms=delay,
            )
        else:
            # Normal exit — schedule short continuation retry
            self.state.completed.add(issue_number)
            self.state.schedule_retry(
                issue_number, attempt=1,
                delay_ms=1000,
            )
            log.info(f"DONE #{issue_number}")

        self.state.persist(self.state_path)

    def _backoff_delay(self, attempt: int) -> int:
        delay = min(10000 * (2 ** (attempt - 1)), self.config.max_retry_backoff_ms)
        return delay

    async def _run_worker(self, issue: Issue) -> None:
        # 1. Ensure worktree
        wt = await self.workspace.ensure_worktree(issue.number)

        # 2. Run after_create hook if new
        if wt.created_now:
            ok = await run_hook(
                "after_create", self.config.hook_after_create,
                cwd=wt.path, timeout_ms=self.config.hook_timeout_ms,
            )
            if not ok:
                raise RuntimeError("after_create hook failed")

        # 3. Run before_run hook
        ok = await run_hook(
            "before_run", self.config.hook_before_run,
            cwd=wt.path, timeout_ms=self.config.hook_timeout_ms,
        )
        if not ok:
            raise RuntimeError("before_run hook failed")

        # 4. Parse issue-level skills
        issue_skills = parse_issue_skills(issue.body)

        # 5. Multi-turn loop
        for turn in range(1, self.config.max_turns + 1):
            # Update state
            if issue.number in self.state.running:
                self.state.running[issue.number].turn = turn

            # Render prompt
            if turn == 1:
                prompt = render_prompt(self.config.prompt_template, issue, attempt=None)
            else:
                prompt = (
                    f"Continue working on issue #{issue.number}: {issue.title}. "
                    f"Check what's been done so far and continue if there's more to do. "
                    f"If the work is complete, commit, push, and create a PR."
                )

            log.info(f"RUN  #{issue.number} turn {turn}/{self.config.max_turns}")

            # Run claude
            result = await self.worker.run_turn(
                prompt=prompt,
                cwd=wt.path,
                issue_skills=issue_skills,
                timeout_ms=self.config.max_retry_backoff_ms,
            )

            if not result.success:
                log.error(f"FAIL #{issue.number} turn {turn}: {result.error}")
                # Run after_run hook (best effort)
                await run_hook(
                    "after_run", self.config.hook_after_run,
                    cwd=wt.path, timeout_ms=self.config.hook_timeout_ms,
                )
                raise RuntimeError(result.error or "Claude turn failed")

            # Check issue state
            try:
                current_state = await self.tracker.fetch_issue_state(issue.number)
            except Exception:
                break

            if current_state != "open":
                log.info(f"CLOSE #{issue.number} — issue is now {current_state}")
                break

        # Run after_run hook
        await run_hook(
            "after_run", self.config.hook_after_run,
            cwd=wt.path, timeout_ms=self.config.hook_timeout_ms,
        )

    async def _reconcile(self) -> None:
        """Check running issues against tracker state."""
        running_numbers = list(self.state.running.keys())
        if not running_numbers:
            return

        try:
            states = await self.tracker.fetch_issue_states(running_numbers)
        except Exception as e:
            log.debug(f"reconcile: state refresh failed, keeping workers: {e}")
            return

        for num, current_state in states.items():
            if current_state == "closed":
                log.info(f"RECONCILE #{num} — closed, stopping worker")
                task = self._running_tasks.get(num)
                if task and not task.done():
                    task.cancel()
                self.state.release(num)
                try:
                    await self.workspace.cleanup_worktree(num)
                except Exception as e:
                    log.error(f"RECONCILE #{num} cleanup failed: {e}")

    async def _handle_retries(self) -> None:
        """Process due retry entries."""
        for entry in self.state.due_retries():
            num = entry.issue_number
            self.state.retry_queue.pop(num, None)

            try:
                candidates = await self.tracker.fetch_candidates()
            except Exception:
                self.state.schedule_retry(
                    num, attempt=entry.attempt + 1,
                    error="retry poll failed",
                    delay_ms=self._backoff_delay(entry.attempt + 1),
                )
                continue

            issue = next((i for i in candidates if i.number == num), None)
            if issue is None:
                self.state.release(num)
                log.info(f"RELEASE #{num} — no longer a candidate")
                continue

            if self.state.available_slots <= 0:
                self.state.schedule_retry(
                    num, attempt=entry.attempt + 1,
                    error="no available slots",
                    delay_ms=self._backoff_delay(entry.attempt + 1),
                )
                continue

            await self._dispatch(issue)

    async def _tick(self) -> None:
        """One poll-dispatch-reconcile cycle."""
        # 1. Reconcile
        await self._reconcile()

        # 2. Handle retries
        await self._handle_retries()

        # 3. Reload config if needed
        if self.workflow_path:
            try:
                self.config = load_workflow(self.workflow_path)
                self.state.max_concurrent = self.config.max_concurrent
                self.tracker.labels = self.config.tracker_labels
                self.tracker.exclude_labels = [
                    l.lower() for l in (self.config.tracker_exclude_labels or [])
                ]
                self.tracker.assignee = self.config.tracker_assignee
            except Exception as e:
                log.error(f"RELOAD failed, keeping last config: {e}")

        # 4. Fetch candidates
        try:
            candidates = await self.tracker.fetch_candidates()
        except Exception as e:
            log.error(f"POLL failed: {e}")
            self.state.persist(self.state_path)
            return

        eligible = [i for i in candidates if self._should_dispatch(i)]
        log.info(
            f"POLL  Found {len(candidates)} issues "
            f"({len(eligible)} eligible, "
            f"{self.state.running_count}/{self.state.max_concurrent} slots used)"
        )

        # 5. Dispatch
        for issue in eligible:
            if self.state.available_slots <= 0:
                break
            await self._dispatch(issue)

        self.state.persist(self.state_path)

    async def run(self) -> None:
        """Main loop."""
        log.info(
            f"Symphony starting — polling every {self.config.poll_interval_ms}ms, "
            f"max {self.config.max_concurrent} concurrent"
        )

        while not self._stop_event.is_set():
            try:
                await self._tick()
            except Exception as e:
                log.error(f"Tick error: {e}")

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.config.poll_interval_ms / 1000,
                )
                break
            except asyncio.TimeoutError:
                pass

        # Cancel all running workers
        for task in self._running_tasks.values():
            task.cancel()
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks.values(), return_exceptions=True)

        log.info("Symphony stopped")

    def stop(self) -> None:
        self._stop_event.set()
```

**Step 4: Run tests**

Run: `pytest tests/test_orchestrator.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add symphony/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: orchestrator with poll-dispatch-reconcile loop"
```

---

### Task 9: CLI Integration

**Files:**
- Modify: `symphony/cli.py`
- Create: `symphony/log.py`

**Step 1: Implement log.py**

```python
"""symphony/log.py — Structured terminal logging."""
from __future__ import annotations

import logging
import sys
from datetime import datetime


class SymphonyFormatter(logging.Formatter):
    COLORS = {
        "START": "\033[32m",   # green
        "DONE": "\033[36m",    # cyan
        "FAIL": "\033[31m",    # red
        "POLL": "\033[34m",    # blue
        "RUN": "\033[33m",     # yellow
        "CLOSE": "\033[36m",   # cyan
        "CLEAN": "\033[90m",   # grey
        "RELEASE": "\033[90m", # grey
        "IDLE": "\033[90m",    # grey
        "RECONCILE": "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        msg = record.getMessage()

        # Colorize known prefixes
        for prefix, color in self.COLORS.items():
            if msg.startswith(prefix):
                msg = f"{color}{msg}{self.RESET}"
                break

        if record.levelno >= logging.ERROR and not any(msg.startswith(p) for p in self.COLORS):
            msg = f"\033[31m{msg}{self.RESET}"

        return f"[{ts}] {msg}"


def setup_logging(verbose: bool = False) -> None:
    logger = logging.getLogger("symphony")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(SymphonyFormatter())
    logger.addHandler(handler)
```

**Step 2: Implement full CLI**

```python
"""symphony/cli.py — CLI entry point."""
from __future__ import annotations

import asyncio
import json
import os
import signal
import sys

import click

from symphony import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """Symphony-CC — autonomous coding agent orchestrator."""
    pass


@main.command()
@click.option("--workflow", "-w", default="WORKFLOW.md", help="Path to WORKFLOW.md")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def start(workflow: str, verbose: bool):
    """Start the Symphony orchestrator in the current directory."""
    from symphony.config import ConfigError, load_workflow
    from symphony.log import setup_logging
    from symphony.orchestrator import Orchestrator

    setup_logging(verbose=verbose)

    project_root = os.getcwd()
    workflow_path = os.path.join(project_root, workflow) if not os.path.isabs(workflow) else workflow

    try:
        config = load_workflow(workflow_path)
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    symphony_dir = os.path.join(project_root, ".symphony")
    state_path = os.path.join(symphony_dir, "state.json")

    orch = Orchestrator(
        config=config,
        project_root=project_root,
        state_path=state_path,
        workflow_path=workflow_path,
    )

    click.echo(f"Symphony v{__version__} — watching {os.path.basename(project_root)}")
    click.echo(
        f"Polling every {config.poll_interval_ms // 1000}s | "
        f"Max {config.max_concurrent} concurrent agents"
    )
    click.echo()

    loop = asyncio.new_event_loop()

    def handle_signal(sig, frame):
        click.echo("\nShutting down...")
        orch.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(orch.run())
    finally:
        loop.close()


@main.command()
def status():
    """Show current orchestrator status."""
    state_path = os.path.join(os.getcwd(), ".symphony", "state.json")

    if not os.path.exists(state_path):
        click.echo("No Symphony instance found in this directory.")
        click.echo("Run 'symphony start' first.")
        sys.exit(1)

    with open(state_path) as f:
        data = json.load(f)

    click.echo(f"Symphony — {os.path.basename(os.getcwd())}")
    click.echo()

    running = data.get("running", [])
    if running:
        click.echo(f"Running ({len(running)} agents):")
        for r in running:
            import time
            elapsed = time.time() - r.get("started_at", time.time())
            mins, secs = divmod(int(elapsed), 60)
            click.echo(
                f"  #{r['issue_number']:>4}  {r['title']:<40} "
                f"turn {r['turn']}/{r['max_turns']}  {mins}m{secs:02d}s"
            )
    else:
        click.echo("No running agents.")

    retrying = data.get("retrying", [])
    if retrying:
        click.echo(f"\nRetrying ({len(retrying)}):")
        for r in retrying:
            click.echo(
                f"  #{r['issue_number']:>4}  attempt {r['attempt']}  "
                f"error: {r.get('error', 'unknown')}"
            )

    completed = data.get("completed_count", 0)
    click.echo(f"\nCompleted this session: {completed}")


@main.command()
def stop():
    """Stop the running orchestrator (sends SIGTERM to the PID in state)."""
    click.echo("Use Ctrl+C in the symphony start terminal, or kill the process.")
```

**Step 3: Verify CLI works**

Run: `symphony --version`
Expected: `symphony-cc, version 0.1.0`

Run: `symphony start --help`
Expected: Shows options

**Step 4: Commit**

```bash
git add symphony/cli.py symphony/log.py
git commit -m "feat: CLI with start, status, stop commands"
```

---

### Task 10: Integration Test with Sample WORKFLOW.md

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
"""tests/test_integration.py — End-to-end smoke test with mocked externals."""
import json
import os
import pytest
from unittest.mock import patch, AsyncMock
from symphony.config import load_workflow
from symphony.orchestrator import Orchestrator
from symphony.tracker import Issue


@pytest.fixture
def sample_workflow(tmp_path):
    wf = tmp_path / "WORKFLOW.md"
    wf.write_text("""---
tracker:
  kind: github
  labels:
    - agent

polling:
  interval_ms: 1000

agent:
  max_concurrent: 2
  max_turns: 2
  command: echo
  permission_mode: acceptEdits
---

Fix issue #{{ issue.number }}: {{ issue.title }}

{{ issue.body }}
""")
    return str(wf)


@pytest.fixture
def mock_issue():
    return Issue(
        number=1, title="Test issue", state="open",
        body="Test body", url="", labels=["agent"],
    )


@pytest.mark.asyncio
async def test_single_tick(sample_workflow, mock_issue, tmp_path):
    config = load_workflow(sample_workflow)
    orch = Orchestrator(
        config=config,
        project_root=str(tmp_path),
        state_path=str(tmp_path / ".symphony" / "state.json"),
        workflow_path=sample_workflow,
    )

    with patch.object(orch.tracker, "fetch_candidates", new_callable=AsyncMock, return_value=[mock_issue]):
        with patch.object(orch, "_run_worker", new_callable=AsyncMock):
            await orch._tick()
            assert orch.state.is_claimed(1)
            assert 1 in orch.state.running
```

**Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integration smoke test for orchestrator tick"
```

---

### Task 11: Add .gitignore and WORKFLOW.md template

**Files:**
- Create: `.gitignore`
- Create: `WORKFLOW.md.example`

**Step 1: Create .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.symphony/
.venv/
```

**Step 2: Create WORKFLOW.md example**

```markdown
---
tracker:
  kind: github
  # labels: ["agent"]         # Uncomment to filter by label
  # exclude_labels: ["blocked"]
  # assignee: "@me"           # Uncomment to only pick up your issues

polling:
  interval_ms: 30000

agent:
  max_concurrent: 3
  max_turns: 5
  command: claude
  permission_mode: acceptEdits
  # skills: []
  # mcp_servers:
  #   - name: playwright
  #     command: npx @playwright/mcp@latest

hooks:
  # after_create: |
  #   npm install
  # before_run: |
  #   git fetch origin main && git rebase origin/main
  timeout_ms: 60000
---

You are an autonomous software engineer working on issue #{{ issue.number }}: {{ issue.title }}.

{{ issue.body }}

{% if attempt %}
This is continuation attempt {{ attempt }}. Review what was already done and continue from where you left off.
{% endif %}

## Instructions

1. Understand the issue requirements
2. Write clean, well-tested code
3. Run existing tests to make sure nothing breaks
4. Commit your changes with a descriptive message
5. Push the branch and create a pull request linking to #{{ issue.number }}
```

**Step 3: Commit**

```bash
git add .gitignore WORKFLOW.md.example
git commit -m "docs: add .gitignore and WORKFLOW.md example template"
```
