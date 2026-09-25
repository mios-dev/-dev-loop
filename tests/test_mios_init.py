#!/usr/bin/env python3
"""mios-init.sh (the script behind /dev-loop:init) -- controls, all against the REAL script.

Prompt resolution (deployed -> pinned local MiOS checkout -> URL) for BOTH files, the context
system.md and the identity MiOS.md, served by a local HTTP server that hands out the REAL bytes
from a MiOS checkout (or plain bytes for the negatives):
  positive  deployed copies win, source "deployed", sha256 equal to the files
  positive  the local MiOS checkout wins over the URL, source "local", for both files
  positive  with no deployed or local copy both URLs are fetched, sha256 equal to the served bytes
  negative  an unreachable URL fails the run (exit 1, "prompt" in failed_required), naming the URL
  negative  an HTML body is refused as "an HTML page, not markdown", naming the URL (either file)
  negative  an empty body is refused as "empty"
  live      MIOS_INIT_LIVE=1: the default GitHub URLs yield MiOS main's files byte for byte,
            proved against a fetch into a FRESH temp dir; the operator's checkout is never touched
            (its .git/shallow and .git/FETCH_HEAD are byte-identical before and after -- that
            assertion is the control)

Pinned checkout (F2): a directory with mios.toml + packages.sh counts as MiOS only when it is a
git work tree whose origin is the MiOS repo.
  negative  a foreign origin (https://example.com/x/y) is logged "ignored: origin is ..." and the
            prompt falls through to the URL
  positive  the same directory with the MiOS origin URL (https, .git, ssh forms) set locally is
            accepted, source "local"
  negative  no git work tree at all is ignored
  positive  $PWD and its parent are not workspace candidates (a correctly-origined checkout there
            is not picked)

URL redaction (F9): userinfo never reaches stdout, stderr, the JSON or the clone log.

Flags (F7): --prompt-only with --packages-only, and --packages-only with --no-packages, exit 2
with a message; the redundant --prompt-only --no-packages still runs.

as_root (F6): proved with the function text extracted from the script, run as a REAL unprivileged
user (via runuser when the suite is root) with a stub `sudo` first on PATH that records its argv
and then emulates env_reset (a clean environment) before running the command -- a stub, as the
finding allows. The child must see HTTPS_PROXY, FEDORA_* and MIOS_* through `sudo -n env NAME=value`.
  negative  with the forwarding line removed the child sees nothing

Wrapper runtime (F1), only where the projection image lives in docker and podman is also on PATH
(this VM): with FEDORA_DEVCONTAINER_NAME=init-fix-test the wrapper lands as
/usr/local/bin/init-fix-test (and /usr/local/bin/fedora, backed up by sha256 first and restored).
The caller's environment says FEDORA_RUNTIME=podman throughout (podman-native default) while the
image lives in docker, which is the state the finding describes.
  positive  the written wrapper says RUNTIME=docker (the runtime that holds the image, passed
            explicitly and overriding the environment) and the step is ok
  negative  with the FEDORA_RUNTIME="$rt" pass-through removed the environment's podman reaches
            the setup script, the wrapper says RUNTIME=podman and the step is recorded failed,
            naming both runtimes
  negative  with the RUNTIME= check also removed the step reports ok for a podman wrapper (the
            original bug), which shows the check is load-bearing

Plan mode (non-Fedora branch forced with MIOS_OS_RELEASE, an absent image with FEDORA_IMAGE):
  positive  names the projection: cloud-fedora-setup.sh + FEDORA_DEVCONTAINER_REPO=...MiOS
  positive  creates nothing: no cache dir, no clone in the workspace

Package step on REAL Fedora (the host when it is Fedora, else inside the mios-dev container,
found in podman first, then docker):
  positive  --packages-only resolves [packages.devcontainer] through MiOS packages.sh and runs
            dnf install -y --setopt=install_weak_deps=False (Nothing to do), finds the venv
            already satisfied and the Containerfile's npm CLIs present
  negative  a mios.toml without [packages.devcontainer] fails naming the section and the file
  negative  an EMPTY section fails inside packages.sh (get_packages_strict), naming the section
  negative  a package dnf cannot find fails naming the package and the log (F8)
  negative  a Containerfile copy without the `npm install -g` line fails naming that file (F5)
  negative  a foreign-origin checkout fails repo:MiOS and packages naming the origin (F2)
  positive  --plan on Fedora names the dnf path, the npm CLIs and the venv, not the projection

Skipped, not passed, when their prerequisite is absent, with the reason printed.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import pwd
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ENV_DIR = REPO / "skills" / "dev-loop" / "scripts" / "env"
SCRIPT = ENV_DIR / "mios-init.sh"
MIOS_ORIGIN = "https://github.com/mios-dev/MiOS"
FOREIGN_ORIGIN = "https://example.com/x/y"


def find_mios() -> Path | None:
    for c in (REPO.parent / "MiOS", Path("/home/user/MiOS"), Path("/workspaces/MiOS")):
        if (c / "usr/share/mios/mios.toml").is_file() and (c / "automation/lib/packages.sh").is_file():
            return c
    return None


MIOS = find_mios()
PROMPT_REL = "usr/share/mios/ai/system.md"
IDENTITY_REL = "MiOS.md"
REAL_PROMPT = (MIOS / PROMPT_REL).read_bytes() if MIOS and (MIOS / PROMPT_REL).is_file() else (
    b"> _FHS: `/usr/share/mios/ai/system.md`_\n\n# MiOS\n\n- a markdown body\n")
REAL_IDENTITY = (MIOS / IDENTITY_REL).read_bytes() if MIOS and (MIOS / IDENTITY_REL).is_file() else (
    b"> _`/MiOS.md` -- the single canonical MiOS AI system identity._\n\n# SYSTEM INSTRUCTION\n\n* an item\n")
HTML = b"<!DOCTYPE html>\n<html><body>proxy error</body></html>\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(p: Path) -> str | None:
    return sha256(p.read_bytes()) if p.is_file() else None


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = {"/system.md": REAL_PROMPT, "/MiOS.md": REAL_IDENTITY, "/html": HTML, "/empty": b""}.get(self.path)
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


def run(args, env_extra, prefix=(), script=SCRIPT, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("MIOS_", "FEDORA_"))}
    env.update(env_extra)
    if prefix:  # the container sees only what `env` passes it explicitly
        cmd = list(prefix) + ["env"] + [f"{k}={v}" for k, v in env_extra.items()] + ["bash", str(script), *args]
    else:
        cmd = ["bash", str(script), *args]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900, cwd=cwd)
    last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "{}"
    try:
        j = json.loads(last)
    except json.JSONDecodeError:
        j = {}
    return p, j


def step(summary, name):
    return next(s for s in summary["steps"] if s["name"] == name)


def make_fake_mios(d: Path, origin: str | None, git: bool = True) -> Path:
    """A directory that carries the two files mios-init consumes plus both prompt files."""
    (d / "usr/share/mios").mkdir(parents=True)
    (d / "usr/share/mios/mios.toml").write_text('[packages.devcontainer]\nenable = true\npkgs = ["bash"]\n')
    (d / "automation/lib").mkdir(parents=True)
    (d / "automation/lib/packages.sh").write_text("# not sourced by these controls\n")
    (d / "usr/share/mios/ai").mkdir(parents=True)
    (d / PROMPT_REL).write_bytes(REAL_PROMPT)
    (d / IDENTITY_REL).write_bytes(REAL_IDENTITY)
    if git:
        subprocess.run(["git", "init", "-q", str(d)], check=True, capture_output=True)
        if origin:
            subprocess.run(["git", "-C", str(d), "remote", "add", "origin", origin], check=True, capture_output=True)
    return d


def copy_env_dir(tmp: Path) -> Path:
    """A byte-identical copy of scripts/env/ inside a temp plugin tree; returns its mios-init.sh."""
    dst = tmp / "plug" / "skills" / "dev-loop" / "scripts" / "env"
    shutil.copytree(ENV_DIR, dst)
    return dst / "mios-init.sh"


def mutate(path: Path, old: str, new: str, tc: unittest.TestCase):
    text = path.read_text()
    tc.assertEqual(text.count(old), 1, f"mutation target must occur exactly once: {old!r}")
    path.write_text(text.replace(old, new))


class _ServerCase(unittest.TestCase):
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
                    "MIOS_IDENTITY_DEPLOYED": str(self.tmp / "no-deployed-identity.md"),
                    "MIOS_SYSTEM_PROMPT_URL": f"{self.base}/system.md",
                    "MIOS_IDENTITY_URL": f"{self.base}/MiOS.md"}
        self.out = self.cache / "mios" / "system.md"
        self.ident = self.cache / "mios" / "MiOS.md"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class PromptResolution(_ServerCase):
    def test_deployed_copy_wins(self):
        d = self.tmp / "deployed.md"
        d.write_bytes(REAL_PROMPT)
        i = self.tmp / "deployed-identity.md"
        i.write_bytes(REAL_IDENTITY)
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_DEPLOYED": str(d), "MIOS_IDENTITY_DEPLOYED": str(i)})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["prompt"]["source"], f"deployed {d}")
        self.assertEqual(j["prompt"]["identity_source"], f"deployed {i}")
        self.assertEqual(self.out.read_bytes(), REAL_PROMPT)
        self.assertEqual(self.ident.read_bytes(), REAL_IDENTITY)
        self.assertEqual(j["prompt"]["sha256"], sha256(REAL_PROMPT))
        self.assertEqual(j["prompt"]["identity_sha256"], sha256(REAL_IDENTITY))
        self.assertEqual(j["prompt"]["identity_path"], str(self.ident))

    @unittest.skipUnless(MIOS, "no MiOS checkout next to this repo")
    def test_local_checkout_beats_url(self):
        (self.ws / "MiOS").symlink_to(MIOS)
        p, j = run(["--prompt-only"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(j["prompt"]["source"].startswith("local "), j["prompt"])
        self.assertTrue(j["prompt"]["identity_source"].startswith("local "), j["prompt"])
        self.assertEqual(self.out.read_bytes(), (MIOS / PROMPT_REL).read_bytes())
        self.assertEqual(self.ident.read_bytes(), (MIOS / IDENTITY_REL).read_bytes())

    def test_url_fetch_when_no_local_copy(self):
        p, j = run(["--prompt-only"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["prompt"]["source"], f"url {self.base}/system.md")
        self.assertEqual(j["prompt"]["identity_source"], f"url {self.base}/MiOS.md")
        self.assertEqual(self.out.read_bytes(), REAL_PROMPT)
        self.assertEqual(self.ident.read_bytes(), REAL_IDENTITY)
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

    def test_html_identity_refused(self):
        url = f"{self.base}/html"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_IDENTITY_URL": url})
        self.assertEqual(p.returncode, 1)
        self.assertEqual(j["failed_required"], ["prompt"])
        self.assertEqual(step(j, "prompt")["detail"], f"identity MiOS.md: {url} returned an HTML page, not markdown")
        self.assertFalse(self.ident.exists())
        self.assertEqual(j["prompt"]["identity_sha256"], "")

    def test_empty_body_refused(self):
        url = f"{self.base}/empty"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 1)
        self.assertEqual(step(j, "prompt")["detail"], f"{url} returned empty")

    @unittest.skipUnless(os.environ.get("MIOS_INIT_LIVE") == "1", "live GitHub fetch: set MIOS_INIT_LIVE=1")
    def test_live_github_equals_main(self):
        # The operator's checkout is never touched: a `git fetch` inside it once cut its history.
        checkout = MIOS or Path("/home/user/MiOS")
        watched = [checkout / ".git" / "shallow", checkout / ".git" / "FETCH_HEAD"]
        before = [file_sha(w) for w in watched]
        env = dict(self.env)
        del env["MIOS_SYSTEM_PROMPT_URL"]
        del env["MIOS_IDENTITY_URL"]
        p, j = run(["--prompt-only"], env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(j["prompt"]["source"].startswith("url https://raw.githubusercontent.com/mios-dev/MiOS/main/"))
        self.assertTrue(j["prompt"]["identity_source"].startswith("url https://raw.githubusercontent.com/mios-dev/MiOS/main/"))
        fresh = self.tmp / "fresh"
        fresh.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=fresh, check=True)
        subprocess.run(["git", "fetch", "-q", "--depth", "1", f"{MIOS_ORIGIN}.git", "main"], cwd=fresh, check=True)
        for rel, out in ((PROMPT_REL, self.out), (IDENTITY_REL, self.ident)):
            main = subprocess.run(["git", "show", f"FETCH_HEAD:{rel}"], cwd=fresh, capture_output=True, check=True).stdout
            self.assertEqual(out.read_bytes(), main, rel)
        self.assertEqual([file_sha(w) for w in watched], before, "the operator's checkout changed")


class PinnedCheckout(_ServerCase):
    def test_foreign_origin_is_ignored_and_falls_through(self):
        make_fake_mios(self.ws / "MiOS", FOREIGN_ORIGIN)
        p, j = run(["--prompt-only"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(f"ignored: origin is {FOREIGN_ORIGIN} (not the MiOS repo)", p.stdout)
        self.assertEqual(j["prompt"]["source"], f"url {self.base}/system.md")
        self.assertEqual(j["prompt"]["identity_source"], f"url {self.base}/MiOS.md")

    def test_mios_origin_is_accepted(self):
        fake = make_fake_mios(self.ws / "MiOS", FOREIGN_ORIGIN)
        for origin in (MIOS_ORIGIN, f"{MIOS_ORIGIN}.git", "git@github.com:mios-dev/MiOS", "git@github.com:mios-dev/MiOS.git"):
            with self.subTest(origin=origin):
                subprocess.run(["git", "-C", str(fake), "remote", "set-url", "origin", origin], check=True)
                p, j = run(["--prompt-only"], self.env)
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertEqual(j["prompt"]["source"], f"local {fake / PROMPT_REL}")
                self.assertEqual(j["prompt"]["identity_source"], f"local {fake / IDENTITY_REL}")
                self.assertNotIn("ignored:", p.stdout)

    def test_no_work_tree_is_ignored(self):
        make_fake_mios(self.ws / "MiOS", None, git=False)
        p, j = run(["--prompt-only"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ignored:", p.stdout)
        self.assertIn("is not a git work tree", p.stdout)
        self.assertEqual(j["prompt"]["source"], f"url {self.base}/system.md")

    def test_no_origin_is_ignored(self):
        make_fake_mios(self.ws / "MiOS", None)
        p, j = run(["--prompt-only"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ignored:", p.stdout)
        self.assertIn("has no origin remote", p.stdout)
        self.assertEqual(j["prompt"]["source"], f"url {self.base}/system.md")

    def test_cwd_and_its_parent_are_not_candidates(self):
        # The script copy lives in a plugin tree whose parent holds no MiOS; a correctly-origined
        # checkout next to the cwd (or its parent) must still not become the workspace root.
        script = copy_env_dir(self.tmp)
        here = self.tmp / "elsewhere"
        make_fake_mios(here / "MiOS", MIOS_ORIGIN)
        (here / "sub").mkdir()
        home = self.tmp / "home"
        home.mkdir()
        env = {k: v for k, v in self.env.items() if k != "MIOS_WORKSPACES"}
        env["HOME"] = str(home)
        for cwd in (here, here / "sub"):
            with self.subTest(cwd=str(cwd)):
                p, j = run(["--plan", "--prompt-only"], env, script=script, cwd=str(cwd))
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertNotEqual(j["workspace"], str(here), "cwd (or its parent) became the workspace root")
                self.assertNotIn(str(here), step(j, "prompt")["detail"])


class Redaction(_ServerCase):
    TOKEN = "FAKETOKEN-not-a-real-secret"

    def test_prompt_url_userinfo_redacted_on_success(self):
        port = self.srv.server_address[1]
        url = f"http://user:{self.TOKEN}@127.0.0.1:{port}/system.md"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["prompt"]["source"], f"url http://***@127.0.0.1:{port}/system.md")
        self.assertNotIn(self.TOKEN, p.stdout + p.stderr)
        self.assertEqual(self.out.read_bytes(), REAL_PROMPT)

    def test_prompt_url_userinfo_redacted_on_failure(self):
        port = closed_port()
        url = f"http://user:{self.TOKEN}@127.0.0.1:{port}/system.md"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 1)
        self.assertIn(f"http://***@127.0.0.1:{port}/system.md", step(j, "prompt")["detail"])
        self.assertNotIn(self.TOKEN, p.stdout + p.stderr)

    def test_clone_url_userinfo_redacted(self):
        port = closed_port()
        base = f"http://user:{self.TOKEN}@127.0.0.1:{port}"
        env = {**self.env, "MIOS_GITHUB_BASE": base, "MIOS_REPOS": "MiOS"}
        p, j = run(["--plan", "--no-packages"], env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(step(j, "repo:MiOS")["detail"],
                         f"would run: git clone --depth 1 -- http://***@127.0.0.1:{port}/MiOS {self.ws / 'MiOS'}")
        self.assertNotIn(self.TOKEN, p.stdout + p.stderr)
        # and the real clone attempt (it fails: nothing listens): detail and log are both redacted
        p, j = run(["--no-packages"], env)
        self.assertEqual(p.returncode, 1, p.stdout)
        d = step(j, "repo:MiOS")
        self.assertEqual(d["status"], "failed")
        self.assertIn(f"http://***@127.0.0.1:{port}/MiOS", d["detail"])
        log = self.cache / "mios" / "mios-init-clone-MiOS.log"
        self.assertIn(str(log), d["detail"])
        self.assertNotIn(self.TOKEN, p.stdout + p.stderr)
        self.assertNotIn(self.TOKEN, log.read_text())


class Flags(unittest.TestCase):
    def test_contradictory_pairs_are_refused(self):
        for flags, msg in ((["--prompt-only", "--packages-only"], "--prompt-only and --packages-only"),
                           (["--packages-only", "--prompt-only"], "--prompt-only and --packages-only"),
                           (["--packages-only", "--no-packages"], "--packages-only and --no-packages"),
                           (["--no-packages", "--packages-only"], "--packages-only and --no-packages")):
            with self.subTest(flags=flags):
                p = subprocess.run(["bash", str(SCRIPT), *flags], capture_output=True, text=True)
                self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
                self.assertIn(f"contradictory flags {msg}", p.stderr)
                self.assertEqual(p.stdout, "", "a refused run must not emit a JSON object")

    def test_redundant_pair_still_runs(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "ws").mkdir()
            p, j = run(["--plan", "--prompt-only", "--no-packages"],
                       {"MIOS_WORKSPACES": str(tmp / "ws"), "XDG_CACHE_HOME": str(tmp / "cache"),
                        "MIOS_SYSTEM_PROMPT_DEPLOYED": str(tmp / "none.md"), "MIOS_IDENTITY_DEPLOYED": str(tmp / "none2.md")})
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertEqual([s["name"] for s in j["steps"]], ["prompt"])
            self.assertEqual(step(j, "prompt")["status"], "planned")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def unprivileged_user() -> str | None:
    """A real unprivileged account this (root) suite can run a command as, via runuser."""
    if not shutil.which("runuser"):
        return None
    for name in ("ubuntu", "vscode", "mios-dev", "nobody"):
        try:
            pw = pwd.getpwnam(name)
        except KeyError:
            continue
        if pw.pw_uid != 0:
            return name
    for pw in pwd.getpwall():
        if pw.pw_uid >= 1000 and pw.pw_shell and not pw.pw_shell.endswith(("nologin", "false")):
            return pw.pw_name
    return None


def as_root_text() -> str:
    m = re.search(r"^as_root\(\) \{\n.*?^\}\n", SCRIPT.read_text(), re.S | re.M)
    assert m, "as_root() not found in mios-init.sh"
    return m.group(0)


class AsRoot(unittest.TestCase):
    """as_root forwards the proxy and FEDORA_*/MIOS_* variables through `sudo -n env NAME=value`.

    The stub `sudo` records its argv to a file, drops -n, then runs the command under `env -i`
    (what sudo's env_reset does) -- so a variable reaches the child ONLY if as_root re-applied it.
    """
    PROBE = 'sh -c \'printf "%s|%s|%s\\n" "${FEDORA_DEVCONTAINER_NAME:-}" "${MIOS_TOML:-}" "${HTTPS_PROXY:-}"\''

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mios-init-asroot."))
        self.tmp.chmod(0o755)
        (self.tmp / "bin").mkdir()
        self.argv = self.tmp / "argv"
        self.argv.touch()
        self.argv.chmod(0o666)
        stub = self.tmp / "bin" / "sudo"
        stub.write_text('#!/bin/sh\n# stub: record argv, emulate env_reset, run the command\n'
                        f'printf \'%s\\n\' "$@" > "{self.argv}"\n'
                        '[ "$1" = -n ] && shift\n'
                        'exec env -i PATH="$PATH" HOME="$HOME" "$@"\n')
        stub.chmod(0o755)
        self.fn = self.tmp / "as_root.sh"
        self.fn.write_text(as_root_text())
        self.fn.chmod(0o644)
        if os.geteuid() != 0:
            self.runner = []
        else:
            user = unprivileged_user()
            if user is None:
                self.skipTest("root, and no unprivileged user to run as (runuser)")
            self.runner = ["runuser", "-u", user, "--"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _call(self):
        cmd = self.runner + ["env", f"PATH={self.tmp / 'bin'}:{os.environ.get('PATH', '/usr/bin:/bin')}",
                             "FEDORA_DEVCONTAINER_NAME=init-fix-probe", "MIOS_TOML=/x/y",
                             "HTTPS_PROXY=http://127.0.0.1:1/", "bash", "-c", f". {self.fn}; as_root {self.PROBE}"]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    def test_variables_reach_the_child_by_name(self):
        p = self._call()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(p.stdout.strip(), "init-fix-probe|/x/y|http://127.0.0.1:1/")
        argv = self.argv.read_text().splitlines()
        self.assertEqual(argv[:2], ["-n", "env"], "as_root must call `sudo -n env ...`")
        for pair in ("FEDORA_DEVCONTAINER_NAME=init-fix-probe", "MIOS_TOML=/x/y", "HTTPS_PROXY=http://127.0.0.1:1/"):
            self.assertIn(pair, argv)
        self.assertEqual(argv[-3:-1], ["sh", "-c"], "the command comes last, after the pairs")

    def test_negative_without_forwarding_the_child_sees_nothing(self):
        text = self.fn.read_text()
        old = '        [ -n "$_val" ] && set -- "$@" "$_v=$_val"\n'
        self.assertEqual(text.count(old), 1)
        self.fn.write_text(text.replace(old, ""))
        p = self._call()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(p.stdout.strip(), "||", "without the forwarding line nothing may reach the child")
        argv = self.argv.read_text().splitlines()
        self.assertNotIn("FEDORA_DEVCONTAINER_NAME=init-fix-probe", argv)


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
               "MIOS_SYSTEM_PROMPT_DEPLOYED": str(self.tmp / "none.md"), "MIOS_IDENTITY_DEPLOYED": str(self.tmp / "none2.md")}
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


def host_is_fedora() -> bool:
    try:
        osr = Path("/etc/os-release").read_text()
    except OSError:
        osr = ""
    return bool(re.search(r"^ID=\"?fedora\"?$", osr, re.M) and shutil.which("dnf"))


def image_holder(image="mios-dev:latest") -> str | None:
    """The runtime whose store holds the projection image: podman first, then docker."""
    for rt in ("podman", "docker"):
        if shutil.which(rt) and subprocess.run([rt, "image", "inspect", image], capture_output=True).returncode == 0:
            return rt
    return None


def fedora_prefix():
    """How to run the script on real Fedora: () on a Fedora host, the mios-dev wrapper otherwise."""
    if host_is_fedora():
        return ()
    if not shutil.which("mios-dev"):
        print("Fedora controls skipped: host is not Fedora and /usr/local/bin/mios-dev is absent", file=sys.stderr)
        return None
    if image_holder() is None:
        print("Fedora controls skipped: neither podman nor docker holds mios-dev:latest", file=sys.stderr)
        return None
    return ("env", "FEDORA_NO_AUTOBUILD=1", "mios-dev")


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
        self.ws = ws
        self.env = {"MIOS_WORKSPACES": str(ws), "MIOS_REPOS": "MiOS", "XDG_CACHE_HOME": str(self.tmp / "cache")}
        self.toml = (MIOS / "usr/share/mios/mios.toml").read_text()
        self.dlog = self.tmp / "cache" / "mios" / "mios-init-dnf.log"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _section(self):
        m = re.search(r"^\[packages\.devcontainer\]\n(?:(?!^\[).*\n)*", self.toml, re.M)
        self.assertIsNotNone(m, "the real mios.toml has no [packages.devcontainer]")
        return m

    def _toml_with_section(self, replacement: str) -> Path:
        m = self._section()
        f = self.tmp / "mios.toml"
        f.write_text(self.toml[:m.start()] + replacement + self.toml[m.end():])
        return f

    def test_dnf_install_of_resolved_set(self):
        p, j = run(["--packages-only"], self.env, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "ok", d)
        self.assertRegex(d["detail"], r"^Fedora host: dnf5? install -y --setopt=install_weak_deps=False of \d+ packages from \[packages\.devcontainer\]")
        self.assertEqual(j["runtime"], "podman")
        self.assertNotIn("prompt", [s["name"] for s in j["steps"]])
        # dnf really ran: its own transcript, not the script's claim, says so
        self.assertIn(str(self.dlog), d["detail"])
        self.assertRegex(self.dlog.read_text(), r"Nothing to do|Complete!|Transaction Summary")
        # the whole Containerfile, already satisfied in the image: dnf, npm CLIs, venv
        self.assertIn("Nothing to do", d["detail"])
        self.assertIn(f"npm CLIs from {self.ws}/MiOS/.devcontainer/Containerfile: present (", d["detail"])
        self.assertIn("venv /usr/lib/mios/agents/.venv: already satisfied (imports fastapi httpx mcp pydantic uvicorn)", d["detail"])

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

    def test_dnf_failure_names_the_package_and_the_log(self):
        m = self._section()
        section = m.group(0)
        self.assertEqual(section.count("pkgs = ["), 1, section)
        f = self._toml_with_section(section.replace("pkgs = [", 'pkgs = [\n    "mios-init-no-such-package-xyz",', 1))
        p, j = run(["--packages-only"], {**self.env, "MIOS_TOML": str(f)}, FEDORA)
        self.assertEqual(p.returncode, 1, p.stdout)
        d = step(j, "packages")
        self.assertEqual(d["status"], "failed")
        self.assertIn("No match for argument: mios-init-no-such-package-xyz", d["detail"])
        self.assertIn(f"(log {self.dlog})", d["detail"])
        self.assertIn("No match for argument: mios-init-no-such-package-xyz", self.dlog.read_text())

    def test_containerfile_without_npm_line_fails_naming_it(self):
        src = (MIOS / ".devcontainer" / "Containerfile").read_text()
        kept = [ln for ln in src.splitlines(keepends=True) if "npm install -g" not in ln]
        self.assertLess(len(kept), len(src.splitlines()), "the real Containerfile has no npm install -g line")
        cf = self.tmp / "Containerfile.no-npm"
        cf.write_text("".join(kept))
        p, j = run(["--packages-only"], {**self.env, "MIOS_CONTAINERFILE": str(cf)}, FEDORA)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertEqual(j["failed_required"], ["packages"])
        self.assertIn(f"no 'npm install -g' line in {cf} (MIOS_CONTAINERFILE)", step(j, "packages")["detail"])
        self.assertFalse(self.dlog.exists(), "dnf must not run when the Containerfile cannot be read")

    def test_foreign_origin_checkout_fails_naming_it(self):
        (self.ws / "MiOS").unlink()
        make_fake_mios(self.ws / "MiOS", FOREIGN_ORIGIN)
        p, j = run(["--packages-only"], self.env, FEDORA)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertEqual(j["failed_required"], ["repo:MiOS", "packages"])
        for name in ("repo:MiOS", "packages"):
            self.assertIn(f"ignored: origin is {FOREIGN_ORIGIN} (not the MiOS repo)", step(j, name)["detail"])
        self.assertFalse(self.dlog.exists())

    def test_plan_names_dnf(self):
        p, j = run(["--plan", "--packages-only"], self.env, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "planned")
        self.assertRegex(d["detail"], r"^Fedora host: would run: dnf5? install -y --setopt=install_weak_deps=False")
        self.assertIn("npm CLIs from", d["detail"])
        self.assertIn("venv /usr/lib/mios/agents/.venv", d["detail"])
        self.assertNotIn("cloud-fedora-setup", d["detail"])
        self.assertFalse((self.tmp / "cache").exists())


def wrapper_control_reason() -> str | None:
    if os.geteuid() != 0:
        return "not root: cannot write /usr/local/bin"
    if host_is_fedora():
        return "host is Fedora: the projection branch does not run here"
    if not (shutil.which("docker") and subprocess.run(["docker", "image", "inspect", "mios-dev:latest"],
                                                      capture_output=True).returncode == 0):
        return "docker does not hold mios-dev:latest (the finding's state: image in docker, podman empty)"
    if not MIOS:
        return "no MiOS checkout to stand in as the workspace's MiOS"
    return None


@unittest.skipUnless(wrapper_control_reason() is None, f"wrapper control skipped: {wrapper_control_reason()}")
class WrapperRuntime(unittest.TestCase):
    """The --wrapper-only branch must write the wrapper for the runtime that holds the image."""
    FEDORA_WRAPPER = Path("/usr/local/bin/fedora")
    TEST_WRAPPER = Path("/usr/local/bin/init-fix-test")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mios-init-wrapper."))
        self.backup = self.FEDORA_WRAPPER.read_bytes() if self.FEDORA_WRAPPER.exists() else None
        self.backup_mode = self.FEDORA_WRAPPER.stat().st_mode if self.backup is not None else None
        self.backup_sha = sha256(self.backup) if self.backup is not None else None
        self.script_sha = file_sha(SCRIPT)
        ws = self.tmp / "ws"
        ws.mkdir()
        (ws / "MiOS").symlink_to(MIOS)
        # FEDORA_RUNTIME=podman in the caller's environment (MiOS is podman-native, so a hook
        # or operator may well set it) while the image lives in docker: the wrapper-only call
        # must pass the runtime that HOLDS the image and override this, and the installed
        # wrapper's RUNTIME= line is what proves which one won.
        self.env = {"MIOS_WORKSPACES": str(ws), "MIOS_REPOS": "MiOS", "XDG_CACHE_HOME": str(self.tmp / "cache"),
                    "FEDORA_DEVCONTAINER_NAME": "init-fix-test", "FEDORA_IMAGE": "mios-dev:latest",
                    "FEDORA_BUILD_CTX": str(self.tmp / "ctx"), "FEDORA_RUNTIME": "podman"}
        self.wlog = self.tmp / "cache" / "mios" / "mios-init-wrapper.log"
        self.TEST_WRAPPER.unlink(missing_ok=True)

    def _restore(self):
        self.TEST_WRAPPER.unlink(missing_ok=True)
        if self.backup is None:
            self.FEDORA_WRAPPER.unlink(missing_ok=True)
        else:
            tmp = self.FEDORA_WRAPPER.with_name(".fedora.restore")
            tmp.write_bytes(self.backup)
            tmp.chmod(self.backup_mode)
            tmp.replace(self.FEDORA_WRAPPER)
            self.assertEqual(file_sha(self.FEDORA_WRAPPER), self.backup_sha, "/usr/local/bin/fedora not restored byte-identical")

    def tearDown(self):
        try:
            self._restore()
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)
        self.assertEqual(file_sha(SCRIPT), self.script_sha, "the real script changed")

    def _run(self, script):
        try:
            p, j = run(["--packages-only"], self.env, script=script)
            wrapper = self.TEST_WRAPPER.read_text() if self.TEST_WRAPPER.exists() else ""
            m = re.search(r"^RUNTIME=(\S+)$", wrapper, re.M)
            return p, j, (m.group(1) if m else None)
        finally:
            self._restore()

    def test_wrapper_is_written_for_the_runtime_holding_the_image(self):
        p, j, rt = self._run(SCRIPT)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "ok", d)
        self.assertEqual(rt, "docker", "the wrapper must name the runtime that holds mios-dev:latest")
        self.assertIn("installed /usr/local/bin/init-fix-test for RUNTIME=docker", d["detail"])
        self.assertIn(f"(log {self.wlog})", d["detail"])
        self.assertEqual(j["runtime"], "docker")

    @unittest.skipUnless(shutil.which("podman"), "podman not on PATH: auto would pick docker anyway")
    def test_negative_without_the_runtime_passthrough_the_step_fails(self):
        script = copy_env_dir(self.tmp)
        self.assertEqual(file_sha(script), self.script_sha, "the copy must be byte-identical before mutation")
        mutate(script, 'FEDORA_RUNTIME="$rt" FEDORA_PROVISION_HOST=0 bash "$cfs" --wrapper-only',
               'FEDORA_PROVISION_HOST=0 bash "$cfs" --wrapper-only', self)
        p, j, rt = self._run(script)
        self.assertEqual(rt, "podman", "without the pass-through the caller's FEDORA_RUNTIME wrote a wrapper for the wrong runtime -- the finding")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "failed", d)
        self.assertIn("lives in docker", d["detail"])
        self.assertIn("says RUNTIME=podman", d["detail"])
        self.assertEqual(j["failed_required"], ["packages"])

    @unittest.skipUnless(shutil.which("podman"), "podman not on PATH: auto would pick docker anyway")
    def test_negative_without_the_check_the_wrong_wrapper_is_reported_ok(self):
        # The original bug: no runtime passed AND no check -> ok:true with a wrapper podman owns.
        script = copy_env_dir(self.tmp)
        mutate(script, 'FEDORA_RUNTIME="$rt" FEDORA_PROVISION_HOST=0 bash "$cfs" --wrapper-only',
               'FEDORA_PROVISION_HOST=0 bash "$cfs" --wrapper-only', self)
        mutate(script, '        if [ "$wrt" = "$rt" ]; then\n            record packages ok 1 "non-Fedora host: image $DC_IMAGE present',
               '        if true; then\n            record packages ok 1 "non-Fedora host: image $DC_IMAGE present', self)
        p, j, rt = self._run(script)
        self.assertEqual(rt, "podman")
        self.assertEqual(p.returncode, 0, "without the RUNTIME= check the wrong wrapper passes: the check is load-bearing")
        self.assertEqual(step(j, "packages")["status"], "ok")


if __name__ == "__main__":
    unittest.main()
