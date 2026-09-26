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

Fetch log (G6): the prompt curl's stderr is kept, redacted, as mios-init-fetch-<name>.log.
  positive  an unreachable URL: the detail names the log, the log holds curl's own "curl: (7)"
            message and the detail carries it
  negative  a copy that discards curl's stderr: the detail names only "curl rc 7", no message

Pinned checkout (F2): a directory with mios.toml + packages.sh counts as MiOS only when it is a
git work tree whose origin is the MiOS repo. The pin is a trust statement, not a boundary (G7):
a directory whose origin is SET to the MiOS URL is accepted, on purpose.
  negative  a foreign origin (https://example.com/x/y) is logged "ignored: origin is ..." and the
            prompt falls through to the URL
  positive  the same directory with the MiOS origin URL (https, .git, ssh forms) set locally is
            accepted, source "local"
  negative  no git work tree at all is ignored
  positive  $PWD and its parent are not workspace candidates (a correctly-origined checkout there
            is not picked)

URL redaction (F9, G4): userinfo never reaches stdout, stderr, the JSON or the clone log; nor
does the value of a credential query parameter (?token=..., GitHub's private-raw form).
  positive  ?token=FAKEQUERYTOKEN: 0 output lines carry it, the source says ?token=***
  negative  a copy with the old userinfo-only sed: exactly 2 lines carry it (the step's log line
            and the JSON) -- what the re-reviewer measured

Flags (F7): --prompt-only with --packages-only, and --packages-only with --no-packages, exit 2
with a message; the redundant --prompt-only --no-packages still runs.

as_root (F6, G2): proved with the function text extracted from the script, run as a REAL
unprivileged user (via runuser when the suite is root) with a stub `sudo` first on PATH that
records its argv, emulates env_reset (a clean environment) and then RUNS the payload -- a stub,
as the finding allows. The forwarded values travel in a 0600 temp file that root's sh sources,
never on sudo's argv.
  positive  the child sees HTTPS_PROXY, FEDORA_* and MIOS_*; the recorded argv holds NO value
            (0 hits for the fake secret), only `-n sh -c <script> sh <envfile> <cmd...>`; the env
            file's mode, recorded from inside the child, was 600; the file is gone afterwards
  negative  a copy with the OLD `sudo -n env NAME=value` form: the fake secret is in the argv
  negative  with the forwarding line removed the child sees nothing

Wrapper runtime (F1, G1, G5), only where the projection image lives in docker and podman is also
on PATH (this VM). The wrapper goes to FEDORA_WRAPPER_DIR=<scratch>/bin, never /usr/local/bin
(the two real wrappers there are sha256-checked before and after every test). The caller's
environment says FEDORA_RUNTIME=podman throughout (podman-native default) while the image lives
in docker, which is the state the finding describes.
  positive  the written wrapper says RUNTIME=docker (the runtime that holds the image, passed
            explicitly and overriding the environment) and the step is ok naming the scratch path
  negative  with the FEDORA_RUNTIME pass-through removed the environment's podman reaches the
            setup script, the wrapper says RUNTIME=podman and the step is recorded failed,
            naming both runtimes
  negative  with the RUNTIME= check also removed the step reports ok for a podman wrapper (the
            original bug), which shows the check is load-bearing
  positive  G1: a planted EXISTING wrapper saying RUNTIME=podman (and one with no RUNTIME= line)
            is rewritten for docker, the step ok with "wrapper rewritten for docker"; --plan names
            the rewrite and changes nothing; a matching wrapper is left byte-identical
  negative  G1: with the mismatch check mutated away the stale podman wrapper is kept and the
            step is skipped/ok -- the finding reproduced
  negative  G5: a copy with one hardcoded /usr/local/bin restored fails claiming
            /usr/local/bin/<name> is missing while the wrapper sits in the scratch dir

Plan mode (non-Fedora branch forced with MIOS_OS_RELEASE, an absent image with FEDORA_IMAGE):
  positive  names the projection: cloud-fedora-setup.sh + FEDORA_DEVCONTAINER_REPO=...MiOS
  positive  creates nothing: no cache dir, no clone in the workspace
  positive  G8: with a stub docker that fails until a marker exists and a stub dockerd that
            creates it (stubs first on PATH; /var/log/dev-loop-dockerd.log shadowed in a private
            mount namespace; the real dockerd untouched), --plan reports docker and the image
            present: the runtime decision is the setup script's --print-runtime, which starts
            the daemon
  negative  G8: with the delegation mutated away the down daemon reads as podman / absent

Package step on REAL Fedora (the host when it is Fedora, else inside the mios-dev container,
found in podman first, then docker):
  positive  --packages-only resolves [packages.devcontainer] through MiOS packages.sh and runs
            dnf install -y --setopt=install_weak_deps=False for real (its log carries the
            transaction); a second run finds nothing to do -- idempotence, which holds whether
            or not the container lagged the checkout's package set -- and the venv is already
            satisfied (every distribution of the real requirements.txt), the Containerfile's
            npm CLIs present
  negative  a mios.toml without [packages.devcontainer] fails naming the section and the file
  negative  an EMPTY section fails inside packages.sh (get_packages_strict), naming the section
  negative  a package dnf cannot find fails naming the package and the log (F8)
  negative  a Containerfile copy without the `npm install -g` line fails naming that file (F5)
  negative  a Containerfile copy without the `pip install -r` fails naming it
  positive  the requirements file is the one the Containerfile's pip is given: the real
            (staged: /usr/src/mios-ssot/<rel>) form maps back by path suffix, and a copy in the
            older `COPY <rel> /tmp/x; pip install -r /tmp/x` form maps back through the COPY
  negative  with the suffix mapping mutated away the real staged Containerfile fails naming the
            path pip is given (the regression a COPY-only parser hit when MiOS a883964 dropped
            the COPY line)
  negative  a foreign-origin checkout fails repo:MiOS and packages naming the origin (F2)
  positive  --plan on Fedora names the dnf path, the npm CLIs and the venv, not the projection
  positive  G3: the venv's expected set is derived from requirements.txt (no literal module list
            in the script; the count in the detail equals the file's distribution count)
  negative  G3: a requirements copy with a fake distribution appended is not satisfied, naming it
  negative  G3: a copy whose check is mutated to always-true reports the fake satisfied
  positive  G9: a Containerfile copy with the npm line split over a backslash continuation yields
            every package
  negative  G9: the old one-line parser yields only the first (the continued ones dropped)

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
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ENV_DIR = REPO / "skills" / "dev-loop" / "scripts" / "env"
SCRIPT = ENV_DIR / "mios-init.sh"
MIOS_ORIGIN = "https://github.com/mios-dev/MiOS"
FOREIGN_ORIGIN = "https://example.com/x/y"
REQS_REL = "usr/lib/mios/agent-pipe/requirements.txt"
CONTAINERFILE_REL = ".devcontainer/Containerfile"


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


def req_names(text: str) -> set[str]:
    """The distribution names a requirements file names, PEP 503 normalised (the script's rule)."""
    names = set()
    for line in text.splitlines():
        m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", line.split("#", 1)[0].strip())
        if m:
            names.add(re.sub(r"[-_.]+", "-", m.group(0).lower()))
    return names


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        path = urlsplit(self.path).path  # ?token=... is the redaction control's business, not routing
        body = {"/system.md": REAL_PROMPT, "/MiOS.md": REAL_IDENTITY, "/html": HTML, "/empty": b""}.get(path)
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
        self.fetch_log = self.cache / "mios" / "mios-init-fetch-system.log"

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

    def test_unreachable_url_fails_naming_it_and_its_log(self):
        url = f"http://127.0.0.1:{closed_port()}/system.md"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("FAILED required step(s): prompt", p.stderr)
        self.assertEqual(j["failed_required"], ["prompt"])
        d = step(j, "prompt")["detail"]
        self.assertIn(url, d)
        self.assertIn("fetch failed", d)
        self.assertFalse(self.out.exists())
        # G6: curl's own message names the cause (7 = could not connect), kept in a log the
        # detail names and carried into the detail itself
        self.assertIn(f"(log {self.fetch_log})", d)
        self.assertRegex(self.fetch_log.read_text(), r"curl: \(7\) ")
        self.assertRegex(d, r"curl rc 7: curl: \(7\) ")

    def test_negative_without_stderr_capture_the_detail_names_only_the_rc(self):
        script = copy_env_dir(self.tmp)
        mutate(script, '-o "$tmp" "$url" 2>"$ftmp"', '-o "$tmp" "$url" 2>/dev/null', self)
        url = f"http://127.0.0.1:{closed_port()}/system.md"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url}, script=script)
        self.assertEqual(p.returncode, 1, p.stdout)
        d = step(j, "prompt")["detail"]
        self.assertIn("curl rc 7", d)
        self.assertNotIn("curl: (7)", d, "without the stderr capture curl's message cannot reach the detail")
        self.assertEqual(self.fetch_log.read_text() if self.fetch_log.exists() else "", "")

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
        # G7: the pin is a trust statement -- an origin SET to the MiOS URL is accepted on purpose.
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
    QTOKEN = "FAKEQUERYTOKEN"
    # The second sed expression of redact_stream: the query-parameter half added for G4.
    QUERY_SED = r""" -e 's,([?&]('"$REDACT_PARAMS"')=)[^&#]*,\1***,g'"""

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
        self.assertNotIn(self.TOKEN, self.fetch_log.read_text(), "curl's own message echoed the userinfo into the log")

    def test_query_token_redacted(self):
        url = f"{self.base}/system.md?token={self.QTOKEN}"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["prompt"]["source"], f"url {self.base}/system.md?token=***")
        self.assertEqual(sum(self.QTOKEN in ln for ln in (p.stdout + p.stderr).splitlines()), 0)
        self.assertEqual(self.out.read_bytes(), REAL_PROMPT, "the redaction must not touch the URL that is fetched")
        # and the failure path: the detail, stderr and the fetch log
        url = f"http://127.0.0.1:{closed_port()}/system.md?token={self.QTOKEN}&x=1"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url})
        self.assertEqual(p.returncode, 1)
        self.assertIn("/system.md?token=***&x=1", step(j, "prompt")["detail"])
        self.assertEqual(sum(self.QTOKEN in ln for ln in (p.stdout + p.stderr).splitlines()), 0)
        self.assertNotIn(self.QTOKEN, self.fetch_log.read_text())

    def test_negative_old_userinfo_only_sed_leaks_the_query_token(self):
        script = copy_env_dir(self.tmp)
        mutate(script, self.QUERY_SED, "", self)
        url = f"{self.base}/system.md?token={self.QTOKEN}"
        p, j = run(["--prompt-only"], {**self.env, "MIOS_SYSTEM_PROMPT_URL": url}, script=script)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        leaked = [ln for ln in p.stdout.splitlines() if self.QTOKEN in ln]
        self.assertEqual(len(leaked), 2, f"the old sed leaks the token on the step line and the JSON: {leaked}")
        self.assertEqual(j["prompt"]["source"], f"url {url}")

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


