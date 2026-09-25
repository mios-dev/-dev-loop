#!/usr/bin/env bash
# cloud-fedora-setup.sh — give an Anthropic-hosted cloud environment a real
# Fedora userspace. Fedora is the worked example of a general pattern: when a
# project needs a userland the fixed cloud VM image cannot provide, build it as
# a container and bind-mount host paths unchanged. Adapt the repo and package
# blocks below for another distro (FEDORA_VERSION / FEDORA_BASE / FEDORA_PACKAGES
# cover Fedora releases only).
#
# WHERE THIS RUNS
#   Paste the whole file into the "Setup script" field of a cloud environment
#   (claude.ai/code -> environment selector -> Add cloud environment). It is
#   kept here so the pasted copy has a versioned, syntax-checked source.
#
# WHY A CONTAINER AND NOT A BASE IMAGE
#   Anthropic-hosted cloud sessions run a fixed Ubuntu 24.04 x86_64 VM, and
#   "replacing the base image entirely isn't supported yet"
#   (code.claude.com/docs/en/cloud-environments#installed-tools). Docker IS
#   pre-installed, and after this script finishes the platform snapshots the
#   filesystem and reuses it for every later session — so an image built here
#   is already on disk next time and costs nothing at startup. A container is
#   therefore the only supported way to get Fedora, and a cheap one.
#
# WHAT YOU GET
#   /usr/local/bin/fedora — run anything in Fedora, same paths, same $PWD:
#       fedora                  # interactive Fedora shell
#       fedora dnf install -y … # Fedora package management
#       fedora cargo build      # build against Fedora's toolchain
#
# SETUP-SCRIPT CONTRACT (docs: cloud-environments#script-requirements)
#   Runs as root. Must exit 0 — a non-zero exit fails the whole session. Must
#   finish inside ~5 minutes or the environment cache won't build. So: no
#   `set -e`, every step guarded, and an unconditional `exit 0` at the end.
#   A failed provision degrades to a plain Ubuntu session with a log line, it
#   never blocks the session.
#
# TUNABLES (set them as environment variables on the same cloud environment)
#   FEDORA_VERSION    Fedora release to base on          (default 44)
#   FEDORA_PACKAGES   package set baked into the image   (default below)
#   FEDORA_IMAGE      derived image tag                  (default dev-loop-fedora:$FEDORA_VERSION)
#   FEDORA_REBUILD=1  force a rebuild even if the image is already cached
#   FEDORA_CA_BUNDLE  egress CA to trust (auto-detected; `none` skips it — only
#                     useful as a negative control, every https fetch then fails)
#   FEDORA_PROVISION_HOST=0  skip provisioning the VM itself (agy, keyring,
#                     grants, dev-loop skill via setup-antigravity.sh), which
#                     otherwise runs first so Claude Code has agy on the host
#
# DEVCONTAINER PROJECTION MODE (worked example: MiOS)
#   Set FEDORA_DEVCONTAINER_REPO and the session becomes a projection of that
#   repo's devcontainer instead of the generic image above:
#       FEDORA_DEVCONTAINER_REPO=https://github.com/mios-dev/MiOS
#       FEDORA_DEVCONTAINER_FILE=.devcontainer/Containerfile   (the default)
#   The repo is shallow-cloned and its Containerfile built UNEDITED with the repo
#   root as context. Its hard-coded `FROM registry.fedoraproject.org/fedora:44`
#   resolves to a base built here first — upstream Fedora plus the egress CA,
#   the pinned repos and CA env (SSL_CERT_FILE, REQUESTS_CA_BUNDLE,
#   NODE_EXTRA_CA_CERTS, PIP_CERT, all inherited by every later layer) — and
#   tagged locally under the upstream name, so the build never pulls the real
#   one. The wrapper is installed as /usr/local/bin/<repo>-dev (MiOS ->
#   mios-dev) and as /usr/local/bin/fedora, both entering the same container.
#   Other tunables in this mode:
#       FEDORA_DEVCONTAINER_REF   branch or tag to clone   (default: repo default)
#       FEDORA_DEVCONTAINER_NAME  wrapper/container name   (default: <repo>-dev)
#       FEDORA_EXEC_USER          user commands run as     (default: root, since
#                                 the bind-mounted workspace is root-owned here;
#                                 set it to the image's own user, e.g. mios-dev,
#                                 to match the devcontainer's remoteUser)
#   <name>:base is built by the Dev Containers CLI from the devcontainer.json
#   beside the Containerfile (Containerfile + features, as VS Code/Codespaces
#   build it; FEDORA_DEVCONTAINER_CLI=0 builds the Containerfile alone); then the lifecycle commands of
#   the devcontainer.json beside it (onCreate/updateContent/postCreate/
#   postStart, remoteUser, workspaceFolder -- read, never restated) run once in
#   a throwaway container and are committed as <name>:latest, the image the
#   wrapper runs. A failed lifecycle degrades to :base and records why in
#   $BUILD_CTX/<name>.lifecycle.
#       FEDORA_DEVCONTAINER_JSON       devcontainer.json path (default: beside the Containerfile)
#       FEDORA_DEVCONTAINER_LIFECYCLE  0 skips the prebuild
#       FEDORA_LIFECYCLE_TIMEOUT_S     bound on the prebuild   (default 900)
#       FEDORA_SETUP_BUDGET_S          defer the prebuild once this many seconds
#                                      of the run are spent    (default 0: never)
#   `--lifecycle` applies a deferred or failed prebuild to the existing :base.
#   Why the devcontainer and not MiOS's own image: ghcr.io/mios-dev/mios:latest
#   is a bootc OCI image of 22.8 GB compressed in 79 layers — far too big for a
#   cloud VM's setup budget and disk. The devcontainer is MiOS's build and dev
#   userspace (just, podman/buildah/skopeo, bootc/ostree/rpm-ostree, rust,
#   node, python3.11 agent venv, ShellCheck, the agent CLIs), which is what a
#   dev session needs; the bootc image is what that toolchain produces.
#
# ALSO USABLE WITHOUT THE SETUP-SCRIPT FIELD
#   `--wrapper-only` installs the wrapper(s) and skips the pull+build,
#   so a SessionStart hook can install it in well under a second and the first
#   `fedora …` call builds the image on demand. Use that when an environment
#   dialog offers no Setup script field, or to keep session startup instant.

