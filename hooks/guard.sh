#!/bin/sh
# PreToolUse(Bash): block sweeping git adds, history rewrites on shared refs, secret printing, pipe-to-shell (SKILL §10, §12)
. "$(dirname "$0")/_lib.sh"; IN=$(cat); CMD=$(json_get "$IN" .tool_input.command)
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])git[[:space:]]+add[[:space:]]+(-A|--all|-u|\.)([[:space:]]|$)' && deny "dev-loop: explicit-path staging only — never git add -A / . / -u (SKILL §12). Use git add <path>."
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])git[[:space:]]+push[[:space:]].*(--force|-f)([[:space:]]|$)' && deny "dev-loop: force-push is irreversible; ask the operator first (SKILL §12)."
echo "$CMD" | grep -Eq '(curl|wget)[^|]*\|[[:space:]]*(sudo[[:space:]]+)?(sh|bash|zsh|pwsh)([[:space:]]|$)' && deny "dev-loop: pipe-to-shell is a supply-chain hole; download, inspect, verify checksum, then run."
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])(printenv|env)[[:space:]]*($|[;&|])|cat[[:space:]]+[^[:space:]]*\.env([[:space:]]|$)|echo[[:space:]]+"?\$\{?[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD)' && deny "dev-loop: that prints secrets into the transcript (SKILL §10). Assert presence by name: [ -n \"\${VAR:-}\" ]."
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])(cat|grep|head|tail|less|more|view)[[:space:]]+.*\.claude\.json' && deny "dev-loop: inspect Claude state via claude CLI commands, never read ~/.claude.json directly (MON-015)."
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])kill[[:space:]]+-(9|KILL|s[[:space:]]+(9|KILL))' && deny "dev-loop: bare kill -9 is forbidden; stop processes through job.py with session isolation (MON-015)."
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])gh[[:space:]]+pr[[:space:]]+merge([[:space:]]|$)' && deny "dev-loop: gh pr merge is a merge path; the operator merges (AGENTS.md)."
exit 0
