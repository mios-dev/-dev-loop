#!/usr/bin/env python3
"""FEDORA_RUNTIME selection in cloud-fedora-setup.sh (MiOS is Podman-native),
FEDORA_WRAPPER_DIR, and the repo SessionStart hook's wrapper install.

Drives the REAL script, the REAL hook and the REAL podman/docker binaries; the
only things a test controls are PATH (how "podman is absent" is produced
without uninstalling anything), a stub `podman` that only exits 125 (how
"podman is on PATH but cannot run" is produced), and the image stores, into
which a layerless probe image is imported from an empty tar (no network) and
removed again. A case whose runtime is not installed is SKIPPED, never passed.
Negative controls run a MUTATED COPY of the script or hook and check the
original's sha256 is unchanged afterwards.

Policy under test:
  auto   -> with both installed: the runtime whose store already holds
            FEDORA_IMAGE; else the first one that can run here (podman info /
            dockerd up), the reason for a skip logged; else podman.
            With one installed: that one.
  podman / docker -> that runtime, or an error naming it: never a fallback,
            not when it is missing and not when it cannot run here
  anything else   -> an error naming the value
An error always ends in exit 0 (the setup-script contract) and builds nothing.

The hook installs the wrapper only when FEDORA_WRAPPER_DIR/fedora is absent:
the environment's own setup script may have installed one for another mode
or runtime, and a rewrite would make the next `fedora` call rebuild everything.

Manual control (heavy, needs ~1 min and network; run on demand):
  env -u FEDORA_DEVCONTAINER_REPO FEDORA_IMAGE=rt-test:44 FEDORA_CONTAINER=rt-test \
      FEDORA_RUNTIME=podman FEDORA_PROVISION_HOST=0 FEDORA_BUILD_CTX=<tmpdir> \
      FEDORA_WRAPPER_DIR=<tmpdir>/bin bash skills/dev-loop/scripts/env/cloud-fedora-setup.sh
  -> "container runtime: podman" ... "ready: Fedora release 44"; the installed
  <tmpdir>/bin/fedora carries RUNTIME=podman and runs through `podman exec`.
  Then `podman rm -f rt-test; podman rmi localhost/rt-test:44`.
"""
import hashlib
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "skills", "dev-loop", "scripts", "env", "cloud-fedora-setup.sh")
HOOK = os.path.join(REPO, ".claude", "hooks", "session-start.sh")
PLUGIN_HOOK = os.path.join(REPO, "hooks", "session-start.sh")
BASH = shutil.which("bash") or "/bin/bash"
# What the script needs before it reaches any runtime call, what install_wrapper
# needs (chmod), and what ensure_dockerd's wait loop needs (sleep).
TOOLS = ("dirname", "basename", "grep", "mkdir", "cp", "mv", "cat", "rm", "tr", "chmod", "sleep")
# Never a real image name: the "neither store holds it" case.
ABSENT = "absent-test:none"


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run(args, path, extra=None, script=SCRIPT):
    """The script under a controlled env. extra values of None unset a key."""
    env = {"PATH": path, "HOME": os.environ.get("HOME", "/root"),
           "FEDORA_PROVISION_HOST": "0", "FEDORA_IMAGE": ABSENT}
    for k, v in (extra or {}).items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    return subprocess.run([BASH, script] + args, env=env, capture_output=True,
                          text=True, timeout=120)


def installed(*runtimes):
    return all(shutil.which(r) for r in runtimes)


def store_holds(runtime, image):
    return subprocess.run([runtime, "image", "inspect", image], capture_output=True).returncode == 0


