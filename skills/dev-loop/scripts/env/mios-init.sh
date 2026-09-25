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
#   2. packages  install what MiOS's ONE .devcontainer/Containerfile installs:
#                  Fedora host  -> on the host itself, the Containerfile's
#                                  three installs: its dnf set
#                                  ([packages.devcontainer] of MiOS
#                                  usr/share/mios/mios.toml, resolved by MiOS
#                                  automation/lib/packages.sh, installed with
#                                  --setopt=install_weak_deps=False as the
#                                  Containerfile does; podman is in that set),
#                                  its global npm CLIs (parsed from the
#                                  Containerfile's `npm install -g` line, never
#                                  a copied list) and the agent-pipe venv
#                                  (python3.11 -m venv /usr/lib/mios/agents/.venv
#                                  + pip install -r usr/lib/mios/agent-pipe/
#                                  requirements.txt; skipped when the venv
#                                  already imports fastapi httpx mcp pydantic
#                                  uvicorn)
#                  other hosts  -> the Containerfile ITSELF, built as an image
#                                  by cloud-fedora-setup.sh (podman first,
#                                  docker where it is the host's only runtime);
#                                  an existing image is never rebuilt, and the
#                                  wrapper is installed for the runtime that
#                                  holds the image and verified to say so
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
# it came from. URLs are logged and emitted with their userinfo redacted
# (https://user:TOKEN@host -> https://***@host).
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
#                                 the CLIs (default <MiOS>/.devcontainer/Containerfile)
#   MIOS_SYSTEM_PROMPT_URL        system.md fetch URL   (default MiOS main on raw.githubusercontent.com)
#   MIOS_SYSTEM_PROMPT_DEPLOYED   deployed system.md    (default /usr/share/mios/ai/system.md)
#   MIOS_IDENTITY_URL             MiOS.md fetch URL     (default MiOS main on raw.githubusercontent.com)
#   MIOS_IDENTITY_DEPLOYED        deployed MiOS.md      (default /ctx/rootmd/MiOS.md)
#   MIOS_OS_RELEASE               os-release file       (default /etc/os-release)
#   FEDORA_DEVCONTAINER_REPO / FEDORA_DEVCONTAINER_NAME / FEDORA_IMAGE
#                                 passed through to cloud-fedora-setup.sh
#   When not root, the proxy variables (HTTPS_PROXY https_proxy HTTP_PROXY
#   http_proxy NO_PROXY no_proxy) and every FEDORA_* / MIOS_* variable that is
#   set are forwarded through `sudo -n env NAME=value ...` (sudo's env_reset
#   would strip them); values are never printed by this script.
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
# The agent-pipe venv exactly as the Containerfile creates it, and the modules
# whose import proves it is already satisfied.
VENV=/usr/lib/mios/agents/.venv
VENV_MODULES="fastapi httpx mcp pydantic uvicorn"
DC_REPO="${FEDORA_DEVCONTAINER_REPO:-https://github.com/mios-dev/MiOS}"
DC_NAME="${FEDORA_DEVCONTAINER_NAME:-mios-dev}"
DC_IMAGE="${FEDORA_IMAGE:-${DC_NAME}:latest}"
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
# Userinfo (anything between :// and the @ before the host) is never logged or
# emitted: a token in https://user:TOKEN@host would land in the transcript.
redact_url() { printf '%s' "$1" | sed -E 's#(://)[^/@]*@#\1***@#g'; }

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
# FEDORA_* / MIOS_* variable that is set are re-applied on the far side as
# `env NAME=value` arguments. The names come from awk's ENVIRON (no env dump
# is ever printed); positional parameters are the only list POSIX sh has, so
# the pairs are appended after the command and the command is then rotated
# to the end.
as_root() {
    if [ "$(id -u)" = 0 ]; then "$@"; return $?; fi
    command -v sudo >/dev/null 2>&1 || { printf 'mios-init: not root and no sudo for: %s\n' "$*" >&2; return 1; }
    _n=$#
    for _v in HTTPS_PROXY https_proxy HTTP_PROXY http_proxy NO_PROXY no_proxy \
              $(awk 'BEGIN { for (k in ENVIRON) if (k ~ /^(FEDORA|MIOS)_[A-Za-z0-9_]*$/) print k }'); do
        eval "_val=\${$_v:-}"
        [ -n "$_val" ] && set -- "$@" "$_v=$_val"
    done
    while [ "$_n" -gt 0 ]; do set -- "$@" "$1"; shift; _n=$((_n - 1)); done
    sudo -n env "$@"
}

