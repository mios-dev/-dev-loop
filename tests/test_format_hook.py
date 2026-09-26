#!/usr/bin/env python3
"""hooks/format.sh must parse a .sh file with the interpreter its shebang names.

The hook ran `sh -n` on every .sh file, so a valid bash script (`declare -A`, arrays) was reported
as a "shell syntax error" and the edit was blocked -- found on MiOS's
.devcontainer/setup-devcontainer.sh, whose untouched HEAD fails `sh -n` the same way.

Controls, through the real hook with a PostToolUse payload:
  positive  a valid bash-only script with a bash shebang passes (no block)
  negative  the same bash-only syntax under a #!/bin/sh shebang is blocked
  negative  a genuinely broken bash script is blocked, naming the file
  positive  a plain POSIX script still passes
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "format.sh"

BASH_ONLY = 'declare -A REPOS=(\n    ["a"]="x"\n)\necho "${REPOS[a]}"\n'


class FormatHookShellParse(unittest.TestCase):
    def run_hook(self, body: str) -> str:
        d = tempfile.mkdtemp()
        p = Path(d) / "script.sh"
        p.write_text(body)
        payload = json.dumps({"tool_input": {"file_path": str(p)}})
        res = subprocess.run(["sh", str(HOOK)], input=payload, capture_output=True, text=True,
                             cwd=d, timeout=30)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout.strip()

    def test_bash_shebang_bash_syntax_passes(self):
        self.assertEqual(self.run_hook("#!/usr/bin/env bash\n" + BASH_ONLY), "")

    def test_sh_shebang_bash_syntax_blocked(self):
        out = self.run_hook("#!/bin/sh\n" + BASH_ONLY)
        self.assertIn('"decision":"block"', out)
        self.assertIn("shell syntax error", out)

    def test_broken_bash_blocked(self):
        out = self.run_hook("#!/bin/bash\nif true; then\n  echo x\n")
        self.assertIn('"decision":"block"', out)
        self.assertIn("script.sh", out)

    def test_posix_passes(self):
        self.assertEqual(self.run_hook("#!/bin/sh\nset -eu\necho ok\n"), "")


if __name__ == "__main__":
    unittest.main()
