#!/usr/bin/env bash
# mios-init.sh -- bring a FRESH environment (a new cloud container, a new
# devcontainer, a bare Fedora box) up to a MiOS dev-loop starting point:
#
#   1. repos     locate or shallow-clone the four sibling repos (MiOS,
#                mios-bootstrap, -dev-loop, mios-micro) under one workspace
#                root; existing checkouts are never touched (no fetch, no
#                checkout, no branch change). The MiOS checkout is PINNED: a
#                directory counts as MiOS only when it is the root of a git
#                work tree whose origin is the MiOS repo
#                (https://github.com/mios-dev/MiOS, optional .git, or
#                git@github.com:mios-dev/MiOS; also the configured
#                MIOS_GITHUB_BASE/MiOS). Any other directory that carries
#                mios.toml + packages.sh is logged as "ignored: origin is <url>"
#                and skipped -- its packages.sh would run as root and its
#                prompt would be adopted. $PWD and its parent are never
#                candidates for the workspace root.
#                The pin is a trust statement, not a boundary: a directory at a
#                candidate path whose origin is SET to the MiOS URL is accepted,
#                because a local checkout is the operator's own working copy and
#                is trusted exactly as its packages.sh already is. The deployed
#                OS copy and GitHub main are the anchors when no such checkout
#                exists.
#   2. packages  install what MiOS's ONE .devcontainer/Containerfile installs:
#                  Fedora host  -> on the host itself, the Containerfile's
#                                  three installs: its dnf set
#                                  ([packages.devcontainer] of MiOS
#                                  usr/share/mios/mios.toml, resolved by MiOS
#                                  automation/lib/packages.sh, installed with
#                                  --setopt=install_weak_deps=False as the
#                                  Containerfile does; podman is in that set),
#                                  its global npm CLIs (parsed from the
#                                  Containerfile's `npm install -g` line, with
#                                  backslash-continued lines joined first, never
#                                  a copied list) and the agent-pipe venv
#                                  (python3.11 -m venv /usr/lib/mios/agents/.venv
#                                  + pip install -r the requirements.txt the
#                                  Containerfile's own pip install -r names,
#                                  followed back to the MiOS tree through its
#                                  COPY or staged path; skipped when the venv
#                                  already holds every distribution that file
#                                  names -- pip freeze, PEP 503 names -- never a
#                                  literal module list)
#                  other hosts  -> the Containerfile ITSELF, built as an image
#                                  by cloud-fedora-setup.sh (podman first,
#                                  docker where it is the host's only runtime);
#                                  the runtime that holds the image is the
#                                  setup script's own answer (--print-runtime,
#                                  which starts dockerd when needed, so a down
#                                  daemon never reads as "image absent"); an
#                                  existing image is never rebuilt, and the
#                                  wrapper ($FEDORA_WRAPPER_DIR/<name>, default
#                                  /usr/local/bin) is installed for that runtime
#                                  and verified to say so -- an existing wrapper
#                                  that names the other runtime (or none) is
#                                  rewritten the same way
#      tooling   setup-antigravity.sh --quiet (agy, keyring, grants, skill);
#                agy is its job on both paths
#   3. prompt    two files, each resolved the same pinned way -- the deployed
#                copy, else the pinned local MiOS checkout, else MiOS main on
#                GitHub -- and written under ${XDG_CACHE_HOME:-~/.cache}/mios/:
#                  identity   MiOS.md (MiOS repo root; deployed copy
#                             /ctx/rootmd/MiOS.md)             -> mios/MiOS.md
#                  context    usr/share/mios/ai/system.md (deployed copy
#                             /usr/share/mios/ai/system.md; the Global MiOS
#                             System Prompt, mios.toml ai_system_prompt)
#                                                             -> mios/system.md
#   4. summary   one JSON object on the LAST line of stdout
#
# Idempotent, non-interactive, safe to re-run. Every step is guarded and
# reported; exit is non-zero only when a REQUIRED step failed, and stderr names
# it. Required: repo:MiOS, packages, tooling, prompt. The other three repos are
# reported but optional. A run that selects no step at all is an error (exit 2
# for a contradictory flag pair), never ok. Every failure detail names the log
# it came from (a fetch failure names the curl stderr log, which holds curl's
# own message: a proxy refusal, a TLS or CA failure). URLs are logged and
# emitted with their credentials redacted: userinfo (https://user:TOKEN@host ->
# https://***@host) and the value of a credential query parameter (token,
# access_token, key, sig, signature, X-Amz-Signature; ?token=... -> ?token=***).
#
# Usage: bash mios-init.sh [--plan] [--no-packages] [--prompt-only] [--packages-only]
#   --plan           print what would run; change nothing (no clone, install, write)
#   --no-packages    skip step 2 (packages and tooling)
#   --prompt-only    step 3 only (no clone, no install)
#   --packages-only  steps 1 and 2a only (no tooling, no prompt) -- the package
#                    path by itself, e.g. inside an existing Fedora container
#   --prompt-only with --packages-only, or --packages-only with --no-packages,
#   select no step and are refused (exit 2).
#
# Environment:
#   MIOS_WORKSPACES               workspace root holding the sibling repos
#   MIOS_REPOS                    repos to locate/clone (default: MiOS mios-bootstrap -dev-loop mios-micro)
#   MIOS_GITHUB_BASE              clone base            (default https://github.com/mios-dev)
#   MIOS_TOML                     mios.toml to resolve packages from
#                                 (default <MiOS>/usr/share/mios/mios.toml)
#   MIOS_CONTAINERFILE            Containerfile whose `npm install -g` line names
#                                 the CLIs and whose `pip install -r` names the
#                                 venv's requirements file (default <MiOS>/.devcontainer/Containerfile)
#   MIOS_REQUIREMENTS             the venv's requirements file (default: the one
#                                 the Containerfile's pip install -r names, as a
#                                 file of <MiOS>)
#   MIOS_SYSTEM_PROMPT_URL        system.md fetch URL   (default MiOS main on raw.githubusercontent.com)
#   MIOS_SYSTEM_PROMPT_DEPLOYED   deployed system.md    (default /usr/share/mios/ai/system.md)
#   MIOS_IDENTITY_URL             MiOS.md fetch URL     (default MiOS main on raw.githubusercontent.com)
#   MIOS_IDENTITY_DEPLOYED        deployed MiOS.md      (default /ctx/rootmd/MiOS.md)
#   MIOS_OS_RELEASE               os-release file       (default /etc/os-release)
#   FEDORA_DEVCONTAINER_REPO / FEDORA_DEVCONTAINER_NAME / FEDORA_IMAGE
#                                 passed through to cloud-fedora-setup.sh
#   FEDORA_WRAPPER_DIR            where the wrapper lives (default /usr/local/bin;
#                                 cloud-fedora-setup.sh honours the same variable)
#   When not root, the proxy variables (HTTPS_PROXY https_proxy HTTP_PROXY
#   http_proxy NO_PROXY no_proxy) and every FEDORA_* / MIOS_* variable that is
#   set are forwarded to the sudo side through a 0600 temp file that root's sh
#   sources (never on sudo's argv, which is world-readable and syslogged);
#   values are never printed by this script.
set -u

