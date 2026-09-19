# dev-loop devcontainer — Ubuntu variant (Fedora is this repo's default; pick
# this config for apt-based parity with Claude Code on the web containers).
ARG UBUNTU_VERSION=24.04
FROM ubuntu:${UBUNTU_VERSION}

ENV DEBIAN_FRONTEND=noninteractive
# apt equivalents of the Fedora config's package set, so the two variants and
# the cloud environment image all present the same toolchain.
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
        git tmux jq curl wget ca-certificates ripgrep python3 python3-pip \
        nodejs npm build-essential \
        dbus gnome-keyring libsecret-tools \
        procps sudo \
        tar gzip unzip zip findutils diffutils patch openssl \
    && rm -rf /var/lib/apt/lists/*

# Claude Code CLI for claude-code manager/lanes (claude -p …)
RUN npm install -g @anthropic-ai/claude-code

# Non-root user; passwordless sudo so setup-antigravity.sh can add packages later
# ubuntu:24.04 ships a stock "ubuntu" account already holding uid 1000, which
# would push dev to 1001 and mismatch host file ownership on the bind mount.
# Drop it so dev lands on 1000, matching the Fedora config.
RUN userdel -r ubuntu 2>/dev/null || true
RUN useradd -m -u 1000 -s /bin/bash dev \
    && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev \
    && chmod 440 /etc/sudoers.d/dev

USER dev
ENV PATH="/home/dev/.local/bin:${PATH}"
