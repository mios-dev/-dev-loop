#!/usr/bin/env bash
# mios-init.sh -- bring a FRESH environment (a new cloud container, a new
# devcontainer, a bare Fedora box) up to a MiOS dev-loop starting point:
#
#   1. repos     locate or shallow-clone the four sibling repos (MiOS,
#                mios-bootstrap, -dev-loop, mios-micro) under one workspace
#                root; existing checkouts are never touched (no fetch, no
#                checkout, no branch change)
#   2. packages  install MiOS packages + dependencies:
#                  Fedora host  -> dnf install -y the [packages.devcontainer]
#                                  set of MiOS usr/share/mios/mios.toml,
#                                  resolved by MiOS automation/lib/packages.sh
#                                  (podman is part of that set: MiOS is podman
#                                  native)
#                  other hosts  -> the identical Fedora userspace, projected by
#                                  cloud-fedora-setup.sh from MiOS's one
#                                  .devcontainer/Containerfile (it uses docker
#                                  only where docker is the only runtime); an
#                                  existing image is never rebuilt
#      tooling   setup-antigravity.sh --quiet (agy, keyring, grants, skill)
#   3. prompt    the Global MiOS System Prompt (MiOS usr/share/mios/ai/system.md,
#                mios.toml ai_system_prompt), from the first of: the deployed
#                /usr/share/mios/ai/system.md, the local MiOS checkout, GitHub
#                main -- written to ${XDG_CACHE_HOME:-~/.cache}/mios/system.md
#   4. summary   one JSON object on the LAST line of stdout
#
# Idempotent, non-interactive, safe to re-run. Every step is guarded and
# reported; exit is non-zero only when a REQUIRED step failed, and stderr names
# it. Required: repo:MiOS, packages, tooling, prompt. The other three repos are
# reported but optional.
#
# Usage: bash mios-init.sh [--plan] [--no-packages] [--prompt-only] [--packages-only]
#   --plan           print what would run; change nothing (no clone, install, write)
#   --no-packages    skip step 2 (packages and tooling)
#   --prompt-only    step 3 only (no clone, no install)
#   --packages-only  steps 1 and 2a only (no tooling, no prompt) -- the package
#                    path by itself, e.g. inside an existing Fedora container
#
# Environment:
#   MIOS_WORKSPACES               workspace root holding the sibling repos
#   MIOS_REPOS                    repos to locate/clone (default: MiOS mios-bootstrap -dev-loop mios-micro)
#   MIOS_GITHUB_BASE              clone base            (default https://github.com/mios-dev)
#   MIOS_TOML                     mios.toml to resolve packages from
#                                 (default <MiOS>/usr/share/mios/mios.toml)
#   MIOS_SYSTEM_PROMPT_URL        prompt fetch URL      (default MiOS main on raw.githubusercontent.com)
#   MIOS_SYSTEM_PROMPT_DEPLOYED   deployed prompt path  (default /usr/share/mios/ai/system.md)
#   MIOS_OS_RELEASE               os-release file       (default /etc/os-release)
#   FEDORA_DEVCONTAINER_REPO / FEDORA_DEVCONTAINER_NAME / FEDORA_IMAGE
#                                 passed through to cloud-fedora-setup.sh
set -u

SELF_DIR=$(cd "$(dirname "$0")" && pwd)
PLUGIN_ROOT=$(cd "$SELF_DIR/../../../.." && pwd)
REPOS="${MIOS_REPOS:-MiOS mios-bootstrap -dev-loop mios-micro}"
GH_BASE="${MIOS_GITHUB_BASE:-https://github.com/mios-dev}"
PROMPT_URL="${MIOS_SYSTEM_PROMPT_URL:-https://raw.githubusercontent.com/mios-dev/MiOS/main/usr/share/mios/ai/system.md}"
DEPLOYED="${MIOS_SYSTEM_PROMPT_DEPLOYED:-/usr/share/mios/ai/system.md}"
OS_RELEASE="${MIOS_OS_RELEASE:-/etc/os-release}"
CACHE_DIR="${XDG_CACHE_HOME:-${HOME:-/root}/.cache}/mios"
PROMPT_OUT="$CACHE_DIR/system.md"
DC_REPO="${FEDORA_DEVCONTAINER_REPO:-https://github.com/mios-dev/MiOS}"
DC_NAME="${FEDORA_DEVCONTAINER_NAME:-mios-dev}"
DC_IMAGE="${FEDORA_IMAGE:-${DC_NAME}:latest}"
export GIT_TERMINAL_PROMPT=0