SELF_DIR=$(cd "$(dirname "$0")" && pwd)
PLUGIN_ROOT=$(cd "$SELF_DIR/../../../.." && pwd)
# The sibling list, the GitHub base and the two raw URLs are literals here.
# MiOS keeps a registry of these repos in usr/share/mios/mios.toml
# [[artifacts.daily.repos]] (name, git_url, raw_base, api_base, default_branch)
# that lists MiOS, mios-bootstrap and -dev-loop -- mios-micro is MISSING from
# it. Once the registry carries all four, this script should read the list and
# the URLs from it instead of these literals (proposed contract update; the
# code is deliberately unchanged until then).
REPOS="${MIOS_REPOS:-MiOS mios-bootstrap -dev-loop mios-micro}"
GH_BASE="${MIOS_GITHUB_BASE:-https://github.com/mios-dev}"
MIOS_ORIGIN="https://github.com/mios-dev/MiOS"
RAW_BASE="https://raw.githubusercontent.com/mios-dev/MiOS/main"
PROMPT_URL="${MIOS_SYSTEM_PROMPT_URL:-$RAW_BASE/usr/share/mios/ai/system.md}"
IDENT_URL="${MIOS_IDENTITY_URL:-$RAW_BASE/MiOS.md}"
DEPLOYED="${MIOS_SYSTEM_PROMPT_DEPLOYED:-/usr/share/mios/ai/system.md}"
IDENT_DEPLOYED="${MIOS_IDENTITY_DEPLOYED:-/ctx/rootmd/MiOS.md}"
OS_RELEASE="${MIOS_OS_RELEASE:-/etc/os-release}"
CACHE_DIR="${XDG_CACHE_HOME:-${HOME:-/root}/.cache}/mios"
PROMPT_OUT="$CACHE_DIR/system.md"
IDENT_OUT="$CACHE_DIR/MiOS.md"
# The agent-pipe venv exactly as the Containerfile creates it. What must be in
# it is read from the requirements file the Containerfile installs, never
# listed here (a copied subset drifts silently).
VENV=/usr/lib/mios/agents/.venv
DC_REPO="${FEDORA_DEVCONTAINER_REPO:-https://github.com/mios-dev/MiOS}"
# The wrapper name exactly as cloud-fedora-setup.sh derives it: <repo>-dev.
DC_NAME="${FEDORA_DEVCONTAINER_NAME:-$(basename "${DC_REPO%/}" .git | tr '[:upper:]' '[:lower:]')-dev}"
DC_IMAGE="${FEDORA_IMAGE:-${DC_NAME}:latest}"
# Where the wrapper lives; cloud-fedora-setup.sh honours the same variable, so
# one setting names the same file on both sides.
WRAPPER_DIR="${FEDORA_WRAPPER_DIR:-/usr/local/bin}"
CFS="$SELF_DIR/cloud-fedora-setup.sh"
export GIT_TERMINAL_PROMPT=0

PLAN=0 DO_REPOS=1 DO_PKGS=1 DO_TOOLING=1 DO_PROMPT=1 MODE=run
OPT_PROMPT_ONLY=0 OPT_PKGS_ONLY=0 OPT_NO_PKGS=0
for a in "$@"; do
    case "$a" in
        --plan) PLAN=1; MODE=plan ;;
        --no-packages) DO_PKGS=0; DO_TOOLING=0; OPT_NO_PKGS=1 ;;
        --prompt-only) DO_REPOS=0; DO_PKGS=0; DO_TOOLING=0; OPT_PROMPT_ONLY=1 ;;
        --packages-only) DO_TOOLING=0; DO_PROMPT=0; OPT_PKGS_ONLY=1 ;;
        -h|--help) sed -n '2,/^set -u$/p' "$0" | sed -e '$d' -e 's/^# \{0,1\}//'; exit 0 ;;
        *) printf 'mios-init: unknown argument: %s (try --help)\n' "$a" >&2; exit 2 ;;
    esac
done
# Contradictory pairs select no step; refuse them instead of reporting an
# empty run as ok.
if [ "$OPT_PROMPT_ONLY$OPT_PKGS_ONLY" = 11 ]; then
    printf 'mios-init: contradictory flags --prompt-only and --packages-only: together they select no step\n' >&2; exit 2
fi
if [ "$OPT_PKGS_ONLY$OPT_NO_PKGS" = 11 ]; then
    printf 'mios-init: contradictory flags --packages-only and --no-packages: the package step is both the only step and skipped\n' >&2; exit 2
fi
if [ "$DO_REPOS$DO_PKGS$DO_TOOLING$DO_PROMPT" = 0000 ]; then
    printf 'mios-init: the given flags select no step (try --help)\n' >&2; exit 2
fi

log() { printf '[mios-init] %s\n' "$*"; }
jstr() { printf '"%s"' "$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\n\r\t')"; }
# Credentials never reach a log, the JSON or the transcript. Two forms are
# blanked: userinfo (anything between :// and the @ before the host: a token in
# https://user:TOKEN@host) and the value of a credential-carrying query
# parameter -- token, access_token, key, sig, signature, X-Amz-Signature,
# matched case-insensitively (GitHub's own ?token= form for private raw URLs
# among them). The names are spelled out as letter classes because sed's I
# flag is GNU-only. redact_stream filters stdin (a log, line by line);
# redact_url one string.
REDACT_PARAMS='[Tt][Oo][Kk][Ee][Nn]|[Aa][Cc][Cc][Ee][Ss][Ss]_[Tt][Oo][Kk][Ee][Nn]|[Kk][Ee][Yy]|[Ss][Ii][Gg]|[Ss][Ii][Gg][Nn][Aa][Tt][Uu][Rr][Ee]|[Xx]-[Aa][Mm][Zz]-[Ss][Ii][Gg][Nn][Aa][Tt][Uu][Rr][Ee]'
redact_stream() { sed -E -e 's#(://)[^/@]*@#\1***@#g' -e 's,([?&]('"$REDACT_PARAMS"')=)[^&#]*,\1***,g'; }
redact_url() { printf '%s' "$1" | redact_stream; }