# The G2 finding's form (HEAD d34b668): every forwarded value on sudo's argv.
OLD_AS_ROOT = r'''as_root() {
    if [ "$(id -u)" = 0 ]; then "$@"; return $?; fi
    command -v sudo >/dev/null 2>&1 || { printf 'mios-init: not root and no sudo for: %s\n' "$*" >&2; return 1; }
    _n=$#
    for _v in HTTPS_PROXY https_proxy HTTP_PROXY http_proxy NO_PROXY no_proxy \
              $(awk 'BEGIN { for (k in ENVIRON) if (k ~ /^(FEDORA|MIOS)_[A-Za-z0-9_]*$/) print k }'); do
        eval "_val=\${$_v:-}"
        [ -n "$_val" ] && set -- "$@" "$_v=$_val"
    done
    while [ "$_n" -gt 0 ]; do set -- "$@" "$1"; shift; _n=$((_n - 1)); done
    sudo -n env "$@"
}
'''


class AsRoot(unittest.TestCase):
    """as_root forwards the proxy and FEDORA_*/MIOS_* variables to the sudo side without putting
    a value on argv: they travel in a 0600 temp file that root's sh sources.

    The stub `sudo` records its argv to a file, drops -n, then runs the command under `env -i`
    (what sudo's env_reset does) -- so a variable reaches the child ONLY if as_root re-applied it,
    and the child really runs, which is what lets it record the env file's mode.
    """
    SECRET = "FAKEPROXYSECRET-not-a-real-secret"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mios-init-asroot."))
        self.tmp.chmod(0o755)
        (self.tmp / "bin").mkdir()
        self.tdir = self.tmp / "t"  # TMPDIR for the env file: writable by the unprivileged user
        self.tdir.mkdir()
        self.tdir.chmod(0o1777)
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
        # What the child prints: the three forwarded values, then the env file's mode as seen
        # from inside the child (the file must exist, 0600, while the command runs).
        self.probe = ('sh -c \'printf "%s|%s|%s\\n" "${FEDORA_DEVCONTAINER_NAME:-}" "${MIOS_TOML:-}" "${HTTPS_PROXY:-}"; '
                      f'stat -c "%a" {self.tdir}/mios-init-env.* 2>/dev/null || echo "no env file"\'')
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
                             f"TMPDIR={self.tdir}", "FEDORA_DEVCONTAINER_NAME=init-fix-probe", "MIOS_TOML=/x/y",
                             f"HTTPS_PROXY=http://user:{self.SECRET}@127.0.0.1:1/",
                             "bash", "-c", f". {self.fn}; as_root {self.probe}"]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    def _env_files(self):
        return sorted(self.tdir.glob("mios-init-env.*"))

    def test_values_reach_the_child_but_never_the_argv(self):
        p = self._call()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        lines = p.stdout.strip().splitlines()
        self.assertEqual(lines[0], f"init-fix-probe|/x/y|http://user:{self.SECRET}@127.0.0.1:1/")
        self.assertEqual(lines[1], "600", "the env file must be 0600 while the child runs (mode recorded by the child)")
        argv = self.argv.read_text().splitlines()
        self.assertEqual(argv[:3], ["-n", "sh", "-c"], "as_root must call `sudo -n sh -c <script> sh <envfile> <cmd...>`")
        self.assertEqual(argv[4], "sh", "the sourcing shell's $0")
        self.assertTrue(argv[5].startswith(str(self.tdir / "mios-init-env.")), argv)
        self.assertEqual(argv[6:8], ["sh", "-c"], "the command follows the env file")
        joined = "\n".join(argv)
        self.assertEqual(joined.count(self.SECRET), 0, "a forwarded value reached sudo's argv")
        self.assertNotIn("init-fix-probe", joined)
        self.assertNotIn("/x/y", joined)
        self.assertEqual(self._env_files(), [], "the env file must be removed after the call")

    def test_negative_old_env_form_puts_the_secret_on_argv(self):
        self.fn.write_text(OLD_AS_ROOT)
        p = self._call()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(p.stdout.startswith(f"init-fix-probe|/x/y|http://user:{self.SECRET}@127.0.0.1:1/\n"))
        argv = self.argv.read_text()
        self.assertGreaterEqual(argv.count(self.SECRET), 1, "the old `sudo -n env NAME=value` form leaks the value on argv -- the finding")
        self.assertIn(f"HTTPS_PROXY=http://user:{self.SECRET}@127.0.0.1:1/", argv.splitlines())

    def test_negative_without_forwarding_the_child_sees_nothing(self):
        text = self.fn.read_text()
        old = '        printf "export %s=\'%s\'\\n" "$_v" "$(printf \'%s\' "$_val" | sed "s/\'/\'\\\\\\\\\'\'/g")"\n'
        self.assertEqual(text.count(old), 1, old)
        self.fn.write_text(text.replace(old, ""))
        p = self._call()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(p.stdout.strip().splitlines()[0], "||", "without the forwarding line nothing may reach the child")
        self.assertNotIn("init-fix-probe", self.argv.read_text())


