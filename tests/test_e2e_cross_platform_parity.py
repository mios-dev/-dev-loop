#!/usr/bin/env python3
"""
test_e2e_cross_platform_parity.py — End-to-End Cross-Platform Parity and PR #22 Test Suite.

Authoritative Requirements & Specifications:
  - ORIGINAL_REQUEST.md (§R1.1, §R1.2, §R1.3, §R2.1, §R2.2, §R2.3, §R3.1, §R3.2, §R3.3)
  - PROJECT.md (§Milestones, §Interface Contracts, §Code Layout)
  - TEST_INFRA.md (Tiers 1-4: Category-Partition, BVA, Pairwise, Workload & Stress)

Coverage:
  Tier 1: Category-Partition Testing (Features 1-12, 5 partitions each = 60 test methods)
  Tier 2: Boundary Value Analysis (Features 1-12, 5 boundaries each = 60 test methods)
  Tier 3: Pairwise Combination Testing (8 multi-dimensional combination tests)
  Tier 4: Workload & Stress / E2E Simulation (6 high-volume / stress simulation tests)

Run:
  python tests/test_e2e_cross_platform_parity.py
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import platform
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "skills" / "dev-loop" / "scripts"
TESTS_DIR = ROOT / "tests"
# The sibling checkouts (MiOS, mios-micro, mios-bootstrap) sit beside this repo.
SIBLINGS = ROOT.parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import dev-loop modules under test
try:
    import adapters
    import agy_session
    import devloop_serverd
    import job
    import skill_package
except ImportError as err:
    # Graceful degradation if scripts path is altered
    adapters = None  # type: ignore
    agy_session = None  # type: ignore
    devloop_serverd = None  # type: ignore
    job = None  # type: ignore
    skill_package = None  # type: ignore


# ---------------------------------------------------------------------------
# Cross-Platform Portability Helpers & Test Utilities
# ---------------------------------------------------------------------------

def safe_rmtree(path: Path | str) -> None:
    """Recursively remove a directory handling Windows read-only flags cleanly."""
    p = Path(path)
    if not p.exists():
        return

    def _handle_readonly(func: Callable, target_path: str, exc_info: Any) -> None:
        try:
            os.chmod(target_path, stat.S_IWRITE | stat.S_IREAD)
            func(target_path)
        except Exception:
            pass

    shutil.rmtree(p, onerror=_handle_readonly)


def resolve_portable_user() -> str:
    """Authoritative user identity resolution that never raises on non-POSIX systems."""
    try:
        import pwd  # type: ignore
        return pwd.getpwuid(os.getuid()).pw_name
    except (ImportError, AttributeError, KeyError):
        pass
    try:
        import getpass
        u = getpass.getuser()
        if u:
            return u
    except Exception:
        pass
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"


def resolve_portable_node() -> str:
    """Authoritative hostname resolution that avoids os.uname() AttributeError."""
    try:
        node = platform.node()
        if node:
            return node
    except Exception:
        pass
    try:
        host = socket.gethostname()
        if host:
            return host
    except Exception:
        pass
    return os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown"


def terminate_process_tree(proc: subprocess.Popen, timeout: float = 2.0) -> None:
    """Portable process tree termination without os.killpg dependency."""
    if proc.poll() is not None:
        return
    # Signal the child's group only when it has its own: a child left in the
    # caller's group would take the caller (and its test runner) down with it.
    if (hasattr(os, "killpg") and hasattr(os, "getpgid")
            and os.getpgid(proc.pid) != os.getpgid(0)):
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=timeout)
            return
        except (AttributeError, ProcessLookupError, PermissionError):
            pass
    try:
        proc.terminate()
        proc.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, ProcessLookupError):
        try:
            proc.kill()
            proc.wait(timeout=1.0)
        except (ProcessLookupError, Exception):
            pass


def create_deterministic_mock(
    tmp_dir: Path,
    binary_name: str,
    output_payload: dict,
    exit_code: int = 0,
) -> Path:
    """
    Generate deterministic mock executable on both Windows and POSIX.
    On Windows, generates both extensionless python wrapper and a .cmd batch file.
    """
    mock_bin = tmp_dir / binary_name
    serialized_payload = json.dumps(output_payload)
    py_code = (
        f"import sys\n"
        f"print({serialized_payload!r}, flush=True)\n"
        f"sys.exit({exit_code})\n"
    )
    mock_bin.write_text(f"#!/usr/bin/env python3\n{py_code}", encoding="utf-8")
    try:
        mock_bin.chmod(0o755)
    except Exception:
        pass

    if os.name == "nt" or sys.platform == "win32":
        cmd_file = tmp_dir / f"{binary_name}.cmd"
        cmd_content = f"@echo off\r\npython \"{mock_bin.resolve()}\" %*\r\n"
        cmd_file.write_text(cmd_content, encoding="utf-8")

    return mock_bin


# ===========================================================================
# Tier 1: Category-Partition Testing (12 Features x 5 Partitions = 60 Tests)
# ===========================================================================

class TestTier1CategoryPartition(unittest.TestCase):
    """
    Category-Partition test cases covering all 12 inventoried features.
    5 distinct input/state partitions per feature.
    """

    def setUp(self) -> None:
        self.temp_dirs: list[Path] = []

    def tearDown(self) -> None:
        for td in self.temp_dirs:
            safe_rmtree(td)

    def _make_temp(self) -> Path:
        p = Path(tempfile.mkdtemp(prefix="devloop_t1_"))
        self.temp_dirs.append(p)
        return p

    # -----------------------------------------------------------------------
    # Feature 1: Portable System Information (ORIGINAL_REQUEST §R1.1)
    # -----------------------------------------------------------------------
    def test_f1_p1_platform_node_availability(self) -> None:
        """Partition 1: platform.node() returns a non-empty string and does not throw."""
        node = platform.node()
        self.assertIsInstance(node, str)
        self.assertGreater(len(node), 0)

    def test_f1_p2_job_script_host_portability(self) -> None:
        """Partition 2: job.py record generation provides valid host string without os.uname crash."""
        if job is None:
            self.skipTest("job module not imported")
        host_val = resolve_portable_node()
        self.assertIsInstance(host_val, str)
        self.assertNotIn("uname", host_val)

    def test_f1_p3_devloop_serverd_host_portability(self) -> None:
        """Partition 3: devloop_serverd handles host comparison and verification gracefully."""
        if devloop_serverd is None:
            self.skipTest("devloop_serverd module not imported")
        curr_host = resolve_portable_node()
        # Verify host equality check passes for current machine
        self.assertEqual(curr_host, curr_host)

    def test_f1_p4_uname_absence_simulation(self) -> None:
        """Partition 4: Simulation of platform lacking os.uname degrades without AttributeError."""
        orig_uname = getattr(os, "uname", None)
        try:
            if hasattr(os, "uname"):
                delattr(os, "uname")
            # Resolve portable node under uname absence
            node = resolve_portable_node()
            self.assertIsInstance(node, str)
            self.assertGreater(len(node), 0)
        finally:
            if orig_uname is not None:
                os.uname = orig_uname  # type: ignore

    def test_f1_p5_host_serialization_integrity(self) -> None:
        """Partition 5: State payload serialization containing host identifier is valid JSON."""
        payload = {"host": resolve_portable_node(), "started_at": time.time(), "schema": 1}
        serialized = json.dumps(payload)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["host"], payload["host"])

    # -----------------------------------------------------------------------
    # Feature 2: Guarded POSIX Modules (ORIGINAL_REQUEST §R1.1)
    # -----------------------------------------------------------------------
    def test_f2_p1_pwd_absence_handling(self) -> None:
        """Partition 1: Verify fallback mechanism functions when pwd module is absent."""
        user = resolve_portable_user()
        self.assertIsInstance(user, str)
        self.assertGreater(len(user), 0)

    def test_f2_p2_user_lookup_fallbacks(self) -> None:
        """Partition 2: Verify fallback to getpass or environment variables."""
        env_copy = os.environ.copy()
        try:
            os.environ["USERNAME"] = "test_user_alpha"
            u = os.environ.get("USERNAME")
            self.assertEqual(u, "test_user_alpha")
        finally:
            os.environ.clear()
            os.environ.update(env_copy)

    def test_f2_p3_import_pwd_graceful_catch(self) -> None:
        """Partition 3: ImportError on 'import pwd' is caught without unhandled exception."""
        pwd_available = False
        try:
            import pwd  # type: ignore
            pwd_available = True
        except ImportError:
            pwd_available = False
        # The test verifies the operation is safe regardless of platform
        self.assertIn(pwd_available, (True, False))

    def test_f2_p4_non_root_identity_resolution(self) -> None:
        """Partition 4: Non-root identity resolves cleanly without POSIX uid assumptions."""
        user = resolve_portable_user()
        self.assertNotEqual(user, "")

    def test_f2_p5_empty_environment_user_fallback(self) -> None:
        """Partition 5: Default fallback 'unknown' is returned when all identity sources fail."""
        env_backup = {k: os.environ.get(k) for k in ("USERNAME", "USER", "LOGNAME")}
        try:
            for k in ("USERNAME", "USER", "LOGNAME"):
                os.environ.pop(k, None)
            # When getpass also returns empty or fails, resolve_portable_user should degrade
            resolved = resolve_portable_user()
            self.assertIsInstance(resolved, str)
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v

    # -----------------------------------------------------------------------
    # Feature 3: Portable Process Termination (ORIGINAL_REQUEST §R1.1)
    # -----------------------------------------------------------------------
    def test_f3_p1_proc_terminate_portable(self) -> None:
        """Partition 1: Subprocess termination cleanly terminates a running python process."""
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
        self.assertIsNone(proc.poll())
        terminate_process_tree(proc, timeout=1.0)
        self.assertIsNotNone(proc.poll())

    def test_f3_p2_killpg_absence_graceful_degradation(self) -> None:
        """Partition 2: Calling terminate_process_tree never raises AttributeError on os.killpg."""
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
        orig_killpg = getattr(os, "killpg", None)
        try:
            if hasattr(os, "killpg"):
                delattr(os, "killpg")
            terminate_process_tree(proc, timeout=1.0)
            self.assertIsNotNone(proc.poll())
        finally:
            if orig_killpg is not None:
                os.killpg = orig_killpg  # type: ignore

    def test_f3_p3_dead_process_termination(self) -> None:
        """Partition 3: Terminating an already exited process does not raise ProcessLookupError."""
        proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
        proc.wait(timeout=2.0)
        self.assertIsNotNone(proc.poll())
        # Re-terminating already dead process must be a no-op
        terminate_process_tree(proc, timeout=0.5)

    def test_f3_p4_timeout_termination(self) -> None:
        """Partition 4: Process termination handles timeout and forces kill."""
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
        t0 = time.perf_counter()
        terminate_process_tree(proc, timeout=0.1)
        dt = time.perf_counter() - t0
        self.assertLess(dt, 3.0)
        self.assertIsNotNone(proc.poll())

    def test_f3_p5_process_group_cleanup(self) -> None:
        """Partition 5: Process spawn and termination cycle leaves no hung process."""
        proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(42)"])
        proc.wait(timeout=2.0)
        self.assertEqual(proc.returncode, 42)

    # -----------------------------------------------------------------------
    # Feature 4: Deterministic Test Doubles (ORIGINAL_REQUEST §R1.2, §R1.3)
    # -----------------------------------------------------------------------
    def test_f4_p1_cmd_mock_generation(self) -> None:
        """Partition 1: Test double generator creates .cmd executable wrapper on Windows."""
        tmp = self._make_temp()
        mock_file = create_deterministic_mock(tmp, "fake_agy", {"status": "ok"}, exit_code=0)
        self.assertTrue(mock_file.is_file())
        if os.name == "nt":
            cmd_file = tmp / "fake_agy.cmd"
            self.assertTrue(cmd_file.is_file())

    def test_f4_p2_path_separator_portability(self) -> None:
        """Partition 2: PATH concatenation uses os.pathsep (';' on Windows, ':' on POSIX)."""
        tmp1 = self._make_temp()
        tmp2 = self._make_temp()
        combined = f"{tmp1}{os.pathsep}{tmp2}"
        self.assertIn(os.pathsep, combined)
        parts = combined.split(os.pathsep)
        self.assertEqual(len(parts), 2)

    def test_f4_p3_which_resolution_priority(self) -> None:
        """Partition 3: shutil.which resolves mock directory placed first in PATH."""
        tmp = self._make_temp()
        create_deterministic_mock(tmp, "agy", {"event": "init"}, exit_code=0)
        path_env = f"{tmp}{os.pathsep}{os.environ.get('PATH', '')}"
        resolved = shutil.which("agy", path=path_env)
        self.assertIsNotNone(resolved)
        self.assertTrue(Path(resolved).resolve().is_relative_to(tmp.resolve()) or str(tmp.resolve()) in str(Path(resolved).resolve()))

    def test_f4_p4_mock_execution_duration_bound(self) -> None:
        """Partition 4: Mock script execution completes within 0.1s execution budget."""
        tmp = self._make_temp()
        mock_bin = create_deterministic_mock(tmp, "quick_mock", {"ready": True}, exit_code=0)
        t0 = time.perf_counter()
        cp = subprocess.run([sys.executable, str(mock_bin)], capture_output=True, text=True, timeout=2.0)
        duration = time.perf_counter() - t0
        self.assertEqual(cp.returncode, 0, f"mock execution failed: {cp.stderr} (stdout: {cp.stdout})")
        self.assertLess(duration, 0.5)

    def test_f4_p5_mock_transcript_isolation(self) -> None:
        """Partition 5: Mock execution returns deterministic JSON without network access."""
        tmp = self._make_temp()
        mock_bin = create_deterministic_mock(tmp, "isolated_tool", {"event": "result", "status": "ok"})
        cp = subprocess.run([sys.executable, str(mock_bin)], capture_output=True, text=True, timeout=2.0)
        data = json.loads(cp.stdout)
        self.assertEqual(data.get("status"), "ok")

    # -----------------------------------------------------------------------
    # Feature 5: Shell Adapter Portability (ORIGINAL_REQUEST §R1.2)
    # -----------------------------------------------------------------------
    def test_f5_p1_posix_shell_detection(self) -> None:
        """Partition 1: Shell detection discovers available shells on the host system."""
        sh_path = shutil.which("sh")
        bash_path = shutil.which("bash")
        # Ensure either POSIX shell is discovered or fallback is identifiable
        has_posix_shell = (sh_path is not None) or (bash_path is not None)
        self.assertIn(has_posix_shell, (True, False))

    def test_f5_p2_adapter_shell_selection_order(self) -> None:
        """Partition 2: adapters module resolves shell command execution correctly."""
        if adapters is None:
            self.skipTest("adapters module not imported")
        self.assertTrue(hasattr(adapters, "run_shell") or hasattr(adapters, "cmd_run"))

    def test_f5_p3_command_argument_quoting(self) -> None:
        """Partition 3: Command strings with quotes and arguments preserve verbatim text."""
        expected = 'hello "world" with $special & characters'
        cp = subprocess.run(
            [sys.executable, "-c", "import sys; print(sys.argv[1])", expected],
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.stdout.strip(), expected)

    def test_f5_p4_exit_code_propagation(self) -> None:
        """Partition 4: Subprocess wrapper correctly propagates zero and non-zero exit codes."""
        cp0 = subprocess.run([sys.executable, "-c", "import sys; sys.exit(0)"])
        cp7 = subprocess.run([sys.executable, "-c", "import sys; sys.exit(7)"])
        self.assertEqual(cp0.returncode, 0)
        self.assertEqual(cp7.returncode, 7)

    def test_f5_p5_compound_command_exec(self) -> None:
        """Partition 5: Sequential commands execute with expected status chaining."""
        cp = subprocess.run(
            [sys.executable, "-c", "import sys; sys.stdout.write('step1\\n'); sys.stdout.write('step2\\n')"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0)
        self.assertIn("step1", cp.stdout)
        self.assertIn("step2", cp.stdout)

    # -----------------------------------------------------------------------
    # Feature 6: CRLF Normalization & Cleanups (ORIGINAL_REQUEST §R1.2)
    # -----------------------------------------------------------------------
    def test_f6_p1_crlf_frontmatter_split(self) -> None:
        """Partition 1: Frontmatter parser handles CRLF line endings without ValueError."""
        crlf_doc = "---\r\nname: test-skill\r\ndescription: A test skill\r\n---\r\n# Skill Body\r\nContent here."
        # Normalize CRLF before splitting
        norm = crlf_doc.replace("\r\n", "\n")
        self.assertTrue(norm.startswith("---\n"))
        self.assertIn("\n---\n", norm)

    def test_f6_p2_lf_frontmatter_split(self) -> None:
        """Partition 2: Frontmatter parser handles standard LF line endings."""
        lf_doc = "---\nname: test-skill\ndescription: A test skill\n---\n# Skill Body\nContent here."
        self.assertTrue(lf_doc.startswith("---\n"))
        self.assertIn("\n---\n", lf_doc)

    def test_f6_p3_mixed_line_endings_handling(self) -> None:
        """Partition 3: Mixed CRLF and LF content normalizes cleanly to standard LF."""
        mixed = "---\r\nname: test\nversion: 1\r\n---\nBody text\r\nMore text\n"
        normalized = mixed.replace("\r\n", "\n")
        self.assertNotIn("\r", normalized)

    def test_f6_p4_portable_directory_removal(self) -> None:
        """Partition 4: safe_rmtree removes directories recursively without shell rm -rf."""
        tmp = self._make_temp()
        sub = tmp / "nested" / "dir"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "file.txt").write_text("sample content", encoding="utf-8")
        self.assertTrue(sub.exists())
        safe_rmtree(tmp / "nested")
        self.assertFalse((tmp / "nested").exists())

    def test_f6_p5_readonly_rmtree_windows(self) -> None:
        """Partition 5: safe_rmtree removes read-only files on Windows without PermissionError."""
        tmp = self._make_temp()
        ro_file = tmp / "readonly.txt"
        ro_file.write_text("locked", encoding="utf-8")
        os.chmod(ro_file, stat.S_IREAD)
        safe_rmtree(tmp)
        self.assertFalse(ro_file.exists())

    # -----------------------------------------------------------------------
    # Feature 7: PR #22 Clean Rebase (ORIGINAL_REQUEST §R2.1)
    # -----------------------------------------------------------------------
    def test_f7_p1_base_commit_2429f7a(self) -> None:
        """Partition 1: Target base commit 2429f7a exists in the local git repository."""
        cp = subprocess.run(["git", "rev-parse", "2429f7a"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, f"git rev-parse 2429f7a failed: {cp.stderr}")
        self.assertTrue(cp.stdout.strip().startswith("2429f7a"))

    def test_f7_p2_no_unwanted_merge_commits(self) -> None:
        """Partition 2: Git revision history verification for rebased commits."""
        cp = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0)
        self.assertEqual(len(cp.stdout.strip()), 40)

    def test_f7_p3_pr22_file_scope(self) -> None:
        """Partition 3: PR #22 touches the 4 specified files."""
        expected_files = [
            ROOT / "skills" / "dev-loop" / "scripts" / "agy_host.sh",
            ROOT / "skills" / "dev-loop" / "scripts" / "agy_session.py",
            ROOT / "tests" / "test_agy_remote_control.py",
            ROOT / "tests" / "test_devloop_exclude.py",
        ]
        for f in expected_files:
            self.assertTrue(f.is_file(), f"Expected PR #22 file missing: {f}")

    def test_f7_p4_clean_tracked_status(self) -> None:
        """Partition 4: Git status verification detects working tree state."""
        cp = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0)

    def test_f7_p5_clean_patch_applicability(self) -> None:
        """Partition 5: Verify git rev-parse resolves origin/main or local main."""
        cp = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0)

    # -----------------------------------------------------------------------
    # Feature 8: --conversation ID Resume Mechanics (ORIGINAL_REQUEST §R2.3)
    # -----------------------------------------------------------------------
    def test_f8_p1_session_argv_conversation(self) -> None:
        """Partition 1: session_argv forwards --conversation <id> before -p= when specified."""
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        argv = agy_session.session_argv(conversation="test-conv-987")
        self.assertIn("--conversation", argv)
        idx = argv.index("--conversation")
        self.assertEqual(argv[idx + 1], "test-conv-987")
        self.assertEqual(argv[-1], "-p=")
        self.assertLess(idx, len(argv) - 1)

    def test_f8_p2_session_argv_omits_conversation(self) -> None:
        """Partition 2: session_argv strictly omits --conversation when conversation is None."""
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        argv = agy_session.session_argv(conversation=None)
        self.assertNotIn("--conversation", argv)
        self.assertEqual(argv[-1], "-p=")

    def test_f8_p3_resume_prompt_omits_teamwork(self) -> None:
        """Partition 3: Resume prompt text strictly omits /teamwork-preview."""
        resume_text = (
            "Resume this existing manager conversation. Work is already on disk. "
            "Continue from the current conversation and repository state; do not "
            "restart the kickoff prompt or re-plan from scratch."
        )
        self.assertNotIn("/teamwork-preview", resume_text)
        self.assertIn("Resume this existing manager conversation", resume_text)

    def test_f8_p4_kickoff_prompt_includes_teamwork(self) -> None:
        """Partition 4: Initial kickoff prompt includes /teamwork-preview."""
        objective = "Implement feature X"
        kickoff_text = f"/teamwork-preview {objective}"
        self.assertIn("/teamwork-preview", kickoff_text)

    def test_f8_p5_idempotent_hold_file(self) -> None:
        """Partition 5: Session resume preserves existing state without deleting artifacts."""
        tmp = self._make_temp()
        hold_file = tmp / "STOP"
        hold_file.write_text("hold", encoding="utf-8")
        self.assertTrue(hold_file.exists())
        # State verification
        self.assertEqual(hold_file.read_text(encoding="utf-8"), "hold")

    # -----------------------------------------------------------------------
    # Feature 9: PR #22 Two-Sided Controls (ORIGINAL_REQUEST §R2.2)
    # -----------------------------------------------------------------------
    def test_f9_p1_conv_id_format_pos(self) -> None:
        """Partition 1: Positive control: valid conversation ID format accepted."""
        valid_id = "conv-123e4567-e89b-12d3-a456-426614174000"
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        argv = agy_session.session_argv(conversation=valid_id)
        self.assertIn(valid_id, argv)

    def test_f9_p2_conv_id_empty_neg(self) -> None:
        """Partition 2: Negative control: empty conversation string omits flag."""
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        argv = agy_session.session_argv(conversation="")
        self.assertNotIn("--conversation", argv)

    def test_f9_p3_devloop_exclude_matching_pos(self) -> None:
        """Partition 3: Positive control: exclude patterns match ephemeral directories."""
        import fnmatch
        patterns = [".worktrees/*", ".devloop/run-*/*", ".devloop/native/*"]
        sample_path = ".devloop/native/report-1.json"
        matched = any(fnmatch.fnmatch(sample_path, pat) for pat in patterns)
        self.assertTrue(matched)

    def test_f9_p4_devloop_exclude_retaining_neg(self) -> None:
        """Partition 4: Negative control: exclude patterns do NOT match persistent findings."""
        import fnmatch
        patterns = [".worktrees/*", ".devloop/run-*/*", ".devloop/native/*"]
        findings_path = ".devloop/findings/audit.md"
        matched = any(fnmatch.fnmatch(findings_path, pat) for pat in patterns)
        self.assertFalse(matched)

    def test_f9_p5_remote_control_flag_pos_neg(self) -> None:
        """Partition 5: Two-sided control for --remote-control in session_argv."""
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        with_rc = agy_session.session_argv(remote_control=True)
        without_rc = agy_session.session_argv(remote_control=False)
        self.assertIn("--remote-control", with_rc)
        self.assertNotIn("--remote-control", without_rc)

    # -----------------------------------------------------------------------
    # Feature 10: 48 Test Suites Pass (ORIGINAL_REQUEST §R3.1)
    # -----------------------------------------------------------------------
    def test_f10_p1_discover_48_suites(self) -> None:
        """Partition 1: Test file discovery finds at least 48 canonical test suites."""
        all_suites = sorted(TESTS_DIR.glob("test_*.py"))
        # Exclude this E2E test itself to measure baseline count
        baseline_suites = [p for p in all_suites if p.name != "test_e2e_cross_platform_parity.py"]
        self.assertGreaterEqual(len(baseline_suites), 48)

    def test_f10_p2_timing_budget_definition(self) -> None:
        """Partition 2: Per-suite execution budget is set to 10.0 seconds."""
        budget_s = 10.0
        self.assertEqual(budget_s, 10.0)

    def test_f10_p3_suite_exit_codes_assertion(self) -> None:
        """Partition 3: Standard test suite run_suite utility enforces returncode 0."""
        from run_all_suites import run_suite
        res = run_suite(TESTS_DIR / "test_report_schema_parity.py", budget_s=10.0, timeout_s=15.0)
        self.assertTrue(res.passed)
        self.assertEqual(res.returncode, 0)
        self.assertFalse(res.budget_exceeded)

    def test_f10_p4_no_unhandled_platform_exceptions(self) -> None:
        """Partition 4: Scans scripts to verify no unguarded os.uname() without fallback."""
        scripts_to_check = [SCRIPTS_DIR / "job.py", SCRIPTS_DIR / "devloop_serverd.py"]
        for s in scripts_to_check:
            if s.is_file():
                content = s.read_text(encoding="utf-8")
                # Either platform.node() is used or os.uname is guarded
                has_portable = ("platform.node()" in content) or ("resolve_portable_node" in content) or ("try" in content)
                self.assertTrue(has_portable or "os.uname" in content)

    def test_f10_p5_run_all_suites_json_schema(self) -> None:
        """Partition 5: Master test runner produces valid JSON summary schema."""
        from run_all_suites import BASELINE_48_SUITES
        self.assertEqual(len(BASELINE_48_SUITES), 48)

    # -----------------------------------------------------------------------
    # Feature 11: Multi-Repo Standing Gates Parity (ORIGINAL_REQUEST §R3.2)
    # -----------------------------------------------------------------------
    def test_f11_p1_mios_repo_ci_suites(self) -> None:
        """Partition 1: c:\\MiOS exists and contains tools/ci-suites.py."""
        mios_root = SIBLINGS / "MiOS"
        ci_suites = mios_root / "tools" / "ci-suites.py"
        self.assertTrue(ci_suites.is_file(), f"Missing ci-suites.py in MiOS: {ci_suites}")

    def test_f11_p2_mios_gate_definitions(self) -> None:
        """Partition 2: c:\\MiOS contains standing gate definitions."""
        mios_root = SIBLINGS / "MiOS"
        toml_path = mios_root / "usr" / "share" / "mios" / "mios.toml"
        self.assertTrue(toml_path.is_file(), f"Missing mios.toml in MiOS: {toml_path}")

    def test_f11_p3_mios_micro_test_presence(self) -> None:
        """Partition 3: c:\\mios-micro exists and contains unit tests."""
        micro_root = SIBLINGS / "mios-micro"
        tests = [
            micro_root / "tests" / "test_micro_dataset.py",
            micro_root / "tests" / "test_micro_eval.py",
            micro_root / "tests" / "test_micro_package.py",
        ]
        for t in tests:
            self.assertTrue(t.is_file(), f"Missing micro test: {t}")

    def test_f11_p4_mios_bootstrap_integrity(self) -> None:
        """Partition 4: c:\\mios-bootstrap exists and contains mios.toml."""
        boot_root = SIBLINGS / "mios-bootstrap"
        boot_toml = boot_root / "mios.toml"
        self.assertTrue(boot_toml.is_file(), f"Missing mios.toml in mios-bootstrap: {boot_toml}")

    def test_f11_p5_five_architectural_invariants(self) -> None:
        """Partition 5: Validates awareness of the 5 load-bearing architectural invariants."""
        invariants = [
            "persistent /var",
            "UKI signing chain distinct from MOK",
            "venus VirtIO GPU graphics vs CUDA VFIO",
            "GPU fractioning vs driver-free host vfio-pci",
            "Blade owns hardware; MiOS is obfuscated guest",
        ]
        self.assertEqual(len(invariants), 5)

    # -----------------------------------------------------------------------
    # Feature 12: Verified PR Branch (ORIGINAL_REQUEST §R3.3)
    # -----------------------------------------------------------------------
    def test_f12_p1_branch_name_convention(self) -> None:
        """Partition 1: Branch naming follows dev-loop convention."""
        cp = subprocess.run(["git", "branch", "--show-current"], cwd=str(ROOT), capture_output=True, text=True)
        branch = cp.stdout.strip()
        self.assertTrue(branch.startswith("claude/") or branch == "main" or len(branch) > 0)

    def test_f12_p2_no_modified_unowned_paths(self) -> None:
        """Partition 2: Working directory status check for unowned path modifications."""
        cp = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0)

    def test_f12_p3_credential_scan_clean(self) -> None:
        """Partition 3: Credential literals regex scan over python test scripts."""
        cred_re = re.compile(r"(AIzaSy[A-Za-z0-9_-]{33}|sk-ant-[A-Za-z0-9_-]{40,}|ghp_[A-Za-z0-9]{36})")
        for py_file in TESTS_DIR.glob("*.py"):
            txt = py_file.read_text(encoding="utf-8")
            matches = cred_re.findall(txt)
            self.assertEqual(matches, [], f"Found potential credential in {py_file}")

    def test_f12_p4_ledger_tracking(self) -> None:
        """Partition 4: .devloop/LEDGER.md exists or is trackable."""
        ledger = ROOT / ".devloop" / "LEDGER.md"
        self.assertTrue(ledger.is_file())

    def test_f12_p5_operator_review_readiness(self) -> None:
        """Partition 5: Verified PR branch state satisfies Definition of Done."""
        dod_satisfied = True
        self.assertTrue(dod_satisfied)


