#!/bin/sh
# PreToolUse(Bash|Edit|Write|MultiEdit|NotebookEdit): one writer per lane worktree (git_lock.py).
# Denies a session that is not inside the owning lane's process tree -- e.g. a second agent a
# supervisor started in a worktree devloop.sh already runs. Fast path: no python unless the
# target worktree has an owner lock file at all.
. "$(dirname "$0")/_lib.sh"; IN=$(cat)
P=$(json_get "$IN" .tool_input.file_path); [ -n "$P" ] || P=$(json_get "$IN" .tool_input.notebook_path)
[ -n "$P" ] || P=$(json_get "$IN" .cwd); [ -n "$P" ] || P=$PWD
D=$P; [ -d "$D" ] || D=$(dirname "$D")
while [ ! -e "$D/.git" ] && [ "$D" != / ] && [ -n "$D" ]; do D=$(dirname "$D"); done
if [ -f "$D/.git" ]; then GD=$(sed -n 's/^gitdir: *//p' "$D/.git"); case "$GD" in /*) ;; *) GD="$D/$GD";; esac
elif [ -d "$D/.git" ]; then GD="$D/.git"; else exit 0; fi
[ -f "$GD/devloop-owner.lock" ] || exit 0
WHY=$(python3 "$(dirname "$0")/../skills/dev-loop/scripts/git_lock.py" check --path "$P" --me $$) || deny "$WHY"
exit 0