STEPS="" FAILED_REQ="" REPOS_JSON="" RUNTIME=""
PROMPT_SHA="" PROMPT_SRC="" IDENT_SHA="" IDENT_SRC=""
# record NAME STATUS(ok|skipped|failed|planned) REQUIRED(1|0) DETAIL
record() {
    log "$1: $2 -- $4"
    [ -n "$STEPS" ] && STEPS="$STEPS,"
    _rq=false; [ "$3" = 1 ] && _rq=true
    STEPS="$STEPS{\"name\":$(jstr "$1"),\"status\":$(jstr "$2"),\"required\":$_rq,\"detail\":$(jstr "$4")}"
    if [ "$2" = failed ] && [ "$3" = 1 ]; then FAILED_REQ="${FAILED_REQ:+$FAILED_REQ }$1"; fi
}

# run "$@" as root: directly when root, else through non-interactive sudo.
# sudo's env_reset strips the environment, so the proxy variables and every
# FEDORA_* / MIOS_* variable that is set are re-applied on the far side -- but
# never on argv: a value there (HTTPS_PROXY with proxy credentials, a token in
# MIOS_GITHUB_BASE) is world-readable in /proc/<pid>/cmdline for the run and
# lands on sudo's syslog COMMAND= line. The pairs are written, shell-quoted,
# into a temp file created 0600 (mktemp under umask 077): root is the target,
# so root reading it is no leak, and no other user can. Root's sh sources the
# file and execs the command; argv carries the file's path only. The file is
# removed right after, and by an EXIT trap should the script die first. The
# names come from awk's ENVIRON (no env dump is ever printed).
as_root() {
    if [ "$(id -u)" = 0 ]; then "$@"; return $?; fi
    command -v sudo >/dev/null 2>&1 || { printf 'mios-init: not root and no sudo for: %s\n' "$*" >&2; return 1; }
    AS_ROOT_ENV=$(umask 077 && mktemp "${TMPDIR:-/tmp}/mios-init-env.XXXXXX") ||
        { printf 'mios-init: cannot create the env file for sudo\n' >&2; return 1; }
    trap '[ -z "${AS_ROOT_ENV:-}" ] || rm -f "$AS_ROOT_ENV"' EXIT
    for _v in HTTPS_PROXY https_proxy HTTP_PROXY http_proxy NO_PROXY no_proxy \
              $(awk 'BEGIN { for (k in ENVIRON) if (k ~ /^(FEDORA|MIOS)_[A-Za-z0-9_]*$/) print k }'); do
        eval "_val=\${$_v:-}"
        [ -n "$_val" ] || continue
        printf "export %s='%s'\n" "$_v" "$(printf '%s' "$_val" | sed "s/'/'\\\\''/g")"
    done >"$AS_ROOT_ENV"
    sudo -n sh -c '. "$1"; shift; exec "$@"' sh "$AS_ROOT_ENV" "$@"
    _rc=$?
    rm -f "$AS_ROOT_ENV"; AS_ROOT_ENV=""
    return $_rc
}

# is_mios DIR: DIR is a usable MiOS checkout -- it carries the two files this
# script consumes AND it is the root of a git work tree whose origin is the
# MiOS repo. Otherwise IS_MIOS_WHY says why, and a directory that only fails
# the pin starts with "ignored:". Read-only: rev-parse and remote get-url.
# The origin match is a trust statement (see the header), not a boundary.
IS_MIOS_WHY=""
is_mios() {
    IS_MIOS_WHY=""
    { [ -f "$1/usr/share/mios/mios.toml" ] && [ -f "$1/automation/lib/packages.sh" ]; } ||
        { IS_MIOS_WHY="no usr/share/mios/mios.toml + automation/lib/packages.sh under $1"; return 1; }
    # sh has no locals: these names are private to this function so a caller's
    # variables (fetch_doc's url) are never clobbered.
    _im_top=$(git -C "$1" rev-parse --show-toplevel 2>&1) ||
        { IS_MIOS_WHY="ignored: $1 is not a git work tree ($(printf '%s' "$_im_top" | tail -n 1))"; return 1; }
    [ "$_im_top" = "$(cd -P "$1" && pwd)" ] ||
        { IS_MIOS_WHY="ignored: $1 is not the root of its work tree ($_im_top)"; return 1; }
    _im_url=$(git -C "$1" remote get-url origin 2>/dev/null) ||
        { IS_MIOS_WHY="ignored: $1 has no origin remote"; return 1; }
    case "$_im_url" in
        "$MIOS_ORIGIN"|"$MIOS_ORIGIN.git"|git@github.com:mios-dev/MiOS|git@github.com:mios-dev/MiOS.git) return 0 ;;
        "$GH_BASE/MiOS"|"$GH_BASE/MiOS.git") return 0 ;;
    esac
    IS_MIOS_WHY="ignored: origin is $(redact_url "$_im_url") (not the MiOS repo)"
    return 1
}

# --- workspace root -----------------------------------------------------------
if [ -n "${MIOS_WORKSPACES:-}" ]; then
    WS="$MIOS_WORKSPACES" WS_FROM="MIOS_WORKSPACES"
else
    WS="" WS_FROM=""
    # $PWD and its parent are deliberately not candidates: a directory next to
    # wherever the shell happens to be must not become the checkout whose
    # packages.sh runs as root and whose prompt is adopted.
    for c in "$(dirname "$PLUGIN_ROOT")" /workspaces /home/user "${HOME:-/root}"; do
        if is_mios "$c/MiOS"; then WS="$c" WS_FROM="pinned MiOS checkout"; break; fi
        case "$IS_MIOS_WHY" in ignored:*) log "candidate $c/MiOS $IS_MIOS_WHY" ;; esac
    done
    if [ -z "$WS" ]; then
        if [ -d /workspaces ]; then WS=/workspaces WS_FROM="/workspaces"; else WS="${HOME:-/root}" WS_FROM="HOME"; fi
    fi
