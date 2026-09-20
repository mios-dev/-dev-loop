#!/usr/bin/env sh
# register-mcp.sh — register the dev-loop MCP stdio server (scripts/devloop_mcp.py) with every
# harness that has a native MCP client config. User scope by default; --project where the harness
# has a project scope. Merges into existing config (other servers and unrelated settings survive),
# parse-checks what it wrote, and refreshes a stale entry rather than only filling an absent one.
#
#   sh skills/dev-loop/scripts/register-mcp.sh [--user|--project] [--dry-run] [--check] [--all]
#        [--harness claude,antigravity,codex,gemini,copilot,cursor,opencode] [--repo DIR]
#        [--server PATH] [--force] [--name NAME]
#
# The portability problem this exists to solve: the plugin's .mcp.json registers the server as
# "${CLAUDE_PLUGIN_ROOT}/skills/dev-loop/scripts/devloop_mcp.py". Measured: Claude Code expands
# ${VAR} at spawn and sets CLAUDE_PLUGIN_ROOT only for plugin-loaded servers; Antigravity performs
# NO substitution at all (the variable reached the child's ENVIRONMENT while argv stayed literal);
# Cursor uses ${env:NAME}, OpenCode uses {env:VAR}, Gemini CLI uses $VAR/${VAR}, and Codex and
# Copilot document none. One bare ${VAR} spelling therefore cannot serve seven harnesses, so every
# file this script writes carries an ABSOLUTE path resolved at registration time. The plugin
# manifest route is the sole exception and this script never touches it.
#
# Confidence is not flattened: claude and antigravity paths/shapes were verified live against the
# installed CLIs; codex, gemini, copilot, cursor and opencode come from vendor docs only and are
# printed as "unverified". Harness CLI surfaces drift — re-probe before trusting them:
#   python3 skills/dev-loop/scripts/adapters.py probe
set -eu

SRC=$(cd "$(dirname "$0")/.." && pwd)                 # skills/dev-loop
NAME=${DEVLOOP_MCP_NAME:-dev-loop}
SERVER=${DEVLOOP_MCP_SERVER:-$SRC/scripts/devloop_mcp.py}
SCOPE=user; DRY=0; CHECK=0; ALL=0; ONLY=""; FORCE=0; ROOT=""
PY=${PYTHON:-python3}

usage() { sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }
while [ $# -gt 0 ]; do
  case "$1" in
    --user|--global) SCOPE=user ;;
    --project) SCOPE=project ;;
    --dry-run) DRY=1 ;;
    --check) CHECK=1 ;;
    --all) ALL=1 ;;
    --force) FORCE=1 ;;
    --harness) ONLY=$2; shift ;;
    --repo) ROOT=$2; shift ;;
    --server) SERVER=$2; shift ;;
    --name) NAME=$2; shift ;;
    -h|--help) usage 0 ;;
    *) echo "register-mcp: unknown argument $1" >&2; usage 64 ;;
  esac
  shift
done

[ -f "$SERVER" ] || { echo "register-mcp: no such server script: $SERVER" >&2; exit 66; }
SERVER=$(cd "$(dirname "$SERVER")" && pwd)/$(basename "$SERVER")   # absolute, because only Claude Code expands ${VAR}
[ -n "$ROOT" ] || ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
ROOT=$(cd "$ROOT" && pwd)
H=${HOME:-~}
ENVJSON='{"CI": "1", "GIT_TERMINAL_PROMPT": "0"}'

# name | cli | format | container key | user path | project path ('' = harness has no project scope) | confidence | native verify cmd ('' = none verified) | entry template (@@P@@ = absolute server path)
#   json  -> merge under the container key of a JSON object, preserving every other key
#   toml  -> merge the [<key>.<name>] table of a TOML file, preserving every other table
#   none  -> the harness has no MCP client config at all; it is skipped with the reason
# Shapes differ on purpose and are not interchangeable: copilot uses "type":"local" plus a "tools"
# selector, opencode fuses argv into one "command" array under a top-level "mcp" key and calls the
# env block "environment", antigravity adds "disabled", codex is TOML.
TABLE='
claude|claude|json|mcpServers|'"$H"'/.claude.json|.mcp.json|verified|claude mcp get @@N@@|{"type": "stdio", "command": "python3", "args": ["@@P@@"], "env": '"$ENVJSON"'}
antigravity|agy|json|mcpServers|'"$H"'/.gemini/config/mcp_config.json||verified|agy mcp list|{"command": "python3", "args": ["@@P@@"], "env": '"$ENVJSON"', "disabled": false}
codex|codex|toml|mcp_servers|'"$H"'/.codex/config.toml|.codex/config.toml|unverified||{"command": "python3", "args": ["@@P@@"], "env": '"$ENVJSON"'}
gemini|gemini|json|mcpServers|'"$H"'/.gemini/settings.json|.gemini/settings.json|unverified||{"command": "python3", "args": ["@@P@@"], "env": '"$ENVJSON"'}
copilot|copilot|json|mcpServers|'"${COPILOT_HOME:-$H/.copilot}"'/mcp-config.json|.copilot/mcp-config.json|unverified||{"type": "local", "command": "python3", "args": ["@@P@@"], "env": '"$ENVJSON"', "tools": ["*"]}
cursor|agent|json|mcpServers|'"$H"'/.cursor/mcp.json|.cursor/mcp.json|unverified||{"command": "python3", "args": ["@@P@@"], "env": '"$ENVJSON"'}
opencode|opencode|json|mcp|'"${XDG_CONFIG_HOME:-$H/.config}"'/opencode/opencode.json|opencode.json|unverified||{"type": "local", "command": ["python3", "@@P@@"], "enabled": true, "environment": '"$ENVJSON"'}
openai-compatible|-|none||||n/a||'