set -u

FEDORA_VERSION="${FEDORA_VERSION:-44}"
FEDORA_BASE="registry.fedoraproject.org/fedora:${FEDORA_VERSION}"
BUILD_CTX=/opt/dev-loop-fedora
# Where update-ca-trust writes the merged bundle (egress CA included).
CA_PEM=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
SELF=$(cd "$(dirname "$0")" 2>/dev/null && pwd)/$(basename "$0")
# The wrapper rebuilds on first use by re-running this script, so it needs a
# path that outlives wherever the environment dialog put the pasted copy.
SCRIPT_CACHE="$BUILD_CTX/cloud-fedora-setup.sh"

DC_REPO="${FEDORA_DEVCONTAINER_REPO:-}"
DC_FILE="${FEDORA_DEVCONTAINER_FILE:-.devcontainer/Containerfile}"
DC_REF="${FEDORA_DEVCONTAINER_REF:-}"
if [ -n "$DC_REPO" ]; then
    dc_base=$(basename "${DC_REPO%/}" .git | tr '[:upper:]' '[:lower:]')
    DC_NAME="${FEDORA_DEVCONTAINER_NAME:-${dc_base}-dev}"
    DC_SRC="$BUILD_CTX/src/$DC_NAME"
    DC_JSON="${FEDORA_DEVCONTAINER_JSON:-$(dirname "$DC_FILE")/devcontainer.json}"
    FEDORA_IMAGE="${FEDORA_IMAGE:-${DC_NAME}:latest}"
    # The Containerfile alone; FEDORA_IMAGE is this plus the committed lifecycle.
    DC_BASE="${FEDORA_IMAGE%:*}:base"
    FEDORA_CONTAINER="${FEDORA_CONTAINER:-$DC_NAME}"
    FEDORA_EXEC_USER="${FEDORA_EXEC_USER:-root}"
    WRAPPER_NAMES="$DC_NAME fedora"
else
    DC_NAME=""
    FEDORA_IMAGE="${FEDORA_IMAGE:-dev-loop-fedora:${FEDORA_VERSION}}"
    FEDORA_CONTAINER="${FEDORA_CONTAINER:-fedora}"
    FEDORA_EXEC_USER="${FEDORA_EXEC_USER:-}"
    WRAPPER_NAMES="fedora"
fi
WRAPPER_ONLY=0
LIFECYCLE_ONLY=0
case "${1:-}" in
    --wrapper-only) WRAPPER_ONLY=1 ;;
    --lifecycle) LIFECYCLE_ONLY=1 ;;
esac

# The generic (non-projection) image only. A MiOS session uses projection mode,
# which builds MiOS's one dev Containerfile instead of this list.
# install_weak_deps=False keeps the build inside budget.
FEDORA_PACKAGES="${FEDORA_PACKAGES:-git tmux jq curl wget ripgrep python3 python3-pip nodejs npm gcc gcc-c++ make procps-ng util-linux shadow-utils sudo which hostname tar gzip unzip zip findutils diffutils patch openssl dbus-daemon dbus-tools gnome-keyring libsecret}"

