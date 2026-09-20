#!/usr/bin/env python3
"""
Control for register-mcp.sh, which writes into config files the user already owns.

The hole this closes
--------------------
scripts/devloop_mcp.py is a working stdio MCP server, but the only thing that registered it was
.mcp.json, whose path is "${CLAUDE_PLUGIN_ROOT}/skills/dev-loop/scripts/devloop_mcp.py". Measured:
Claude Code's plugin loader is the only thing that sets and expands that variable. Antigravity was
observed spawning the same shim with the variable present in the child's ENVIRONMENT while argv
stayed the literal "${DEVLOOP_TEST_ROOT}/lit.py" -- no substitution at all. Cursor spells it
${env:NAME}, OpenCode {env:VAR}, Gemini CLI $VAR. So the server was registered exactly nowhere
except a Claude Code plugin install, and the fix is a script that writes an absolute path per
harness in that harness's own schema.

The dangerous part of that fix is not the writing, it is the file it writes into: ~/.claude.json,
~/.codex/config.toml and ~/.config/opencode/opencode.json are live user state holding OTHER MCP
servers and unrelated settings. A "registration" that replaces the file with a one-server document
is a data-loss bug wearing a success message, and it would pass any test that only asserts
"dev-loop is present afterwards". Hence the negative control below: every merge case seeds an
unrelated server plus an unrelated top-level setting first and asserts BOTH survive.

The second failure this guards is a check that cannot fail. `--check` exists to prove a
registration is current; a --check that returns 0 whatever the file says proves nothing. So the
stale case drives it both ways: exit 1 on a wrong path, exit 0 once refreshed.

Registration itself is not proof the harness can call the tools. This drives the script and the
files; it does not launch any harness. Only claude and antigravity are installed here, and only
their config paths were ever verified live -- the other five come from vendor docs, which is why
the script prints "unverified" beside them.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUG = os.path.dirname(HERE)
SCRIPT = os.path.join(PLUG, "skills", "dev-loop", "scripts", "register-mcp.sh")
SERVER = os.path.join(PLUG, "skills", "dev-loop", "scripts", "devloop_mcp.py")

# name -> (path under the fake HOME, container key, format)
USER_TARGETS = {
    "claude": (".claude.json", "mcpServers", "json"),
    "antigravity": (".gemini/config/mcp_config.json", "mcpServers", "json"),
    "codex": (".codex/config.toml", "mcp_servers", "toml"),
    "gemini": (".gemini/settings.json", "mcpServers", "json"),
    "copilot": (".copilot/mcp-config.json", "mcpServers", "json"),
    "cursor": (".cursor/mcp.json", "mcpServers", "json"),
    "opencode": (".config/opencode/opencode.json", "mcp", "json"),
}


def run(home, *args, repo=None):
    """Drive the script against a throwaway HOME so no real user config is ever touched."""
    env = dict(os.environ)
    env["HOME"] = home
    env["XDG_CONFIG_HOME"] = os.path.join(home, ".config")
    env["COPILOT_HOME"] = os.path.join(home, ".copilot")
    cmd = ["sh", SCRIPT, "--all", *args]
    if repo:
        cmd += ["--repo", repo]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=repo or PLUG)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def entry(path, key, fmt, name="dev-loop"):
    """Read one server entry back through a real parser -- not a regex over the text."""
    with open(path, "rb") as fh:
        raw = fh.read()
    doc = tomllib.loads(raw.decode()) if fmt == "toml" else json.loads(raw.decode())
    return doc, doc.get(key, {}).get(name)


def seed(home):
    """A believable pre-existing config: someone else's MCP server plus unrelated settings."""
    def w(rel, text):
        p = os.path.join(home, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
    weather_json = {"type": "stdio", "command": "node", "args": ["/opt/weather.js"]}
    w(".claude.json", json.dumps({"numStartups": 42, "mcpServers": {"weather": weather_json}}, indent=2))
    w(".gemini/config/mcp_config.json", json.dumps({"mcpServers": {"weather": weather_json}}))
    w(".gemini/settings.json", json.dumps({"theme": "GitHub", "mcpServers": {"weather": weather_json}}))
    w(".copilot/mcp-config.json", json.dumps({"mcpServers": {"weather": weather_json}}))
    w(".cursor/mcp.json", json.dumps({"mcpServers": {"weather": weather_json}}))
    w(".config/opencode/opencode.json",
      json.dumps({"theme": "opencode", "mcp": {"weather": {"type": "local", "command": ["node", "/opt/weather.js"]}}}))
    w(".codex/config.toml",
      'model = "o4"\n\n[mcp_servers.weather]\ncommand = "node"\nargs = ["/opt/weather.js"]\n\n[tui]\ntheme = "dark"\n')


class Base(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="devloop-mcp-home-")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def path(self, harness):
        rel, key, fmt = USER_TARGETS[harness]
        return os.path.join(self.home, rel), key, fmt


class TestCleanRegistration(Base):
    """Positive control: a clean machine ends up with a usable, absolute-path entry everywhere."""

    def test_every_harness_gets_a_parseable_absolute_entry(self):
        p = run(self.home)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for harness in USER_TARGETS:
            with self.subTest(harness=harness):
                path, key, fmt = self.path(harness)
                self.assertTrue(os.path.exists(path), f"{harness}: nothing written to {path}")
                _doc, got = entry(path, key, fmt)
                self.assertIsNotNone(got, f"{harness}: no dev-loop entry in {path}")
                blob = json.dumps(got)
                self.assertIn(SERVER, blob, f"{harness}: entry does not point at the server")
                self.assertNotIn("${", blob, f"{harness}: an unexpanded variable would never resolve here")

    def test_the_registered_path_actually_exists(self):
        # A registration pointing at a non-existent file is registered and useless. The
        # ${CLAUDE_PLUGIN_ROOT} form failed exactly this way outside a plugin session.
        run(self.home)
        path, key, fmt = self.path("cursor")
        _doc, got = entry(path, key, fmt)
        self.assertTrue(os.path.isfile(got["args"][0]), "the registered path must be openable by python3")

    def test_each_harness_gets_its_own_schema(self):
        # The shapes are not interchangeable; copying Claude Code's object everywhere is a
        # silently-broken registration on the two harnesses whose schema differs most.
        run(self.home)
        _d, oc = entry(*self.path("opencode"))
        self.assertEqual(oc["command"][0], "python3", "opencode fuses argv into one command array")
        self.assertIn("environment", oc, "opencode names the env block 'environment'")
        self.assertNotIn("args", oc)
        _d, cp = entry(*self.path("copilot"))
        self.assertEqual(cp.get("type"), "local", "copilot's stdio type is 'local', not 'stdio'")
        self.assertEqual(cp.get("tools"), ["*"], "omitting 'tools' can expose no tools at all")
        _d, ag = entry(*self.path("antigravity"))
        self.assertIs(ag.get("disabled"), False, "the agy CLI writes a 'disabled' flag")

    def test_a_runtime_without_mcp_config_is_skipped_by_name(self):
        p = run(self.home)
        self.assertRegex(p.stdout, r"openai-compatible\s+SKIP\s+no MCP client config",
                         "a runtime with no MCP mechanism must be named and skipped, not quietly written to")


class TestExistingConfigSurvives(Base):
    """Negative control: registration must not be a rewrite of the user's file."""

    def test_unrelated_server_and_settings_survive_every_format(self):
        seed(self.home)
        p = run(self.home)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for harness in USER_TARGETS:
            with self.subTest(harness=harness):
                path, key, fmt = self.path(harness)
                doc, got = entry(path, key, fmt)
                self.assertIsNotNone(got, f"{harness}: dev-loop was not added")
                other = doc.get(key, {}).get("weather")
                self.assertIsNotNone(other, f"{harness}: the user's other MCP server was destroyed")
                self.assertIn("/opt/weather.js", json.dumps(other), f"{harness}: the other server was mangled")

    def test_unrelated_top_level_keys_survive(self):
        seed(self.home)
        run(self.home)
        doc, _ = entry(*self.path("claude"))
        self.assertEqual(doc.get("numStartups"), 42, "~/.claude.json holds live session state, not just servers")
        doc, _ = entry(*self.path("opencode"))
        self.assertEqual(doc.get("theme"), "opencode")
        doc, _ = entry(*self.path("gemini"))
        self.assertEqual(doc.get("theme"), "GitHub", "mcpServers lives inside the general settings file")
        doc, _ = entry(*self.path("codex"))
        self.assertEqual(doc.get("model"), "o4", "the TOML merge must not eat sibling tables")
        self.assertEqual(doc.get("tui", {}).get("theme"), "dark", "including tables AFTER the replaced one")

    def test_a_backup_of_the_previous_contents_is_left_behind(self):
        seed(self.home)
        run(self.home)
        path, _k, _f = self.path("claude")
        self.assertTrue(os.path.exists(path + ".devloop-bak"), "the pre-merge file must be recoverable")
        self.assertIn("weather", read(path + ".devloop-bak"))


class TestRefreshNotMerelyFill(Base):
    """An entry that exists but points somewhere else is the common case after a move."""

    def _make_stale(self):
        run(self.home)
        for harness in ("claude", "codex"):
            path, _k, fmt = self.path(harness)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text.replace(SERVER, "/gone/devloop_mcp.py"))

    def test_check_fails_on_a_stale_entry_and_passes_once_refreshed(self):
        self._make_stale()
        bad = run(self.home, "--check", "--harness", "claude,codex")
        self.assertEqual(bad.returncode, 1, "a --check that cannot fail proves nothing:\n" + bad.stdout)
        self.assertIn("STALE", bad.stdout)
        fixed = run(self.home, "--harness", "claude,codex")
        self.assertIn("refreshed", fixed.stdout, "a differing entry must be rewritten, not left alone")
        good = run(self.home, "--check", "--harness", "claude,codex")
        self.assertEqual(good.returncode, 0, good.stdout)
        self.assertNotIn("STALE", good.stdout)

    def test_check_reports_a_missing_entry_as_a_problem(self):
        p = run(self.home, "--check", "--harness", "claude")
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("MISSING", p.stdout)

    def test_refresh_keeps_the_other_servers(self):
        seed(self.home)
        self._make_stale()
        run(self.home, "--harness", "claude,codex")
        for harness in ("claude", "codex"):
            doc, got = entry(*self.path(harness))
            self.assertIn(SERVER, json.dumps(got))
            self.assertIsNotNone(doc[USER_TARGETS[harness][1]].get("weather"), f"{harness}: refresh ate a sibling")

    def test_second_run_is_a_no_op(self):
        run(self.home)
        path, _k, _f = self.path("claude")
        before = read(path)
        again = run(self.home)
        self.assertEqual(again.returncode, 0)
        self.assertIn("already current", again.stdout)
        self.assertEqual(before, read(path), "an unchanged registration must not rewrite files")