def setUpModule():
    """dockerd needs containerd/runc/iptables that the tests' minimal PATH
    hides, so if the daemon is down it is started ONCE here, through the
    script's own ensure_dockerd under the full PATH (an explicit docker pick
    followed by its usability check)."""
    if installed("docker") and subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        d = tempfile.mkdtemp(prefix="rt-mod-")
        try:
            run(["--wrapper-only"], os.environ["PATH"],
                {"FEDORA_RUNTIME": "docker", "FEDORA_WRAPPER_DIR": os.path.join(d, "bin"),
                 "FEDORA_BUILD_CTX": os.path.join(d, "ctx")})
        finally:
            shutil.rmtree(d, ignore_errors=True)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rt-sel-")
        self.ctx = os.path.join(self.tmp, "ctx")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def bindir(self, *runtimes):
        """A PATH holding the script's tools plus exactly the named runtimes
        (docker brings dockerd, which ensure_dockerd looks for)."""
        d = tempfile.mkdtemp(dir=self.tmp)
        names = TOOLS + runtimes + (("dockerd",) if "docker" in runtimes and shutil.which("dockerd") else ())
        for t in names:
            src = shutil.which(t)
            if src is None:
                self.skipTest(f"{t} is not installed")
            os.symlink(src, os.path.join(d, t))
        return d

    def stub_podman(self, d, code=125):
        """A podman that is on PATH but cannot run: it only exits with `code`
        (podman's own exit status for a failed command), for every argv."""
        p = os.path.join(d, "podman")
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"#!/bin/sh\nexit {code}\n")
        os.chmod(p, 0o755)
        return d

    def pick(self, value, path, extra=None, script=SCRIPT):
        e = dict(extra or {})
        if value:
            e["FEDORA_RUNTIME"] = value
        r = run(["--print-runtime"], path, e, script)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.last = r
        return r.stdout.strip()

    def mutated(self, src_path, old, new):
        """A copy of src_path with exactly one occurrence of `old` replaced."""
        with open(src_path, encoding="utf-8") as f:
            src = f.read()
        self.assertEqual(src.count(old), 1, f"mutation target not unique in {src_path}: {old!r}")
        p = os.path.join(self.tmp, "mutated-" + os.path.basename(src_path))
        with open(p, "w", encoding="utf-8") as f:
            f.write(src.replace(old, new))
        os.chmod(p, 0o755)
        return p

    def assert_refused(self, value, path, named, extra=None):
        """Full run (not --print-runtime): error names it, exit 0, nothing built."""
        e = {"FEDORA_RUNTIME": value, "FEDORA_BUILD_CTX": self.ctx,
             "FEDORA_IMAGE": "rt-sel-never:0", "FEDORA_CONTAINER": "rt-sel-never",
             "FEDORA_WRAPPER_DIR": os.path.join(self.tmp, "bin")}
        e.update(extra or {})
        r = run([], path, e)
        self.assertEqual(r.returncode, 0, "setup-script contract: always exit 0")
        self.assertIn(f"FEDORA_RUNTIME={value}", r.stdout)
        self.assertIn(named, r.stdout)
        self.assertIn("skipping Fedora provisioning", r.stdout)
        self.assertNotIn("container runtime:", r.stdout)
        self.assertNotIn("building", r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.ctx, "Dockerfile")),
                         "a refused runtime must not even write a build context")
        return r


class RuntimeSelection(Base):
    # --- positive ---------------------------------------------------------
    def test_auto_prefers_podman_when_neither_store_holds_the_image(self):
        if not installed("podman"):
            self.skipTest("podman is not installed")
        path = self.bindir("podman", "docker") if installed("docker") else self.bindir("podman")
        self.assertEqual(self.pick(None, path), "podman")
        self.assertNotIn("already lives in", self.last.stderr)

    def test_auto_takes_docker_when_podman_absent(self):
        if not installed("docker"):
            self.skipTest("docker is not installed")
        self.assertEqual(self.pick("auto", self.bindir("docker")), "docker")

    def test_explicit_docker_honoured_even_with_podman_present(self):
        if not installed("docker", "podman"):
            self.skipTest("needs both docker and podman")
        self.assertEqual(self.pick("docker", self.bindir("podman", "docker")), "docker")

    def test_explicit_podman(self):
        if not installed("podman"):
            self.skipTest("podman is not installed")
        self.assertEqual(self.pick("podman", self.bindir("podman")), "podman")

    # --- negative ---------------------------------------------------------
    def test_explicit_podman_missing_is_refused_not_swapped_for_docker(self):
        if not installed("docker"):
            self.skipTest("docker is not installed (the fallback target)")
        path = self.bindir("docker")
        self.assertEqual(self.pick("podman", path), "")
        self.assert_refused("podman", path, "podman is not on PATH")

    def test_explicit_docker_missing_is_refused(self):
        path = self.bindir("podman") if installed("podman") else self.bindir()
        self.assertEqual(self.pick("docker", path), "")
        self.assert_refused("docker", path, "docker is not on PATH")

    def test_bogus_value_is_refused(self):
        path = self.bindir(*[t for t in ("podman", "docker") if installed(t)])
        self.assertEqual(self.pick("bogus", path), "")
        self.assert_refused("bogus", path, "not a supported runtime")

    def test_auto_with_no_runtime_is_refused(self):
        path = self.bindir()
        self.assertEqual(self.pick("auto", path), "")
        self.assert_refused("auto", path, "neither podman nor docker")