log() { printf '[fedora-env] %s\n' "$*"; }

# --- 1. the Docker daemon -----------------------------------------------------
# Present but not started: the environment cache restores files, never running
# processes, so this is also what /usr/local/bin/fedora does on a cold session.
ensure_dockerd() {
    docker info >/dev/null 2>&1 && return 0
    command -v dockerd >/dev/null 2>&1 || { log "dockerd is not installed — cannot provision Fedora"; return 1; }
    log "starting dockerd"
    ( dockerd >/var/log/dev-loop-dockerd.log 2>&1 & ) >/dev/null 2>&1
    i=0
    while [ "$i" -lt 45 ]; do
        docker info >/dev/null 2>&1 && return 0
        i=$((i + 1)); sleep 1
    done
    log "dockerd did not come up in 45s (see /var/log/dev-loop-dockerd.log)"
    return 1
}

# --- 2. the egress proxy's CA -------------------------------------------------
# Cloud sessions reach the network through a TLS-terminating proxy, so a
# container that doesn't trust its CA fails every https fetch with
# "self-signed certificate in certificate chain". Bake the CA into the image's
# trust store rather than turning verification off anywhere.
find_ca_bundle() {
    [ "${FEDORA_CA_BUNDLE:-}" = none ] && return 1
    for c in "${FEDORA_CA_BUNDLE:-}" "${SSL_CERT_FILE:-}" "${CURL_CA_BUNDLE:-}" \
             /root/.ccr/ca-bundle.crt /etc/ssl/certs/ca-certificates.crt; do
        [ -n "$c" ] && [ -f "$c" ] && { printf '%s' "$c"; return 0; }
    done
    return 1
}

# --- 3. build context ---------------------------------------------------------
# Repos are pinned to dl.fedoraproject.org instead of the default metalink.
# A metalink hands dnf a different third-party mirror hostname on every run,
# which no network allowlist can cover; dl.fedoraproject.org is the canonical
# master and is one stable host to allow. GPG checking stays on.
write_build_context() {
    mkdir -p "$BUILD_CTX/repos" "$BUILD_CTX/ca" || return 1

    cat > "$BUILD_CTX/repos/fedora.repo" <<'REPO'
[fedora]
name=Fedora $releasever - $basearch
baseurl=https://dl.fedoraproject.org/pub/fedora/linux/releases/$releasever/Everything/$basearch/os/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$releasever-$basearch
skip_if_unavailable=False
REPO

    cat > "$BUILD_CTX/repos/fedora-updates.repo" <<'REPO'
[updates]
name=Fedora $releasever - $basearch - Updates
baseurl=https://dl.fedoraproject.org/pub/fedora/linux/updates/$releasever/Everything/$basearch/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$releasever-$basearch
skip_if_unavailable=False
REPO

    ca_line=""
    if ca=$(find_ca_bundle); then
        cp "$ca" "$BUILD_CTX/ca/egress-proxy-ca.crt" 2>/dev/null &&
            ca_line='COPY ca/egress-proxy-ca.crt /etc/pki/ca-trust/source/anchors/egress-proxy-ca.crt'
        log "trusting egress CA from $ca"
    else
        log "no egress CA bundle found — continuing with the image's own trust store"
    fi

    # The shared base: what makes a stock Fedora image usable behind the proxy.
    # Every later FROM inherits its ENV, so a devcontainer's own RUN lines
    # (pip, npm, curl) trust the proxy with no edit to its Containerfile.
    # Repos other than the two pinned above are disabled rather than deleted,
    # because a devcontainer's plain `dnf install` has no --disablerepo and
    # would otherwise reach whatever extra repos the base image ships.
    cat > "$BUILD_CTX/Dockerfile.base" <<DOCKERFILE
ARG FEDORA_BASE=${FEDORA_BASE}
FROM \${FEDORA_BASE}
COPY repos/ /etc/yum.repos.d/
RUN for f in /etc/yum.repos.d/*.repo; do \\
        case "\$f" in */fedora.repo|*/fedora-updates.repo) ;; \\
            *) sed -i 's/^enabled *= *1/enabled=0/' "\$f" ;; esac; \\
    done
${ca_line}
RUN update-ca-trust extract || true
# The minimal Fedora image ships no /etc/pki/tls/certs/ca-bundle.crt compat
# symlink, so anything hardcoding that classic path fails to load any CA.
RUN mkdir -p /etc/pki/tls/certs \\
    && ln -sf /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/pki/tls/certs/ca-bundle.crt
# pip ships its own CA list (certifi) and node its own compiled-in one, so the
# system store alone is not enough for either: point both at it explicitly.
ENV SSL_CERT_FILE=${CA_PEM} \\
    CURL_CA_BUNDLE=${CA_PEM} \\
    REQUESTS_CA_BUNDLE=${CA_PEM} \\
    NODE_EXTRA_CA_CERTS=${CA_PEM} \\
    PIP_CERT=${CA_PEM}
