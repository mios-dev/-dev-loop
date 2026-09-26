#!/usr/bin/env python3
"""
agy_settings.py -- the ONE writer of Antigravity CLI settings for this repo.

Two jobs, both measured against agy 1.2.7:

1. Headless permission grants. Unchanged from the inline block that used to live in
   setup-antigravity.sh: exact tool names and `command(<binary>)` prefixes, merged into
   whatever the file already holds.

2. `artifactReviewPolicy`. /teamwork-preview's own protocol forbids invoking the team "before
   explicit user approval", and a brief that says "do not ask" does not count. Measured: a
   manager told not to ask did the whole job solo, 100 responses with 1 subagent. agy has a
   setting for exactly this, `artifactReviewPolicy`, and it is VALIDATED:

       "turbo"                      -> accepted (rc 0, settings load cleanly)
       "ARTIFACT_REVIEW_MODE_TURBO" -> "failed to load cli settings, using DEFAULTS:
                                       invalid settings: artifactReviewPolicy: unrecognized value"

   Using defaults means EVERY setting is dropped, the permission grants included, so one bad
   spelling silently turns every headless lane into an auto-denied one. That is why this
   writer refuses any value outside the measured set rather than writing it and hoping.

   The accepted spellings changed under the same key. agy 1.2.11, measured 2026-09-26: "turbo"
   is refused ("invalid settings: artifactReviewPolicy: unrecognized value") and the binary
   carries always-proceed / request-review / agent-decides instead. So the value set is read
   from the INSTALLED binary, never assumed.

Usage:
  agy_settings.py [--settings PATH] [--agy PATH] ensure-grants
  agy_settings.py [--settings PATH] [--agy PATH] review-policy VALUE
  agy_settings.py [--settings PATH] clear-review-policy
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

DEFAULT_SETTINGS = Path(os.environ.get("HOME", "~")) / ".gemini" / "antigravity-cli" / "settings.json"

GRANTS = ["read_file(*)", "write_file(*)"] + [f"command({c})" for c in (
    "sh", "bash", "python3", "git", "cat", "grep", "head", "tail", "ls", "find",
    "wc", "sed", "awk", "mkdir", "cp", "mv", "printf", "echo", "jq", "cd")]

# Two generations of spellings for ARTIFACT_REVIEW_MODE_{ALWAYS,AUTO,TURBO}. 1.2.7: only "turbo"
# was exercised end to end. 1.2.11: "turbo" refused; the new names are read from its binary.
LEGACY_POLICIES = ("always", "auto", "turbo")
CURRENT_POLICIES = ("request-review", "agent-decides", "always-proceed")
CURRENT_MARKER = b"always-proceed"


class SettingsError(Exception):
    pass


def load(path: Path) -> dict:
    """A corrupt or non-object file is REPORTED, never silently replaced with {}.

    The inline writer this replaces did `except JSONDecodeError: cfg = {}` and then wrote that
    back -- so a single stray byte erased every setting the operator had made."""
    if not path.is_file():
        return {}
    try:
        cfg = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        raise SettingsError(f"{path} is not readable JSON ({e}); refusing to overwrite it")
    if not isinstance(cfg, dict):
        raise SettingsError(f"{path} does not hold a JSON object; refusing to overwrite it")
    return cfg


def save(path: Path, cfg: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n")
    tmp.replace(path)   # atomic: a reader never sees half a settings file


def ensure_grants(cfg: dict) -> int:
    allow = cfg.setdefault("permissions", {}).setdefault("allow", [])
    for rule in GRANTS:
        if rule not in allow:
            allow.append(rule)
    return len(allow)


def review_policies(agy: str | None) -> tuple[str, ...]:
    """The spellings the installed agy accepts, read from its binary."""
    path = agy or shutil.which("agy")
    if not path:
        raise SettingsError("agy not found, so the accepted artifactReviewPolicy spellings are "
                            "unknown; nothing is written (pass --agy PATH)")
    try:
        with open(path, "rb") as fh:
            blob = fh.read()
    except OSError as e:
        raise SettingsError(f"cannot read {path} ({e}); nothing is written")
    return CURRENT_POLICIES if CURRENT_MARKER in blob else LEGACY_POLICIES


def set_review_policy(cfg: dict, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise SettingsError(
            f"artifactReviewPolicy {value!r} is not one of {list(allowed)} (the spellings this agy "
            "accepts). agy rejects an unrecognized value by dropping EVERY setting (grants "
            "included), so it is not written")
    cfg["artifactReviewPolicy"] = value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ap.add_argument("--agy", default=None, help="agy binary to read spellings from (default: PATH)")
    sub.add_parser("ensure-grants")
    rp = sub.add_parser("review-policy")
    rp.add_argument("value")
    sub.add_parser("clear-review-policy")
    a = ap.parse_args()
    try:
        cfg = load(a.settings)
        if a.cmd == "ensure-grants":
            total = ensure_grants(cfg)
            save(a.settings, cfg)
            print(f"[antigravity-setup] {len(GRANTS)} grant(s) ensured, {total} total")
            stale = cfg.get("artifactReviewPolicy")
            if stale is not None and (a.agy or shutil.which("agy")) and stale not in review_policies(a.agy):
                print(f"agy_settings: WARNING artifactReviewPolicy {stale!r} is not accepted by this "
                      "agy, which then drops every setting; run: agy_settings.py clear-review-policy",
                      file=sys.stderr)
        elif a.cmd == "clear-review-policy":
            if cfg.pop("artifactReviewPolicy", None) is not None:
                save(a.settings, cfg)
            print("[antigravity-setup] artifactReviewPolicy cleared")
        else:
            set_review_policy(cfg, a.value, review_policies(a.agy))
            save(a.settings, cfg)
            print(f"[antigravity-setup] artifactReviewPolicy = {a.value}")
    except SettingsError as e:
        print(f"agy_settings: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