PLAN=0 DO_REPOS=1 DO_PKGS=1 DO_TOOLING=1 DO_PROMPT=1 MODE=run
for a in "$@"; do
    case "$a" in
        --plan) PLAN=1; MODE=plan ;;
        --no-packages) DO_PKGS=0; DO_TOOLING=0 ;;
        --prompt-only) DO_REPOS=0; DO_PKGS=0; DO_TOOLING=0 ;;
        --packages-only) DO_TOOLING=0; DO_PROMPT=0 ;;
        -h|--help) sed -n '2,/^set -u$/p' "$0" | sed -e '$d' -e 's/^# \{0,1\}//'; exit 0 ;;
        *) printf 'mios-init: unknown argument: %s (try --help)\n' "$a" >&2; exit 2 ;;
    esac
done

log() { printf '[mios-init] %s\n' "$*"; }
jstr() { printf '"%s"' "$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\n\r\t')"; }

STEPS="" FAILED_REQ="" REPOS_JSON="" RUNTIME="" PROMPT_SHA="" PROMPT_SRC=""
# record NAME STATUS(ok|skipped|failed|planned) REQUIRED(1|0) DETAIL
record() {
    log "$1: $2 -- $4"
    [ -n "$STEPS" ] && STEPS="$STEPS,"
    req=false; [ "$3" = 1 ] && req=true
    STEPS="$STEPS{\"name\":$(jstr "$1"),\"status\":$(jstr "$2"),\"required\":$req,\"detail\":$(jstr "$4")}"
    if [ "$2" = failed ] && [ "$3" = 1 ]; then FAILED_REQ="${FAILED_REQ:+$FAILED_REQ }$1"; fi
}

as_root() { # run "$@" as root: directly, or via non-interactive sudo
    if [ "$(id -u)" = 0 ]; then "$@"
    elif command -v sudo >/dev/null 2>&1; then sudo -n "$@"
    else printf 'mios-init: not root and no sudo for: %s\n' "$*" >&2; return 1
    fi
}

is_mios() { [ -f "$1/usr/share/mios/mios.toml" ] && [ -f "$1/automation/lib/packages.sh" ]; }

# --- workspace root -----------------------------------------------------------
if [ -n "${MIOS_WORKSPACES:-}" ]; then
    WS="$MIOS_WORKSPACES" WS_FROM="MIOS_WORKSPACES"
else
    WS="" WS_FROM=""
    for c in "$(dirname "$PLUGIN_ROOT")" "$(dirname "$PWD")" "$PWD" /workspaces /home/user "${HOME:-/root}"; do
        if is_mios "$c/MiOS"; then WS="$c" WS_FROM="existing MiOS checkout"; break; fi
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
        if [ -e "$d/.git" ]; then
            state=present; record "repo:$r" skipped "$req" "present at $d (left as is)"
        elif [ -e "$d" ] && [ -n "$(ls -A "$d" 2>/dev/null)" ]; then
            state=failed; record "repo:$r" failed "$req" "$d exists, is not empty and is not a git checkout"
        elif [ "$PLAN" = 1 ]; then
            state=planned; record "repo:$r" planned "$req" "would run: git clone --depth 1 -- $GH_BASE/$r $d"
        elif mkdir -p "$WS" && git clone --quiet --depth 1 -- "$GH_BASE/$r" "$d" >/dev/null 2>&1; then
            state=cloned; record "repo:$r" ok "$req" "shallow-cloned $GH_BASE/$r into $d"
        else
            state=failed; record "repo:$r" failed "$req" "git clone --depth 1 -- $GH_BASE/$r $d failed"
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

packages_fedora() {
    toml="${MIOS_TOML:-$MIOS_DIR/usr/share/mios/mios.toml}"
    is_mios "$MIOS_DIR" || { record packages failed 1 "no MiOS checkout at $MIOS_DIR (packages.sh and mios.toml come from it)"; return; }
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
    if [ "$PLAN" = 1 ]; then
        record packages planned 1 "Fedora host: would run: $dnf install -y <$n packages of [packages.devcontainer] from $toml>"
        return
    fi
    mkdir -p "$CACHE_DIR" 2>/dev/null
    dlog="$CACHE_DIR/mios-init-dnf.log"
    # $pkgs is a whitespace-separated package list: word splitting is intended.
    # shellcheck disable=SC2086
    if as_root "$dnf" install -y $pkgs >"$dlog" 2>&1; then
        if grep -q 'Nothing to do' "$dlog"; then what="all already installed"; else what="installed"; fi
        record packages ok 1 "Fedora host: $dnf install -y of $n packages from [packages.devcontainer] ($what; log $dlog)"
    else
        record packages failed 1 "Fedora host: $dnf install -y of $n packages failed: $(tail -n 2 "$dlog" | tr '\n' ' ')"
    fi
    command -v podman >/dev/null 2>&1 || RUNTIME=none
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
            record packages planned 1 "$how: image $DC_IMAGE present ($rt); would run: bash $cfs --wrapper-only"
            return
        fi
        if as_root env FEDORA_DEVCONTAINER_REPO="$DC_REPO" FEDORA_PROVISION_HOST=0 bash "$cfs" --wrapper-only >/dev/null 2>&1 &&
            [ -x "/usr/local/bin/$DC_NAME" ]; then
            record packages ok 1 "non-Fedora host: image $DC_IMAGE present ($rt); installed /usr/local/bin/$DC_NAME"
        else
            record packages failed 1 "non-Fedora host: image present but cloud-fedora-setup.sh --wrapper-only did not install /usr/local/bin/$DC_NAME"
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
        record packages ok 1 "non-Fedora host: projected $DC_IMAGE ($rt) from $DC_REPO; enter it with /usr/local/bin/$DC_NAME"
    else
        record packages failed 1 "non-Fedora host: cloud-fedora-setup.sh left no $DC_IMAGE image: $(tail -n 2 "$plog" | tr '\n' ' ')"
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
            record tooling failed 1 "setup-antigravity.sh failed: $(tail -n 2 "$tlog" | tr '\n' ' ')"
        fi
    fi
fi

# --- 3. the Global MiOS System Prompt -----------------------------------------
looks_markdown() { # non-empty text, not an HTML page, carries a markdown construct
    [ -s "$1" ] || { echo "empty"; return 1; }
    grep -Iq . "$1" || { echo "not text"; return 1; }
    first=$(grep -m 1 -v '^[[:space:]]*$' "$1")
    case "$first" in
        '<!DOCTYPE'*|'<!doctype'*|'<html'*|'<HTML'*) echo "an HTML page, not markdown"; return 1 ;;
    esac
    grep -Eq '^(#{1,6} |> |[-*] |[0-9]+\. |```)' "$1" || { echo "no markdown construct"; return 1; }
}