TMPD=$(mktemp -d); trap 'rm -rf "$TMPD"' EXIT INT TERM
printf '%s\n' "$TABLE" | grep -v '^[[:space:]]*$' > "$TMPD/table"

MODE="write"
if [ "$CHECK" = 1 ]; then MODE="check"; elif [ "$DRY" = 1 ]; then MODE="dry"; fi
printf 'dev-loop MCP registration  server=%s  scope=%s  mode=%s\n' "$SERVER" "$SCOPE" "$MODE"
if [ "$SCOPE" = project ]; then printf 'project root: %s\n' "$ROOT"; fi

FAILED=0; TOUCHED=0
while IFS='|' read -r hname cli fmt key upath ppath conf vnative tmpl; do
  [ -n "$hname" ] || continue
  if [ -n "$ONLY" ]; then
    case ",$ONLY," in *",$hname,"*) : ;; *) continue ;; esac
  fi

  if [ "$fmt" = none ]; then
    printf '%-18s SKIP        no MCP client config exists for this runtime; expose the loop host-side from %s/assets/openai-tools.json instead\n' "$hname" "$SRC"
    continue
  fi
  if [ "$ALL" = 0 ] && ! command -v "$cli" >/dev/null 2>&1; then
    printf '%-18s SKIP        %s not on PATH (pass --all to write the config anyway)\n' "$hname" "$cli"
    continue
  fi

  if [ "$SCOPE" = project ]; then
    if [ -z "$ppath" ]; then
      printf '%-18s SKIP        no project scope: this harness reads MCP config only from %s (re-run with --user to write it, knowing it applies machine-wide)\n' "$hname" "$upath"
      continue
    fi
    file=$ROOT/$ppath
  else
    file=$upath
  fi

  tmpl=$(printf '%s' "$tmpl" | sed "s|@@P@@|$SERVER|g")
  out=$("$PY" - "$MODE" "$file" "$fmt" "$key" "$NAME" "$SERVER" "$tmpl" "$FORCE" <<'PY'
import json, os, re, shutil, sys, tempfile

mode, path, fmt, key, name, server, tmpl, force = sys.argv[1:9]
force = force == "1"
desired = json.loads(tmpl)

def say(status, msg):
    print("%s %s" % (status, msg))
    raise SystemExit(0)

BARE = re.compile(r"^[A-Za-z0-9_-]+$")
def tkey(k):
    return k if BARE.match(k) else json.dumps(k)

def tval(v):
    if isinstance(v, bool):  return "true" if v else "false"
    if isinstance(v, str):   return json.dumps(v)          # TOML basic string == JSON string
    if isinstance(v, (int, float)): return repr(v)
    if isinstance(v, list):  return "[" + ", ".join(tval(x) for x in v) + "]"
    if isinstance(v, dict):  return "{ " + ", ".join("%s = %s" % (tkey(k), tval(x)) for k, x in v.items()) + " }"
    raise TypeError(v)

def toml_block(table, name, entry):
    body = "".join("%s = %s\n" % (tkey(k), tval(v)) for k, v in entry.items())
    return "[%s.%s]\n%s" % (table, tkey(name), body)

def load(text):
    """Return (whole document as dict, the container dict holding named servers)."""
    if fmt == "json":
        doc = json.loads(text) if text.strip() else {}
        if not isinstance(doc, dict):
            raise ValueError("top level is not an object")
        box = doc.get(key)
        return doc, (box if isinstance(box, dict) else {})
    import tomllib
    doc = tomllib.loads(text)
    box = doc.get(key)
    return doc, (box if isinstance(box, dict) else {})

text = ""
if os.path.exists(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    try:
        doc, box = load(text)
    except Exception as exc:                       # noqa: BLE001 - any parse failure is the same decision
        if not force:
            say("ERROR", "%s is not valid %s (%s); refusing to overwrite it - fix it or pass --force" % (path, fmt, exc))
        doc, box, text = {}, {}, ""
else:
    doc, box = {}, {}

current = box.get(name)
pre_siblings = [k for k in box if k != name]   # must survive the merge, whatever the format
same = current == desired

if mode == "check":
    if current is None:
        say("MISSING", "%s not registered in %s" % (name, path))
    if same:
        say("OK", "%s in %s is current (%s)" % (name, path, server))
    say("STALE", "%s in %s does not match the current server path %s -> re-run without --check" % (name, path, server))

if current is not None and not same and "${CLAUDE_PLUGIN_ROOT}" in json.dumps(current) and not force:
    say("SKIP", "%s holds a ${CLAUDE_PLUGIN_ROOT}-relative entry - that is the Claude Code plugin pointer, which only the plugin loader expands (installed, the server is named plugin:%s:%s). Not rewriting it; pass --force to replace it with an absolute path." % (path, name, name))

if same:
    say("OK", "%s already current in %s" % (name, path))

verb = "created" if current is None else "refreshed"
if mode == "dry":
    say("DRY", "would %s %s in %s" % ("create" if current is None else "refresh", name, path))

# ---- merge, preserving every unrelated key -------------------------------------------------
if fmt == "json":
    box = doc.get(key)
    if not isinstance(box, dict):
        box = {}
    box[name] = desired
    doc[key] = box
    new_text = json.dumps(doc, indent=2) + "\n"
else:
    lines = text.splitlines(True)
    hdr = re.compile(r'^\s*\[\s*%s\s*\.\s*("?)%s\1\s*\]\s*$' % (re.escape(key), re.escape(name)))
    start, end = None, len(lines)
    for i, ln in enumerate(lines):
        if start is None:
            if hdr.match(ln):
                start = i
            continue
        if ln.lstrip().startswith("["):
            end = i
            break
    block = toml_block(key, name, desired)
    if start is None:
        sep = "" if (not text or text.endswith("\n\n")) else ("\n" if text.endswith("\n") else "\n\n")
        new_text = text + sep + block
    else:
        new_text = "".join(lines[:start]) + block + "".join(lines[end:])

backup = None
if os.path.exists(path):
    backup = path + ".devloop-bak"
    shutil.copy2(path, backup)
else:
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)

fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".devloop-mcp-")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    os.replace(tmp, path)
except Exception:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise

