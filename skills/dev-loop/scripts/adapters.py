#!/usr/bin/env python3
"""
adapters.py — the one code path every host uses (stdlib only, Linux/macOS/Windows).

  validate  <lanes.json> [--out normalized.json]   schema + v1→v2 alias normalisation + DAG check
  order     <normalized.json>                       lane ids in dependency order (one per line)
  waves     <normalized.json>                       one line per parallel wave (space-separated ids)
  lane      <normalized.json> <id> --out lane.json  one lane with worker defaults merged
  run       --lane lane.json --wt DIR --report R --log L [--skill SKILL.md] [--shell sh|pwsh]
            build the harness command, run it (cwd=DIR, env, outer timeout), normalise its output
            into the canonical devloop_report at R. exit 0 = status done, 1 otherwise.
  build     (same args as run)                      print the argv that `run` would execute (JSON)
  owned     --lane lane.json --wt DIR               ownership audit; exit 1 + list on violation
  gate      --lane lane.json --wt DIR --run RUNDIR  positive / negative(+expect, tree-restore) / full
                                                    exit 0 pass, 1 fail, 2 vacuous
  secrets   --wt DIR                                staged-diff secret scan (gitleaks if present)
  deps      --wt DIR [--force]                      supply-chain gate when a lockfile/manifest is staged (osv-scanner, pip-audit, cargo-audit, npm audit, govulncheck, socket)
  probe     [--harness h ...]                       verify harness binaries + relied-on flags via --help (run at install and after CLI upgrades)
  ledger    --status S --objective O [--done --next --blockers --unverified]   append a handoff note to .devloop/LEDGER.md
  git       --wt DIR -- <git args>                  git with index.lock retry (≤5 × 500 ms backoff)
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DEFAULT = HERE.parent / "SKILL.md"  # scripts/ -> skill dir
HARNESSES = ["claude-code", "codex", "gemini-cli", "antigravity", "copilot", "opencode", "cursor", "openai-compatible", "custom"]
V1_HARNESS = {"claude": "claude-code", "gemini": "gemini-cli", "cloudcode": "antigravity", "openai": "openai-compatible",
              "copilot": "copilot", "opencode": "opencode", "cursor": "cursor", "antigravity": "antigravity", "codex": "codex"}
BINARY = {"claude-code": "claude", "codex": "codex", "gemini-cli": "gemini", "antigravity": "agy", "copilot": "copilot", "opencode": "opencode", "cursor": "agent"}
# flags the adapter relies on, probed with `<bin> --help` by `probe`; a miss means the CLI moved under us
PROBE_FLAGS = {"claude-code": ["--output-format", "--max-budget-usd", "--permission-mode", "--allowedTools", "--json-schema"],
               "codex": ["exec", "--json", "--cd", "--sandbox", "--ask-for-approval", "--output-schema"],
               "gemini-cli": ["-p", "--output-format", "--yolo"],
               "antigravity": ["-p", "--output-format", "--print-timeout", "--dangerously-skip-permissions"],
               "copilot": ["-p", "--allow-tool", "--deny-tool", "--output-format", "--add-dir", "--no-ask-user"],
               "opencode": ["run", "--format", "--agent", "--model"],
               "cursor": ["-p", "--output-format", "--force", "--workspace"]}
REPORT_KEYS = ["status", "objective", "summary", "changed_paths", "positive_controls", "negative_controls",
               "full_gate", "phantoms_dismissed", "unverified", "contract_updates", "questions", "next"]
STATUSES = {"done", "partial", "blocked", "converged_stuck", "budget", "halted"}
NONINTERACTIVE = {"CI": "1", "GIT_TERMINAL_PROMPT": "0", "GIT_PAGER": "cat", "PAGER": "cat", "NO_COLOR": "1",
                  "DEBIAN_FRONTEND": "noninteractive", "PIP_NO_INPUT": "1", "npm_config_yes": "true"}
SECRET_RE = re.compile(r"(api[_-]?key|secret|token|password|BEGIN (RSA|OPENSSH|EC|PGP) PRIVATE)\s*[:=\"']", re.I)


def die(msg: str, code: int = 64) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------- spec handling
def normalize_spec(spec: dict) -> dict:
    """Accept v1 (uploaded lineage) and v2 specs; return v2."""
    s = dict(spec)
    if "base_branch" in s: s["base_ref"] = s.pop("base_branch")
    if "worktree_dir" in s: s["worktree_root"] = s.pop("worktree_dir")
    if "timeout_seconds" in s: s.setdefault("worker", {})["timeout_s"] = s.pop("timeout_seconds")
    if "reconcile_and_clean" in s: s.pop("reconcile_and_clean")
    if s.get("terminal_layout") in ("detached_ps", "detached_sh"): s["terminal_layout"] = "detached"
    if s.get("terminal_layout") == "headless_py": s["terminal_layout"] = "headless"
    s["version"] = "2"
    s.setdefault("worktree_root", ".worktrees")
    lanes = []
    for l in s.get("lanes", []):
        l = dict(l)
        if "worker_id" in l: l["id"] = l.pop("worker_id").lower()
        if "command" in l and "objective" not in l: l["objective"] = l.pop("command")
        if "test_cmd" in l and "positive_cmd" not in l: l["positive_cmd"] = l.pop("test_cmd")
        w = dict(l.get("worker", {}))
        if "harness" in l: w["harness"] = V1_HARNESS.get(l.pop("harness"), l.get("harness", w.get("harness")))
        if "env" in l: w["env"] = l.pop("env")
        if w: l["worker"] = w
        # v1 lanes had no controls: make the gap loud, not silent
        l.setdefault("owned_paths", ["**"])
        l.setdefault("negative_control_cmd", "false")
        l.setdefault("negative_expect", "")
        lanes.append(l)
    s["lanes"] = lanes
    return s


def validate_spec(spec: dict) -> list[str]:
    errs: list[str] = []
    try:
        import jsonschema  # type: ignore
        schema = json.loads((HERE.parent / "assets" / "lane-schema.json").read_text("utf-8"))
        for e in jsonschema.Draft202012Validator(schema).iter_errors(spec):
            errs.append(f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}")
    except ImportError:
        for k in ("version", "base_ref", "lanes"):
            if k not in spec: errs.append(f"missing {k}")
        for l in spec.get("lanes", []):
            for k in ("id", "objective", "owned_paths", "positive_cmd", "negative_control_cmd", "negative_expect"):
                if k not in l: errs.append(f"lane {l.get('id')}: missing {k}")
            h = l.get("worker", {}).get("harness")
            if h and h not in HARNESSES: errs.append(f"lane {l.get('id')}: unknown harness {h}")
    ids = [l.get("id") for l in spec.get("lanes", [])]
    if len(ids) != len(set(ids)): errs.append("duplicate lane ids")
    for l in spec.get("lanes", []):
        for d in l.get("depends_on", []):
            if d not in ids: errs.append(f"lane {l['id']}: depends_on unknown lane {d}")
        wt = l.get("worktree", "")
        if wt and (".." in wt or wt.startswith(("/", "\\"))): errs.append(f"lane {l['id']}: bad worktree path")
        if l.get("negative_control_cmd") == "false" and not l.get("negative_expect"):
            errs.append(f"lane {l['id']}: no real negative control (v1 lane?) — add negative_control_cmd/negative_expect")
    try:
        order_lanes(spec)
    except ValueError as e:
        errs.append(str(e))
    return errs


def order_lanes(spec: dict) -> list[str]:
    deps = {l["id"]: set(l.get("depends_on", [])) for l in spec["lanes"]}
    out: list[str] = []
    while deps:
        ready = sorted(i for i, d in deps.items() if not d - set(out))
        if not ready: raise ValueError(f"depends_on cycle among {sorted(deps)}")
        out += ready
        for i in ready: deps.pop(i)
    return out


def merged_lane(spec: dict, lane_id: str) -> dict:
    l = next((x for x in spec["lanes"] if x["id"] == lane_id), None)
    if l is None: die(f"no lane {lane_id}")
    l = dict(l)
    w = {"harness": "openai-compatible", "max_turns": 40, "timeout_s": 1800, "temperature": 0, "api_key_env": "OPENAI_API_KEY"}
    w.update(spec.get("worker", {})); w.update(l.get("worker", {}))
    l["worker"] = w
    l["_base_ref"] = spec["base_ref"]
    return l


# ---------------------------------------------------------------- prompt + command
def lane_prompt(lane: dict, wt: Path, skill: Path) -> str:
    return (
        f"You are an L2 lane worker under the Dev Loop skill. Read {skill} first — it is the operating "
        f"procedure — then execute the loop for this lane.\n\n"
        f"# LANE CONTRACT (binding)\n"
        f"- lane id: {lane['id']}  role: {lane.get('role','worker')}  domain: {lane.get('domain','')}\n"
        f"- worktree (your cwd; ALWAYS use `git -C {wt}`): {wt}\n"
        f"- owned_paths — modify ONLY these: {json.dumps(lane['owned_paths'])}\n"
        f"- read_paths: {json.dumps(lane.get('read_paths', []))}\n"
        f"- positive_cmd: {lane['positive_cmd']}\n- negative_control_cmd: {lane['negative_control_cmd']}\n"
        f"- negative_expect (regex): {lane['negative_expect']}\n"
        f"- full_gate_cmd: {lane.get('full_gate_cmd') or '(none)'}\n"
        f"- budget: max_turns={lane['worker']['max_turns']} timeout_s={lane['worker']['timeout_s']}\n"
        "- Do NOT run git add/commit/push/rebase/reset, generators, or edit contract files; the host does that.\n"
        "- Run both controls yourself and report their real exit codes; status=done only if both held.\n"
        "- Finish your final message with a ```json code block containing a single object whose key is "
        "\"devloop_report\" (schema in SKILL.md §13). Nothing after that block.\n\n"
        f"# OBJECTIVE\n{lane['objective']}\n\n{lane.get('extra_context', '')}"
    )


def report_schema() -> dict:
    tools = json.loads((HERE.parent / "assets" / "openai-tools.json").read_text("utf-8"))
    rep = next(t["function"]["parameters"] for t in tools if t["function"]["name"] == "report")
    return {"type": "object", "additionalProperties": False, "required": ["devloop_report"], "properties": {"devloop_report": rep}}


def build_argv(lane: dict, wt: Path, report: Path, lane_json: Path, skill: Path, prompt_file: Path) -> list[str]:
    w = lane["worker"]; h = w["harness"]; n = str(w["max_turns"]); t = str(w["timeout_s"])
    obj = prompt_file.read_text("utf-8")
    structured = w.get("structured_output", True)
    if h == "claude-code":
        # --max-turns was removed from the claude CLI (gone by 2.1.276); the lane
        # budget is the outer timeout plus optional --max-budget-usd.
        argv = ["claude", "-p", obj, "--output-format", "json",
                "--permission-mode", w.get("permission_mode", "dontAsk"),
                "--allowedTools", w.get("allowed_tools", "Read,Edit,Write,Glob,Grep,Bash")]
        if structured: argv += ["--json-schema", json.dumps(report_schema())]
        if w.get("model"): argv += ["--model", w["model"]]
        if w.get("max_budget_usd"): argv += ["--max-budget-usd", str(w["max_budget_usd"])]
    elif h == "codex":
        # --cd is the real write fence (issue #24214: --add-dir is not); never --full-auto (it overrides --sandbox)
        argv = ["codex", "exec", "--json", "--cd", str(wt), "--sandbox", w.get("sandbox", "workspace-write"),
                "--ask-for-approval", w.get("permission_mode", "never"), "--ephemeral"]
        if structured:
            sf = report.with_name(f"schema-{lane['id']}.json"); sf.write_text(json.dumps(report_schema()), "utf-8")
            argv += ["--output-schema", str(sf), "-o", str(report.with_name(f"last-{lane['id']}.txt"))]
        if w.get("model"): argv += ["--model", w["model"]]
        argv += [obj]
    elif h == "gemini-cli":
        # text output on purpose: --output-format json aborts on any non-fatal tool error (issue #9281)
        argv = ["gemini", "-p", obj, "--output-format", w.get("output_format", "text"), "--yolo"]
        if w.get("model"): argv += ["-m", w["model"]]
    elif h == "antigravity":  # flag surface verified against agy 1.2.6 --help (adapters.py probe, 2026-09)
        argv = ["agy", "-p", obj, "--output-format", "json", "--print-timeout", f"{t}s", "--dangerously-skip-permissions"]
        if w.get("model"): argv += ["--model", w["model"]]
        if w.get("sandbox"): argv += ["--sandbox", w["sandbox"]]
    elif h == "copilot":
        argv = ["copilot", "-p", obj, "--output-format", "json", "--add-dir", str(wt), "--no-ask-user", "-s"]
        tools = w.get("allowed_tools")  # e.g. "shell(git:*),shell(pytest:*),write" ; deny always wins over allow
        argv += [f"--allow-tool={x.strip()}" for x in tools.split(",")] if tools else ["--allow-all-tools"]
        argv += ["--deny-tool=shell(git push:*)", "--deny-tool=shell(git commit:*)"]
        if w.get("model"): argv += ["--model", w["model"]]
        if w.get("agent"): argv += ["--agent", w["agent"]]
    elif h == "opencode":  # keep lanes single-agent: --format json drops subagent parts (issue #49300)
        argv = ["opencode", "run", "--format", "json"]
        if w.get("agent"): argv += ["--agent", w["agent"]]
        if w.get("model"): argv += ["--model", w["model"]]
        argv += [obj]
    elif h == "cursor":  # without --force print mode proposes but applies nothing
        argv = ["agent", "-p", "--output-format", "json", "--force", "--workspace", str(wt)]
        if w.get("model"): argv += ["--model", w["model"]]
        argv += [obj]
    elif h == "openai-compatible":
        argv = [sys.executable, str(HERE / "devloop_worker.py"), "--lane", str(lane_json), "--skill", str(skill),
                "--report", str(report), "--cwd", str(wt)]
    elif h == "custom":
        tpl = w.get("command") or die("custom harness needs worker.command")
        import shlex
        argv = [a.format(obj=obj, wt=str(wt), report=str(report), lane_json=str(lane_json), n=n, t=t, skill=str(skill))
                for a in shlex.split(tpl, posix=(os.name != "nt"))]
    else:
        die(f"unknown harness {h}")
    if w.get("extra_args"):
        import shlex
        argv += shlex.split(w["extra_args"], posix=(os.name != "nt"))
    return argv


# ---------------------------------------------------------------- report normalisation
def _extract_text(harness: str, stdout: str) -> str:
    """Unwrap the harness's native envelope to the assistant's final text (best effort, never raises)."""
    txt = stdout.strip()
    try:
        if harness == "codex":
            last = ""
            for line in txt.splitlines():
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                item = ev.get("item") if isinstance(ev, dict) else None
                for cand in (item, ev):
                    if isinstance(cand, dict) and cand.get("type") in ("agent_message", "message", "assistant") and cand.get("text"):
                        last = cand["text"]
            return last or txt
        if harness == "opencode":
            last = ""
            for line in txt.splitlines():
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for cand in (ev, ev.get("part") if isinstance(ev, dict) else None):
                    if isinstance(cand, dict) and cand.get("type") == "text" and isinstance(cand.get("text"), str):
                        last = cand["text"]
            return last or txt
        d = json.loads(txt)
        if isinstance(d, dict):
            if isinstance(d.get("structured_output"), dict) and "devloop_report" in d["structured_output"]:
                return json.dumps(d["structured_output"])  # claude --json-schema / agy structured_output
            for k in ("result", "response", "output", "text", "content"):  # claude-code, gemini/agy, custom
                if isinstance(d.get(k), str):
                    return d[k]
            if "devloop_report" in d:
                return txt
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return txt


def _balanced_json_objects(text: str):
    """Yield every top-level {...} substring that parses, scanning with brace balance (strings respected)."""
    i = 0
    while True:
        i = text.find("{", i)
        if i < 0:
            return
        depth = 0; in_str = False; esc = False
        for j in range(i, len(text)):
            c = text[j]
            if in_str:
                if esc: esc = False
                elif c == "\\": esc = True
                elif c == '"': in_str = False
            elif c == '"': in_str = True
            elif c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        yield json.loads(text[i:j + 1])
                    except json.JSONDecodeError:
                        pass
                    break
        i += 1


def find_report_block(text: str) -> dict | None:
    found = None
    for d in _balanced_json_objects(text):
        if isinstance(d, dict) and isinstance(d.get("devloop_report"), dict):
            found = d["devloop_report"]  # keep the LAST one
        elif isinstance(d, dict) and "status" in d and "objective" in d and "positive_controls" in d:
            found = d
    return found


def normalize_report(lane: dict, harness: str, stdout: str, exit_code: int, timed_out: bool, turns: int | None) -> dict:
    text = _extract_text(harness, stdout)
    rep = find_report_block(text)
    synth = rep is None
    if synth:
        status = "budget" if timed_out else ("halted" if exit_code not in (0,) and not text else "partial")
        if harness == "antigravity" and exit_code == 12: status = "budget"
        rep = {"status": status, "objective": lane["objective"], "summary": text[-1500:] if text else "(no output)"}
    rep = {k: rep.get(k, [] if k in ("changed_paths", "positive_controls", "negative_controls", "phantoms_dismissed",
                                       "unverified", "contract_updates", "questions") else "") for k in REPORT_KEYS}
    if not isinstance(rep["full_gate"], dict): rep["full_gate"] = {"cmd": "", "exit": -1}
    if rep["status"] not in STATUSES: rep["status"] = "partial"
    if synth: rep["unverified"] = list(rep["unverified"]) + ["no devloop_report block emitted by the lane"]
    if timed_out and rep["status"] == "done": rep["status"] = "budget"
    if exit_code != 0 and rep["status"] == "done": rep["status"] = "partial"; rep["unverified"].append(f"harness exit {exit_code}")
    try:
        env = json.loads(stdout.strip())
        if isinstance(env, dict) and env.get("permission_denials"):
            rep["unverified"].append(f"harness denied {len(env['permission_denials'])} tool call(s) (permission_denials) — work may be incomplete")
            if rep["status"] == "done": rep["status"] = "partial"
        if isinstance(env, dict) and env.get("is_error") and rep["status"] == "done": rep["status"] = "partial"
    except (json.JSONDecodeError, AttributeError):
        pass
    rep["_meta"] = {"lane": lane["id"], "harness": harness, "exit": exit_code, "timed_out": timed_out, "turns": turns}
    return rep


# ---------------------------------------------------------------- shell helpers
def shell_argv(cmd: str, prefer: str | None = None) -> list[str]:
    if prefer == "pwsh" or (prefer is None and os.name == "nt" and shutil.which("pwsh")):
        return ["pwsh", "-NoProfile", "-NonInteractive", "-Command", cmd]
    if os.name == "nt" and not shutil.which("sh"):
        return ["cmd", "/c", cmd]
    return ["sh", "-c", cmd]


def run_shell(cmd: str, cwd: Path, timeout: int, env: dict | None = None, prefer: str | None = None):
    e = {**os.environ, **NONINTERACTIVE, **(env or {})}
    try:
        cp = subprocess.run(shell_argv(cmd, prefer), cwd=cwd, env=e, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return cp.returncode, cp.stdout + cp.stderr, False
    except subprocess.TimeoutExpired as ex:
        out = (ex.stdout or "") if isinstance(ex.stdout, str) else ""
        return 124, out + f"\nTIMEOUT after {timeout}s", True


def git(wt: Path, *args: str, retries: int = 5) -> subprocess.CompletedProcess:
    for attempt in range(1, retries + 1):
        cp = subprocess.run(["git", "-C", str(wt), *args], capture_output=True, text=True, env={**os.environ, **NONINTERACTIVE})
        if cp.returncode == 0 or "index.lock" not in cp.stderr or attempt == retries:
            return cp
        time.sleep(0.5 * attempt)
    return cp


def tree_snapshot(wt: Path) -> str:
    return git(wt, "status", "--porcelain", "--untracked-files=all").stdout + git(wt, "diff").stdout


def changed_paths(wt: Path) -> list[str]:
    return [line[3:].strip().strip('"') for line in git(wt, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()]


def is_owned(path: str, owned: list[str]) -> bool:
    p = path.replace("\\", "/")
    for o in owned:
        o = o.replace("\\", "/")
        if p == o or fnmatch.fnmatch(p, o) or p.startswith(o.rstrip("/*") + "/"):
            return True
    return False


# ---------------------------------------------------------------- subcommands
def cmd_validate(a):
    spec = normalize_spec(json.loads(Path(a.spec).read_text("utf-8")))
    errs = validate_spec(spec)
    if errs: die("lanes.json invalid:\n  " + "\n  ".join(errs))
    if a.out: Path(a.out).write_text(json.dumps(spec, indent=2), "utf-8")
    print(f"lanes.json ok: {len(spec['lanes'])} lanes; order: {' '.join(order_lanes(spec))}")


def cmd_order(a):
    print("\n".join(order_lanes(json.loads(Path(a.spec).read_text("utf-8")))))


def waves(spec: dict) -> list[list[str]]:
    deps = {l["id"]: set(l.get("depends_on", [])) for l in spec["lanes"]}
    done: set[str] = set(); out: list[list[str]] = []
    while deps:
        ready = sorted(i for i, d in deps.items() if d <= done)
        if not ready: raise ValueError(f"depends_on cycle among {sorted(deps)}")
        out.append(ready); done |= set(ready)
        for i in ready: deps.pop(i)
    return out


def cmd_waves(a):
    print("\n".join(" ".join(w) for w in waves(json.loads(Path(a.spec).read_text("utf-8")))))


def cmd_lane(a):
    l = merged_lane(json.loads(Path(a.spec).read_text("utf-8")), a.id)
    Path(a.out).write_text(json.dumps(l, indent=2), "utf-8")
    print(l["worker"]["harness"])


def _prep(a):
    lane = json.loads(Path(a.lane).read_text("utf-8"))
    wt = Path(a.wt).resolve(); report = Path(a.report).resolve(); skill = Path(a.skill).resolve()
    prompt_file = report.with_name(f"prompt-{lane['id']}.md")
    prompt_file.write_text(lane_prompt(lane, wt, skill), "utf-8")
    return lane, wt, report, skill, prompt_file


def cmd_build(a):
    lane, wt, report, skill, pf = _prep(a)
    print(json.dumps(build_argv(lane, wt, report, Path(a.lane).resolve(), skill, pf)))


def cmd_run(a):
    lane, wt, report, skill, pf = _prep(a)
    w = lane["worker"]; h = w["harness"]
    argv = build_argv(lane, wt, report, Path(a.lane).resolve(), skill, pf)
    if not shutil.which(argv[0]) and not Path(argv[0]).exists():
        rep = normalize_report(lane, h, "", 127, False, None); rep["status"] = "halted"
        rep["unverified"].append(f"harness binary not found: {argv[0]}")
        report.write_text(json.dumps(rep, indent=2), "utf-8"); die(f"[{lane['id']}] {argv[0]} not found", 1)
    env = {**os.environ, **NONINTERACTIVE, **w.get("env", {})}
    if h == "openai-compatible" and w.get("base_url"): env["OPENAI_BASE_URL"] = w["base_url"]
    if w.get("model"): env.setdefault("DEVLOOP_MODEL", w["model"])
    log = Path(a.log).resolve() if a.log else report.with_name(f"worker-{lane['id']}.log")
    t0 = time.time(); timed_out = False
    try:
        cp = subprocess.run(argv, cwd=wt, env=env, capture_output=True, text=True, timeout=int(w["timeout_s"]), stdin=subprocess.DEVNULL)
        code, out, err = cp.returncode, cp.stdout, cp.stderr
    except subprocess.TimeoutExpired as ex:
        timed_out = True; code = 124
        out = ex.stdout if isinstance(ex.stdout, str) else (ex.stdout or b"").decode("utf-8", "replace")
        err = ex.stderr if isinstance(ex.stderr, str) else (ex.stderr or b"").decode("utf-8", "replace")
    log.write_text(f"$ {' '.join(argv[:2])} …\n--- stdout\n{out}\n--- stderr\n{err}\n--- exit {code} in {time.time()-t0:.0f}s\n", "utf-8")
    if h == "openai-compatible" and report.exists() and not timed_out:
        rep = json.loads(report.read_text("utf-8"))  # the worker wrote the canonical report itself
    else:
        last = report.with_name(f"last-{lane['id']}.txt")
        if h == "codex" and last.exists():
            out = last.read_text("utf-8") or out
        turns = None
        try:
            d = json.loads(out.strip()); turns = d.get("num_turns")
        except (json.JSONDecodeError, AttributeError):
            pass
        rep = normalize_report(lane, h, out, code, timed_out, turns)
        report.write_text(json.dumps(rep, indent=2), "utf-8")
    print(f"[{lane['id']}] harness={h} exit={code} status={rep['status']} report={report}")
    sys.exit(0 if rep["status"] == "done" else 1)


def cmd_owned(a):
    lane = json.loads(Path(a.lane).read_text("utf-8")); wt = Path(a.wt)
    paths = changed_paths(wt)
    bad = [p for p in paths if not is_owned(p, lane["owned_paths"])]
    if bad: die("OWNERSHIP VIOLATION: " + ", ".join(bad), 1)
    print(f"ownership ok: {len(paths)} path(s)")


def cmd_gate(a):
    lane = json.loads(Path(a.lane).read_text("utf-8")); wt = Path(a.wt).resolve(); run = Path(a.run); lid = lane["id"]
    t = int(lane.get("worker", {}).get("timeout_s", 1800))
    code, out, _ = run_shell(lane["positive_cmd"], wt, t, prefer=a.shell)
    (run / f"pos-{lid}.log").write_text(out, "utf-8")
    if code != 0: die(f"positive: FAIL (exit {code}, see pos-{lid}.log)", 1)
    print("positive: PASS")
    before = tree_snapshot(wt)
    # Park the lane's work BEFORE the control runs: a broken control can wipe
    # uncommitted lane edits (e.g. a `git checkout -- <file>` trap restores from
    # the INDEX, i.e. the seed), and a post-control diff would park nothing.
    pre_patch = git(wt, "diff").stdout + git(wt, "diff", "--cached").stdout
    code, out, _ = run_shell(lane["negative_control_cmd"], wt, t, prefer=a.shell)
    (run / f"neg-{lid}.log").write_text(out, "utf-8")
    after = tree_snapshot(wt)
    if before != after:
        (run / f"lane-{lid}.patch").write_text(pre_patch, "utf-8")
        die("negative control did not restore the tree — control is broken (SKILL §6); pre-control diff parked", 2)
    if code == 0: die("negative control PASSED => VACUOUS LANE. Refusing to merge.", 2)
    if lane["negative_expect"] and not re.search(lane["negative_expect"], out):
        die(f"negative failed but did NOT name the planted violation (/{lane['negative_expect']}/). Refusing.", 2)
    print("negative: FAILED for the expected reason")
    if lane.get("mutation_cmd"):
        code, out, _ = run_shell(lane["mutation_cmd"], wt, t, prefer=a.shell)
        (run / f"mut-{lid}.log").write_text(out, "utf-8")
        if code != 0: die(f"mutation gate: FAIL (exit {code}) — surviving mutants mean the tests cannot fail (SKILL §7)", 2)
        print("mutation gate: PASS")
    if lane.get("full_gate_cmd"):
        code, out, _ = run_shell(lane["full_gate_cmd"], wt, t, prefer=a.shell)
        (run / f"full-{lid}.log").write_text(out, "utf-8")
        if code != 0: die(f"full gate: FAIL (exit {code})", 1)
        print("full gate: PASS")


def cmd_secrets(a):
    wt = Path(a.wt)
    if shutil.which("gitleaks"):
        cp = subprocess.run(["gitleaks", "protect", "--staged", "--no-banner", "--redact"], cwd=wt, capture_output=True, text=True)
        if cp.returncode != 0: die("gitleaks: secrets in staged diff\n" + cp.stdout[-2000:], 1)
        print("secrets: clean (gitleaks)"); return
    diff = git(wt, "diff", "--cached").stdout
    hits = [ln for ln in diff.splitlines() if ln.startswith("+") and SECRET_RE.search(ln)]
    if hits: die(f"secrets: {len(hits)} suspicious added line(s) (regex fallback) — install gitleaks for real scanning", 1)
    print("secrets: clean (regex fallback)")


LOCKFILES = {"package-lock.json": ["npm", "audit", "--audit-level=high"], "pnpm-lock.yaml": ["pnpm", "audit", "--audit-level", "high"],
             "yarn.lock": ["yarn", "npm", "audit", "--severity", "high"], "requirements.txt": ["pip-audit", "-r", "requirements.txt"],
             "poetry.lock": ["pip-audit"], "uv.lock": ["pip-audit"], "Cargo.lock": ["cargo", "audit"], "go.sum": ["govulncheck", "./..."],
             "Gemfile.lock": ["bundle", "audit", "check"], "composer.lock": ["composer", "audit"]}


def cmd_deps(a):
    """Supply-chain gate: runs only when a lockfile/manifest changed in the staged diff (or --force)."""
    wt = Path(a.wt)
    changed = set(git(wt, "diff", "--cached", "--name-only").stdout.split())
    touched = [f for f in LOCKFILES if f in changed or Path(f).name in {Path(c).name for c in changed}]
    if not touched and not a.force: print("deps: no dependency change staged; gate skipped (state this in the report)"); return
    ran = 0; failed = []
    if shutil.which("osv-scanner"):
        cp = subprocess.run(["osv-scanner", "--lockfile", *sum([[f"{f}"] for f in touched], []), "--format", "table"] if touched else ["osv-scanner", "-r", "."], cwd=wt, capture_output=True, text=True)
        ran += 1; (failed.append("osv-scanner") if cp.returncode not in (0,) and "no package" not in cp.stdout.lower() else None)
    for f in touched or list(LOCKFILES):
        cmd = LOCKFILES[f]
        if (wt / f).exists() and shutil.which(cmd[0]):
            cp = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, timeout=600); ran += 1
            if cp.returncode != 0: failed.append(f"{cmd[0]} ({f}): {(cp.stdout + cp.stderr)[-600:]}")
    if shutil.which("socket") and touched:
        cp = subprocess.run(["socket", "scan", "create", ".", "--json"], cwd=wt, capture_output=True, text=True); ran += 1
        if cp.returncode != 0: failed.append("socket")
    if ran == 0: die("deps: dependency change staged but NO audit tool is installed (osv-scanner / pip-audit / cargo-audit / npm audit / govulncheck / socket). Refusing — an unauditable dependency change is not done.", 1)
    if failed: die("deps: supply-chain gate FAILED\n  " + "\n  ".join(failed), 1)
    print(f"deps: clean ({ran} audit(s); {', '.join(touched)})")


def cmd_probe(a):
    """Check each harness binary + the flags the adapter relies on. Exit 1 if a wanted harness is missing or drifted."""
    bad = 0
    for h in (a.harness or list(BINARY)):
        b = BINARY[h]; path = shutil.which(b)
        if not path: print(f"{h:18} {b:8} MISSING"); bad += 1 if a.harness else 0; continue
        try:
            sub = ["exec", "--help"] if h == "codex" else (["run", "--help"] if h == "opencode" else ["--help"])
            hp = subprocess.run([b, *sub], capture_output=True, text=True, timeout=30); text = hp.stdout + hp.stderr
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"{h:18} {b:8} {path}  help failed: {e}"); bad += 1; continue
        missing = [f for f in PROBE_FLAGS.get(h, []) if f not in text]
        print(f"{h:18} {b:8} {path}  " + ("ok" if not missing else f"DRIFT: flags not in --help: {missing}"))
        bad += 1 if missing else 0
    sys.exit(1 if bad else 0)


def cmd_ledger(a):
    """Append a handoff note to .devloop/LEDGER.md (git-committed progress ledger) — the Ralph-style fresh-context state."""
    root = Path(a.root); lf = root / ".devloop" / "LEDGER.md"; lf.parent.mkdir(parents=True, exist_ok=True)
    head = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    entry = (f"\n## {time.strftime('%Y-%m-%d %H:%M')} · {head} · {a.status}\n"
             f"- objective: {a.objective}\n- done: {a.done or '-'}\n- next: {a.next or '-'}\n- blockers: {a.blockers or '-'}\n- unverified: {a.unverified or '-'}\n")
    if not lf.exists(): lf.write_text("# Dev Loop ledger (handoff notes; newest last)\n", "utf-8")
    with lf.open("a", encoding="utf-8") as f: f.write(entry)
    print(f"ledger: appended to {lf}")


def cmd_git(a):
    cp = git(Path(a.wt), *a.args)
    sys.stdout.write(cp.stdout); sys.stderr.write(cp.stderr); sys.exit(cp.returncode)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("validate"); p.add_argument("spec"); p.add_argument("--out"); p.set_defaults(f=cmd_validate)
    p = sp.add_parser("order"); p.add_argument("spec"); p.set_defaults(f=cmd_order)
    p = sp.add_parser("waves"); p.add_argument("spec"); p.set_defaults(f=cmd_waves)
    p = sp.add_parser("lane"); p.add_argument("spec"); p.add_argument("id"); p.add_argument("--out", required=True); p.set_defaults(f=cmd_lane)
    for name, f in (("run", cmd_run), ("build", cmd_build)):
        p = sp.add_parser(name); p.add_argument("--lane", required=True); p.add_argument("--wt", required=True)
        p.add_argument("--report", required=True); p.add_argument("--log"); p.add_argument("--skill", default=str(SKILL_DEFAULT))
        p.add_argument("--shell", choices=["sh", "pwsh"]); p.set_defaults(f=f)
    p = sp.add_parser("owned"); p.add_argument("--lane", required=True); p.add_argument("--wt", required=True); p.set_defaults(f=cmd_owned)
    p = sp.add_parser("gate"); p.add_argument("--lane", required=True); p.add_argument("--wt", required=True)
    p.add_argument("--run", required=True); p.add_argument("--shell", choices=["sh", "pwsh"]); p.set_defaults(f=cmd_gate)
    p = sp.add_parser("secrets"); p.add_argument("--wt", required=True); p.set_defaults(f=cmd_secrets)
    p = sp.add_parser("deps"); p.add_argument("--wt", required=True); p.add_argument("--force", action="store_true"); p.set_defaults(f=cmd_deps)
    p = sp.add_parser("probe"); p.add_argument("--harness", nargs="*"); p.set_defaults(f=cmd_probe)
    p = sp.add_parser("ledger"); p.add_argument("--root", default="."); p.add_argument("--status", required=True); p.add_argument("--objective", required=True)
    p.add_argument("--done"); p.add_argument("--next"); p.add_argument("--blockers"); p.add_argument("--unverified"); p.set_defaults(f=cmd_ledger)
    p = sp.add_parser("git"); p.add_argument("--wt", required=True); p.add_argument("args", nargs=argparse.REMAINDER); p.set_defaults(f=cmd_git)
    a = ap.parse_args()
    if getattr(a, "args", None) and a.args and a.args[0] == "--": a.args = a.args[1:]
    a.f(a)


if __name__ == "__main__":
    main()