class ImageHome(Base):
    """auto keeps an existing image where it is (R1). Each runtime has its
    own store: choosing the other one would rebuild from scratch and strand
    the image that exists."""

    HOME_CHECK = "if image_home; then"

    def setUp(self):
        super().setUp()
        self.tar = os.path.join(self.tmp, "empty.tar")
        with tarfile.open(self.tar, "w"):
            pass
        self.imported = []

    def tearDown(self):
        for runtime, tag in self.imported:
            subprocess.run([runtime, "rmi", "-f", tag], capture_output=True)
        super().tearDown()

    def probe_image(self, runtime):
        """A layerless image that exists in `runtime`'s store only."""
        tag = f"rt-home-{os.getpid()}:{runtime}"
        r = subprocess.run([runtime, "import", self.tar, tag], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.imported.append((runtime, tag))
        other = "docker" if runtime == "podman" else "podman"
        self.assertFalse(store_holds(other, tag), f"{tag} leaked into {other}'s store")
        return tag

    def both(self):
        if not installed("podman", "docker"):
            self.skipTest("needs both podman and docker")
        return self.bindir("podman", "docker")

    # --- positive ---------------------------------------------------------
    def test_image_in_docker_keeps_docker(self):
        path = self.both()
        tag = self.probe_image("docker")
        self.assertEqual(self.pick(None, path, {"FEDORA_IMAGE": tag}), "docker")
        self.assertIn(f"auto: {tag} already lives in docker -- keeping it there", self.last.stderr)

    def test_image_in_podman_keeps_podman(self):
        path = self.both()
        tag = self.probe_image("podman")
        self.assertEqual(self.pick(None, path, {"FEDORA_IMAGE": tag}), "podman")
        self.assertIn(f"auto: {tag} already lives in podman -- keeping it there", self.last.stderr)

    def test_image_in_neither_is_podman(self):
        path = self.both()
        self.assertEqual(self.pick(None, path, {"FEDORA_IMAGE": ABSENT}), "podman")
        self.assertNotIn("already lives in", self.last.stderr)

    def test_projection_defaults_on_a_vm_whose_image_is_in_docker(self):
        """The finding as reported: FEDORA_DEVCONTAINER_REPO=MiOS resolves
        FEDORA_IMAGE to mios-dev:latest, which this VM holds in docker only."""
        path = self.both()
        if not store_holds("docker", "mios-dev:latest") or store_holds("podman", "mios-dev:latest"):
            self.skipTest("mios-dev:latest is not docker-only on this host")
        self.assertEqual(self.pick(None, path, {"FEDORA_IMAGE": None,
                                                "FEDORA_DEVCONTAINER_REPO": "https://github.com/mios-dev/MiOS"}),
                         "docker")
        self.assertIn("mios-dev:latest already lives in docker", self.last.stderr)

    def test_explicit_runtime_ignores_the_image_home(self):
        path = self.both()
        tag = self.probe_image("docker")
        self.assertEqual(self.pick("podman", path, {"FEDORA_IMAGE": tag}), "podman")
        self.assertNotIn("already lives in", self.last.stderr)

    # --- negative ---------------------------------------------------------
    def test_without_the_home_check_auto_strands_the_docker_image(self):
        """Mutate the home check away: the same docker-only image now yields
        podman, the pre-fix behaviour the finding describes."""
        path = self.both()
        tag = self.probe_image("docker")
        before = sha256(SCRIPT)
        cut = self.mutated(SCRIPT, self.HOME_CHECK, "if false; then")
        self.assertEqual(self.pick(None, path, {"FEDORA_IMAGE": tag}, script=cut), "podman")
        self.assertNotIn("already lives in", self.last.stderr)
        self.assertEqual(sha256(SCRIPT), before, "the real script must be untouched")
        self.assertEqual(self.pick(None, path, {"FEDORA_IMAGE": tag}), "docker")


class Usability(Base):
    """auto picks a runtime that can run, not one that is merely on PATH (R2).
    Explicit runtimes still never fall back."""

    USABILITY_CHECK = 'runtime_usable "$r" && { RT=$r; return 0; }'
    WHY = "podman info failed -- podman cannot run here"

    def docker_plus_dead_podman(self):
        if not installed("docker"):
            self.skipTest("docker is not installed (the fall-through target)")
        return self.stub_podman(self.bindir("docker"))

    # --- positive ---------------------------------------------------------
    def test_auto_falls_through_to_docker_when_podman_cannot_run(self):
        path = self.docker_plus_dead_podman()
        self.assertEqual(self.pick(None, path), "docker")
        self.assertIn(f"auto: {self.WHY} -- falling through to the next installed runtime", self.last.stderr)

    def test_auto_installs_a_docker_wrapper_when_podman_cannot_run(self):
        """--wrapper-only is what the hook runs: the baked RUNTIME must be the
        one that works, or the first `fedora` call dies on the dead podman."""
        path = self.docker_plus_dead_podman()
        wd = os.path.join(self.tmp, "bin")
        r = run(["--wrapper-only"], path, {"FEDORA_BUILD_CTX": self.ctx, "FEDORA_WRAPPER_DIR": wd})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(self.WHY, r.stdout)
        with open(os.path.join(wd, "fedora"), encoding="utf-8") as f:
            self.assertIn("\nRUNTIME=docker\n", f.read())

    # --- negative ---------------------------------------------------------
    def test_explicit_podman_that_cannot_run_is_refused_not_swapped(self):
        path = self.docker_plus_dead_podman()
        self.assertEqual(self.pick("podman", path), "podman", "selection is by PATH; the refusal comes at use")
        r = self.assert_refused("podman", path, "refusing to fall back to another runtime")
        self.assertIn(self.WHY, r.stdout)

    def test_without_the_usability_check_auto_picks_the_dead_podman(self):
        path = self.docker_plus_dead_podman()
        before = sha256(SCRIPT)
        cut = self.mutated(SCRIPT, self.USABILITY_CHECK, "{ RT=$r; return 0; }")
        self.assertEqual(self.pick(None, path, script=cut), "podman")
        self.assertEqual(sha256(SCRIPT), before, "the real script must be untouched")
        self.assertEqual(self.pick(None, path), "docker")


class WrapperDir(Base):
    """FEDORA_WRAPPER_DIR moves every wrapper write (R3, script side)."""

    def test_wrapper_lands_in_the_dir_and_bakes_it(self):
        path = self.bindir(*[t for t in ("podman", "docker") if installed(t)])
        if not (installed("podman") or installed("docker")):
            self.skipTest("no container runtime installed")
        wd = os.path.join(self.tmp, "bin")
        system = "/usr/local/bin/fedora"
        before = sha256(system) if os.path.exists(system) else None
        r = run(["--wrapper-only"], path, {"FEDORA_BUILD_CTX": self.ctx, "FEDORA_WRAPPER_DIR": wd})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"installed fedora in {wd}", r.stdout)
        w = os.path.join(wd, "fedora")
        self.assertTrue(os.stat(w).st_mode & stat.S_IXUSR)
        with open(w, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("\nRUNTIME=" + self.pick(None, path) + "\n", src)
        self.assertIn(f"FEDORA_WRAPPER_DIR={wd}", src, "an on-demand build must verify the same wrapper")
        if before is not None:
            self.assertEqual(sha256(system), before, "the system wrapper must be untouched")


class Hook(Base):
    """The repo SessionStart hook installs the wrapper only when none exists
    (R3, hook side). It is run for real, so it also runs setup-antigravity.sh
    --quiet (idempotent, ~2s with agy present; without agy it would install it
    over the network, so the case is skipped there)."""

    GUARD = 'if [ ! -e "$WRAPPER_DIR/fedora" ]; then'
    SENTINEL = "#!/bin/sh\necho sentinel wrapper, installed by the environment\n"

    def setUp(self):
        super().setUp()
        if not os.access(os.path.join(os.environ.get("HOME", "/root"), ".local", "bin", "agy"), os.X_OK):
            self.skipTest("agy is not installed: the hook would provision it over the network")
        if not (installed("podman") or installed("docker")):
            self.skipTest("no container runtime installed")
        self.wd = os.path.join(self.tmp, "bin")
        os.makedirs(self.wd)

    def hook_env(self):
        # The session's own FEDORA_* would make the mode depend on the host.
        env = {k: v for k, v in os.environ.items() if not k.startswith("FEDORA_")}
        env.update({"CLAUDE_CODE_REMOTE": "true", "CLAUDE_PROJECT_DIR": REPO,
                    "FEDORA_WRAPPER_DIR": self.wd, "FEDORA_BUILD_CTX": self.ctx,
                    "FEDORA_IMAGE": ABSENT})
        return env

    def run_hook(self, hook=HOOK):
        r = subprocess.run([BASH, hook], env=self.hook_env(), capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def plant(self):
        p = os.path.join(self.wd, "fedora")
        with open(p, "w", encoding="utf-8") as f:
            f.write(self.SENTINEL)
        os.chmod(p, 0o755)
        return p, sha256(p)

    # --- positive ---------------------------------------------------------
    def test_existing_wrapper_is_untouched(self):
        p, before = self.plant()
        r = self.run_hook()
        self.assertEqual(sha256(p), before, "the hook rewrote an existing wrapper")
        self.assertNotIn("installed fedora", r.stdout)

    def test_absent_wrapper_is_installed(self):
        r = self.run_hook()
        p = os.path.join(self.wd, "fedora")
        self.assertTrue(os.path.exists(p), r.stdout)
        with open(p, encoding="utf-8") as f:
            self.assertIn("\nRUNTIME=", f.read())
        self.assertIn(f"installed fedora in {self.wd}", r.stdout)

    def test_plugin_hook_never_installs_the_wrapper(self):
        """hooks/session-start.sh (the plugin hook) only revives the keyring;
        if it ever called --wrapper-only it would need the same guard."""
        with open(PLUGIN_HOOK, encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("--wrapper-only", src)
        self.assertNotIn("cloud-fedora-setup", src)

    # --- negative ---------------------------------------------------------
    def test_without_the_guard_the_hook_clobbers_the_wrapper(self):
        p, before = self.plant()
        hook_before = sha256(HOOK)
        cut = self.mutated(HOOK, self.GUARD, "if true; then")
        self.run_hook(cut)
        self.assertNotEqual(sha256(p), before, "the unguarded hook should have rewritten the wrapper")
        with open(p, encoding="utf-8") as f:
            self.assertIn("\nRUNTIME=", f.read())
        self.assertEqual(sha256(HOOK), hook_before, "the real hook must be untouched")


class NoHardwiredDocker(unittest.TestCase):
    """Every container call goes through the chosen runtime ($RT, or $RUNTIME
    in the generated wrapper); `docker` survives only in the dockerd starter."""

    CALL = re.compile(r"(?<![\w/.-])docker\s+(pull|tag|build|image|run|exec|"
                      r"commit|rm|start|inspect)\b")

    def test_no_bare_docker_subcommand(self):
        bad = []
        with open(SCRIPT, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if line.lstrip().startswith("#"):
                    continue
                if self.CALL.search(line):
                    bad.append(f"{n}: {line.rstrip()}")
        self.assertEqual(bad, [], "hard-wired docker calls:\n" + "\n".join(bad))

    def test_devcontainers_cli_gets_docker_path_for_podman(self):
        with open(SCRIPT, encoding="utf-8") as f:
            src = f.read()
        self.assertRegex(src, r'\[ "\$RT" = podman \] && set -- "\$@" --docker-path podman')

    def test_wrapper_bakes_runtime(self):
        with open(SCRIPT, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("printf 'RUNTIME=%q\\n' \"$RT\"", src)
        self.assertIn('FEDORA_RUNTIME="$RUNTIME"', src)

    def test_no_hardwired_wrapper_dir(self):
        """Every wrapper path goes through $WRAPPER_DIR (FEDORA_WRAPPER_DIR)."""
        bad = []
        with open(SCRIPT, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if line.lstrip().startswith("#") or "WRAPPER_DIR=" in line:
                    continue
                if "/usr/local/bin" in line:
                    bad.append(f"{n}: {line.rstrip()}")
        self.assertEqual(bad, [], "hard-wired wrapper dir:\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
