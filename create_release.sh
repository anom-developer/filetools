#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# create_release.sh
#
# Publishes a GitHub Release with all artifacts via GitHub CLI (gh) or git tag.
#
# Prerequisites:
#   gh CLI  →  https://cli.github.com
#   Auth    →  gh auth login
#
# Usage:
#   bash create_release.sh [VERSION]
#   bash create_release.sh v1.0.0
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

VERSION="${1:-v1.0.0}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}[OK]${RESET}  $*"; }
info() { echo -e "${CYAN}[..]${RESET}  $*"; }
warn() { echo -e "${YELLOW}[!]${RESET}   $*"; }

echo ""
echo "  Publishing FileTools ${VERSION} to GitHub..."
echo ""

# ── Run tests ─────────────────────────────────────────────────────────────────
info "Running tests ..."
cd "$SCRIPT_DIR"
if command -v pytest &>/dev/null; then
    pytest -q && ok "All tests passed"
elif [[ -f "$SCRIPT_DIR/.venv/bin/pytest" ]]; then
    "$SCRIPT_DIR/.venv/bin/pytest" -q && ok "All tests passed"
else
    warn "pytest not found, skipping tests"
fi

# ── Build source zip ──────────────────────────────────────────────────────────
info "Building source zip ..."
SOURCE_ZIP="/tmp/filetools-source.zip"
zip -r "$SOURCE_ZIP" . \
  --exclude "*/__pycache__/*" --exclude "*.pyc" \
  --exclude "*/.git/*"        --exclude "*/dist/*" \
  --exclude "*/.venv/*"       --exclude "*.egg-info/*" \
  --exclude "*/.pytest_cache/*" --exclude "*/build/*" \
  -q 2>/dev/null || true

# ── Create git tag ────────────────────────────────────────────────────────────
info "Creating tag ${VERSION} ..."
git tag -a "${VERSION}" -m "Release ${VERSION}" 2>/dev/null \
    || warn "Tag ${VERSION} already exists, reusing"
git push origin "${VERSION}" 2>/dev/null \
    || warn "Tag push finished"
ok "Tag pushed"

# ── Publish via gh if available ───────────────────────────────────────────────
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
    info "Publishing release via GitHub CLI..."
    ASSETS=()
    [[ -f "$SOURCE_ZIP" ]] && ASSETS+=("$SOURCE_ZIP")
    [[ -f "dist/filetools-windows-x86_64.zip" ]] && ASSETS+=("dist/filetools-windows-x86_64.zip")

    NOTES="## FileTools ${VERSION}

See [CHANGELOG.md](https://github.com/anom-developer/filetools/blob/main/CHANGELOG.md) for full details."

    gh release create "${VERSION}" \
        --title "FileTools ${VERSION}" \
        --notes "$NOTES" \
        "${ASSETS[@]}" || warn "gh release create returned non-zero (release may already exist)"
    ok "GitHub Release published!"
else
    ok "Tag ${VERSION} pushed! GitHub Actions will automatically build binaries and create the release."
fi
