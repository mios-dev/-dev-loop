#!/usr/bin/env python3
"""mios-init.sh (the script behind /dev-loop:init) -- controls, all against the REAL script.

Prompt resolution (deployed -> local MiOS checkout -> URL), served by a local HTTP server that
hands out the REAL system.md bytes from a MiOS checkout (or plain bytes for the negatives):
  positive  deployed copy wins, source "deployed", sha256 equal to the file
  positive  local MiOS checkout wins over the URL, source "local"
  positive  with no deployed or local copy the URL is fetched, sha256 equal to the served bytes
  negative  an unreachable URL fails the run (exit 1, "prompt" in failed_required), naming the URL
  negative  an HTML body is refused as "an HTML page, not markdown", naming the URL
  negative  an empty body is refused as "empty"
  live      MIOS_INIT_LIVE=1: the default GitHub URL yields MiOS origin/main's file byte for byte

Plan mode (non-Fedora branch forced with MIOS_OS_RELEASE, an absent image with FEDORA_IMAGE):
  positive  names the projection: cloud-fedora-setup.sh + FEDORA_DEVCONTAINER_REPO=...MiOS
  positive  creates nothing: no cache dir, no clone in the workspace

Package step on REAL Fedora (the host when it is Fedora, else inside the mios-dev container):
  positive  --packages-only resolves [packages.devcontainer] through MiOS packages.sh and runs
            dnf install -y (a no-op where every package is present)
  negative  a mios.toml without [packages.devcontainer] fails naming the section and the file
  negative  an EMPTY section fails inside packages.sh (get_packages_strict), naming the section
  positive  --plan on Fedora names the dnf path, not the projection

Skipped, not passed, when their prerequisite is absent: no MiOS checkout (local-source and
package controls), no Fedora (package controls), no MIOS_INIT_LIVE=1 (live control).
"""
from __future__ import annotations

import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPT = REPO / "skills" / "dev-loop" / "scripts" / "env" / "mios-init.sh"


def find_mios() -> Path | None:
    for c in (REPO.parent / "MiOS", Path("/home/user/MiOS"), Path("/workspaces/MiOS")):
        if (c / "usr/share/mios/mios.toml").is_file() and (c / "automation/lib/packages.sh").is_file():
            return c
    return None


MIOS = find_mios()
PROMPT_REL = "usr/share/mios/ai/system.md"
REAL_PROMPT = (MIOS / PROMPT_REL).read_bytes() if MIOS and (MIOS / PROMPT_REL).is_file() else (
    b"> _FHS: `/usr/share/mios/ai/system.md`_\n\n# MiOS\n\n- a markdown body\n")
HTML = b"<!DOCTYPE html>\n<html><body>proxy error</body></html>\n"


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = {"/system.md": REAL_PROMPT, "/html": HTML, "/empty": b""}.get(self.path)
        if body is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def closed_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run(args, env_extra, prefix=()):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("MIOS_", "FEDORA_"))}
    env.update(env_extra)
    if prefix:  # the container sees only what `env` passes it explicitly
        cmd = list(prefix) + ["env"] + [f"{k}={v}" for k, v in env_extra.items()] + ["bash", str(SCRIPT), *args]
    else:
        cmd = ["bash", str(SCRIPT), *args]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
    last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "{}"
    return p, json.loads(last)


def step(summary, name):
    return next(s for s in summary["steps"] if s["name"] == name)


class PromptResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = self.tmp / "ws"
        self.ws.mkdir()
        self.cache = self.tmp / "cache"
        self.env = {"MIOS_WORKSPACES": str(self.ws), "XDG_CACHE_HOME": str(self.cache),
                    "MIOS_SYSTEM_PROMPT_DEPLOYED": str(self.tmp / "no-deployed.md"),
                    "MIOS_SYSTEM_PROMPT_URL": f"{self.base}/system.md"}
        self.out = self.cache / "mios" / "system.md"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_deployed_copy_wins(self):
        d = self.tmp / "deployed.md"
        d.write_bytes(REAL_PROMPT)
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_DEPLOYED": str(d)})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["prompt"]["source"], f"deployed {d}")
        self.assertEqual(self.out.read_bytes(), REAL_PROMPT)
        import hashlib
        self.assertEqual(j["prompt"]["sha256"], hashlib.sha256(REAL_PROMPT).hexdigest())

    @unittest.skipUnless(MIOS, "no MiOS checkout next to this repo")
    def test_local_checkout_beats_url(self):
        (self.ws / "MiOS").symlink_to(MIOS)
        p, j = run(["--prompt-only"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(j["prompt"]["source"].startswith("local "), j["prompt"])
        self.assertEqual(self.out.read_bytes(), (MIOS / PROMPT_REL).read_bytes())

    def test_url_fetch_when_no_local_copy(self):
        p, j = run(["--prompt-only"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["prompt"]["source"], f"url {self.base}/system.md")
        self.assertEqual(self.out.read_bytes(), REAL_PROMPT)
        self.assertTrue(j["ok"])

    def test_unreachable_url_fails_naming_it(self):
        url = f"http://127.0.0.1:{closed_port()}/system.md"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("FAILED required step(s): prompt", p.stderr)
        self.assertEqual(j["failed_required"], ["prompt"])
        self.assertIn(url, step(j, "prompt")["detail"])
        self.assertIn("fetch failed", step(j, "prompt")["detail"])
        self.assertFalse(self.out.exists())

    def test_html_body_refused(self):
        url = f"{self.base}/html"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 1)
        self.assertEqual(step(j, "prompt")["detail"], f"{url} returned an HTML page, not markdown")
        self.assertFalse(self.out.exists())

    def test_empty_body_refused(self):
        url = f"{self.base}/empty"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 1)
        self.assertEqual(step(j, "prompt")["detail"], f"{url} returned empty")

    @unittest.skipUnless(os.environ.get("MIOS_INIT_LIVE") == "1" and MIOS, "live GitHub fetch: set MIOS_INIT_LIVE=1")
    def test_live_github_equals_origin_main(self):
        env = dict(self.env)
        del env["MIOS_SYSTEM_PROMPT_URL"]
        p, j = run(["--prompt-only"], env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(j["prompt"]["source"].startswith("url https://raw.githubusercontent.com/mios-dev/MiOS/main/"))
        subprocess.run(["git", "-C", str(MIOS), "fetch", "-q", "--depth", "1", "origin", "main"], check=True)
        main = subprocess.run(["git", "-C", str(MIOS), "show", f"FETCH_HEAD:{PROMPT_REL}"],
                              capture_output=True, check=True).stdout
        self.assertEqual(self.out.read_bytes(), main)


class PlanMode(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "ws").mkdir()
        (self.tmp / "os-release").write_text('ID=ubuntu\nVERSION_ID="24.04"\n')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_non_fedora_plan_names_projection_and_changes_nothing(self):
        env = {"MIOS_WORKSPACES": str(self.tmp / "ws"), "XDG_CACHE_HOME": str(self.tmp / "cache"),
               "MIOS_OS_RELEASE": str(self.tmp / "os-release"), "FEDORA_IMAGE": "mios-init-absent:none",
               "MIOS_SYSTEM_PROMPT_DEPLOYED": str(self.tmp / "none.md")}
        p, j = run(["--plan"], env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["mode"], "plan")
        d = step(j, "packages")
        self.assertEqual(d["status"], "planned")
        self.assertIn("non-Fedora host", d["detail"])
        self.assertIn("cloud-fedora-setup.sh", d["detail"])
        self.assertIn("FEDORA_DEVCONTAINER_REPO=https://github.com/mios-dev/MiOS", d["detail"])
        self.assertEqual({s["status"] for s in j["steps"]}, {"planned"})
        self.assertFalse((self.tmp / "cache").exists(), "--plan wrote the cache dir")
        self.assertEqual(list((self.tmp / "ws").iterdir()), [], "--plan cloned into the workspace")

    def test_unknown_flag_is_rejected(self):
        p = subprocess.run(["bash", str(SCRIPT), "--bogus"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("unknown argument: --bogus", p.stderr)


def fedora_prefix():
    """How to run the script on real Fedora: () on a Fedora host, the mios-dev wrapper otherwise."""
    try:
        osr = Path("/etc/os-release").read_text()
    except OSError:
        osr = ""
    if re.search(r"^ID=\"?fedora\"?$", osr, re.M) and shutil.which("dnf"):
        return ()
    if shutil.which("mios-dev") and shutil.which("docker") and subprocess.run(
            ["docker", "image", "inspect", "mios-dev:latest"], capture_output=True).returncode == 0:
        return ("env", "FEDORA_NO_AUTOBUILD=1", "mios-dev")
    return None


FEDORA = fedora_prefix() if MIOS else None


@unittest.skipUnless(FEDORA is not None, "needs a MiOS checkout and real Fedora (host or the mios-dev container)")
class FedoraPackages(unittest.TestCase):
    def setUp(self):
        # Under $HOME: the mios-dev container bind-mounts /root and /home/*, not /tmp.
        base = Path.home() / ".cache"
        base.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="mios-init-test.", dir=base))
        ws = self.tmp / "ws"
        ws.mkdir()
        (ws / "MiOS").symlink_to(MIOS)
        self.env = {"MIOS_WORKSPACES": str(ws), "MIOS_REPOS": "MiOS", "XDG_CACHE_HOME": str(self.tmp / "cache")}
        self.toml = (MIOS / "usr/share/mios/mios.toml").read_text()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _toml_with_section(self, replacement: str) -> Path:
        m = re.search(r"^\[packages\.devcontainer\]\n(?:(?!^\[).*\n)*", self.toml, re.M)
        self.assertIsNotNone(m, "the real mios.toml has no [packages.devcontainer]")
        f = self.tmp / "mios.toml"
        f.write_text(self.toml[:m.start()] + replacement + self.toml[m.end():])
        return f

    def test_dnf_install_of_resolved_set(self):
        p, j = run(["--packages-only"], self.env, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "ok", d)
        self.assertRegex(d["detail"], r"^Fedora host: dnf5? install -y of \d+ packages from \[packages\.devcontainer\]")
        self.assertEqual(j["runtime"], "podman")
        self.assertNotIn("prompt", [s["name"] for s in j["steps"]])
        # dnf really ran: its own transcript, not the script's claim, says so
        dlog = self.tmp / "cache" / "mios" / "mios-init-dnf.log"
        self.assertIn(str(dlog), d["detail"])
        self.assertRegex(dlog.read_text(), r"Nothing to do|Complete!|Transaction Summary")

    def test_missing_section_fails_naming_it(self):
        f = self._toml_with_section("")
        p, j = run(["--packages-only"], {**self.env, "MIOS_TOML": str(f)}, FEDORA)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertEqual(j["failed_required"], ["packages"])
        self.assertEqual(step(j, "packages")["detail"], f"[packages.devcontainer] is missing from {f}")

    def test_empty_section_fails_in_packages_sh(self):
        f = self._toml_with_section("[packages.devcontainer]\nenable = true\npkgs = []\n\n")
        p, j = run(["--packages-only"], {**self.env, "MIOS_TOML": str(f)}, FEDORA)
        self.assertEqual(p.returncode, 1, p.stdout)
        d = step(j, "packages")["detail"]
        self.assertIn("automation/lib/packages.sh", d)
        self.assertIn("[packages.devcontainer] is empty or undefined", d)

    def test_plan_names_dnf(self):
        p, j = run(["--plan", "--packages-only"], self.env, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "planned")
        self.assertRegex(d["detail"], r"^Fedora host: would run: dnf5? install -y")
        self.assertNotIn("cloud-fedora-setup", d["detail"])
        self.assertFalse((self.tmp / "cache").exists())


if __name__ == "__main__":
    unittest.main()
