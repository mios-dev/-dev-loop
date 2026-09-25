#!/usr/bin/env sh
# Register the dev-loop hook wiring with every harness that has a native hook API.
#
#   sh hooks/register-hooks.sh [--all] [--user] [--project] [--dry-run]
#                              [--harness claude,antigravity,codex,gemini,copilot,cursor,opencode]
#
# Mirrors skills/dev-loop/scripts/install.sh: a pipe-delimited TABLE of
# harness|detect|... and harnesses whose CLI is absent are skipped unless --all or
# --harness names them. Default scope here is --user (install.sh defaults to project).
#
# Idempotence: this compares CONTENT, not presence. A presence-only check is the bug
# it exists to avoid -- a file that already exists can never be updated, so the
# wiring rots silently the first time a hook script or a harness path changes.
#
# What it writes: hook manifests that make each harness execute the scripts in this
# directory. Those scripts are arbitrary shell, run at session start and on tool
# calls. That is a real privilege. So: every path it touches is printed; the
# manifests reference this repo IN PLACE rather than copying it (the one exception
# is OpenCode, whose plugin module must live in the plugins directory); and
# --dry-run prints the entire plan without writing anything.
set -eu

HOOKS=$(cd "$(dirname "$0")" && pwd)
PLUG=$(cd "$HOOKS/.." && pwd)
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
H=${HOME:-~}
ALL=0; USER_SCOPE=1; DRY=0; ONLY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --all) ALL=1;;
    --user|--global) USER_SCOPE=1;;
    --project) USER_SCOPE=0;;
    --dry-run) DRY=1;;
    --harness) [ $# -ge 2 ] || { echo "--harness needs a value" >&2; exit 64; }; ONLY=$2; shift;;
    -h|--help) sed -n '2,25p' "$0"; exit 0;;
    *) echo "unknown $1" >&2; exit 64;;
  esac
  shift
done

# name | detect | mechanism | asset (relative to hooks/; - = derive from hooks/hooks.json)
#      | user dest | project dest | mode
#
# mechanism "-" means NO native hook API is known for that harness. Those rows are
# reported out loud and nothing is written for them: a file a harness never reads is
# worse than no file.
#
# mode  merge-hooks = merge the asset's "hooks" object into the destination JSON,
#                     replacing only dev-loop-owned entries and leaving the rest alone
#       named       = replace the destination's "dev-loop" top-level key
#       file        = write the asset whole (its own file; nothing else to preserve)
TABLE='
claude|claude|settings-hooks|-|'"$H"'/.claude/settings.json|.claude/settings.json|merge-hooks
antigravity|agy|hooks.json|antigravity/hooks.json|'"$H"'/.gemini/config/hooks.json|.agents/hooks.json|named
codex|codex|hooks.json|codex/hooks.json|'"$H"'/.codex/hooks.json|.codex/hooks.json|merge-hooks
gemini|gemini|settings-hooks|gemini/hooks.fragment.json|'"$H"'/.gemini/settings.json|.gemini/settings.json|merge-hooks
copilot|.github|hooks-dir|copilot/dev-loop.json|'"$H"'/.copilot/hooks/dev-loop.json|.github/hooks/dev-loop.json|file
cursor|.cursor|hooks.json|cursor/hooks.json|'"$H"'/.cursor/hooks.json|.cursor/hooks.json|merge-hooks
opencode|opencode|plugin-module|opencode/dev-loop.js|'"$H"'/.config/opencode/plugins/dev-loop.js|.opencode/plugins/dev-loop.js|file
hermes|hermes|-|-|-|-|-
'

# A --harness name that is not in the table is an error, not a silent no-op.
if [ -n "$ONLY" ]; then
  for want in $(printf '%s' "$ONLY" | tr ',' ' '); do
    printf '%s' "$TABLE" | cut -d'|' -f1 | grep -qx "$want" \
      || { echo "unknown harness: $want (known: $(printf '%s' "$TABLE" | cut -d'|' -f1 | tr -s '\n' ' '))" >&2; exit 64; }
  done
fi