# is_mios DIR: DIR is a usable MiOS checkout -- it carries the two files this
# script consumes AND it is the root of a git work tree whose origin is the
# MiOS repo. Otherwise IS_MIOS_WHY says why, and a directory that only fails
# the pin starts with "ignored:". Read-only: rev-parse and remote get-url.
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
            sed -E 's#(://)[^/@]*@#\1***@#g' "$ctmp" >"$clog" 2>/dev/null; rm -f "$ctmp"
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

image_runtime() { # prints the runtime that holds $DC_IMAGE, podman first
    for rt in podman docker; do
        command -v "$rt" >/dev/null 2>&1 || continue
        "$rt" image inspect "$DC_IMAGE" >/dev/null 2>&1 && { printf '%s' "$rt"; return 0; }
    done
    return 1
}

wrapper_runtime() { # prints the RUNTIME= the installed wrapper was written for
    sed -n 's/^RUNTIME=//p' "/usr/local/bin/$DC_NAME" 2>/dev/null | head -n 1
}

venv_satisfied() {
    [ -x "$VENV/bin/python" ] &&
        "$VENV/bin/python" -c "import $(printf '%s' "$VENV_MODULES" | tr ' ' ',')" >/dev/null 2>&1
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
    # recreated exactly as it does it.
    cf="${MIOS_CONTAINERFILE:-$MIOS_DIR/.devcontainer/Containerfile}"
    reqs="$MIOS_DIR/usr/lib/mios/agent-pipe/requirements.txt"
    [ -f "$cf" ] || { record packages failed 1 "Containerfile not found: $cf (MIOS_CONTAINERFILE)"; return; }
    npm_line=$(grep -m 1 -E '(^|[[:space:]])npm install -g[[:space:]]' "$cf")
    [ -n "$npm_line" ] ||
        { record packages failed 1 "no 'npm install -g' line in $cf (MIOS_CONTAINERFILE): the CLI set is read from the Containerfile, never copied"; return; }
    clis=""
    for t in $(printf '%s\n' "$npm_line" | sed -e 's/.*npm install -g//' -e 's/[\\&;|].*//'); do
        case "$t" in -*) ;; *) clis="${clis:+$clis }$t" ;; esac
    done
    [ -n "$clis" ] || { record packages failed 1 "the 'npm install -g' line in $cf names no package"; return; }
    [ -f "$reqs" ] || { record packages failed 1 "requirements.txt not found: $reqs"; return; }
    cli_missing=""
    if command -v npm >/dev/null 2>&1; then
        for p in $clis; do npm ls -g --depth=0 "$p" >/dev/null 2>&1 || cli_missing="${cli_missing:+$cli_missing }$p"; done
    else
        cli_missing=$clis
    fi
    venv_ok=0; venv_satisfied && venv_ok=1
    if [ "$PLAN" = 1 ]; then
        d="Fedora host: would run: $dnf install -y --setopt=install_weak_deps=False <$n packages of [packages.devcontainer] from $toml>"
        if [ -n "$cli_missing" ]; then d="$d; would run: npm install -g $cli_missing (from $cf)"; else d="$d; npm CLIs from $cf: present ($clis)"; fi
        if [ "$venv_ok" = 1 ]; then d="$d; venv $VENV: already satisfied"; else d="$d; would run: python3.11 -m venv $VENV && pip install -r $reqs"; fi
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
        d="$d; venv $VENV: already satisfied (imports $VENV_MODULES)"
    elif ! command -v python3.11 >/dev/null 2>&1; then
        record packages failed 1 "$d; venv $VENV: python3.11 is not on PATH after the dnf set (log $dlog)"
        return
    elif as_root sh -c 'install -d -m 0755 "$1" && python3.11 -m venv "$2" && "$2/bin/pip" install --no-cache-dir -r "$3"' \
            _ "$(dirname "$VENV")" "$VENV" "$reqs" >"$vlog" 2>&1 && venv_satisfied; then
        d="$d; venv $VENV: created from $reqs (log $vlog)"
    else
        record packages failed 1 "$d; venv $VENV from $reqs failed: $(tail -n 2 "$vlog" 2>/dev/null | tr '\n' ' ')(log $vlog)"
        return
    fi
    record packages ok 1 "$d"
}