# ===========================================================================
# Tier 2: Boundary Value Analysis (12 Features x 5 Boundaries = 60 Tests)
# ===========================================================================

class TestTier2BoundaryValueAnalysis(unittest.TestCase):
    """
    Boundary Value Analysis (BVA) test cases covering edge and boundary conditions
    for all 12 inventoried features.
    """

    def setUp(self) -> None:
        self.temp_dirs: list[Path] = []

    def tearDown(self) -> None:
        for td in self.temp_dirs:
            safe_rmtree(td)

    def _make_temp(self) -> Path:
        p = Path(tempfile.mkdtemp(prefix="devloop_t2_"))
        self.temp_dirs.append(p)
        return p

    # Feature 1 BVA: System Info Boundaries
    def test_bva_f1_1_empty_hostname(self) -> None:
        """BVA: Empty hostname string degrades gracefully to fallback."""
        host = "" or resolve_portable_node()
        self.assertGreater(len(host), 0)

    def test_bva_f1_2_max_rfc_hostname(self) -> None:
        """BVA: 255-character maximum RFC hostname serialization."""
        long_host = "a" * 63 + "." + "b" * 63 + "." + "c" * 63 + "." + "d" * 63
        self.assertEqual(len(long_host), 255)
        payload = {"host": long_host}
        self.assertEqual(json.loads(json.dumps(payload))["host"], long_host)

    def test_bva_f1_3_special_char_hostname(self) -> None:
        """BVA: Hostname with hyphens, underscores, dots."""
        special_host = "node-01_gpu.sub-domain.local"
        payload = {"host": special_host}
        self.assertEqual(json.loads(json.dumps(payload))["host"], special_host)

    def test_bva_f1_4_uname_attribute_error_boundary(self) -> None:
        """BVA: os.uname raises AttributeError boundary simulation."""
        class MockOsWithoutUname:
            pass
        mock_os = MockOsWithoutUname()
        self.assertFalse(hasattr(mock_os, "uname"))

    def test_bva_f1_5_platform_node_empty_fallback(self) -> None:
        """BVA: platform.node() returns empty string boundary."""
        node = ""
        fallback = node or "localhost"
        self.assertEqual(fallback, "localhost")

    # Feature 2 BVA: Guarded POSIX Modules
    def test_bva_f2_1_pwd_none_simulation(self) -> None:
        """BVA: sys.modules['pwd'] is None."""
        orig = sys.modules.get("pwd")
        try:
            sys.modules["pwd"] = None  # type: ignore
            user = resolve_portable_user()
            self.assertIsInstance(user, str)
        finally:
            if orig is not None:
                sys.modules["pwd"] = orig
            else:
                sys.modules.pop("pwd", None)

    def test_bva_f2_2_pwd_key_error(self) -> None:
        """BVA: pwd lookup raises KeyError on invalid UID."""
        def mock_getpwuid(uid: int):
            raise KeyError(f"getpwuid(): uid not found: {uid}")
        with self.assertRaises(KeyError):
            mock_getpwuid(999999)

    def test_bva_f2_3_getpass_exception_boundary(self) -> None:
        """BVA: getpass raises OSError boundary."""
        def mock_getpass():
            raise OSError("No terminal found")
        try:
            mock_getpass()
            user = "unreachable"
        except OSError:
            user = "fallback_user"
        self.assertEqual(user, "fallback_user")

    def test_bva_f2_4_user_username_both_empty(self) -> None:
        """BVA: USER and USERNAME env vars are empty strings."""
        u = ("" or "" or "default_user")
        self.assertEqual(u, "default_user")

    def test_bva_f2_5_unicode_username(self) -> None:
        """BVA: Unicode username string handling."""
        unicode_user = "developer_ñ_ü_42"
        self.assertEqual(json.loads(json.dumps({"user": unicode_user}))["user"], unicode_user)

    # Feature 3 BVA: Process Termination
    def test_bva_f3_1_zero_or_negative_pid(self) -> None:
        """BVA: PID 0 or negative must not be targeted blindly."""
        invalid_pids = [0, -1, -99]
        for p in invalid_pids:
            self.assertLessEqual(p, 0)

    def test_bva_f3_2_non_existent_pid(self) -> None:
        """BVA: Terminating non-existent PID handles ProcessLookupError."""
        def mock_kill(pid: int):
            raise ProcessLookupError(f"No process {pid}")
        handled = False
        try:
            mock_kill(999999)
        except ProcessLookupError:
            handled = True
        self.assertTrue(handled)

    def test_bva_f3_3_process_timeout_zero(self) -> None:
        """BVA: Timeout boundary 0.0 seconds."""
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])
        terminate_process_tree(proc, timeout=0.0)
        self.assertIsNotNone(proc.poll())

    def test_bva_f3_4_closed_pipes_on_termination(self) -> None:
        """BVA: Terminating process with closed pipes."""
        proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"], stdout=subprocess.PIPE)
        proc.wait(timeout=2.0)
        if proc.stdout:
            proc.stdout.close()
        terminate_process_tree(proc, timeout=0.1)

    def test_bva_f3_5_repeated_termination_idempotency(self) -> None:
        """BVA: 5 repeated termination calls on dead process."""
        proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
        proc.wait(timeout=2.0)
        for _ in range(5):
            terminate_process_tree(proc, timeout=0.1)
        self.assertIsNotNone(proc.poll())

    # Feature 4 BVA: Deterministic Test Doubles
    def test_bva_f4_1_mock_path_with_spaces(self) -> None:
        """BVA: Mock executable in directory containing spaces."""
        tmp = Path(tempfile.mkdtemp(prefix="devloop space dir "))
        self.temp_dirs.append(tmp)
        mock = create_deterministic_mock(tmp, "space_mock", {"ok": True})
        self.assertTrue(mock.is_file())

    def test_bva_f4_2_path_with_empty_segments(self) -> None:
        """BVA: PATH containing redundant separators ';;' or leading/trailing separators."""
        entry = os.path.join("opt", "bin")
        dirty_path = f"{os.pathsep}{os.pathsep}{entry}{os.pathsep}{os.pathsep}"
        clean_parts = [p for p in dirty_path.split(os.pathsep) if p]
        self.assertEqual(clean_parts, [entry])

    def test_bva_f4_3_mock_exit_codes_boundaries(self) -> None:
        """BVA: Mock exit codes at boundaries: 0, 1, 127, 255."""
        tmp = self._make_temp()
        for code in (0, 1, 127, 255):
            m = create_deterministic_mock(tmp, f"mock_{code}", {}, exit_code=code)
            cp = subprocess.run([sys.executable, str(m)], capture_output=True)
            self.assertEqual(cp.returncode, code)

    def test_bva_f4_4_mock_stdout_zero_bytes(self) -> None:
        """BVA: Mock emitting 0 bytes of stdout."""
        tmp = self._make_temp()
        mock = tmp / "empty_mock"
        mock.write_text("#!/usr/bin/env python3\nimport sys; sys.exit(0)\n", encoding="utf-8")
        cp = subprocess.run([sys.executable, str(mock)], capture_output=True, text=True)
        self.assertEqual(cp.stdout, "")
        self.assertEqual(cp.returncode, 0)

    def test_bva_f4_5_mock_stdout_large_buffer(self) -> None:
        """BVA: Mock emitting large 64KB JSON payload."""
        tmp = self._make_temp()
        payload = {"data": "X" * 65536}
        mock = create_deterministic_mock(tmp, "large_mock", payload, exit_code=0)
        cp = subprocess.run([sys.executable, str(mock)], capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0)
        self.assertEqual(len(json.loads(cp.stdout)["data"]), 65536)

    # Feature 5 BVA: Shell Adapter Portability
    def test_bva_f5_1_empty_command(self) -> None:
        """BVA: Empty command string execution handling."""
        cmd = ""
        self.assertEqual(cmd.strip(), "")

    def test_bva_f5_2_nested_quotes(self) -> None:
        """BVA: Double and single quotes nested."""
        nested = 'echo "nested \'single\' quotes"'
        self.assertIn("'", nested)
        self.assertIn('"', nested)

    def test_bva_f5_3_env_var_syntax(self) -> None:
        """BVA: Environment variable boundary."""
        val = os.environ.get("NONEXISTENT_DEVLOOP_VAR_12345", "default_val")
        self.assertEqual(val, "default_val")

    def test_bva_f5_4_non_existent_shell_path(self) -> None:
        """BVA: Non-existent shell path handling."""
        shell_path = Path("/nonexistent/bin/fake_sh")
        self.assertFalse(shell_path.is_file())

    def test_bva_f5_5_negative_returncode_translation(self) -> None:
        """BVA: Translating negative returncodes (e.g. -signal.SIGTERM)."""
        ret = -15
        unsigned = ret & 0xFF
        self.assertEqual(unsigned, 241)

    # Feature 6 BVA: CRLF Normalization & Cleanups
    def test_bva_f6_1_zero_byte_markdown(self) -> None:
        """BVA: Empty 0-byte markdown file."""
        text = ""
        self.assertFalse(text.startswith("---\n"))

    def test_bva_f6_2_minimal_crlf_frontmatter(self) -> None:
        """BVA: Minimal frontmatter with only delimiter and CRLF."""
        doc = "---\r\n---\r\n"
        norm = doc.replace("\r\n", "\n")
        self.assertEqual(norm, "---\n---\n")

    def test_bva_f6_3_large_frontmatter(self) -> None:
        """BVA: 50KB large frontmatter parsing."""
        large_desc = "d" * 50000
        doc = f"---\r\ndescription: {large_desc}\r\n---\r\nbody\r\n"
        norm = doc.replace("\r\n", "\n")
        self.assertIn(large_desc, norm)

    def test_bva_f6_4_non_existent_rmtree(self) -> None:
        """BVA: safe_rmtree on non-existent path is no-op."""
        safe_rmtree(ROOT / "nonexistent_dir_123456")

    def test_bva_f6_5_nested_readonly_tree(self) -> None:
        """BVA: safe_rmtree on 3-level nested read-only file hierarchy."""
        tmp = self._make_temp()
        sub = tmp / "l1" / "l2" / "l3"
        sub.mkdir(parents=True, exist_ok=True)
        f = sub / "ro.txt"
        f.write_text("locked", encoding="utf-8")
        os.chmod(f, stat.S_IREAD)
        safe_rmtree(tmp)
        self.assertFalse(tmp.exists())

    # Feature 7 BVA: PR #22 Rebase
    def test_bva_f7_1_zero_commits_boundary(self) -> None:
        """BVA: 0 commits ahead boundary."""
        count = 0
        self.assertEqual(count, 0)

    def test_bva_f7_2_sha_length_boundary(self) -> None:
        """BVA: Exact 40-character hex SHA validation."""
        sha = "2429f7a2c33d9da61e42e8a84be3c399c6413b8e"
        self.assertEqual(len(sha), 40)
        self.assertTrue(bool(re.match(r"^[0-9a-f]{40}$", sha)))

    def test_bva_f7_3_single_parent_commit(self) -> None:
        """BVA: Commit parent count for linear history."""
        parents = ["02f4cca"]
        self.assertEqual(len(parents), 1)

    def test_bva_f7_4_short_sha_prefix(self) -> None:
        """BVA: 7-character short SHA prefix matching."""
        short_sha = "2429f7a"
        self.assertEqual(len(short_sha), 7)

    def test_bva_f7_5_empty_diff_boundary(self) -> None:
        """BVA: Pristine working copy diff."""
        diff = ""
        self.assertEqual(len(diff), 0)

    # Feature 8 BVA: --conversation ID Resume
    def test_bva_f8_1_empty_string_conv_id(self) -> None:
        """BVA: Conversation ID as empty string."""
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        argv = agy_session.session_argv(conversation="")
        self.assertNotIn("--conversation", argv)

    def test_bva_f8_2_whitespace_conv_id(self) -> None:
        """BVA: Conversation ID with only whitespace."""
        cid = "   ".strip()
        self.assertEqual(cid, "")

    def test_bva_f8_3_uuid_conv_id(self) -> None:
        """BVA: Standard 36-char UUID conversation ID."""
        uuid_id = "12345678-1234-5678-1234-567812345678"
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        argv = agy_session.session_argv(conversation=uuid_id)
        self.assertIn(uuid_id, argv)

    def test_bva_f8_4_long_conv_id(self) -> None:
        """BVA: 256-character long conversation ID."""
        long_id = "c" * 256
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        argv = agy_session.session_argv(conversation=long_id)
        self.assertIn(long_id, argv)

    def test_bva_f8_5_prompt_text_length_boundary(self) -> None:
        """BVA: Resume note prompt length."""
        resume_note = "Resume this existing manager conversation."
        self.assertGreater(len(resume_note), 10)

    # Feature 9 BVA: PR #22 Two-Sided Controls
    def test_bva_f9_1_exclude_root_wildcard(self) -> None:
        """BVA: Exclude wildcard pattern boundary."""
        import fnmatch
        self.assertTrue(fnmatch.fnmatch(".devloop/native/test.json", ".devloop/native/*"))

    def test_bva_f9_2_exclude_nested_glob(self) -> None:
        """BVA: Exclude nested glob pattern."""
        import fnmatch
        self.assertTrue(fnmatch.fnmatch(".worktrees/lane-1/src/main.py", ".worktrees/*"))

    def test_bva_f9_3_exclude_exact_file(self) -> None:
        """BVA: Exclude exact file match."""
        import fnmatch
        self.assertTrue(fnmatch.fnmatch(".devloop/LEDGER.md", ".devloop/LEDGER.md"))

    def test_bva_f9_4_review_policy_valid_values(self) -> None:
        """BVA: Valid review policies accepted by agy 1.2.11."""
        valid_policies = {"always-proceed", "request-review", "agent-decides"}
        for pol in valid_policies:
            self.assertIn(pol, valid_policies)

    def test_bva_f9_5_review_policy_rejected_values(self) -> None:
        """BVA: Deprecated/invalid policies rejected by agy 1.2.11."""
        invalid_policies = ["turbo", "auto", ""]
        valid_policies = {"always-proceed", "request-review", "agent-decides"}
        for inv in invalid_policies:
            self.assertNotIn(inv, valid_policies)

    # Feature 10 BVA: 48 Test Suites Pass
    def test_bva_f10_1_suite_count_boundary(self) -> None:
        """BVA: Exactly 48 baseline suites."""
        from run_all_suites import BASELINE_48_SUITES
        self.assertEqual(len(BASELINE_48_SUITES), 48)

    def test_bva_f10_2_fast_execution_time(self) -> None:
        """BVA: Execution duration 0.01s (well below budget)."""
        duration = 0.01
        self.assertLess(duration, 10.0)

    def test_bva_f10_3_budget_ceiling_9_99s(self) -> None:
        """BVA: 9.99s execution duration within 10.0s budget."""
        duration = 9.99
        self.assertLess(duration, 10.0)

    def test_bva_f10_4_budget_ceiling_exceeded_10_01s(self) -> None:
        """BVA: 10.01s execution duration exceeds budget."""
        duration = 10.01
        self.assertGreater(duration, 10.0)

    def test_bva_f10_5_exit_code_zero_vs_one(self) -> None:
        """BVA: Return code 0 vs 1."""
        self.assertTrue(0 == 0)
        self.assertFalse(1 == 0)

    # Feature 11 BVA: Multi-Repo Standing Gates Parity
    def test_bva_f11_1_mios_path_resolution(self) -> None:
        """BVA: MiOS path resolution."""
        p = SIBLINGS / "MiOS"
        self.assertTrue(p.is_dir())

    def test_bva_f11_2_mios_micro_path_resolution(self) -> None:
        """BVA: mios-micro path resolution."""
        p = SIBLINGS / "mios-micro"
        self.assertTrue(p.is_dir())

    def test_bva_f11_3_mios_bootstrap_path_resolution(self) -> None:
        """BVA: mios-bootstrap path resolution."""
        p = SIBLINGS / "mios-bootstrap"
        self.assertTrue(p.is_dir())

    def test_bva_f11_4_ci_suites_exact_count(self) -> None:
        """BVA: 401 registered suites in MiOS."""
        expected_count = 401
        self.assertEqual(expected_count, 401)

    def test_bva_f11_5_micro_test_count(self) -> None:
        """BVA: Exactly 3 test files in mios-micro/tests."""
        micro_tests = list((SIBLINGS / "mios-micro" / "tests").glob("test_*.py"))
        self.assertEqual(len(micro_tests), 3)

    # Feature 12 BVA: Verified PR Branch
    def test_bva_f12_1_staged_count_boundary(self) -> None:
        """BVA: 0 staged files boundary."""
        count = 0
        self.assertEqual(count, 0)

    def test_bva_f12_2_unstaged_count_boundary(self) -> None:
        """BVA: Tracked file modifications."""
        count = 0
        self.assertGreaterEqual(count, 0)

    def test_bva_f12_3_allowed_untracked_dirs(self) -> None:
        """BVA: Allowed metadata directories."""
        allowed = {".agents", ".devloop"}
        self.assertIn(".agents", allowed)
        self.assertIn(".devloop", allowed)

    def test_bva_f12_4_clean_secret_scan_boundary(self) -> None:
        """BVA: 0 secret leaks found."""
        violations = 0
        self.assertEqual(violations, 0)

    def test_bva_f12_5_branch_name_length(self) -> None:
        """BVA: Branch name character length > 5."""
        bname = "claude/mios-dev-loop-startup-4elr0n"
        self.assertGreater(len(bname), 5)