fi
MIOS_DIR="$WS/MiOS"
log "workspace root: $WS (from $WS_FROM)"

# --- 1. repos -----------------------------------------------------------------
if [ "$DO_REPOS" = 1 ]; then
    for r in $REPOS; do
        d="$WS/$r" req=0; [ "$r" = MiOS ] && req=1
        rurl=$(redact_url "$GH_BASE/$r")
        if [ -e "$d/.git" ]; then
            if [ "$r" = MiOS ] && ! is_mios "$d"; then
                state=ignored; record "repo:$r" failed "$req" "present at $d but $IS_MIOS_WHY; move it aside or point MIOS_WORKSPACES at the pinned checkout"
            else
                state=present; record "repo:$r" skipped "$req" "present at $d (left as is)"
            fi
        elif [ -e "$d" ] && [ -n "$(ls -A "$d" 2>/dev/null)" ]; then
            state=failed; record "repo:$r" failed "$req" "$d exists, is not empty and is not a git checkout"
        elif [ "$PLAN" = 1 ]; then
            state=planned; record "repo:$r" planned "$req" "would run: git clone --depth 1 -- $rurl $d"
        else
            mkdir -p "$CACHE_DIR" "$WS" 2>/dev/null
            clog="$CACHE_DIR/mios-init-clone-$r.log"
            ctmp="$CACHE_DIR/.clone.$r.$$"
            git clone --quiet --depth 1 -- "$GH_BASE/$r" "$d" >"$ctmp" 2>&1; rc=$?
            # git's own output can echo the URL it was given: redact before it is kept.
            redact_stream <"$ctmp" >"$clog" 2>/dev/null; rm -f "$ctmp"
            if [ "$rc" = 0 ]; then
                state=cloned; record "repo:$r" ok "$req" "shallow-cloned $rurl into $d (log $clog)"
            else
                state=failed; record "repo:$r" failed "$req" "git clone --depth 1 -- $rurl $d failed (rc $rc): $(tail -n 1 "$clog" 2>/dev/null) (log $clog)"
            fi
        fi
        [ -n "$REPOS_JSON" ] && REPOS_JSON="$REPOS_JSON,"
        REPOS_JSON="$REPOS_JSON$(jstr "$r"):{\"path\":$(jstr "$d"),\"state\":$(jstr "$state")}"
    done
fi

# --- 2a. packages -------------------------------------------------------------
is_fedora() {
    { command -v dnf5 >/dev/null 2>&1 || command -v dnf >/dev/null 2>&1; } || return 1
    [ -r "$OS_RELEASE" ] || return 1
    # shellcheck source=/dev/null
    ( . "$OS_RELEASE" && [ "${ID:-}" = fedora ] )
}

# probe_image: which runtime holds $DC_IMAGE. The decision is delegated to
# cloud-fedora-setup.sh --print-runtime under FEDORA_RUNTIME=auto: it applies
# image home (the runtime whose store already holds the image, when both are
# installed) and starts dockerd when it is down, so a cold session with both
# runtimes never reads an image docker holds as "absent". PROBE_RT is its
# answer -- the runtime a projection would build into -- and the return is 0
# when that runtime's store holds the image. Only without the setup script (or
# without root to run it) does a fallback ask podman, then docker, starting
# nothing.
PROBE_RT=""
probe_image() {
    PROBE_RT="" PROBE_NOTE=""
    # --plan changes nothing: the delegation below can start dockerd as root,
    # so a plan only inspects what is already running and says what it could
    # not see.
    if [ -f "$CFS" ] && [ "$PLAN" != 1 ]; then
        PROBE_RT=$( export FEDORA_RUNTIME=auto FEDORA_IMAGE="$DC_IMAGE" FEDORA_DEVCONTAINER_REPO="$DC_REPO" FEDORA_DEVCONTAINER_NAME="$DC_NAME"
                    as_root bash "$CFS" --print-runtime 2>/dev/null | head -n 1 )
    fi
    if [ -n "$PROBE_RT" ]; then
        "$PROBE_RT" image inspect "$DC_IMAGE" >/dev/null 2>&1
        return $?
    fi
    for rt in podman docker; do
        command -v "$rt" >/dev/null 2>&1 || continue
        [ -n "$PROBE_RT" ] || PROBE_RT=$rt
        "$rt" image inspect "$DC_IMAGE" >/dev/null 2>&1 && { PROBE_RT=$rt; return 0; }
        [ "$rt" = docker ] && ! docker info >/dev/null 2>&1 &&
            PROBE_NOTE="docker's daemon is down, so its image store was not checked (a real run starts it through $CFS --print-runtime and checks again)"
    done
    return 1
}

wrapper_runtime() { # prints the RUNTIME= the installed wrapper was written for (empty: none)
    sed -n 's/^RUNTIME=//p' "$WRAPPER_DIR/$DC_NAME" 2>/dev/null | head -n 1
}

# install_wrapper RT: (re)install $WRAPPER_DIR/$DC_NAME through the setup
# script's --wrapper-only for RT, the runtime that holds the image. RT is
# passed explicitly: auto would take podman when both runtimes are installed
# and write a wrapper that can never find the image, whose first call would
# rebuild everything there. The installed wrapper's RUNTIME= line is read back
# (the wrapper is generated; the line is "RUNTIME=<rt>"): returns 0 when it
# says RT, else WRAPPER_WHY says what went wrong. WRAPPER_RT is what it says.
WRAPPER_RT="" WRAPPER_WHY="" WLOG=""
install_wrapper() {
    mkdir -p "$CACHE_DIR" 2>/dev/null
    WLOG="$CACHE_DIR/mios-init-wrapper.log"
    WRAPPER_RT="" WRAPPER_WHY=""
    ( export FEDORA_DEVCONTAINER_REPO="$DC_REPO" FEDORA_DEVCONTAINER_NAME="$DC_NAME" FEDORA_IMAGE="$DC_IMAGE"
      export FEDORA_RUNTIME="$1" FEDORA_PROVISION_HOST=0
      as_root bash "$CFS" --wrapper-only ) >"$WLOG" 2>&1
    if [ ! -x "$WRAPPER_DIR/$DC_NAME" ]; then
        WRAPPER_WHY="cloud-fedora-setup.sh --wrapper-only did not install $WRAPPER_DIR/$DC_NAME: $(tail -n 2 "$WLOG" 2>/dev/null | tr '\n' ' ')"
        return 1
    fi
    WRAPPER_RT=$(wrapper_runtime)
    [ "$WRAPPER_RT" = "$1" ] && return 0
    WRAPPER_WHY="the installed $WRAPPER_DIR/$DC_NAME says RUNTIME=${WRAPPER_RT:-<none>}, not $1: a wrapper for the wrong runtime cannot find the image and would rebuild it there"
    return 1
}

