#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# create_release.sh
#
# Publishes a GitHub Release with all artifacts via GitHub CLI (gh).
#
# Prerequisites:
#   gh CLI  →  https://cli.github.com
#   Auth    →  gh auth login
#
# Usage:
#   bash create_release.sh [VERSION]
#   bash create_release.sh v0.2.0
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

VERSION="${1:-v0.1.0}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}[OK]${RESET}  $*"; }
info() { echo -e "${CYAN}[..]${RESET}  $*"; }
warn() { echo -e "${YELLOW}[!]${RESET}   $*"; }

echo ""
echo "  Publishing FileTools ${VERSION} to GitHub..."
echo ""

# ── Check gh ─────────────────────────────────────────────────────────────────
if ! command -v gh &>/dev/null; then
    echo "  gh CLI not found. Install from: https://cli.github.com"
    exit 1
fi

gh auth status &>/dev/null || { echo "  Run: gh auth login"; exit 1; }
ok "gh CLI authenticated"

# ── Run tests ─────────────────────────────────────────────────────────────────
info "Running tests ..."
cd "$SCRIPT_DIR"
if command -v pytest &>/dev/null; then
    pytest -q && ok "All tests passed"
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
  --exclude "*/.pytest_cache/*" \
  -q
ok "Source zip: $SOURCE_ZIP  ($(du -sh "$SOURCE_ZIP" | cut -f1))"

# ── Build Linux binaries (if PyInstaller available) ───────────────────────────
LINUX_ARCHIVE=""
if command -v pyinstaller &>/dev/null; then
    info "Building Linux binaries ..."
    pyinstaller --onefile --name converter --distpath /tmp/ft_dist/ \
        --workpath /tmp/ft_build/ --specpath /tmp/ \
        converter/__main__.py -y --log-level WARN
    pyinstaller --onefile --name searcher  --distpath /tmp/ft_dist/ \
        --workpath /tmp/ft_build/ --specpath /tmp/ \
        searcher/__main__.py  -y --log-level WARN
    LINUX_ARCHIVE="/tmp/filetools-linux-x86_64.tar.gz"
    tar -czf "$LINUX_ARCHIVE" -C /tmp/ft_dist converter searcher
    ok "Linux archive: $LINUX_ARCHIVE  ($(du -sh "$LINUX_ARCHIVE" | cut -f1))"
else
    warn "pyinstaller not found — skipping Linux binaries (pip install pyinstaller)"
fi

# ── Create git tag ────────────────────────────────────────────────────────────
info "Creating tag ${VERSION} ..."
git tag -a "${VERSION}" -m "Release ${VERSION}" 2>/dev/null \
    || warn "Tag ${VERSION} already exists, reusing"
git push origin "${VERSION}" 2>/dev/null \
    || warn "Tag already on remote, continuing"
ok "Tag pushed"

# ── Publish release ───────────────────────────────────────────────────────────
info "Publishing release ..."

ASSETS=("$SOURCE_ZIP")
[[ -n "$LINUX_ARCHIVE" ]] && ASSETS+=("$LINUX_ARCHIVE")

NOTES="## FileTools ${VERSION}

See [CHANGELOG.md](https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/blob/main/CHANGELOG.md) for full details."

gh release create "${VERSION}" \
    --title "FileTools ${VERSION}" \
    --notes "$NOTES" \
    "${ASSETS[@]}"

ok "Release published!"
echo ""
echo "  → $(gh repo view --json url -q .url)/releases/tag/${VERSION}"
echo ""