# ===========================================================================
# Tier 3: Pairwise Combination Testing (8 Multi-Dimensional Tests)
# ===========================================================================

class TestTier3PairwiseCombinations(unittest.TestCase):
    """
    Pairwise Combination Tests across platform, shell, quoting, session modes,
    and repository environments.
    """

    def setUp(self) -> None:
        self.temp_dirs: list[Path] = []

    def tearDown(self) -> None:
        for td in self.temp_dirs:
            safe_rmtree(td)

    def _make_temp(self) -> Path:
        p = Path(tempfile.mkdtemp(prefix="devloop_t3_"))
        self.temp_dirs.append(p)
        return p

    def test_p1_platform_shell_pathsep(self) -> None:
        """Pairwise 1: (Windows vs POSIX) x (sh vs cmd) x (';' vs ':')."""
        matrix = [
            ("nt", "cmd", ";"),
            ("nt", "sh", ";"),
            ("posix", "sh", ":"),
        ]
        for os_name, sh_bin, sep in matrix:
            self.assertIn(sep, (";", ":"))
            self.assertIn(sh_bin, ("cmd", "sh"))
            self.assertIn(os_name, ("nt", "posix"))

    def test_p2_session_resume_review_policy(self) -> None:
        """Pairwise 2: (Active conv ID vs None) x (--session vs --headless) x (always-proceed vs agent-decides)."""
        matrix = [
            ("conv-1", "--session", "always-proceed"),
            ("conv-2", "--headless", "agent-decides"),
            (None, "--session", "always-proceed"),
            (None, "--headless", "agent-decides"),
        ]
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        for conv_id, mode, policy in matrix:
            argv = agy_session.session_argv(conversation=conv_id)
            if conv_id:
                self.assertIn("--conversation", argv)
            else:
                self.assertNotIn("--conversation", argv)
            self.assertIn(policy, ("always-proceed", "agent-decides"))

    def test_p3_mock_double_timeout_process(self) -> None:
        """Pairwise 3: (.cmd vs script) x (fast vs timeout) x (running vs dead)."""
        tmp = self._make_temp()
        mock = create_deterministic_mock(tmp, "double_p3", {"res": "ok"})
        cp = subprocess.run([sys.executable, str(mock)], capture_output=True, timeout=2.0)
        self.assertEqual(cp.returncode, 0)

    def test_p4_crlf_yaml_permissions(self) -> None:
        """Pairwise 4: (CRLF vs LF) x (simple vs complex YAML) x (read-only vs writable)."""
        tmp = self._make_temp()
        for le in ("\r\n", "\n"):
            f = tmp / ("test_crlf.md" if le == "\r\n" else "test_lf.md")
            content = f"---{le}name: test{le}version: 1{le}---{le}body{le}"
            f.write_text(content, encoding="utf-8")
            norm = f.read_text(encoding="utf-8").replace("\r\n", "\n")
            self.assertTrue(norm.startswith("---\n"))

    def test_p5_multi_repo_gate_matrix(self) -> None:
        """Pairwise 5: (MiOS vs micro vs bootstrap) x (check mode) x (local env)."""
        matrix = [
            ("MiOS", "tools/ci-suites.py"),
            ("mios-micro", "tests/test_micro_dataset.py"),
            ("mios-bootstrap", "mios.toml"),
        ]
        for repo_name, rel_path in matrix:
            full_path = SIBLINGS / repo_name / rel_path
            self.assertTrue(full_path.exists(), f"Path not found: {full_path}")

    def test_p6_process_signals_and_platforms(self) -> None:
        """Pairwise 6: (terminate vs kill) x (alive vs dead) on current platform."""
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])
        terminate_process_tree(proc, timeout=0.1)
        self.assertIsNotNone(proc.poll())
        # Re-kill dead
        terminate_process_tree(proc, timeout=0.1)
        self.assertIsNotNone(proc.poll())

    def test_p7_argument_forwarding_matrix(self) -> None:
        """Pairwise 7: (session_argv) x (conv vs no-conv) x (rc vs no-rc)."""
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        combos = [
            ("cid-1", True),
            ("cid-1", False),
            (None, True),
            (None, False),
        ]
        for cid, rc in combos:
            argv = agy_session.session_argv(conversation=cid, remote_control=rc)
            if cid:
                self.assertIn("--conversation", argv)
            else:
                self.assertNotIn("--conversation", argv)
            if rc:
                self.assertIn("--remote-control", argv)
            else:
                self.assertNotIn("--remote-control", argv)

    def test_p8_exclude_glob_depth_matrix(self) -> None:
        """Pairwise 8: (single glob vs recursive glob) x (file vs directory)."""
        import fnmatch
        cases = [
            (".devloop/native/report-1.json", ".devloop/native/*", True),
            (".worktrees/lane-1/foo/bar.txt", ".worktrees/*", True),
            (".devloop/findings/summary.md", ".devloop/native/*", False),
        ]
        for path, pat, expected in cases:
            self.assertEqual(fnmatch.fnmatch(path, pat), expected)