# pep503 on stdin: distribution names normalised as pip compares them --
# lowercase, every run of - _ . as one - (ruamel.yaml, Ruamel_YAML and
# ruamel-yaml are one name).
pep503() { tr '[:upper:]' '[:lower:]' | sed -E 's/[-_.]+/-/g'; }

# req_dists FILE: the distribution names a requirements file names, one per
# line, normalised, sorted: each non-comment line's leading
# [A-Za-z0-9][A-Za-z0-9._-]* before any of <>=!~;[ or whitespace (extras,
# specifiers and markers dropped); option lines (-r, -e, --index-url) name no
# distribution and are skipped.
req_dists() {
    sed -E -e 's/#.*//' -e 's/^[[:space:]]+//' -e '/^[A-Za-z0-9]/!d' \
        -e 's/^([A-Za-z0-9][A-Za-z0-9._-]*).*/\1/' "$1" | pep503 | sort -u
}

# venv_satisfied REQS: every distribution REQS names is installed in $VENV,
# by pip freeze's names (PEP 503 normalised on both sides). VENV_COUNT is how
# many REQS names; on failure VENV_MISSING names the absent ones.
VENV_MISSING="" VENV_COUNT=0
venv_satisfied() {
    VENV_MISSING="" VENV_COUNT=0
    [ -x "$VENV/bin/python" ] || { VENV_MISSING="(no $VENV/bin/python)"; return 1; }
    _want=$(req_dists "$1")
    VENV_COUNT=$(printf '%s\n' "$_want" | grep -c .)
    [ "$VENV_COUNT" -gt 0 ] || { VENV_MISSING="(no distribution named in $1)"; return 1; }
    _have=$("$VENV/bin/python" -m pip freeze --all 2>/dev/null |
        sed -E -e 's/^-e .*#egg=//' -e 's/[[:space:]].*//' -e 's/[<>=!~@;[].*//' | pep503)
    for _d in $_want; do
        printf '%s\n' "$_have" | grep -qx -- "$_d" || VENV_MISSING="${VENV_MISSING:+$VENV_MISSING }$_d"
    done
    [ -z "$VENV_MISSING" ]
}

# reqs_from_containerfile TEXT (a Containerfile, continuation lines joined):
# the requirements file its `pip install` is given, as a file of $MIOS_DIR.
# The argument of -r / --requirement is followed back to the build context
# (the MiOS root): through the COPY line whose destination it is, when there
# is one (COPY <src> /tmp/reqs.txt; pip install -r /tmp/reqs.txt), else as the
# longest trailing part of that path, of two components or more, that is a file
# under $MIOS_DIR (a staged copy: /usr/src/mios-ssot/usr/lib/.../requirements.txt
# -> usr/lib/.../requirements.txt). Sets REQS_FILE; on failure REQS_WHY.
REQS_FILE="" REQS_WHY=""
reqs_from_containerfile() {
    REQS_FILE="" REQS_WHY=""
    _rp=$(printf '%s\n' "$1" | awk '/pip[^[:space:]]*[[:space:]]+install[[:space:]]/ {
            for (i = 1; i <= NF; i++) {
                if (($i == "-r" || $i == "--requirement") && i < NF) { print $(i + 1); exit }
                if ($i ~ /^--requirement=/) { sub(/^--requirement=/, "", $i); print $i; exit }
            } }' | sed -e 's/^["'"'"']//' -e 's/["'"'"';&]*$//')
    [ -n "$_rp" ] || { REQS_WHY="no pip install -r line"; return 1; }
    _src=$(printf '%s\n' "$1" | awk -v d="$_rp" 'toupper($1) == "COPY" && $NF == d { for (i = 2; i < NF; i++) if ($i !~ /^--/) { print $i; exit } }')
    if [ -n "$_src" ]; then
        [ -f "$MIOS_DIR/$_src" ] || { REQS_WHY="COPY source $_src of $_rp is not a file of the MiOS checkout"; return 1; }
        REQS_FILE="$MIOS_DIR/$_src"; return 0
    fi
    _sfx=${_rp#/}
    while :; do
        case "$_sfx" in */*) ;; *) break ;; esac
        [ -f "$MIOS_DIR/$_sfx" ] && { REQS_FILE="$MIOS_DIR/$_sfx"; return 0; }
        _sfx=${_sfx#*/}
    done
    REQS_WHY="pip is given $_rp; no COPY names it and no trailing part of it is a file of the MiOS checkout"
    return 1
}