DOCKERFILE

    # The generic image: the base plus a package set. --disablerepo='*' pins
    # the install to exactly the two repos above.
    { cat "$BUILD_CTX/Dockerfile.base"
      cat <<DOCKERFILE
RUN dnf -y --disablerepo='*' --enablerepo=fedora --enablerepo=updates \\
        --setopt=install_weak_deps=False install ${FEDORA_PACKAGES} \\
    && dnf clean all
DOCKERFILE
    } > "$BUILD_CTX/Dockerfile"
}

# --- 4. the wrapper -----------------------------------------------------------
# Self-healing on purpose: it starts dockerd and the container itself, so it
# works in every later session even though only files survive the snapshot.
install_wrapper() {
    # Write-then-rename, never write in place: this script can be invoked BY
    # the wrapper (on-demand build), and bash reads a script incrementally by
    # byte offset — truncating and rewriting the file a shell is executing
    # makes it resume mid-line on shifted offsets. A rename swaps the directory
    # entry and leaves the running shell's open inode untouched.
    tmp=/usr/local/bin/.fedora-wrapper.$$
    # Values are baked in (not read from the session env) so the wrapper keeps
    # meaning the same image in a later session that sets nothing, and an
    # on-demand build rebuilds the same mode.
    {
        printf '#!/usr/bin/env bash\n'
        printf '# Run a command inside this environment'"'"'s Fedora userspace.\n'
        printf '#   %s                 interactive shell\n' "${WRAPPER_NAMES%% *}"
        printf '#   %s <cmd> [args…]   run <cmd> in the container\n' "${WRAPPER_NAMES%% *}"
        printf '# Host paths are bind-mounted at the SAME absolute path and $PWD is\n'
        printf '# preserved, so a path means the same thing on both sides.\n'
        printf '# Generated by %s — edit that, not this.\n' "$SCRIPT_CACHE"
        printf 'set -u\n'
        printf 'IMAGE="${FEDORA_IMAGE:-%s}"\n' "$FEDORA_IMAGE"
        printf 'CONTAINER="${FEDORA_CONTAINER:-%s}"\n' "$FEDORA_CONTAINER"
        printf 'EXEC_USER="${FEDORA_EXEC_USER:-%s}"\n' "$FEDORA_EXEC_USER"
        printf 'SETUP_SCRIPT=%q\n' "$SCRIPT_CACHE"
        printf 'LIFECYCLE_STATUS=%q\n' "$BUILD_CTX/${DC_NAME:-none}.lifecycle"
        printf 'BUILD_ENV=(FEDORA_VERSION=%q FEDORA_IMAGE="$IMAGE" FEDORA_CONTAINER="$CONTAINER"' "$FEDORA_VERSION"
        printf ' FEDORA_DEVCONTAINER_REPO=%q FEDORA_DEVCONTAINER_FILE=%q' "$DC_REPO" "$DC_FILE"
        printf ' FEDORA_DEVCONTAINER_REF=%q FEDORA_DEVCONTAINER_NAME=%q)\n' "$DC_REF" "$DC_NAME"
        cat <<'WRAPPER'
die() { printf '%s: %s\n' "${0##*/}" "$*" >&2; exit 1; }

ensure_dockerd() {
    docker info >/dev/null 2>&1 && return 0
    command -v dockerd >/dev/null 2>&1 || die "dockerd is not installed"
    ( dockerd >/var/log/dev-loop-dockerd.log 2>&1 & ) >/dev/null 2>&1
    i=0
    while [ "$i" -lt 45 ]; do
        docker info >/dev/null 2>&1 && return 0
        i=$((i + 1)); sleep 1
    done
    die "dockerd did not start (see /var/log/dev-loop-dockerd.log)"
}

run_args() {
    # --network host: the egress proxy listens on the VM's 127.0.0.1, which a
    # bridged container cannot reach.
    printf '%s\n' --network host
    # /home per entry, never whole: mounting it would hide the image's own
    # home directories (a devcontainer user's ~/.local/bin, where MiOS puts agy).
    for d in /home/* /root /workspace /srv /opt/dev-loop-fedora; do
        [ -d "$d" ] && printf '%s\n%s\n' -v "$d:$d"
    done
    for v in HTTPS_PROXY https_proxy NO_PROXY no_proxy HTTP_PROXY http_proxy; do
        [ -n "${!v:-}" ] && printf '%s\n%s\n' -e "$v=${!v}"
    done
    # Fedora's own trust store, where update-ca-trust puts the egress CA at build
    # time. Use the extracted bundle, not the /etc/pki/tls/certs/ca-bundle.crt
    # compat path: it is the file update-ca-trust actually writes.
    for v in SSL_CERT_FILE CURL_CA_BUNDLE REQUESTS_CA_BUNDLE NODE_EXTRA_CA_CERTS PIP_CERT; do
        printf '%s\n%s\n' -e "$v=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"
    done
}

ensure_image() {
    docker image inspect "$IMAGE" >/dev/null 2>&1 && return 0
    # FEDORA_NO_AUTOBUILD guards the recursion: the setup script verifies itself
    # by calling this wrapper, and a failed build must not bounce the two off
    # each other forever.
    [ "${FEDORA_NO_AUTOBUILD:-0}" = 1 ] &&
        die "image $IMAGE is missing and the build did not produce it (see /var/log/dev-loop-fedora-build.log)"
    [ -r "$SETUP_SCRIPT" ] || die "image $IMAGE is missing — re-run $SETUP_SCRIPT"
    printf '%s: first use — building %s, this takes a few minutes…\n' "${0##*/}" "$IMAGE" >&2
    env "${BUILD_ENV[@]}" FEDORA_NO_AUTOBUILD=1 bash "$SETUP_SCRIPT" >&2
    docker image inspect "$IMAGE" >/dev/null 2>&1 ||
        die "build failed (see /var/log/dev-loop-fedora-build.log)"
}

ensure_container() {
    state=$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null) || state=""
    case "$state" in
        running) return 0 ;;
        "")
            # A new container is a cold start: say once if the image lacks its lifecycle.
            if [ -r "$LIFECYCLE_STATUS" ] && [ "$(cat "$LIFECYCLE_STATUS")" != ok ]; then
                printf '%s: devcontainer lifecycle not applied to %s (%s)\n' \
                    "${0##*/}" "$IMAGE" "$(cat "$LIFECYCLE_STATUS")" >&2
            fi
            mapfile -t args < <(run_args)
            # A concurrent first call may win the name; its container is as good.
            docker run -d --name "$CONTAINER" "${args[@]}" "$IMAGE" sleep infinity >/dev/null 2>&1 ||
                [ "$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null)" = running ] ||
                die "could not start the Fedora container"
            ;;
        *) docker start "$CONTAINER" >/dev/null || die "could not restart $CONTAINER" ;;
    esac
}

