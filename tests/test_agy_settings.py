#!/usr/bin/env python3
"""
Controls for scripts/env/agy_settings.py, the one writer of Antigravity CLI settings.

The failure these guard is SILENT and total. agy 1.2.7, measured: an unrecognized
`artifactReviewPolicy` makes agy log "failed to load cli settings, using defaults" and drop
EVERY setting, the headless permission grants included. Headless agy then auto-denies every tool
and still reports success. A settings writer that accepts any string turns one typo into a fleet
of lanes that can do nothing.

Both sides:
  positive: the measured value is written; grants and unrelated keys are preserved
  negative: an unrecognized value is refused and the file is byte-for-byte unchanged; a corrupt
            file is refused rather than replaced with {} (the old inline writer's behaviour)

Run: python3 tests/test_agy_settings.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "skills" / "dev-loop" / "scripts" / "env" / "agy_settings.py"
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}{'' if cond else ': ' + detail}")
    if not cond:
        FAILURES.append(name)


def run(settings: Path, *args: str, agy: Path | None = None) -> subprocess.CompletedProcess:
    pre = ["--agy", str(agy)] if agy else []
    return subprocess.run([sys.executable, str(TOOL), "--settings", str(settings), *pre, *args],
                          capture_output=True, text=True, timeout=30)


def fake_agy(td: str, name: str, strings: list[str]) -> Path:
    """Stands in for the agy binary: only the enum strings the writer reads. Those strings are the
    ones in the real 1.2.7 and 1.2.11 binaries; the 1.2.11 refusal of "turbo" was measured live."""
    p = Path(td) / name
    p.write_bytes(b"\0".join(x.encode() for x in strings))
    return p


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        legacy = fake_agy(td, "agy-1.2.7", ["ARTIFACT_REVIEW_MODE_TURBO", "turbo"])
        current = fake_agy(td, "agy-1.2.11", ["ARTIFACT_REVIEW_MODE_TURBO", "always-proceed",
                                              "request-review", "agent-decides"])
        s = Path(td) / "settings.json"
        s.write_text(json.dumps({"trustedWorkspaces": ["/repo"], "permissions": {"allow": ["command(make)"]}}))

        print("grants:")
        cp = run(s, "ensure-grants")
        d = json.loads(s.read_text())
        check("ensure-grants exits 0", cp.returncode == 0, cp.stderr)
        check("existing grant kept", "command(make)" in d["permissions"]["allow"])
        check("read_file(*) granted", "read_file(*)" in d["permissions"]["allow"])
        check("unrelated key kept", d.get("trustedWorkspaces") == ["/repo"])
        n = len(d["permissions"]["allow"])
        run(s, "ensure-grants")
        check("idempotent", len(json.loads(s.read_text())["permissions"]["allow"]) == n)

        print("review policy, positive:")
        cp = run(s, "review-policy", "turbo", agy=legacy)
        d = json.loads(s.read_text())
        check("turbo accepted", cp.returncode == 0 and d.get("artifactReviewPolicy") == "turbo", cp.stderr)
        check("grants survive the policy write", len(d["permissions"]["allow"]) == n)

        print("review policy, negative:")
        before = s.read_bytes()
        cp = run(s, "review-policy", "ARTIFACT_REVIEW_MODE_TURBO", agy=legacy)
        check("the enum spelling agy rejects is refused", cp.returncode != 0, cp.stdout)
        check("and the file is byte-for-byte unchanged", s.read_bytes() == before)
        check("the refusal says why", "dropping EVERY setting" in cp.stderr, cp.stderr)

        print("agy 1.2.11 spellings:")
        cp = run(s, "ensure-grants", agy=current)
        check("a stale turbo is flagged on 1.2.11", "not accepted by this agy" in cp.stderr, cp.stderr)
        before = s.read_bytes()
        cp = run(s, "review-policy", "turbo", agy=current)
        check("turbo is refused on 1.2.11", cp.returncode != 0 and s.read_bytes() == before,
              cp.stdout + cp.stderr)
        check("the refusal names the accepted spellings", "request-review" in cp.stderr, cp.stderr)
        cp = run(s, "review-policy", "request-review", agy=current)
        check("request-review accepted on 1.2.11",
              cp.returncode == 0 and json.loads(s.read_text()).get("artifactReviewPolicy") == "request-review",
              cp.stderr)
        cp = run(s, "clear-review-policy")
        d = json.loads(s.read_text())
        check("clear-review-policy removes the key", cp.returncode == 0 and "artifactReviewPolicy" not in d,
              cp.stderr)
        check("and keeps the grants", len(d["permissions"]["allow"]) == n)
        before = s.read_bytes()
        cp = run(s, "review-policy", "request-review", agy=Path(td) / "no-such-agy")
        check("no readable agy: refused, file unchanged", cp.returncode != 0 and s.read_bytes() == before,
              cp.stdout + cp.stderr)

        print("corrupt file:")
        s.write_text('{"permissions": {"allow": ["command(make)"]')     # truncated JSON
        corrupt = s.read_bytes()
        cp = run(s, "ensure-grants")
        check("a corrupt file is refused, not replaced with {}",
              cp.returncode != 0 and s.read_bytes() == corrupt, cp.stdout + cp.stderr)

        print("fresh container:")
        f = Path(td) / "new" / "settings.json"
        cp = run(f, "review-policy", "turbo", agy=legacy)
        check("creates the file when absent", cp.returncode == 0 and json.loads(f.read_text()) == {"artifactReviewPolicy": "turbo"})
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        return 1
    print("all agy-settings controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