packages_fedora() {
    toml="${MIOS_TOML:-$MIOS_DIR/usr/share/mios/mios.toml}"
    is_mios "$MIOS_DIR" ||
        { record packages failed 1 "no usable MiOS checkout at $MIOS_DIR ($IS_MIOS_WHY); packages.sh, mios.toml, the Containerfile and requirements.txt come from it"; return; }
    [ -f "$toml" ] || { record packages failed 1 "mios.toml not found: $toml"; return; }
    grep -q '^\[packages\.devcontainer\]' "$toml" ||
        { record packages failed 1 "[packages.devcontainer] is missing from $toml"; return; }
    errf=$(mktemp) || { record packages failed 1 "mktemp failed"; return; }
    # MIOS_TOML is exported before sourcing (globals.sh defaults it when unset)
    # and re-set after: sourcing common.sh -> userenv.sh with a MiOS checkout
    # as cwd was measured to reset it to /usr/share/mios/mios.toml.
    pkgs=$(cd / && MIOS_TOML="$toml" bash -c \
        '. "$1/automation/lib/packages.sh" >/dev/null || exit 3; MIOS_TOML="$2"; export MIOS_TOML; get_packages_strict devcontainer' \
        _ "$MIOS_DIR" "$toml" 2>"$errf")
    rc=$?
    err=$(tail -n 1 "$errf" 2>/dev/null); rm -f "$errf"
    if [ "$rc" != 0 ] || [ -z "$(printf '%s' "$pkgs" | tr -d '[:space:]')" ]; then
        record packages failed 1 "[packages.devcontainer] did not resolve through $MIOS_DIR/automation/lib/packages.sh (rc $rc): $err"
        return
    fi
    # shellcheck disable=SC2086
    n=$(printf '%s\n' $pkgs | grep -c .)
    dnf=dnf; command -v dnf5 >/dev/null 2>&1 && dnf=dnf5
    RUNTIME=podman
    # The Containerfile's other two installs. Its global npm CLIs are READ from
    # its `npm install -g` line (a copied list would drift); the venv is
    # recreated exactly as it does it, from the requirements file its pip installs.
    cf="${MIOS_CONTAINERFILE:-$MIOS_DIR/.devcontainer/Containerfile}"
    [ -f "$cf" ] || { record packages failed 1 "Containerfile not found: $cf (MIOS_CONTAINERFILE)"; return; }
    # Backslash-continued lines are joined before any line is parsed: a
    # `RUN npm install -g a \` split over two lines must not silently lose its
    # continuation.
    cfj=$(sed -e :a -e '/\\$/N; s/\\\n//; ta' "$cf")
    npm_line=$(printf '%s\n' "$cfj" | grep -m 1 -E '(^|[[:space:]])npm install -g[[:space:]]')
    [ -n "$npm_line" ] ||
        { record packages failed 1 "no 'npm install -g' line in $cf (MIOS_CONTAINERFILE): the CLI set is read from the Containerfile, never copied"; return; }
    clis=""
    for t in $(printf '%s\n' "$npm_line" | sed -e 's/.*npm install -g//' -e 's/[\\&;|].*//'); do
        case "$t" in -*) ;; *) clis="${clis:+$clis }$t" ;; esac
    done
    [ -n "$clis" ] || { record packages failed 1 "the 'npm install -g' line in $cf names no package"; return; }
    reqs="${MIOS_REQUIREMENTS:-}"
    if [ -z "$reqs" ]; then
        reqs_from_containerfile "$cfj" ||
            { record packages failed 1 "no 'pip install -r <file>' in $cf (MIOS_CONTAINERFILE) that maps to a file of $MIOS_DIR${REQS_WHY:+ ($REQS_WHY)}: the venv's requirements file is read from the Containerfile (or MIOS_REQUIREMENTS)"; return; }
        reqs=$REQS_FILE
    fi
    [ -f "$reqs" ] || { record packages failed 1 "requirements.txt not found: $reqs"; return; }
    cli_missing=""
    if command -v npm >/dev/null 2>&1; then
        for p in $clis; do npm ls -g --depth=0 "$p" >/dev/null 2>&1 || cli_missing="${cli_missing:+$cli_missing }$p"; done
    else
        cli_missing=$clis
    fi
    venv_ok=0; venv_satisfied "$reqs" && venv_ok=1
    if [ "$PLAN" = 1 ]; then
        d="Fedora host: would run: $dnf install -y --setopt=install_weak_deps=False <$n packages of [packages.devcontainer] from $toml>"
        if [ -n "$cli_missing" ]; then d="$d; would run: npm install -g $cli_missing (from $cf)"; else d="$d; npm CLIs from $cf: present ($clis)"; fi
        if [ "$venv_ok" = 1 ]; then d="$d; venv $VENV: already satisfied (all $VENV_COUNT distributions of $reqs installed)"
        else d="$d; venv $VENV: missing $VENV_MISSING (of $VENV_COUNT in $reqs); would run: python3.11 -m venv $VENV && pip install -r $reqs"; fi
        record packages planned 1 "$d"
        return
    fi
    mkdir -p "$CACHE_DIR" 2>/dev/null
    dlog="$CACHE_DIR/mios-init-dnf.log"
    # $pkgs is a whitespace-separated package list: word splitting is intended.
    # shellcheck disable=SC2086
    if as_root "$dnf" install -y --setopt=install_weak_deps=False $pkgs >"$dlog" 2>&1; then
        if grep -q 'Nothing to do' "$dlog"; then what="all already installed: Nothing to do"; else what="installed"; fi
        d="Fedora host: $dnf install -y --setopt=install_weak_deps=False of $n packages from [packages.devcontainer] ($what; log $dlog)"
    else
        why=$(grep -E 'No match for argument|Unable to find a match|unavailable|not available|Failed to resolve' "$dlog" 2>/dev/null | head -n 3 | tr '\n' ' ')
        [ -n "$why" ] || why=$(tail -n 2 "$dlog" 2>/dev/null | tr '\n' ' ')
        record packages failed 1 "Fedora host: $dnf install -y --setopt=install_weak_deps=False of $n packages failed: ${why}(log $dlog)"
        return
    fi
    command -v podman >/dev/null 2>&1 || RUNTIME=none
    nlog="$CACHE_DIR/mios-init-npm.log"
    if [ -n "$cli_missing" ]; then
        # shellcheck disable=SC2086
        if command -v npm >/dev/null 2>&1 && as_root npm install -g $cli_missing >"$nlog" 2>&1; then
            d="$d; npm CLIs from $cf: installed $cli_missing (log $nlog)"
        else
            record packages failed 1 "$d; npm install -g $cli_missing (from $cf) failed: $(tail -n 2 "$nlog" 2>/dev/null | tr '\n' ' ')(log $nlog)"
            return
        fi
    else
        d="$d; npm CLIs from $cf: present ($clis)"
    fi
    vlog="$CACHE_DIR/mios-init-venv.log"
    if [ "$venv_ok" = 1 ]; then
        d="$d; venv $VENV: already satisfied (all $VENV_COUNT distributions of $reqs installed)"
    elif ! command -v python3.11 >/dev/null 2>&1; then
        record packages failed 1 "$d; venv $VENV: python3.11 is not on PATH after the dnf set (log $dlog)"
        return
    elif as_root sh -c 'install -d -m 0755 "$1" && python3.11 -m venv "$2" && "$2/bin/pip" install --no-cache-dir -r "$3"' \
            _ "$(dirname "$VENV")" "$VENV" "$reqs" >"$vlog" 2>&1 && venv_satisfied "$reqs"; then
        d="$d; venv $VENV: created from $reqs (all $VENV_COUNT distributions installed; log $vlog)"
    else
        record packages failed 1 "$d; venv $VENV from $reqs failed: ${VENV_MISSING:+still missing $VENV_MISSING; }$(tail -n 2 "$vlog" 2>/dev/null | tr '\n' ' ')(log $vlog)"
        return
    fi
    record packages ok 1 "$d"
}