[ "$DRY" = 1 ] && echo "(dry run -- nothing will be written)" || true
RC=0
OLDIFS=$IFS
IFS='
'
for row in $TABLE; do
  IFS='|'
  # shellcheck disable=SC2086
  set -- $row
  IFS=$OLDIFS
  name=$1; det=$2; mech=$3; asset=$4; udest=$5; pdest=$6; mode=$7
  [ -n "$name" ] || continue
  case ",$ONLY," in ",,"|*",$name,"*) ;; *) continue;; esac

  if [ "$mech" = "-" ]; then
    echo "[$name] SKIP: no native hook mechanism is known for this harness -- nothing written."
    continue
  fi

  if [ "$ALL" = 0 ] && [ -z "$ONLY" ] \
     && ! command -v "$det" >/dev/null 2>&1 \
     && [ ! -e "$ROOT/$det" ] && [ ! -e "$H/$det" ]; then
    echo "[$name] skipped: not installed here (looked for '$det'). Use --all or --harness $name to wire it anyway."
    continue
  fi

  if [ "$USER_SCOPE" = 1 ]; then DEST="$udest"; else
    case "$pdest" in /*) DEST="$pdest";; *) DEST="$ROOT/$pdest";; esac
  fi
  case "$asset" in -) SRC="$HOOKS/hooks.json";; *) SRC="$HOOKS/$asset";; esac
  if [ ! -f "$SRC" ]; then
    echo "[$name] ERROR: missing asset $SRC" >&2; RC=1; continue
  fi

  python3 - "$name" "$mode" "$SRC" "$DEST" "$HOOKS" "$PLUG" "$DRY" <<'PY' || RC=1
import json, os, re, sys

name, mode, src, dest, hooks_dir, plug, dry = sys.argv[1:8]
dry = dry == "1"

# Every command this repo installs names either the per-harness adapter or one of
# the hook scripts. That is the identity used to find OUR entries in a shared file
# and replace them, without touching anyone else's hooks.
OURS = re.compile(r"devloop-hook\.(py|js)|/hooks/(guard|no-env|format|stop-gate|"
                  r"session-start|prompt-context|pre-compact)\.sh")

raw = open(src, encoding="utf-8").read()
raw = raw.replace("${DEVLOOP_HOOKS}", hooks_dir).replace("${CLAUDE_PLUGIN_ROOT}", plug)

def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None
    except Exception as e:
        print("[%s] ERROR: %s is not valid JSON (%s); refusing to overwrite it" % (name, path, e),
              file=sys.stderr)
        sys.exit(1)

if mode == "file":
    desired = raw
    try:
        with open(dest, encoding="utf-8") as fh:
            current = fh.read()
    except FileNotFoundError:
        current = None
else:
    asset = json.loads(raw)
    cur = load(dest)
    current = json.dumps(cur, indent=2, sort_keys=True) + "\n" if cur is not None else None
    doc = json.loads(json.dumps(cur)) if isinstance(cur, dict) else {}

    if mode == "named":
        for key, val in asset.items():
            doc[key] = val
    else:  # merge-hooks
        if "version" in asset and "version" not in doc:
            doc["version"] = asset["version"]
        events = doc.get("hooks")
        if not isinstance(events, dict):
            events = {}
        # Drop every dev-loop entry anywhere in the destination first, so events we
        # no longer wire do not linger, then add the current ones back.
        for ev in list(events):
            kept = [e for e in events[ev] if not OURS.search(json.dumps(e))]
            if kept:
                events[ev] = kept
            else:
                del events[ev]
        for ev, entries in asset.get("hooks", {}).items():
            events.setdefault(ev, [])
            events[ev] = events[ev] + list(entries)
        doc["hooks"] = events
    desired = json.dumps(doc, indent=2, sort_keys=True) + "\n"

if current == desired:
    print("[%s] ok (unchanged): %s" % (name, dest))
    sys.exit(0)

verb = "would install" if dry and current is None else \
       "would refresh" if dry else \
       "installed" if current is None else "refreshed"
print("[%s] %s: %s" % (name, verb, dest))
if dry:
    sys.exit(0)
os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
tmp = dest + ".devloop-tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    fh.write(desired)
os.replace(tmp, dest)
PY
done
IFS=$OLDIFS

echo "hook scripts live in $HOOKS and are referenced in place; re-run after moving this repo."
exit $RC
