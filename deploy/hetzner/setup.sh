#!/usr/bin/env bash
# Run on the Hetzner server as the `kronos` user, after cloud-init has finished.
# Clones the repo, installs Python 3.11 + dependencies (CPU torch) and checks the config.
set -euo pipefail

# SSH URL + read-only deploy key (see deploy/hetzner/README.md) for a private repo.
REPO_URL="${REPO_URL:-git@github.com:pinxaolives/KronosTrading.git}"
# Development branch until it is merged; then use main.
BRANCH="${BRANCH:-claude/serene-brown-ffl49r}"
APP_DIR="${APP_DIR:-$HOME/KronosTrading}"

export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || { echo "uv not found; did cloud-init finish?"; exit 1; }

if [[ ! -d "$APP_DIR/.git" ]]; then
  git clone --branch "$BRANCH" --recurse-submodules "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"
git submodule update --init --recursive

uv python install 3.11
make setup-kronos

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created .env from template — edit it to add your tokens."
fi

make check
uv run kt config-check
echo "Setup complete."