ensure_dockerd
# Before ensure_container, never after: an on-demand build runs the setup
# script, which verifies itself through this same wrapper and may create the
# container — so any container state read earlier would already be stale.
ensure_image
ensure_container

workdir=$PWD
case $workdir in
    /home/*|/root|/root/*|/workspace/*|/srv/*) ;;
    *) workdir=/ ;;
esac

exec_flags=(-i -w "$workdir")
if [ -n "$EXEC_USER" ]; then
    exec_flags+=(-u "$EXEC_USER")
    [ "$EXEC_USER" = root ] && exec_flags+=(-e HOME=/root)
fi
[ -t 0 ] && [ -t 1 ] && exec_flags+=(-t)

if [ "$#" -eq 0 ]; then
    exec docker exec "${exec_flags[@]}" "$CONTAINER" bash -l
fi
exec docker exec "${exec_flags[@]}" "$CONTAINER" "$@"
WRAPPER
    } > "$tmp" || { rm -f "$tmp"; return 1; }
    chmod 0755 "$tmp" || { rm -f "$tmp"; return 1; }
    for n in $WRAPPER_NAMES; do
        cp -f "$tmp" "/usr/local/bin/.$n.$$" && mv -f "/usr/local/bin/.$n.$$" "/usr/local/bin/$n" ||
            { rm -f "$tmp"; return 1; }
    done
    rm -f "$tmp"
}

# Keep a copy of this script where the wrapper can find it on a later session
# (the pasted copy's path is the dialog's business, not ours). Same
# write-then-rename rule as the wrapper: the wrapper may be running this copy.
cache_self() {
    [ "$SELF" = "$SCRIPT_CACHE" ] && return 0
    grep -q 'cloud-fedora-setup' "$SELF" 2>/dev/null || return 1
    mkdir -p "$BUILD_CTX" && cp -f "$SELF" "$SCRIPT_CACHE.$$" && mv -f "$SCRIPT_CACHE.$$" "$SCRIPT_CACHE"
}

# --- 5. devcontainer projection -------------------------------------------------
# Shallow clone into a temp dir and swap, so a failed fetch keeps the last good
# checkout rather than leaving none.
fetch_devcontainer_src() {
    tmp="$DC_SRC.new.$$"
    rm -rf "$tmp"
    set -- git clone --quiet --depth 1
    [ -n "$DC_REF" ] && set -- "$@" --branch "$DC_REF"
    if "$@" "$DC_REPO" "$tmp" >>/var/log/dev-loop-fedora-build.log 2>&1; then
        rm -rf "$DC_SRC" && mkdir -p "$(dirname "$DC_SRC")" && mv "$tmp" "$DC_SRC"
        return $?
    fi
    rm -rf "$tmp"
    [ -d "$DC_SRC/.git" ] && { log "clone of $DC_REPO failed — reusing the last checkout"; return 0; }
    log "clone of $DC_REPO failed (see /var/log/dev-loop-fedora-build.log)"
    return 1
}

# Build the CA-trusting base and tag it under the name the Containerfile's FROM
# uses, then build the Containerfile unedited: docker resolves FROM from the
# local store before any registry, so it lands on the shadow. The real upstream
# is kept as dev-loop-fedora-upstream:<tag> so a rebuild never bases the shadow
# on itself.
build_devcontainer() {
    fetch_devcontainer_src || return 1
    cf="$DC_SRC/$DC_FILE"
    [ -f "$cf" ] || { log "$DC_FILE not found in $DC_REPO"; return 1; }
    from=$(awk 'toupper($1) == "FROM" { for (i = 2; i <= NF; i++) if ($i !~ /^--/) { print $i; exit } }' "$cf")
    case "$from" in
        */fedora:*|fedora:*)
            tag=${from##*:}
            upstream="dev-loop-fedora-upstream:$tag"
            log "pulling $from"
            if docker pull "$from" >/dev/null 2>&1 && docker tag "$from" "$upstream"; then :
            elif docker image inspect "$upstream" >/dev/null 2>&1; then
                log "pull failed — reusing the cached $upstream"
            else
                log "pull failed — is registry.fedoraproject.org allowed by this environment's network policy?"
                return 1
            fi
            log "building the base and tagging it locally as $from"
            docker build --network host -f "$BUILD_CTX/Dockerfile.base" \
                --build-arg "FEDORA_BASE=$upstream" \
                -t "dev-loop-fedora-base:$tag" -t "$from" \
                "$BUILD_CTX" >>/var/log/dev-loop-fedora-build.log 2>&1 || return 1
            ;;
        *) log "FROM '$from' is not a Fedora image — building it without the CA/repo base" ;;
    esac
    if [ -f "$DC_SRC/$DC_JSON" ] && cli=$(dc_cli); then
        log "building $DC_BASE with the Dev Containers CLI ($DC_JSON: Containerfile + features)"
        "$cli" build --workspace-folder "$DC_SRC" --config "$DC_SRC/$DC_JSON" \
            --image-name "$DC_BASE" >>/var/log/dev-loop-fedora-build.log 2>&1 || return 1
    else
        log "building $DC_BASE from $DC_REPO:$DC_FILE (Containerfile only: no features applied)"
        docker build --network host -f "$cf" -t "$DC_BASE" \
            "$DC_SRC" >>/var/log/dev-loop-fedora-build.log 2>&1 || return 1
    fi
    run_lifecycle
}