class TestRefusals(Base):
    def test_dry_run_writes_nothing(self):
        p = run(self.home, "--dry-run")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("would create", p.stdout)
        for harness in USER_TARGETS:
            path, _k, _f = self.path(harness)
            self.assertFalse(os.path.exists(path), f"{harness}: --dry-run created {path}")

    def test_an_unparseable_config_is_left_alone(self):
        path, _k, _f = self.path("cursor")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{ this is not json")
        p = run(self.home, "--harness", "cursor")
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("ERROR", p.stdout)
        self.assertEqual(read(path), "{ this is not json",
                         "a file we cannot parse is a file we cannot safely merge")

    def test_a_plugin_relative_entry_is_not_clobbered(self):
        # .mcp.json doubles as the Claude Code plugin's mcpServers pointer, where
        # ${CLAUDE_PLUGIN_ROOT} does resolve. Overwriting it with an absolute path would
        # break the plugin install for every other checkout.
        repo = tempfile.mkdtemp(prefix="devloop-mcp-repo-")
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        original = json.dumps({"mcpServers": {"dev-loop": {
            "command": "python3",
            "args": ["${CLAUDE_PLUGIN_ROOT}/skills/dev-loop/scripts/devloop_mcp.py"]}}})
        with open(os.path.join(repo, ".mcp.json"), "w", encoding="utf-8") as fh:
            fh.write(original)
        p = run(self.home, "--project", "--harness", "claude", repo=repo)
        self.assertIn("SKIP", p.stdout)
        self.assertIn("CLAUDE_PLUGIN_ROOT", p.stdout)
        self.assertEqual(read(os.path.join(repo, ".mcp.json")), original)
        forced = run(self.home, "--project", "--harness", "claude", "--force", repo=repo)
        self.assertIn("refreshed", forced.stdout, "--force is the documented way through")
        _doc, got = entry(os.path.join(repo, ".mcp.json"), "mcpServers", "json")
        self.assertIn(SERVER, json.dumps(got))

    def test_a_harness_without_project_scope_does_not_get_a_global_write(self):
        # agy reads MCP config only from ~/.gemini/config/mcp_config.json. Silently writing
        # there during a --project run would enable the server for every repo on the machine.
        repo = tempfile.mkdtemp(prefix="devloop-mcp-repo-")
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        p = run(self.home, "--project", "--harness", "antigravity", repo=repo)
        self.assertIn("no project scope", p.stdout)
        path, _k, _f = self.path("antigravity")
        self.assertFalse(os.path.exists(path), "a --project run must not touch machine-wide config")


class TestOutput(Base):
    def test_a_verification_command_is_printed_per_target(self):
        p = run(self.home)
        for harness in USER_TARGETS:
            self.assertIn(f"--check --all --harness {harness}", p.stdout,
                          f"{harness}: no command offered that proves the entry is current")

    def test_confidence_is_not_flattened(self):
        p = run(self.home)
        self.assertRegex(p.stdout, r"claude .*\[verified\]")
        self.assertRegex(p.stdout, r"antigravity .*\[verified\]")
        for harness in ("codex", "gemini", "copilot", "cursor", "opencode"):
            self.assertRegex(p.stdout, rf"{harness} .*\[unverified\]",
                             f"{harness} was never observed live; the output must say so")


if __name__ == "__main__":
    unittest.main(verbosity=2 if "-v" in sys.argv else 1)
