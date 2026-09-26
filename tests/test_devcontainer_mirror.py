#!/usr/bin/env python3
"""The Fedora devcontainer image here is MiOS's, byte for byte.

`.devcontainer/Containerfile` in this repo is a mirror of MiOS's
`.devcontainer/Containerfile` -- the ONE MiOS dev image, edited in MiOS only.
A mirror that drifts silently forks the image, so this compares the two
files byte for byte against the first MiOS copy it can reach, in this order:

  1. DEVLOOP_MIOS_CONTAINERFILE, when set (a path to MiOS's copy);
  2. a sibling checkout, read-only: ../MiOS (next to this repo), then
     /home/user/MiOS;
  3. https://raw.githubusercontent.com/mios-dev/MiOS/main/.devcontainer/Containerfile
     fetched with `curl --compressed` (the CDN gzips unsolicited).

Skipped, not passed, only when none of those is reachable, and the skip says
why for each. A missing local copy is a FAILURE, never a skip.

Controls:
  positive  the local copy is identical to the MiOS copy (test_mirror_matches_mios)
  negative  one byte changed in the local copy is reported naming
            .devcontainer/Containerfile, the reference and the first differing
            line (test_one_changed_byte_is_named, on a scratch copy, so the tree
            is never touched). Planting the same change in the real file makes
            test_mirror_matches_mios fail with that same message.

Run: python3 tests/test_devcontainer_mirror.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIRROR = Path(".devcontainer") / "Containerfile"
LOCAL = ROOT / MIRROR
REMOTE = "https://raw.githubusercontent.com/mios-dev/MiOS/main/.devcontainer/Containerfile"
# What every genuine copy of the file contains; an HTML error page or a captive
# portal answering the fetch does not, so it is refused as a reference.
SIGNATURE = b"FROM registry.fedoraproject.org/fedora:"


def _candidates() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    env = os.environ.get("DEVLOOP_MIOS_CONTAINERFILE")
    if env:
        out.append(("DEVLOOP_MIOS_CONTAINERFILE", Path(env)))
    out.append(("sibling checkout ../MiOS", ROOT.parent / "MiOS" / MIRROR))
    out.append(("checkout /home/user/MiOS", Path("/home/user/MiOS") / MIRROR))
    return out


def reference() -> tuple[bytes, str] | list[str]:
    """MiOS's bytes and where they came from, or the reasons nothing was reachable."""
    why: list[str] = []
    for label, path in _candidates():
        if not path.is_file():
            why.append(f"{label}: {path} is not a file")
            continue
        data = path.read_bytes()
        if SIGNATURE not in data:
            why.append(f"{label}: {path} is not the MiOS Containerfile (no '{SIGNATURE.decode()}')")
            continue
        return data, f"{label} ({path})"
    try:
        p = subprocess.run(
            ["curl", "-fsSL", "--compressed", "--retry", "3", "--retry-delay", "2",
             "--max-time", "60", REMOTE],
            capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        why.append(f"{REMOTE}: curl did not run: {exc}")
        return why
    if p.returncode != 0:
        why.append(f"{REMOTE}: curl exit {p.returncode}: {p.stderr.decode(errors='replace').strip()}")
        return why
    if SIGNATURE not in p.stdout:
        why.append(f"{REMOTE}: {len(p.stdout)} bytes that are not the MiOS Containerfile")
        return why
    return p.stdout, REMOTE


def compare(local: bytes, ref: bytes, ref_label: str) -> str | None:
    """None when identical; otherwise a message naming the mirror and the first difference."""
    if local == ref:
        return None
    n = min(len(local), len(ref))
    off = next((i for i in range(n) if local[i] != ref[i]), n)
    line = local[:off].count(b"\n") + 1
    return (f"{MIRROR} differs from MiOS ({ref_label}): first difference at byte {off}, "
            f"line {line} (local {len(local)} bytes, MiOS {len(ref)} bytes). "
            f"Edit the file in MiOS and mirror it; never edit the mirror.")


class DevcontainerMirror(unittest.TestCase):
    def test_local_copy_exists_and_is_the_one_image(self):
        self.assertTrue(LOCAL.is_file(), f"missing: {MIRROR} (the MiOS dev image mirror)")
        data = LOCAL.read_bytes()
        self.assertIn(SIGNATURE, data, f"{MIRROR} is not a Fedora Containerfile")
        self.assertIn(b"the one MiOS dev image", data,
                      f"{MIRROR} lacks the mirror header; it is not MiOS's Containerfile")

    def test_mirror_matches_mios(self):
        self.assertTrue(LOCAL.is_file(), f"missing: {MIRROR}")
        ref = reference()
        if isinstance(ref, list):
            raise unittest.SkipTest("no MiOS Containerfile reachable, so the mirror was NOT "
                                    "checked:\n  " + "\n  ".join(ref))
        data, label = ref
        print(f"[devcontainer-mirror] reference: {label}", file=sys.stderr)
        report = compare(LOCAL.read_bytes(), data, label)
        self.assertIsNone(report, report)

    def test_one_changed_byte_is_named(self):
        self.assertTrue(LOCAL.is_file(), f"missing: {MIRROR}")
        good = LOCAL.read_bytes()
        i = len(good) // 2  # any one byte, so this does not depend on the file's text
        bad = good[:i] + bytes([good[i] ^ 0x01]) + good[i + 1:]
        self.assertIsNone(compare(good, good, "self"))
        report = compare(bad, good, "scratch")
        self.assertIsNotNone(report)
        self.assertIn(str(MIRROR), report)
        self.assertIn(f"byte {i}", report)
        # a length change is caught too, not only a substitution
        self.assertIsNotNone(compare(good + b"\n", good, "scratch"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