# The Dev Containers CLI reads devcontainer.json and applies its features the
# way VS Code and Codespaces do, so the image is the devcontainer and not only
# its Containerfile: measured on MiOS, the common-utils feature adds 16 packages
# (bash-completion, man-db, strace, which, ...) that a plain build lacks. It is
# installed once under $BUILD_CTX, so it is in the snapshot. Its build still
# resolves FROM to the local CA-trusting shadow. FEDORA_DEVCONTAINER_CLI=0
# falls back to the plain build.
dc_cli() {
    [ "${FEDORA_DEVCONTAINER_CLI:-1}" = 0 ] && return 1
    cli="$BUILD_CTX/dccli/node_modules/.bin/devcontainer"
    if [ ! -x "$cli" ]; then
        command -v npm >/dev/null 2>&1 || return 1
        npm install --silent --prefix "$BUILD_CTX/dccli" @devcontainers/cli \
            >>/var/log/dev-loop-fedora-build.log 2>&1 || return 1
    fi
    [ -x "$cli" ] && printf '%s' "$cli"
}

# --- 6. devcontainer lifecycle prebuild ----------------------------------------
# A devcontainer is its Containerfile PLUS its lifecycle commands: MiOS's apply
# the root overlay, build miosd and the native tools, and provision agy. A cold
# cloud session restores files, never containers, so running the lifecycle in
# the session's container would be lost on the next one. It runs once here and
# is committed into FEDORA_IMAGE -- a Codespaces-style prebuild. The commands,
# user and workspace folder are read from the repo's devcontainer.json, never
# restated, so they cannot drift from what a devcontainer runs.
dc_json_get() {
    python3 - "$DC_SRC/$DC_JSON" "$1" <<'PY'
import json, re, shlex, sys
raw = open(sys.argv[1], encoding="utf-8").read()
try:
    d = json.loads(raw)
except ValueError:  # JSONC: whole-line // comments and trailing commas
    raw = re.sub(r"(?m)^\s*//.*$", "", raw)
    d = json.loads(re.sub(r",(\s*[}\]])", r"\1", raw))
v = d.get(sys.argv[2], "")
if isinstance(v, list):      # exec form
    v = shlex.join(v)
elif isinstance(v, dict):    # parallel form: run the entries in order
    v = " && ".join(x if isinstance(x, str) else shlex.join(x) for x in v.values())
print(v)
PY
}