class PlanMode(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "ws").mkdir()
        (self.tmp / "os-release").write_text('ID=ubuntu\nVERSION_ID="24.04"\n')
        self.env = {"MIOS_WORKSPACES": str(self.tmp / "ws"), "XDG_CACHE_HOME": str(self.tmp / "cache"),
                    "MIOS_OS_RELEASE": str(self.tmp / "os-release"), "FEDORA_IMAGE": "mios-init-absent:none",
                    "MIOS_SYSTEM_PROMPT_DEPLOYED": str(self.tmp / "none.md"), "MIOS_IDENTITY_DEPLOYED": str(self.tmp / "none2.md")}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_non_fedora_plan_names_projection_and_changes_nothing(self):
        p, j = run(["--plan"], self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(j["mode"], "plan")
        d = step(j, "packages")
        self.assertEqual(d["status"], "planned")
        self.assertIn("non-Fedora host", d["detail"])
        self.assertIn("cloud-fedora-setup.sh", d["detail"])
        self.assertIn("FEDORA_DEVCONTAINER_REPO=https://github.com/mios-dev/MiOS", d["detail"])
        self.assertIn("image mios-init-absent:none not found", d["detail"])
        self.assertEqual({s["status"] for s in j["steps"]}, {"planned"})
        self.assertFalse((self.tmp / "cache").exists(), "--plan wrote the cache dir")
        self.assertEqual(list((self.tmp / "ws").iterdir()), [], "--plan cloned into the workspace")

    def test_unknown_flag_is_rejected(self):
        p = subprocess.run(["bash", str(SCRIPT), "--bogus"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("unknown argument: --bogus", p.stderr)


def down_daemon_control_reason() -> str | None:
    if os.geteuid() != 0:
        return "not root: unshare -m and the setup script's daemon start need root"
    if not shutil.which("podman"):
        return "podman not on PATH: the fallback's podman-first order is what the negative shows"
    if not shutil.which("unshare") or subprocess.run(["unshare", "-m", "true"], capture_output=True).returncode != 0:
        return "no private mount namespace (unshare -m): the real dockerd log cannot be shadowed"
    return None


@unittest.skipUnless(down_daemon_control_reason() is None, f"down-daemon control skipped: {down_daemon_control_reason()}")
class DownDaemon(unittest.TestCase):
    """G8: a cold session has dockerd down and both runtimes installed. The runtime and image-home
    decision is delegated to cloud-fedora-setup.sh --print-runtime, which starts dockerd; without
    that, a down daemon reads as "image absent" and --plan says podman.

    Stubs first on PATH: `docker` fails (daemon "down") until a marker exists, `dockerd` creates
    it. The real dockerd is never stopped; the setup script's /var/log/dev-loop-dockerd.log is
    shadowed by a bind mount inside a private mount namespace (unshare -m) so the stub's start
    never truncates the real daemon's log. The real podman answers for itself (it holds nothing).
    """
    IMAGE = "mios-init-g8-probe:test"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mios-init-g8."))
        (self.tmp / "ws").mkdir()
        (self.tmp / "bin").mkdir()
        (self.tmp / "os-release").write_text("ID=ubuntu\n")
        self.marker = self.tmp / "dockerd-up"
        stubs = self.tmp / "stubs"
        stubs.mkdir()
        (stubs / "docker").write_text(f'#!/bin/sh\n# stub docker: the daemon is "down" until the marker exists\n'
                                      f'[ -e "{self.marker}" ] || exit 1\nexit 0\n')
        (stubs / "dockerd").write_text(f'#!/bin/sh\n# stub dockerd: coming up creates the marker\ntouch "{self.marker}"\nexit 0\n')
        for f in (stubs / "docker", stubs / "dockerd"):
            f.chmod(0o755)
        shadow = self.tmp / "dockerd.log"
        shadow.touch()
        self.prefix = ("unshare", "-m", "sh", "-c",
                       'mount --bind "$1" /var/log/dev-loop-dockerd.log && shift && exec "$@"', "sh", str(shadow))
        self.env = {"MIOS_WORKSPACES": str(self.tmp / "ws"), "XDG_CACHE_HOME": str(self.tmp / "cache"),
                    "MIOS_OS_RELEASE": str(self.tmp / "os-release"), "FEDORA_IMAGE": self.IMAGE,
                    "FEDORA_WRAPPER_DIR": str(self.tmp / "bin"), "FEDORA_BUILD_CTX": str(self.tmp / "ctx"),
                    "PATH": f"{stubs}:{os.environ.get('PATH', '/usr/bin:/bin')}"}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_plan_starts_nothing_and_says_what_it_could_not_see(self):
        """--plan changes nothing (re-review round 3): it must not start dockerd as root, and it
        must say the docker store went unchecked instead of calling the image absent."""
        p, j = run(["--plan", "--packages-only"], self.env, self.prefix)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "planned", d)
        self.assertIn("docker's daemon is down, so its image store was not checked", d["detail"])
        self.assertFalse(self.marker.exists(), "a plan started dockerd")

    def test_negative_without_the_plan_guard_the_plan_starts_dockerd(self):
        """Removing the guard restores the delegation inside --plan: dockerd is started (the
        finding) and the image is then reported in docker, which also proves the delegation path."""
        script = copy_env_dir(self.tmp)
        mutate(script, 'if [ -f "$CFS" ] && [ "$PLAN" != 1 ]; then', 'if [ -f "$CFS" ]; then', self)
        p, j = run(["--plan", "--packages-only"], self.env, self.prefix, script=script)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertIn(f"image {self.IMAGE} present (docker)", d["detail"])
        self.assertTrue(self.marker.exists(), "the delegation started dockerd")


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
    VENV = "/usr/lib/mios/agents/.venv"

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
        self.containerfile = (MIOS / CONTAINERFILE_REL).read_text()
        self.reqs_text = (MIOS / REQS_REL).read_text()
        self.reqs = ws / "MiOS" / REQS_REL
        self.cf = ws / "MiOS" / CONTAINERFILE_REL
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

    def _npm_line(self):
        line = next(ln for ln in self.containerfile.splitlines() if "npm install -g" in ln)
        pkgs = line.split("npm install -g", 1)[1].split()
        self.assertGreaterEqual(len(pkgs), 2, "the control needs a line with at least two packages to split")
        return line, pkgs

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
        self.assertRegex(d["detail"], r"\((installed|all already installed: Nothing to do); log ")
        self.assertRegex(self.dlog.read_text(), r"Nothing to do|Complete!|Transaction Summary")
        # Idempotence is the state-independent control: the container may lag the checkout's
        # package set (measured: MiOS a7de8f4 added btop, fastfetch and oh-my-posh after the
        # image was built, and the first run installed exactly those), so what the first run
        # had to install is its business; the second run must find nothing to do.
        p2, j2 = run(["--packages-only"], self.env, FEDORA)
        self.assertEqual(p2.returncode, 0, p2.stdout + p2.stderr)
        d2 = step(j2, "packages")
        self.assertEqual(d2["status"], "ok", d2)
        self.assertIn("(all already installed: Nothing to do; log ", d2["detail"])
        self.assertIn("Nothing to do", self.dlog.read_text())
        # the rest of the Containerfile, already satisfied in the image: npm CLIs, venv
        self.assertIn(f"npm CLIs from {self.cf}: present (", d["detail"])
        n = len(req_names(self.reqs_text))
        self.assertIn(f"venv {self.VENV}: already satisfied (all {n} distributions of {self.reqs} installed)", d["detail"])

    def test_venv_expected_set_is_derived_from_requirements(self):
        # G3: no literal module list in the script; the expected set is the requirements file's.
        text = SCRIPT.read_text()
        self.assertNotIn("VENV_MODULES", text)
        self.assertNotRegex(text, r"fastapi httpx mcp pydantic uvicorn", "the hand-copied 5-of-N subset is back")
        n = len(req_names(self.reqs_text))
        self.assertGreater(n, 5, "the real requirements.txt names more than the old five modules")
        p, j = run(["--plan", "--packages-only"], self.env, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(f"venv {self.VENV}: already satisfied (all {n} distributions of {self.reqs} installed)", step(j, "packages")["detail"])

    def test_missing_distribution_is_named(self):
        f = self.tmp / "requirements.txt"
        f.write_text(self.reqs_text + "mios-init-no-such-dist>=1\n")
        n = len(req_names(f.read_text()))
        p, j = run(["--plan", "--packages-only"], {**self.env, "MIOS_REQUIREMENTS": str(f)}, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "planned")
        self.assertIn(f"venv {self.VENV}: missing mios-init-no-such-dist (of {n} in {f}); would run: python3.11 -m venv {self.VENV} && pip install -r {f}", d["detail"])
        self.assertNotIn("already satisfied", d["detail"])

    def test_negative_always_true_check_reports_the_fake_satisfied(self):
        script = copy_env_dir(self.tmp)
        mutate(script, '    [ -z "$VENV_MISSING" ]\n}\n', '    true\n}\n', self)
        f = self.tmp / "requirements.txt"
        f.write_text(self.reqs_text + "mios-init-no-such-dist>=1\n")
        p, j = run(["--plan", "--packages-only"], {**self.env, "MIOS_REQUIREMENTS": str(f)}, FEDORA, script=script)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")["detail"]
        self.assertIn(f"venv {self.VENV}: already satisfied", d, "with the check mutated away the fake distribution passes")
        self.assertNotIn("mios-init-no-such-dist", d)

    def test_npm_continuation_lines_are_joined(self):
        line, pkgs = self._npm_line()
        split = line.replace(f" {pkgs[0]} ", f" {pkgs[0]} \\\n    ", 1)
        self.assertNotEqual(split, line)
        cf = self.tmp / "Containerfile.continued"
        cf.write_text(self.containerfile.replace(line, split))
        p, j = run(["--plan", "--packages-only"], {**self.env, "MIOS_CONTAINERFILE": str(cf)}, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")["detail"]
        self.assertIn(f"npm CLIs from {cf}: present ({' '.join(pkgs)})", d)

    def test_negative_one_line_parser_drops_the_continued_packages(self):
        line, pkgs = self._npm_line()
        cf = self.tmp / "Containerfile.continued"
        cf.write_text(self.containerfile.replace(line, line.replace(f" {pkgs[0]} ", f" {pkgs[0]} \\\n    ", 1)))
        script = copy_env_dir(self.tmp)
        # Only the npm parser reads the unjoined file (the requirements lookup keeps the joined text).
        mutate(script, '''npm_line=$(printf '%s\\n' "$cfj" | grep''', '''npm_line=$(cat "$cf" | grep''', self)
        p, j = run(["--plan", "--packages-only"], {**self.env, "MIOS_CONTAINERFILE": str(cf)}, FEDORA, script=script)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")["detail"]
        self.assertIn(f"npm CLIs from {cf}: present ({pkgs[0]})", d, "the old parser stops at the backslash")
        for dropped in pkgs[1:]:
            self.assertNotIn(dropped, d, f"the one-line parser silently dropped {dropped}")

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
        kept = [ln for ln in self.containerfile.splitlines(keepends=True) if "npm install -g" not in ln]
        self.assertLess(len(kept), len(self.containerfile.splitlines()), "the real Containerfile has no npm install -g line")
        cf = self.tmp / "Containerfile.no-npm"
        cf.write_text("".join(kept))
        p, j = run(["--packages-only"], {**self.env, "MIOS_CONTAINERFILE": str(cf)}, FEDORA)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertEqual(j["failed_required"], ["packages"])
        self.assertIn(f"no 'npm install -g' line in {cf} (MIOS_CONTAINERFILE)", step(j, "packages")["detail"])
        self.assertFalse(self.dlog.exists(), "dnf must not run when the Containerfile cannot be read")

    def _pip_r(self):
        m = re.search(r"pip install[^\n]*?(?:\\\n[^\n]*?)*?-r[ \t]+(\S+)", self.containerfile)
        self.assertIsNotNone(m, "the real Containerfile has no pip install -r")
        return m

    def test_containerfile_without_pip_requirements_fails_naming_it(self):
        m = self._pip_r()
        cf = self.tmp / "Containerfile.no-pip-r"
        cf.write_text(self.containerfile[:m.start(1) - 3] + self.containerfile[m.end(1):])
        self.assertNotIn(m.group(1), cf.read_text())
        p, j = run(["--packages-only"], {**self.env, "MIOS_CONTAINERFILE": str(cf)}, FEDORA)
        self.assertEqual(p.returncode, 1, p.stdout)
        d = step(j, "packages")["detail"]
        self.assertIn(f"no 'pip install -r <file>' in {cf} (MIOS_CONTAINERFILE)", d)
        self.assertIn("(no pip install -r line)", d)
        self.assertFalse(self.dlog.exists())

    def test_real_containerfile_requirements_map_to_the_mios_file(self):
        # Whatever form the real file uses, the detail names the MiOS requirements file.
        self._pip_r()
        p, j = run(["--plan", "--packages-only"], self.env, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(f"distributions of {self.reqs} installed", step(j, "packages")["detail"])

    def test_copy_form_maps_back_through_the_copy(self):
        m = self._pip_r()
        dest = "/tmp/mios-init-copy-form-requirements.txt"
        text = self.containerfile[:m.start(1)] + dest + self.containerfile[m.end(1):]
        first_run = text.index("\nRUN ")
        text = text[:first_run] + f"\nCOPY {REQS_REL} {dest}" + text[first_run:]
        cf = self.tmp / "Containerfile.copy-form"
        cf.write_text(text)
        p, j = run(["--plan", "--packages-only"], {**self.env, "MIOS_CONTAINERFILE": str(cf)}, FEDORA)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(f"distributions of {self.reqs} installed", step(j, "packages")["detail"])

    def test_negative_without_the_suffix_mapping_the_staged_form_fails(self):
        m = self._pip_r()
        if m.group(1).lstrip("/") == REQS_REL:
            self.skipTest("the real Containerfile gives pip the MiOS-relative path itself")
        script = copy_env_dir(self.tmp)
        mutate(script, '    _sfx=${_rp#/}\n', '    _sfx=nothing\n', self)
        p, j = run(["--plan", "--packages-only"], self.env, FEDORA, script=script)
        self.assertEqual(p.returncode, 1, p.stdout)
        d = step(j, "packages")["detail"]
        self.assertIn(f"pip is given {m.group(1)}; no COPY names it", d, "a parser without the suffix mapping cannot follow a staged path")

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
        self.assertIn(f"venv {self.VENV}", d["detail"])
        self.assertNotIn("cloud-fedora-setup", d["detail"])
        self.assertFalse((self.tmp / "cache").exists())


def wrapper_control_reason() -> str | None:
    if os.geteuid() != 0:
        return "not root: the runtime probe (dockerd) and the setup script need root"
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
    """The wrapper must be written for the runtime that holds the image -- on the missing-wrapper
    path (F1) and on the existing-wrapper path (G1) -- into FEDORA_WRAPPER_DIR (G5)."""
    PROTECTED = (Path("/usr/local/bin/mios-dev"), Path("/usr/local/bin/fedora"))
    NAME = "init-fix-test"
    # The lines a mutation restores to the finding's state.
    PASSTHROUGH = '      export FEDORA_RUNTIME="$1" FEDORA_PROVISION_HOST=0\n'
    RT_CHECK = '    [ "$WRAPPER_RT" = "$1" ] && return 0\n'
    MISMATCH_CHECK = '            if [ "$wrt" = "$rt" ]; then\n                record packages skipped 1'
    INSTALLED_CHECK = ('    if [ ! -x "$WRAPPER_DIR/$DC_NAME" ]; then\n'
                       '        WRAPPER_WHY="cloud-fedora-setup.sh --wrapper-only did not install $WRAPPER_DIR/$DC_NAME:')

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mios-init-wrapper."))
        self.protected = {p: file_sha(p) for p in self.PROTECTED}
        self.script_sha = file_sha(SCRIPT)
        ws = self.tmp / "ws"
        ws.mkdir()
        (ws / "MiOS").symlink_to(MIOS)
        self.wdir = self.tmp / "bin"
        self.wdir.mkdir()
        self.wrapper = self.wdir / self.NAME
        # FEDORA_RUNTIME=podman in the caller's environment (MiOS is podman-native, so a hook
        # or operator may well set it) while the image lives in docker: the wrapper-only call
        # must pass the runtime that HOLDS the image and override this, and the installed
        # wrapper's RUNTIME= line is what proves which one won.
        self.env = {"MIOS_WORKSPACES": str(ws), "MIOS_REPOS": "MiOS", "XDG_CACHE_HOME": str(self.tmp / "cache"),
                    "FEDORA_DEVCONTAINER_NAME": self.NAME, "FEDORA_IMAGE": "mios-dev:latest",
                    "FEDORA_WRAPPER_DIR": str(self.wdir), "FEDORA_BUILD_CTX": str(self.tmp / "ctx"),
                    "FEDORA_RUNTIME": "podman"}
        self.wlog = self.tmp / "cache" / "mios" / "mios-init-wrapper.log"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        self.assertEqual({p: file_sha(p) for p in self.PROTECTED}, self.protected, "a control wrote /usr/local/bin")
        self.assertFalse(Path("/usr/local/bin", self.NAME).exists(), "a control wrote /usr/local/bin")
        self.assertEqual(file_sha(SCRIPT), self.script_sha, "the real script changed")

    def _run(self, script, args=("--packages-only",)):
        p, j = run(list(args), self.env, script=script)
        wrapper = self.wrapper.read_text() if self.wrapper.exists() else ""
        m = re.search(r"^RUNTIME=(\S+)$", wrapper, re.M)
        return p, j, (m.group(1) if m else None)

    def _plant(self, text: str):
        self.wrapper.write_text(text)
        self.wrapper.chmod(0o755)

    def test_wrapper_is_written_for_the_runtime_holding_the_image(self):
        p, j, rt = self._run(SCRIPT)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "ok", d)
        self.assertEqual(rt, "docker", "the wrapper must name the runtime that holds mios-dev:latest")
        self.assertIn(f"installed {self.wrapper} for RUNTIME=docker", d["detail"])
        self.assertIn(f"(log {self.wlog})", d["detail"])
        self.assertEqual(j["runtime"], "docker")
        # G5: the wrapper (and its `fedora` twin) landed in FEDORA_WRAPPER_DIR, generated by the setup script
        self.assertIn("Generated by", self.wrapper.read_text())
        self.assertTrue((self.wdir / "fedora").is_file())

    @unittest.skipUnless(shutil.which("podman"), "podman not on PATH: auto would pick docker anyway")
    def test_negative_without_the_runtime_passthrough_the_step_fails(self):
        script = copy_env_dir(self.tmp)
        self.assertEqual(file_sha(script), self.script_sha, "the copy must be byte-identical before mutation")
        mutate(script, self.PASSTHROUGH, '      export FEDORA_PROVISION_HOST=0\n', self)
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
        mutate(script, self.PASSTHROUGH, '      export FEDORA_PROVISION_HOST=0\n', self)
        mutate(script, self.RT_CHECK, '    return 0\n', self)
        p, j, rt = self._run(script)
        self.assertEqual(rt, "podman")
        self.assertEqual(p.returncode, 0, "without the RUNTIME= check the wrong wrapper passes: the check is load-bearing")
        self.assertEqual(step(j, "packages")["status"], "ok")

    def test_stale_wrapper_is_rewritten_for_the_runtime_holding_the_image(self):
        # G1: the existing-wrapper path reads the wrapper's RUNTIME= line; a wrapper for the other
        # runtime, or one from a generation that wrote no such line, is rewritten.
        for planted, said in (("#!/bin/sh\nRUNTIME=podman\nexit 3\n", "RUNTIME=podman"),
                              ("#!/bin/sh\n# an older generation: no RUNTIME= line\nexit 3\n", "RUNTIME=<none>")):
            with self.subTest(planted=said):
                self._plant(planted)
                p, j, rt = self._run(SCRIPT)
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                d = step(j, "packages")
                self.assertEqual(d["status"], "ok", d)
                self.assertIn(f"{self.wrapper} said {said}: wrapper rewritten for docker", d["detail"])
                self.assertEqual(rt, "docker")
                self.assertIn("Generated by", self.wrapper.read_text(), "the planted stub must be replaced by the generated wrapper")
                self.assertEqual(j["runtime"], "docker")

    def test_stale_wrapper_plan_names_the_rewrite_and_changes_nothing(self):
        self._plant("#!/bin/sh\nRUNTIME=podman\nexit 3\n")
        before = file_sha(self.wrapper)
        p, j, rt = self._run(SCRIPT, ("--plan", "--packages-only"))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "planned", d)
        self.assertIn(f"{self.wrapper} says RUNTIME=podman; would run: FEDORA_RUNTIME=docker", d["detail"])
        self.assertEqual(file_sha(self.wrapper), before, "--plan rewrote the wrapper")
        self.assertEqual(rt, "podman")

    def test_matching_wrapper_is_left_alone(self):
        self._plant("#!/bin/sh\nRUNTIME=docker\nexit 3\n")
        before = file_sha(self.wrapper)
        p, j, rt = self._run(SCRIPT)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "skipped", d)
        self.assertIn(f"{self.wrapper} says RUNTIME=docker; enter it with {self.wrapper}", d["detail"])
        self.assertEqual(file_sha(self.wrapper), before, "a matching wrapper must be left byte-identical")

    def test_negative_without_the_mismatch_check_the_stale_wrapper_is_kept(self):
        # G1 reproduced: the check mutated away -> skipped/ok with the stale podman wrapper.
        script = copy_env_dir(self.tmp)
        mutate(script, self.MISMATCH_CHECK, '            if true; then\n                record packages skipped 1', self)
        self._plant("#!/bin/sh\nRUNTIME=podman\nexit 3\n")
        p, j, rt = self._run(script)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(step(j, "packages")["status"], "skipped")
        self.assertTrue(j["ok"])
        self.assertEqual(rt, "podman", "the stale wrapper survives when the RUNTIME= line is not read -- the finding")

    @unittest.skipUnless(shutil.which("podman"), "podman not on PATH: auto would pick docker anyway")
    def test_negative_stale_wrapper_whose_rewrite_still_disagrees_fails_naming_both(self):
        # G1's last clause: the rewrite went through (here: without the pass-through, so the
        # environment's podman won again) and the wrapper still disagrees -> failed, both named.
        script = copy_env_dir(self.tmp)
        mutate(script, self.PASSTHROUGH, '      export FEDORA_PROVISION_HOST=0\n', self)
        self._plant("#!/bin/sh\nRUNTIME=podman\nexit 3\n")
        p, j, rt = self._run(script)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "failed", d)
        self.assertIn("lives in docker", d["detail"])
        self.assertIn("said RUNTIME=podman and after a rewrite for docker", d["detail"])
        self.assertIn("says RUNTIME=podman, not docker", d["detail"])
        self.assertEqual(rt, "podman")
        self.assertIn("Generated by", self.wrapper.read_text(), "the rewrite did happen; it is its runtime that is wrong")

    def test_negative_hardcoded_wrapper_dir_fails_claiming_usr_local_bin(self):
        # G5: one /usr/local/bin restored in a copy -> the wrapper lands in FEDORA_WRAPPER_DIR but
        # the step fails claiming /usr/local/bin/<name> is missing.
        script = copy_env_dir(self.tmp)
        mutate(script, self.INSTALLED_CHECK, self.INSTALLED_CHECK.replace("$WRAPPER_DIR/$DC_NAME", "/usr/local/bin/$DC_NAME"), self)
        p, j, rt = self._run(script)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        d = step(j, "packages")
        self.assertEqual(d["status"], "failed", d)
        self.assertIn(f"did not install /usr/local/bin/{self.NAME}", d["detail"])
        self.assertEqual(rt, "docker", "the setup script honoured FEDORA_WRAPPER_DIR; only the hardcoded check missed it")


if __name__ == "__main__":
    unittest.main()
