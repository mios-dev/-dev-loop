#!/usr/bin/env python3
"""FEDORA_RUNTIME selection in cloud-fedora-setup.sh (MiOS is Podman-native).

Drives the REAL script with the REAL podman/docker binaries; the only thing a
test controls is PATH, which is how "podman is absent" is produced without
uninstalling anything. A case whose runtime is not installed is SKIPPED, never
passed.

Policy under test:
  auto   -> podman when on PATH, else docker
  podman / docker -> that runtime, or an error naming it (no silent fallback)
  anything else   -> an error naming the value
An error always ends in exit 0 (the setup-script contract) and builds nothing.

Manual control (heavy, needs ~1 min and network; run on demand):
  env -u FEDORA_DEVCONTAINER_REPO FEDORA_IMAGE=rt-test:44 FEDORA_CONTAINER=rt-test \
      FEDORA_RUNTIME=podman FEDORA_PROVISION_HOST=0 FEDORA_BUILD_CTX=<tmpdir> \
      bash skills/dev-loop/scripts/env/cloud-fedora-setup.sh
  -> "container runtime: podman" ... "ready: Fedora release 44"; the installed
  /usr/local/bin/fedora carries RUNTIME=podman and runs through `podman exec`.
  It overwrites /usr/local/bin/fedora: back it up first and restore it after,
  then `podman rm -f rt-test; podman rmi localhost/rt-test:44`.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "skills", "dev-loop", "scripts", "env", "cloud-fedora-setup.sh")
BASH = shutil.which("bash") or "/bin/bash"
# What the script needs before it reaches any runtime call.
TOOLS = ("dirname", "basename", "grep", "mkdir", "cp", "mv", "cat", "rm", "tr")


def run(args, path, extra=None):
    env = {"PATH": path, "HOME": os.environ.get("HOME", "/root"),
           "FEDORA_PROVISION_HOST": "0"}
    env.update(extra or {})
    return subprocess.run([BASH, SCRIPT] + args, env=env, capture_output=True,
                          text=True, timeout=60)


class RuntimeSelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rt-sel-")
        self.ctx = os.path.join(self.tmp, "ctx")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def bindir(self, *runtimes):
        """A PATH holding the script's tools plus exactly the named runtimes."""
        d = tempfile.mkdtemp(dir=self.tmp)
        for t in TOOLS + runtimes:
            src = shutil.which(t)
            if src is None:
                self.skipTest(f"{t} is not installed")
            os.symlink(src, os.path.join(d, t))
        return d

    def pick(self, value, path):
        r = run(["--print-runtime"], path, {"FEDORA_RUNTIME": value} if value else None)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def assert_refused(self, value, path, named):
        """Full run (not --print-runtime): error names it, exit 0, nothing built."""
        r = run([], path, {"FEDORA_RUNTIME": value, "FEDORA_BUILD_CTX": self.ctx,
                           "FEDORA_IMAGE": "rt-sel-never:0",
                           "FEDORA_CONTAINER": "rt-sel-never"})
        self.assertEqual(r.returncode, 0, "setup-script contract: always exit 0")
        self.assertIn(f"FEDORA_RUNTIME={value}", r.stdout)
        self.assertIn(named, r.stdout)
        self.assertIn("skipping Fedora provisioning", r.stdout)
        self.assertNotIn("container runtime:", r.stdout)
        self.assertNotIn("building", r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.ctx, "Dockerfile")),
                         "a refused runtime must not even write a build context")

    # --- positive ---------------------------------------------------------
    def test_auto_prefers_podman_when_present(self):
        if not shutil.which("podman"):
            self.skipTest("podman is not installed")
        self.assertEqual(self.pick(None, self.bindir("podman", "docker")
                                   if shutil.which("docker") else self.bindir("podman")),
                         "podman")

    def test_auto_takes_docker_when_podman_absent(self):
        if not shutil.which("docker"):
            self.skipTest("docker is not installed")
        self.assertEqual(self.pick("auto", self.bindir("docker")), "docker")

    def test_explicit_docker_honoured_even_with_podman_present(self):
        if not (shutil.which("docker") and shutil.which("podman")):
            self.skipTest("needs both docker and podman")
        self.assertEqual(self.pick("docker", self.bindir("podman", "docker")), "docker")

    def test_explicit_podman(self):
        if not shutil.which("podman"):
            self.skipTest("podman is not installed")
        self.assertEqual(self.pick("podman", self.bindir("podman")), "podman")

    # --- negative ---------------------------------------------------------
    def test_explicit_podman_missing_is_refused_not_swapped_for_docker(self):
        if not shutil.which("docker"):
            self.skipTest("docker is not installed (the fallback target)")
        path = self.bindir("docker")
        self.assertEqual(self.pick("podman", path), "")
        self.assert_refused("podman", path, "podman is not on PATH")

    def test_explicit_docker_missing_is_refused(self):
        path = self.bindir("podman") if shutil.which("podman") else self.bindir()
        self.assertEqual(self.pick("docker", path), "")
        self.assert_refused("docker", path, "docker is not on PATH")

    def test_bogus_value_is_refused(self):
        path = self.bindir(*[t for t in ("podman", "docker") if shutil.which(t)])
        self.assertEqual(self.pick("bogus", path), "")
        self.assert_refused("bogus", path, "not a supported runtime")

    def test_auto_with_no_runtime_is_refused(self):
        path = self.bindir()
        self.assertEqual(self.pick("auto", path), "")
        self.assert_refused("auto", path, "neither podman nor docker")


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


if __name__ == "__main__":
    unittest.main()