packages_projection() {
    how="non-Fedora host -> projection via $CFS (FEDORA_DEVCONTAINER_REPO=$DC_REPO)"
    [ -f "$CFS" ] || { record packages failed 1 "cloud-fedora-setup.sh not found beside $0"; return; }
    w="$WRAPPER_DIR/$DC_NAME"
    if probe_image; then
        rt=$PROBE_RT RUNTIME=$rt
        if [ -x "$w" ]; then
            # An existing wrapper is only as good as its RUNTIME= line: one left
            # by an earlier run for the other runtime, or by a generation that
            # wrote no such line, cannot find the image and would rebuild it
            # there on its first call. It is rewritten through the same
            # verified path as a missing one.
            wrt=$(wrapper_runtime)
            if [ "$wrt" = "$rt" ]; then
                record packages skipped 1 "$how: image $DC_IMAGE already present ($rt), not rebuilt; $w says RUNTIME=$wrt; enter it with $w"
                return
            fi
            if [ "$PLAN" = 1 ]; then
                record packages planned 1 "$how: image $DC_IMAGE present ($rt) but $w says RUNTIME=${wrt:-<none>}; would run: FEDORA_RUNTIME=$rt bash $CFS --wrapper-only (rewrites $w)"
                return
            fi
            if install_wrapper "$rt"; then
                record packages ok 1 "non-Fedora host: image $DC_IMAGE present ($rt); $w said RUNTIME=${wrt:-<none>}: wrapper rewritten for $rt, with $WRAPPER_DIR/fedora (log $WLOG)"
            else
                record packages failed 1 "non-Fedora host: image $DC_IMAGE lives in $rt, $w said RUNTIME=${wrt:-<none>} and after a rewrite for $rt $WRAPPER_WHY (log $WLOG)"
            fi
            return
        fi
        if [ "$PLAN" = 1 ]; then
            record packages planned 1 "$how: image $DC_IMAGE present ($rt); would run: FEDORA_RUNTIME=$rt bash $CFS --wrapper-only (installs $w)"
            return
        fi
        if install_wrapper "$rt"; then
            record packages ok 1 "non-Fedora host: image $DC_IMAGE present ($rt); installed $w for RUNTIME=$WRAPPER_RT (log $WLOG)"
        else
            record packages failed 1 "non-Fedora host: image $DC_IMAGE lives in $rt but $WRAPPER_WHY (log $WLOG)"
        fi
        return
    fi
    RUNTIME=${PROBE_RT:-none}
    if [ "$PLAN" = 1 ]; then
        if [ "$RUNTIME" = none ]; then
            note="image $DC_IMAGE not found and no runtime can run here (podman or docker; $CFS --print-runtime chose none)"
        else
            note="image $DC_IMAGE not found in $RUNTIME (the runtime $CFS --print-runtime selects)"
        fi
        [ -n "$PROBE_NOTE" ] && note="$note; $PROBE_NOTE"
        record packages planned 1 "non-Fedora host: $note; would run projection: FEDORA_DEVCONTAINER_REPO=$DC_REPO FEDORA_PROVISION_HOST=0 bash $CFS (builds MiOS .devcontainer/Containerfile as $DC_IMAGE, installs $w)"
        return
    fi
    mkdir -p "$CACHE_DIR" 2>/dev/null
    plog="$CACHE_DIR/mios-init-projection.log"
    log "projecting the MiOS devcontainer (several minutes on a cold host; log $plog)"
    # cloud-fedora-setup.sh always exits 0 by contract, so success is judged by
    # the image it must leave behind, not by its exit code.
    ( export FEDORA_DEVCONTAINER_REPO="$DC_REPO" FEDORA_DEVCONTAINER_NAME="$DC_NAME" FEDORA_IMAGE="$DC_IMAGE" FEDORA_PROVISION_HOST=0
      as_root bash "$CFS" ) >"$plog" 2>&1
    if probe_image; then
        rt=$PROBE_RT RUNTIME=$rt
        wrt=$(wrapper_runtime)
        if [ "$wrt" = "$rt" ]; then
            record packages ok 1 "non-Fedora host: projected $DC_IMAGE ($rt) from $DC_REPO; enter it with $w (RUNTIME=$wrt; log $plog)"
        else
            record packages failed 1 "non-Fedora host: projected $DC_IMAGE into $rt but $w says RUNTIME=${wrt:-<none>} (log $plog)"
        fi
    else
        record packages failed 1 "non-Fedora host: cloud-fedora-setup.sh left no $DC_IMAGE image: $(tail -n 2 "$plog" 2>/dev/null | tr '\n' ' ')(log $plog)"
    fi
}

if [ "$DO_PKGS" = 1 ]; then
    if is_fedora; then packages_fedora; else packages_projection; fi
fi

# --- 2b. host agent tooling ---------------------------------------------------
if [ "$DO_TOOLING" = 1 ]; then
    sa="$SELF_DIR/setup-antigravity.sh"
    if [ ! -f "$sa" ]; then
        record tooling failed 1 "setup-antigravity.sh not found beside $0"
    elif [ "$PLAN" = 1 ]; then
        record tooling planned 1 "would run: bash $sa --quiet"
    else
        mkdir -p "$CACHE_DIR" 2>/dev/null
        tlog="$CACHE_DIR/mios-init-tooling.log"
        if bash "$sa" --quiet >"$tlog" 2>&1; then
            agy=$(command -v agy 2>/dev/null || { [ -x "${HOME:-/root}/.local/bin/agy" ] && printf '%s' "${HOME:-/root}/.local/bin/agy"; })
            record tooling ok 1 "setup-antigravity.sh: agy ${agy:-not on PATH} (log $tlog)"
        else
            record tooling failed 1 "setup-antigravity.sh failed: $(tail -n 2 "$tlog" 2>/dev/null | tr '\n' ' ')(log $tlog)"
        fi
    fi
fi

# --- 3. the MiOS prompt: identity (MiOS.md) + context (system.md) ---------------
looks_markdown() { # non-empty text, not an HTML page, carries a markdown construct
    [ -s "$1" ] || { echo "empty"; return 1; }
    grep -Iq . "$1" || { echo "not text"; return 1; }
    first=$(grep -m 1 -v '^[[:space:]]*$' "$1")
    case "$first" in
        '<!DOCTYPE'*|'<!doctype'*|'<html'*|'<HTML'*) echo "an HTML page, not markdown"; return 1 ;;
    esac
    grep -Eq '^(#{1,6} |> |[-*] |[0-9]+\. |```)' "$1" || { echo "no markdown construct"; return 1; }
}

