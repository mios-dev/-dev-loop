# dev-loop devcontainer — Fedora (default image family for this repo).
# Everything a dev-loop host or lane needs: git, tmux, jq, python3, the Secret
# Service keyring stack for Antigravity credential caching, Node.js + Claude
# Code for claude-code lanes. The Antigravity CLI itself is installed per-user
# at postCreate by setup-antigravity.sh (its installer targets ~/.local/bin).
# Nothing pinned: the base floats on Fedora's latest release.
FROM registry.fedoraproject.org/fedora:latest

# Same package set as the cloud environment's Fedora image
# (skills/dev-loop/scripts/env/cloud-fedora-setup.sh), so a devcontainer and a
# cloud session present the same Fedora. install_weak_deps=False keeps it lean.
RUN dnf -y --setopt=install_weak_deps=False install \
        git tmux jq curl wget ripgrep python3 python3-pip \
        nodejs npm gcc gcc-c++ make \
        dbus-daemon dbus-tools gnome-keyring libsecret \
        procps-ng util-linux shadow-utils sudo which hostname \
        tar gzip unzip zip findutils diffutils patch openssl \
    && dnf clean all

# Claude Code CLI for claude-code manager/lanes (claude -p …)
RUN npm install -g @anthropic-ai/claude-code

# Non-root user; passwordless sudo so setup-antigravity.sh can add packages later
RUN useradd -m -s /bin/bash dev \
    && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev \
    && chmod 440 /etc/sudoers.d/dev

USER dev
ENV PATH="/home/dev/.local/bin:${PATH}"