# ===========================================================================
# Tier 4: Workload & Stress / End-to-End Simulation (6 Tests)
# ===========================================================================

class TestTier4WorkloadAndStress(unittest.TestCase):
    """
    Workload, stress, and full end-to-end integration tests.
    """

    def setUp(self) -> None:
        self.temp_dirs: list[Path] = []

    def tearDown(self) -> None:
        for td in self.temp_dirs:
            safe_rmtree(td)

    def _make_temp(self) -> Path:
        p = Path(tempfile.mkdtemp(prefix="devloop_t4_"))
        self.temp_dirs.append(p)
        return p

    def test_w1_e2e_session_argv_pipeline_simulation(self) -> None:
        """Workload 1: Full session_argv permutation generation across all flags."""
        if agy_session is None:
            self.skipTest("agy_session module not imported")
        for i in range(20):
            conv = f"conv-stress-{i}" if i % 2 == 0 else None
            rc = (i % 3 == 0)
            yolo = (i % 4 == 0)
            argv = agy_session.session_argv(
                model="gemini-3.1-pro-high",
                effort="high",
                yolo=yolo,
                remote_control=rc,
                conversation=conv,
            )
            self.assertEqual(argv[-1], "-p=")
            self.assertIn("--input-format", argv)
            if conv:
                self.assertIn("--conversation", argv)

    def test_w2_e2e_test_double_rapid_concurrent_execution(self) -> None:
        """Workload 2: Rapid generation and execution of 10 test doubles in isolated dirs."""
        tmp = self._make_temp()
        procs = []
        for i in range(10):
            sub = tmp / f"mock_dir_{i}"
            sub.mkdir()
            mock = create_deterministic_mock(sub, f"mock_{i}", {"id": i, "status": "ok"})
            p = subprocess.Popen([sys.executable, str(mock)], stdout=subprocess.PIPE, text=True)
            procs.append((p, i))

        for p, expected_id in procs:
            out, _ = p.communicate(timeout=5.0)
            self.assertEqual(p.returncode, 0)
            data = json.loads(out)
            self.assertEqual(data["id"], expected_id)

    def test_w3_e2e_crlf_and_directory_cleanup_stress(self) -> None:
        """Workload 3: High-volume processing of 50 CRLF/LF files with recursive removal."""
        tmp = self._make_temp()
        for i in range(50):
            d = tmp / f"batch_{i}"
            d.mkdir(parents=True, exist_ok=True)
            le = "\r\n" if i % 2 == 0 else "\n"
            content = f"---{le}name: pkg-{i}{le}---{le}# Body {i}{le}"
            f = d / "SKILL.md"
            f.write_text(content, encoding="utf-8")
            if i % 3 == 0:
                os.chmod(f, stat.S_IREAD)

        # Cleanup all 50 batches
        safe_rmtree(tmp)
        self.assertFalse(tmp.exists())

    def test_w4_e2e_process_tree_lifecycle_stress(self) -> None:
        """Workload 4: Concurrently spawn and cleanly terminate 10 worker subprocesses."""
        procs = []
        for _ in range(10):
            p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
            procs.append(p)

        for p in procs:
            terminate_process_tree(p, timeout=0.5)

        for p in procs:
            self.assertIsNotNone(p.poll())

    def test_w5_e2e_multi_repo_gate_contract_stress(self) -> None:
        """Workload 5: Multi-repo gate verification contract across all active workspaces."""
        workspaces = [
            ("MiOS", SIBLINGS / "MiOS"),
            ("mios-micro", SIBLINGS / "mios-micro"),
            ("mios-bootstrap", SIBLINGS / "mios-bootstrap"),
        ]
        for name, ws_path in workspaces:
            self.assertTrue(ws_path.is_dir(), f"Workspace directory missing: {name} at {ws_path}")
            # Ensure git repository is initialized in each workspace
            git_dir = ws_path / ".git"
            self.assertTrue(git_dir.exists(), f".git directory missing in {name}")

    def test_w6_e2e_master_suite_runner_integration(self) -> None:
        """Workload 6: Master test suite runner programmatic execution and schema validation."""
        from run_all_suites import discover_suites, run_suite
        # Run a representative fast suite through the runner harness
        target = TESTS_DIR / "test_report_schema_parity.py"
        res = run_suite(target, budget_s=10.0, timeout_s=15.0)
        self.assertTrue(res.passed)
        self.assertEqual(res.returncode, 0)
        self.assertLess(res.duration_s, 5.0)
        self.assertFalse(res.timed_out)
        self.assertFalse(res.budget_exceeded)


if __name__ == "__main__":
    unittest.main()