# ---- parse-check what was written, and roll back if it is wrong ----------------------------
def rollback():
    if backup:
        shutil.copy2(backup, path)
    elif os.path.exists(path):
        os.unlink(path)

try:
    with open(path, encoding="utf-8") as fh:
        rdoc, rbox = load(fh.read())
    if rbox.get(name) != desired:
        raise ValueError("%s read back as %r" % (name, rbox.get(name)))
    lost = [k for k in pre_siblings if k not in rbox]
    if lost:
        raise ValueError("lost sibling servers %s" % lost)
except Exception as exc:                            # noqa: BLE001
    rollback()
    say("ERROR", "wrote %s but it did not parse back correctly (%s); restored the previous contents" % (path, exc))

siblings = [k for k in rbox if k != name]
say("WROTE", "%s %s in %s%s" % (verb, name, path, (" (kept %d other server(s): %s)" % (len(siblings), ", ".join(sorted(siblings)))) if siblings else ""))
PY
)
  st=${out%% *}; msg=${out#* }
  printf '%-18s %-11s %s [%s]\n' "$hname" "$st" "$msg" "$conf"
  case "$st" in
    ERROR|STALE|MISSING) FAILED=$((FAILED + 1)) ;;
    WROTE|OK|DRY) TOUCHED=$((TOUCHED + 1)) ;;
  esac

  if [ "$st" = WROTE ] || [ "$st" = OK ] || [ "$st" = DRY ]; then
    scopeflag=""
    if [ "$SCOPE" = project ]; then scopeflag=" --project"; fi
    printf '%18s verify: sh %s/scripts/register-mcp.sh --check --all --harness %s%s\n' "" "$SRC" "$hname" "$scopeflag"
    if [ -n "$vnative" ]; then
      printf '%18s verify (native, %s): %s\n' "" "$conf" "$(printf '%s' "$vnative" | sed "s|@@N@@|$NAME|g")"
    fi
  fi
done < "$TMPD/table"

if [ "$SCOPE" = project ] && [ "$CHECK" = 0 ] && [ "$DRY" = 0 ]; then
  printf 'note: a project-scope MCP server in Claude Code needs interactive approval before it connects, and Codex reads .codex/config.toml only for a trusted project.\n'
fi
printf 'targets handled: %d   problems: %d\n' "$TOUCHED" "$FAILED"
[ "$FAILED" = 0 ] || exit 1