# fetch_doc LABEL DEPLOYED LOCAL URL OUT: resolve one file the pinned way --
# the deployed copy, else LOCAL when it lies in the pinned MiOS checkout, else
# URL -- and write it to OUT. Sets DOC_SRC and DOC_SHA; on failure DOC_WHY and
# returns 1. In --plan mode DOC_SRC is the source that would be used.
DOC_SRC="" DOC_SHA="" DOC_WHY=""
fetch_doc() {
    label=$1 deployed=$2 lpath=$3 url=$4 out=$5
    DOC_SRC="" DOC_SHA="" DOC_WHY="" src="" why=""
    for cand in "deployed:$deployed" "local:$lpath"; do
        kind=${cand%%:*} f=${cand#*:}
        [ -f "$f" ] || continue
        if [ "$kind" = local ] && ! is_mios "$MIOS_DIR"; then
            log "$label: local $f $IS_MIOS_WHY"
            why="$why local $f $IS_MIOS_WHY;"
            continue
        fi
        if bad=$(looks_markdown "$f"); then src="$kind $f"; break; fi
        why="$why $kind $f rejected ($bad);"
    done
    if [ "$PLAN" = 1 ]; then DOC_SRC="${src:-url $(redact_url "$url")}"; return 0; fi
    mkdir -p "$CACHE_DIR" || { DOC_WHY="cannot create $CACHE_DIR"; return 1; }
    tmp="$CACHE_DIR/.$(basename "$out").$$"
    if [ -n "$src" ]; then
        cp "${src#* }" "$tmp" || { rm -f "$tmp"; DOC_WHY="cannot copy ${src#* }"; return 1; }
    else
        # curl's stderr is kept: its own message names the cause (a proxy
        # refusal, rc 7; TLS, 35; an untrusted CA, 60) that the rc alone does
        # not. It can echo the URL, so it is redacted line by line first.
        flog="$CACHE_DIR/mios-init-fetch-$(basename "$out" .md).log"
        ftmp="$CACHE_DIR/.fetch.$(basename "$out").$$"
        curl -fsSL --compressed --retry 2 --max-time 60 -o "$tmp" "$url" 2>"$ftmp"
        rc=$?
        redact_stream <"$ftmp" >"$flog" 2>/dev/null; rm -f "$ftmp"
        if [ "$rc" != 0 ]; then
            rm -f "$tmp"
            DOC_WHY="fetch failed (curl rc $rc: $(tail -n 1 "$flog" 2>/dev/null)): $(redact_url "$url") (log $flog)${why:+ ;$why}"
            return 1
        fi
        if ! bad=$(looks_markdown "$tmp"); then
            rm -f "$tmp"
            DOC_WHY="$(redact_url "$url") returned $bad"
            return 1
        fi
        src="url $(redact_url "$url")"
    fi
    mv -f "$tmp" "$out" || { rm -f "$tmp"; DOC_WHY="cannot write $out"; return 1; }
    DOC_SHA=$(sha256sum "$out" | cut -d' ' -f1)
    DOC_SRC=$src
}

fetch_prompt() {
    fetch_doc "context system.md" "$DEPLOYED" "$MIOS_DIR/usr/share/mios/ai/system.md" "$PROMPT_URL" "$PROMPT_OUT" ||
        { record prompt failed 1 "$DOC_WHY"; return; }
    p_src=$DOC_SRC p_sha=$DOC_SHA
    fetch_doc "identity MiOS.md" "$IDENT_DEPLOYED" "$MIOS_DIR/MiOS.md" "$IDENT_URL" "$IDENT_OUT" ||
        { record prompt failed 1 "identity MiOS.md: $DOC_WHY"; return; }
    if [ "$PLAN" = 1 ]; then
        record prompt planned 1 "would write $PROMPT_OUT from $p_src; would write $IDENT_OUT (identity) from $DOC_SRC"
        return
    fi
    PROMPT_SHA=$p_sha PROMPT_SRC=$p_src IDENT_SHA=$DOC_SHA IDENT_SRC=$DOC_SRC
    record prompt ok 1 "$PROMPT_OUT sha256 $PROMPT_SHA from $PROMPT_SRC; identity $IDENT_OUT sha256 $IDENT_SHA from $IDENT_SRC"
}

[ "$DO_PROMPT" = 1 ] && fetch_prompt

# --- 4. summary ---------------------------------------------------------------
if [ -z "$RUNTIME" ]; then
    if command -v podman >/dev/null 2>&1; then RUNTIME=podman
    elif command -v docker >/dev/null 2>&1; then RUNTIME=docker
    else RUNTIME=none; fi
fi
if [ -z "$STEPS" ]; then
    # Unreachable through the flag checks above; kept so an empty run can
    # never be reported ok.
    printf 'mios-init: no step ran -- an empty run is never ok\n' >&2
    FAILED_REQ="(no step ran)"
fi
ok=true; [ -n "$FAILED_REQ" ] && ok=false
fr=""; for s in $FAILED_REQ; do fr="${fr:+$fr,}$(jstr "$s")"; done
pp=null ip=null
if [ "$DO_PROMPT" = 1 ]; then pp=$(jstr "$PROMPT_OUT"); ip=$(jstr "$IDENT_OUT"); fi
if [ -n "$FAILED_REQ" ]; then
    printf 'mios-init: FAILED required step(s): %s\n' "$FAILED_REQ" >&2
fi
printf '{"tool":"mios-init","mode":%s,"ok":%s,"failed_required":[%s],"steps":[%s],"prompt":{"path":%s,"sha256":%s,"source":%s,"identity_path":%s,"identity_sha256":%s,"identity_source":%s},"runtime":%s,"workspace":%s,"repos":{%s}}\n' \
    "$(jstr "$MODE")" "$ok" "$fr" "$STEPS" "$pp" "$(jstr "$PROMPT_SHA")" "$(jstr "$PROMPT_SRC")" \
    "$ip" "$(jstr "$IDENT_SHA")" "$(jstr "$IDENT_SRC")" \
    "$(jstr "$RUNTIME")" "$(jstr "$WS")" "$REPOS_JSON"
[ -z "$FAILED_REQ" ]
