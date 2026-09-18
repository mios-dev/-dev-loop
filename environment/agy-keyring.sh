#!/bin/sh
# Compat wrapper (sourceable) — the canonical script ships inside the skill.
#   . environment/agy-keyring.sh          (from anywhere inside the repo)
_dl_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
# shellcheck disable=SC1091
. "$_dl_root/skills/dev-loop/scripts/env/agy-keyring.sh"
