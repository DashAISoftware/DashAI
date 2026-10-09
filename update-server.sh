#!/usr/bin/env bash
# update-server.sh — Pull latest changes and rebuild DashAI on the server.
#
# Usage:
#   ./update-server.sh              # Normal update
#   ./update-server.sh --setup      # First-time: set the production API URL
#   ./update-server.sh --api-url https://example.com/api   # Override API URL once
#
# On the server, run --setup once. After that, plain ./update-server.sh is enough.
# The production URL lives in DashAI/front/.env.production.local (gitignored),
# so git pull never overwrites it and git stash is no longer needed.

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── Defaults ─────────────────────────────────────────────────────────────────
CONDA_ENV="dashai"
ENV_LOCAL="DashAI/front/.env.production.local"
SETUP=false
CUSTOM_API_URL=""

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --setup)       SETUP=true; shift ;;
    --api-url)     CUSTOM_API_URL="$2"; shift 2 ;;
    --help|-h)
      sed -n '2,12p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) error "Unknown argument: $1. Use --help for usage." ;;
  esac
done

# ── Locate repo root (script must live there) ─────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
[[ -f "DashAI/front/.env.production" ]] || error "Run this script from the DashAI repo root."

# ── Conda activation ──────────────────────────────────────────────────────────
info "Activating conda environment '$CONDA_ENV'..."
# shellcheck disable=SC1091
if command -v conda &>/dev/null; then
  eval "$(conda shell.bash hook)"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
else
  error "conda not found. Add conda to PATH or adjust this script."
fi
conda activate "$CONDA_ENV"
success "Conda environment active."

# ── First-time setup: create .env.production.local ───────────────────────────
if [[ "$SETUP" == true ]] || [[ -n "$CUSTOM_API_URL" ]]; then
  if [[ -z "$CUSTOM_API_URL" ]]; then
    read -rp "Enter the production API URL (e.g. https://dashai.dcc.uchile.cl/api): " CUSTOM_API_URL
  fi
  [[ -z "$CUSTOM_API_URL" ]] && error "API URL cannot be empty."
  echo "REACT_APP_API_URL=${CUSTOM_API_URL}" > "$ENV_LOCAL"
  success "Saved API URL to $ENV_LOCAL → ${CUSTOM_API_URL}"
fi

# Warn if .env.production.local is missing (first run without --setup)
if [[ ! -f "$ENV_LOCAL" ]]; then
  warn ".env.production.local not found."
  warn "The build will use the default localhost URL from .env.production."
  warn "Run with --setup to configure the production URL permanently."
fi

# ── Git pull ──────────────────────────────────────────────────────────────────
info "Pulling latest changes..."
git pull
success "Git up to date."

# ── Frontend build ────────────────────────────────────────────────────────────
info "Installing frontend dependencies..."
(cd DashAI/front && yarn install)

info "Building frontend..."
(cd DashAI/front && yarn build)
success "Frontend built."

# ── Python dependencies ───────────────────────────────────────────────────────
info "Installing Python dependencies..."
if command -v uv &>/dev/null; then
  # uv targets the active conda env and reads deps from pyproject.toml
  uv pip install -e .
else
  warn "uv not found, falling back to pip (consider installing uv: https://docs.astral.sh/uv/)."
  pip install -e .
fi
success "Python dependencies installed."

# ── Restart service ───────────────────────────────────────────────────────────
info "Restarting dashai service..."
systemctl --user restart dashai
success "Service restarted."

echo ""
echo -e "${GREEN}✓ DashAI updated successfully.${NC}"
if [[ -f "$ENV_LOCAL" ]]; then
  echo -e "  API URL: ${CYAN}$(grep REACT_APP_API_URL "$ENV_LOCAL" | cut -d= -f2-)${NC}"
fi
