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

Usage:
  agy_settings.py [--settings PATH] ensure-grants
  agy_settings.py [--settings PATH] review-policy VALUE     # always | auto | turbo
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_SETTINGS = Path(os.environ.get("HOME", "~")) / ".gemini" / "antigravity-cli" / "settings.json"

GRANTS = ["read_file(*)", "write_file(*)"] + [f"command({c})" for c in (
    "sh", "bash", "python3", "git", "cat", "grep", "head", "tail", "ls", "find",
    "wc", "sed", "awk", "mkdir", "cp", "mv", "printf", "echo", "jq", "cd")]

# The lowercase spellings of ARTIFACT_REVIEW_MODE_{ALWAYS,AUTO,TURBO} from the agy 1.2.7 binary.
# Only "turbo" has been exercised end to end; the other two are the same enum's siblings.
REVIEW_POLICIES = ("always", "auto", "turbo")


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


def set_review_policy(cfg: dict, value: str) -> None:
    if value not in REVIEW_POLICIES:
        raise SettingsError(
            f"artifactReviewPolicy {value!r} is not one of {list(REVIEW_POLICIES)}. agy rejects an "
            "unrecognized value by dropping EVERY setting (grants included), so it is not written")
    cfg["artifactReviewPolicy"] = value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ensure-grants")
    rp = sub.add_parser("review-policy")
    rp.add_argument("value")
    a = ap.parse_args()
    try:
        cfg = load(a.settings)
        if a.cmd == "ensure-grants":
            total = ensure_grants(cfg)
            save(a.settings, cfg)
            print(f"[antigravity-setup] {len(GRANTS)} grant(s) ensured, {total} total")
        else:
            set_review_policy(cfg, a.value)
            save(a.settings, cfg)
            print(f"[antigravity-setup] artifactReviewPolicy = {a.value}")
    except SettingsError as e:
        print(f"agy_settings: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
