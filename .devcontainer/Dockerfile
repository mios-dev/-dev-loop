# dev-loop devcontainer — Fedora (default image family for this repo).
# Everything a dev-loop host or lane needs: git, tmux, jq, python3, the Secret
# Service keyring stack for Antigravity credential caching, Node.js + Claude
# Code for claude-code lanes. The Antigravity CLI itself is installed per-user
# at postCreate by setup-antigravity.sh (its installer targets ~/.local/bin).
ARG FEDORA_VERSION=44
FROM registry.fedoraproject.org/fedora:${FEDORA_VERSION}

RUN dnf -y install \
        git tmux jq curl python3 python3-pip \
        dbus-daemon dbus-tools gnome-keyring libsecret \
        procps-ng util-linux shadow-utils sudo which hostname tar unzip \
        nodejs npm \
    && dnf clean all

# Claude Code CLI for claude-code manager/lanes (claude -p …)
RUN npm install -g @anthropic-ai/claude-code

# Non-root user; passwordless sudo so setup-antigravity.sh can add packages later
RUN useradd -m -s /bin/bash dev \
    && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev \
    && chmod 440 /etc/sudoers.d/dev

USER dev
ENV PATH="/home/dev/.local/bin:${PATH}"
