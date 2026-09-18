# dev-loop devcontainer — Ubuntu variant (Fedora is this repo's default; pick
# this config for apt-based parity with Claude Code on the web containers).
ARG UBUNTU_VERSION=24.04
FROM ubuntu:${UBUNTU_VERSION}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
        git tmux jq curl ca-certificates python3 python3-pip \
        dbus gnome-keyring libsecret-tools \
        procps sudo tar unzip \
        nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Claude Code CLI for claude-code manager/lanes (claude -p …)
RUN npm install -g @anthropic-ai/claude-code

# Non-root user; passwordless sudo so setup-antigravity.sh can add packages later
RUN useradd -m -s /bin/bash dev \
    && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev \
    && chmod 440 /etc/sudoers.d/dev

USER dev
ENV PATH="/home/dev/.local/bin:${PATH}"