packages_projection() {
    cfs="$SELF_DIR/cloud-fedora-setup.sh"
    how="non-Fedora host -> projection via $cfs (FEDORA_DEVCONTAINER_REPO=$DC_REPO)"
    [ -f "$cfs" ] || { record packages failed 1 "cloud-fedora-setup.sh not found beside $0"; return; }
    if rt=$(image_runtime); then
        RUNTIME=$rt
        if [ -x "/usr/local/bin/$DC_NAME" ]; then
            record packages skipped 1 "$how: image $DC_IMAGE already present ($rt), not rebuilt; enter it with /usr/local/bin/$DC_NAME"
            return
        fi
        if [ "$PLAN" = 1 ]; then
            record packages planned 1 "$how: image $DC_IMAGE present ($rt); would run: FEDORA_RUNTIME=$rt bash $cfs --wrapper-only"
            return
        fi
        mkdir -p "$CACHE_DIR" 2>/dev/null
        wlog="$CACHE_DIR/mios-init-wrapper.log"
        # The image lives in ONE runtime's store, so the wrapper must be written
        # for that runtime: it is passed explicitly (auto would take podman when
        # both are installed and write a wrapper that can never find the image,
        # and the first call would rebuild everything there), and the installed
        # wrapper's RUNTIME= line is checked before ok is recorded.
        as_root env FEDORA_DEVCONTAINER_REPO="$DC_REPO" FEDORA_RUNTIME="$rt" FEDORA_PROVISION_HOST=0 bash "$cfs" --wrapper-only >"$wlog" 2>&1
        if [ ! -x "/usr/local/bin/$DC_NAME" ]; then
            record packages failed 1 "non-Fedora host: image $DC_IMAGE present ($rt) but cloud-fedora-setup.sh --wrapper-only did not install /usr/local/bin/$DC_NAME: $(tail -n 2 "$wlog" 2>/dev/null | tr '\n' ' ')(log $wlog)"
            return
        fi
        wrt=$(wrapper_runtime)
        if [ "$wrt" = "$rt" ]; then
            record packages ok 1 "non-Fedora host: image $DC_IMAGE present ($rt); installed /usr/local/bin/$DC_NAME for RUNTIME=$wrt (log $wlog)"
        else
            record packages failed 1 "non-Fedora host: image $DC_IMAGE lives in $rt but the installed /usr/local/bin/$DC_NAME says RUNTIME=${wrt:-<none>}: a wrapper for the wrong runtime cannot find the image and would rebuild it there (log $wlog)"
        fi
        return
    fi
    if command -v podman >/dev/null 2>&1; then RUNTIME=podman
    elif command -v docker >/dev/null 2>&1; then RUNTIME=docker
    else RUNTIME=none; fi
    if [ "$PLAN" = 1 ]; then
        note="image $DC_IMAGE not found"
        [ "$RUNTIME" = docker ] && ! docker info >/dev/null 2>&1 &&
            note="image state unknown: the docker daemon is not running (the setup script starts it and skips the build when the image is there)"
        record packages planned 1 "non-Fedora host: $note; would run projection: FEDORA_DEVCONTAINER_REPO=$DC_REPO FEDORA_PROVISION_HOST=0 bash $cfs (builds MiOS .devcontainer/Containerfile as $DC_IMAGE, installs /usr/local/bin/$DC_NAME)"
        return
    fi
    mkdir -p "$CACHE_DIR" 2>/dev/null
    plog="$CACHE_DIR/mios-init-projection.log"
    log "projecting the MiOS devcontainer (several minutes on a cold host; log $plog)"
    # cloud-fedora-setup.sh always exits 0 by contract, so success is judged by
    # the image it must leave behind, not by its exit code.
    as_root env FEDORA_DEVCONTAINER_REPO="$DC_REPO" FEDORA_PROVISION_HOST=0 bash "$cfs" >"$plog" 2>&1
    if rt=$(image_runtime); then
        RUNTIME=$rt
        wrt=$(wrapper_runtime)
        if [ "$wrt" = "$rt" ]; then
            record packages ok 1 "non-Fedora host: projected $DC_IMAGE ($rt) from $DC_REPO; enter it with /usr/local/bin/$DC_NAME (RUNTIME=$wrt; log $plog)"
        else
            record packages failed 1 "non-Fedora host: projected $DC_IMAGE into $rt but /usr/local/bin/$DC_NAME says RUNTIME=${wrt:-<none>} (log $plog)"
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
        curl -fsSL --compressed --retry 2 --max-time 60 -o "$tmp" "$url" 2>/dev/null
        rc=$?
        if [ "$rc" != 0 ]; then
            rm -f "$tmp"
            DOC_WHY="fetch failed (curl rc $rc): $(redact_url "$url")${why:+ ;$why}"
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