fetch_prompt() {
    tmp="$CACHE_DIR/.system.md.$$"
    src="" why=""
    for cand in "deployed:$DEPLOYED" "local:$MIOS_DIR/usr/share/mios/ai/system.md"; do
        kind=${cand%%:*} f=${cand#*:}
        [ -f "$f" ] || continue
        if bad=$(looks_markdown "$f"); then src="$kind $f"; break; fi
        why="$why $kind $f rejected ($bad);"
    done
    if [ "$PLAN" = 1 ]; then
        record prompt planned 1 "would write $PROMPT_OUT from ${src:-$PROMPT_URL}"
        return
    fi
    mkdir -p "$CACHE_DIR" || { record prompt failed 1 "cannot create $CACHE_DIR"; return; }
    if [ -n "$src" ]; then
        cp "${src#* }" "$tmp" || { rm -f "$tmp"; record prompt failed 1 "cannot copy ${src#* }"; return; }
    else
        curl -fsSL --compressed --retry 2 --max-time 60 -o "$tmp" "$PROMPT_URL" 2>/dev/null
        rc=$?
        if [ "$rc" != 0 ]; then
            rm -f "$tmp"
            record prompt failed 1 "fetch failed (curl rc $rc): $PROMPT_URL${why:+ ;$why}"
            return
        fi
        if ! bad=$(looks_markdown "$tmp"); then
            rm -f "$tmp"
            record prompt failed 1 "$PROMPT_URL returned $bad"
            return
        fi
        src="url $PROMPT_URL"
    fi
    mv -f "$tmp" "$PROMPT_OUT" || { rm -f "$tmp"; record prompt failed 1 "cannot write $PROMPT_OUT"; return; }
    PROMPT_SHA=$(sha256sum "$PROMPT_OUT" | cut -d' ' -f1)
    PROMPT_SRC=$src
    record prompt ok 1 "$PROMPT_OUT sha256 $PROMPT_SHA from $src"
}

[ "$DO_PROMPT" = 1 ] && fetch_prompt

# --- 4. summary ---------------------------------------------------------------
if [ -z "$RUNTIME" ]; then
    if command -v podman >/dev/null 2>&1; then RUNTIME=podman
    elif command -v docker >/dev/null 2>&1; then RUNTIME=docker
    else RUNTIME=none; fi
fi
ok=true; [ -n "$FAILED_REQ" ] && ok=false
fr=""; for s in $FAILED_REQ; do fr="${fr:+$fr,}$(jstr "$s")"; done
pp=null; [ "$DO_PROMPT" = 1 ] && pp=$(jstr "$PROMPT_OUT")
if [ -n "$FAILED_REQ" ]; then
    printf 'mios-init: FAILED required step(s): %s\n' "$FAILED_REQ" >&2
fi
printf '{"tool":"mios-init","mode":%s,"ok":%s,"failed_required":[%s],"steps":[%s],"prompt":{"path":%s,"sha256":%s,"source":%s},"runtime":%s,"workspace":%s,"repos":{%s}}\n' \
    "$(jstr "$MODE")" "$ok" "$fr" "$STEPS" "$pp" "$(jstr "$PROMPT_SHA")" "$(jstr "$PROMPT_SRC")" \
    "$(jstr "$RUNTIME")" "$(jstr "$WS")" "$REPOS_JSON"
[ -z "$FAILED_REQ" ]
