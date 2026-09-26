#!/usr/bin/env python3
"""The plugin's SessionStart hook revives agy's keyring in a cloud session, for any repo.

In a cloud environment agy survives in the snapshot but its keyring daemon (a process) does not,
and the repo's own SessionStart hook runs only in sessions rooted in this repo. The plugin hook
loads in every session (CLAUDE_CODE_PLUGIN_DIRS), so it revives the daemon and appends the bus
address to CLAUDE_ENV_FILE, which Claude Code sources before every later tool call.

Controls, against the real dbus-daemon + gnome-keyring (an empty AGY_CLOUD_DIR is a cold start):
  positive  CLAUDE_CODE_REMOTE=true: the env file gets DBUS_SESSION_BUS_ADDRESS, and a shell that
            sources it finds org.freedesktop.secrets owned on that bus
  negative  without CLAUDE_CODE_REMOTE the env file stays empty
  positive  the hook prints nothing extra to stdout (stdout becomes session context)
Skipped, not passed, when agy, dbus-daemon or gnome-keyring-daemon is absent.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "session-start.sh"
AGY = Path.home() / ".local" / "bin" / "agy"


@unittest.skipUnless(AGY.exists() and shutil.which("dbus-daemon") and shutil.which("gnome-keyring-daemon")
                     and shutil.which("dbus-send"), "agy or the keyring stack is not installed")
class SessionStartKeyring(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.kr = self.tmp / "kr"
        self.kr.mkdir()
        self.envf = self.tmp / "env"
        self.envf.write_text("")
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        subprocess.run(["pkill", "-f", f"--address=unix:path={self.kr}/bus"], capture_output=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_hook(self, remote: bool) -> str:
        env = {k: v for k, v in os.environ.items() if k not in ("DBUS_SESSION_BUS_ADDRESS", "CLAUDE_CODE_REMOTE")}
        env.update(CLAUDE_ENV_FILE=str(self.envf), AGY_CLOUD_DIR=str(self.kr), CLAUDE_PLUGIN_ROOT=str(ROOT))
        if remote:
            env["CLAUDE_CODE_REMOTE"] = "true"
        res = subprocess.run(["sh", str(HOOK)], env=env, cwd=self.tmp, capture_output=True, text=True, timeout=30)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def test_remote_cold_start_exports_live_bus(self):
        out = self.run_hook(remote=True)
        self.assertEqual(out, "")
        body = self.envf.read_text()
        self.assertIn("export DBUS_SESSION_BUS_ADDRESS=", body)
        probe = subprocess.run(
            ["sh", "-c", f". '{self.envf}'; dbus-send --session --dest=org.freedesktop.DBus --type=method_call "
             "--print-reply /org/freedesktop/DBus org.freedesktop.DBus.NameHasOwner string:org.freedesktop.secrets"],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(probe.returncode, 0, probe.stderr)
        self.assertIn("boolean true", probe.stdout)

    def test_local_session_writes_nothing(self):
        self.run_hook(remote=False)
        self.assertEqual(self.envf.read_text(), "")


if __name__ == "__main__":
    unittest.main()