run_lifecycle() {
    status_file="$BUILD_CTX/$DC_NAME.lifecycle"
    # The platform snapshots the environment only if the setup script finishes
    # inside its budget, and the prebuild alone takes minutes. So when the
    # budget is already spent, defer instead of overrunning: the image is the
    # bare Containerfile, the status says so, and `--lifecycle` applies it later.
    # 0 (the default) means no budget -- always prebuild.
    budget=${FEDORA_SETUP_BUDGET_S:-0}
    if [ "$LIFECYCLE_ONLY" = 0 ] && [ "${FEDORA_NO_AUTOBUILD:-0}" != 1 ] && [ "$budget" -gt 0 ] && [ $((SECONDS - SETUP_T0)) -ge "$budget" ]; then
        echo "deferred: ${budget}s setup budget spent before it started; run: bash $SCRIPT_CACHE --lifecycle" > "$status_file"
        docker tag "$DC_BASE" "$FEDORA_IMAGE"
        log "lifecycle: $(cat "$status_file")"
        return
    fi
    if [ "${FEDORA_DEVCONTAINER_LIFECYCLE:-1}" = 0 ] || [ ! -f "$DC_SRC/$DC_JSON" ]; then
        log "no lifecycle prebuild ($DC_JSON absent or FEDORA_DEVCONTAINER_LIFECYCLE=0)"
        echo "skipped" > "$status_file"
        docker tag "$DC_BASE" "$FEDORA_IMAGE"
        return
    fi
    user=$(dc_json_get remoteUser); user=${user:-root}
    wsf=$(dc_json_get workspaceFolder); wsf=${wsf:-/workspaces/$(basename "${DC_REPO%/}" .git)}
    cmds=""
    for k in onCreateCommand updateContentCommand postCreateCommand postStartCommand; do
        c=$(dc_json_get "$k")
        [ -n "$c" ] && cmds="${cmds:+$cmds && }{ $c; }"
    done
    if [ -z "$cmds" ]; then
        echo "skipped" > "$status_file"; docker tag "$DC_BASE" "$FEDORA_IMAGE"; return
    fi
    # The lifecycle writes build output into the workspace as the devcontainer user.
    uid=$(docker run --rm --entrypoint id "$DC_BASE" -u "$user" 2>/dev/null) &&
        chown -R "$uid:$uid" "$DC_SRC"
    pc="$DC_NAME-prebuild"
    docker rm -f "$pc" >/dev/null 2>&1
    # Argument list via `set --`, not an array: validate.sh parses every env
    # script with `sh -n`, as fetch_devcontainer_src above already respects.
    set -- docker run -d --name "$pc" --network host -v "$DC_SRC:$wsf"
    for v in HTTPS_PROXY https_proxy NO_PROXY no_proxy HTTP_PROXY http_proxy; do
        val=$(printenv "$v") && [ -n "$val" ] && set -- "$@" -e "$v=$val"
    done
    log "running the $DC_JSON lifecycle as $user in $wsf"
    lc_started=$SECONDS
    if ! "$@" "$DC_BASE" sleep infinity >/dev/null 2>>/var/log/dev-loop-fedora-build.log; then
        echo "failed: could not start the prebuild container" > "$status_file"
    elif timeout "${FEDORA_LIFECYCLE_TIMEOUT_S:-900}" docker exec -u "$user" -w "$wsf" "$pc" \
            bash -lc "$cmds" >>/var/log/dev-loop-fedora-build.log 2>&1; then
        docker commit --change 'CMD ["/usr/bin/zsh"]' "$pc" "$FEDORA_IMAGE" >/dev/null &&
            echo "ok" > "$status_file"
    else
        echo "failed: rc=$? (see /var/log/dev-loop-fedora-build.log)" > "$status_file"
    fi
    docker rm -f "$pc" >/dev/null 2>&1
    # A failed lifecycle degrades to the bare Containerfile image, never to none,
    # and says so: the status file is what `mios-dev` reports on a cold start.
    docker image inspect "$FEDORA_IMAGE" >/dev/null 2>&1 || docker tag "$DC_BASE" "$FEDORA_IMAGE"
    log "lifecycle: $(cat "$status_file") in $((SECONDS - lc_started))s"
}

