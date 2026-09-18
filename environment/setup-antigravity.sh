#!/bin/sh
# Compat wrapper — the canonical script ships inside the skill so every
# dev-loop install carries it. All arguments pass through.
exec bash "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/skills/dev-loop/scripts/env/setup-antigravity.sh" "$@"
