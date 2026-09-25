#!/usr/bin/env python3
"""The agy installer fetch must survive an unsolicited `Content-Encoding: gzip`.

antigravity.google's CDN serves the installer gzip-encoded from some cache nodes even when the
request carries no Accept-Encoding (measured 2026-09-25: ~1 response in 3). Plain `curl -fsSL`
writes those gzip bytes verbatim and `bash install.sh` dies "cannot execute binary file" (rc 126),
so setup-antigravity.sh failed on roughly every third container. fetch-installer.sh passes
`--compressed` and refuses any payload without a `#!` line.

Controls, against a local HTTP server that ALWAYS gzip-encodes (the bad cache node, made
deterministic) and the real curl:
  positive  fetch-installer.sh yields the original script, byte for byte
  negative  the same helper with --compressed stripped fails, naming "not a shell script"
  negative  an HTML body served plainly is refused the same way
  wiring    setup-antigravity.sh routes the download through the helper (AGY_INSTALLER_URL)
Skipped, not passed, when `curl` is not on PATH.
"""
from __future__ import annotations

import gzip
import http.server
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_DIR = HERE.parent / "skills" / "dev-loop" / "scripts" / "env"
HELPER = ENV_DIR / "fetch-installer.sh"
SETUP = ENV_DIR / "setup-antigravity.sh"

SCRIPT = b"#!/bin/bash\necho installer-ran\n"
HTML = b"<html><body>captive portal</body></html>\n"


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/gz":
            body, enc = gzip.compress(SCRIPT), "gzip"
        elif self.path == "/html":
            body, enc = HTML, None
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/x-sh")
        if enc:
            self.send_header("Content-Encoding", enc)  # sent whatever the request asked for
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@unittest.skipUnless(shutil.which("curl"), "curl not on PATH")
class FetchInstallerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        cls.env = dict(os.environ, NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def _run(self, helper: Path, path: str):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        dest = Path(d) / "install.sh"
        p = subprocess.run(["bash", str(helper), self.base + path, str(dest)],
                           capture_output=True, text=True, env=self.env, timeout=60)
        return p, dest

    def test_positive_gzip_is_decoded(self):
        p, dest = self._run(HELPER, "/gz")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(dest.read_bytes(), SCRIPT)
        run = subprocess.run(["bash", str(dest)], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.stdout.strip(), "installer-ran")

    def test_negative_without_compressed_is_refused(self):
        src = HELPER.read_text()
        self.assertEqual(src.count("curl -fsSL --compressed "), 1, "mutation anchor moved")
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        mutant = Path(d) / "fetch-installer.sh"
        mutant.write_text(src.replace("curl -fsSL --compressed ", "curl -fsSL ", 1))
        p, dest = self._run(mutant, "/gz")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not a shell script", p.stderr)
        self.assertTrue(dest.read_bytes().startswith(b"\x1f\x8b"), "plant did not land: body not gzip")

    def test_negative_html_is_refused(self):
        p, _ = self._run(HELPER, "/html")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not a shell script", p.stderr)

    def test_setup_routes_through_helper(self):
        src = SETUP.read_text()
        self.assertIn('bash "$SCRIPT_DIR/fetch-installer.sh" "${AGY_INSTALLER_URL:-', src)
        self.assertNotRegex(src, r"(?m)^[^#]*curl [^\n]*install\.sh")


if __name__ == "__main__":
    unittest.main()