# --- 7. the host --------------------------------------------------------------
# Claude Code itself runs on the VM, not in the container, so the host gets the
# Antigravity CLI, keyring stack, headless grants and dev-loop skill too. Done
# here, the result is in the snapshot and every session starts with agy
# installed; only the keyring daemon has to be revived per session (the
# plugin's SessionStart hook does that).
provision_host() {
    [ "${FEDORA_PROVISION_HOST:-1}" = 0 ] && return 0
    for s in "$(dirname "$SELF")/setup-antigravity.sh" /opt/dev-loop/skills/dev-loop/scripts/env/setup-antigravity.sh; do
        [ -f "$s" ] || continue
        log "provisioning the host: agy, keyring, grants, dev-loop skill"
        if timeout "${FEDORA_HOST_TIMEOUT_S:-300}" bash "$s" --quiet >/var/log/dev-loop-host-setup.log 2>&1; then
            log "host: agy $("$HOME/.local/bin/agy" --version 2>/dev/null | head -1)"
        else
            log "host provisioning failed (see /var/log/dev-loop-host-setup.log)"
        fi
        return 0
    done
    log "setup-antigravity.sh not found — host not provisioned"
}

build_generic() {
    log "pulling $FEDORA_BASE"
    docker pull "$FEDORA_BASE" >/dev/null 2>&1 || { log "pull failed — is registry.fedoraproject.org allowed by this environment's network policy?"; return 1; }
    log "building $FEDORA_IMAGE"
    # --network host so the build itself reaches the proxy on 127.0.0.1.
    docker build --network host \
        --build-arg "FEDORA_BASE=$FEDORA_BASE" \
        -t "$FEDORA_IMAGE" "$BUILD_CTX" >>/var/log/dev-loop-fedora-build.log 2>&1
}

# --- main ---------------------------------------------------------------------
main() {
    SETUP_T0=$SECONDS
    first=${WRAPPER_NAMES%% *}
    cache_self || log "could not cache this script at $SCRIPT_CACHE — first-use builds need a manual re-run"

    if [ "$WRAPPER_ONLY" = 1 ]; then
        install_wrapper && log "installed $WRAPPER_NAMES in /usr/local/bin (builds $FEDORA_IMAGE on first use)" ||
            log "could not install the wrapper"
        return 0
    fi

    if [ "$LIFECYCLE_ONLY" = 1 ]; then
        [ -n "$DC_REPO" ] || { log "--lifecycle needs FEDORA_DEVCONTAINER_REPO (projection mode)"; return 0; }
        ensure_dockerd || return 0
        docker image inspect "$DC_BASE" >/dev/null 2>&1 || { log "$DC_BASE is missing -- run this script without --lifecycle first"; return 0; }
        run_lifecycle
        docker rm -f "$FEDORA_CONTAINER" >/dev/null 2>&1
        return 0
    fi

    # First, and not from the wrapper's on-demand build: agy on the host is the
    # cheapest and most essential piece, so a later overrun cannot cost it.
    [ "${FEDORA_NO_AUTOBUILD:-0}" = 1 ] || provision_host

    ensure_dockerd || { log "skipping Fedora provisioning"; return 0; }

    if [ "${FEDORA_REBUILD:-0}" != "1" ] && docker image inspect "$FEDORA_IMAGE" >/dev/null 2>&1; then
        log "$FEDORA_IMAGE already present — skipping build"
    else
        started=$SECONDS
        : > /var/log/dev-loop-fedora-build.log 2>/dev/null
        write_build_context || { log "could not write the build context"; return 0; }
        if [ -n "$DC_REPO" ]; then build_devcontainer; else build_generic; fi ||
            { log "build failed — tail of /var/log/dev-loop-fedora-build.log:"
              tail -n 15 /var/log/dev-loop-fedora-build.log 2>/dev/null
              return 0; }
        log "built $FEDORA_IMAGE in $((SECONDS - started))s"
        # A rebuilt image leaves the old container on the old image.
        docker rm -f "$FEDORA_CONTAINER" >/dev/null 2>&1
    fi

    if [ "${FEDORA_NO_AUTOBUILD:-0}" = 1 ]; then
        log "invoked by the wrapper — leaving /usr/local/bin/$first as it is"
    else
        install_wrapper || { log "could not install the wrapper"; return 0; }
    fi

    if ver=$(FEDORA_NO_AUTOBUILD=1 "/usr/local/bin/$first" cat /etc/fedora-release 2>/dev/null); then
        log "ready: $ver — run '$first <command>' or '$first' for a shell"
    else
        log "image built but the wrapper could not start a container"
    fi
}

main
exit 0
