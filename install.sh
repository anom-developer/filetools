#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}[OK]${RESET}  $*"; }
info() { echo -e "${CYAN}[..]${RESET}  $*"; }
warn() { echo -e "${YELLOW}[!]${RESET}   $*"; }
err()  { echo -e "${RED}[ERR]${RESET} $*" >&2; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════╗"
echo "║       FileTools — Installer             ║"
echo "║   Converter + Searcher CLI utilities    ║"
echo -e "╚══════════════════════════════════════════╝${RESET}"
echo ""

# ── 1. Найти Python 3.8+ ───────────────────────────────────────────────────────
PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3.9 python3.8 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        if "$candidate" -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    err "Python 3.8+ not found."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  Install via Homebrew:  brew install python"
        echo "  Or download from:      https://python.org/downloads/"
    else
        echo "  Ubuntu/Debian:  sudo apt install python3 python3-venv python3-pip"
        echo "  Fedora/RHEL:    sudo dnf install python3"
        echo "  Arch:           sudo pacman -S python"
    fi
    exit 1
fi

PY_VER=$("$PYTHON" --version 2>&1)
ok "Python: $PYTHON  ($PY_VER)"

# ── 2. Проверить venv ─────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import venv" &>/dev/null; then
    err "Module 'venv' not found."
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    exit 1
fi

# ── 3. Виртуальное окружение ──────────────────────────────────────────────────
echo ""
VENV="$SCRIPT_DIR/.venv"
if [[ -d "$VENV" ]]; then
    ok ".venv already exists"
else
    info "Creating virtual environment ..."
    "$PYTHON" -m venv "$VENV"
    ok "Virtual environment created"
fi

# ── 4. Обновить pip ───────────────────────────────────────────────────────────
info "Upgrading pip ..."
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel --quiet
ok "pip upgraded"

# ── 5. Установить пакет ───────────────────────────────────────────────────────
echo ""
info "Installing FileTools ..."
"$VENV/bin/pip" install -e "$SCRIPT_DIR" --quiet
ok "FileTools installed"

# ── 6. Проверить ─────────────────────────────────────────────────────────────
echo ""
info "Verifying ..."
"$VENV/bin/python" -m converter --help &>/dev/null && ok "converter OK"
"$VENV/bin/python" -m searcher  --help &>/dev/null && ok "searcher OK"

# ── 7. Создать wrapper-скрипты ───────────────────────────────────────────────
cat > "$SCRIPT_DIR/converter" << WRAPPER
#!/usr/bin/env bash
"$VENV/bin/python" -m converter "\$@"
WRAPPER
chmod +x "$SCRIPT_DIR/converter"

cat > "$SCRIPT_DIR/searcher" << WRAPPER
#!/usr/bin/env bash
"$VENV/bin/python" -m searcher "\$@"
WRAPPER
chmod +x "$SCRIPT_DIR/searcher"

ok "Wrappers ./converter and ./searcher created"

# ── 8. Предложить добавить в PATH ────────────────────────────────────────────
echo ""
SHELL_RC=""
if   [[ -n "${ZSH_VERSION:-}"  ]]; then SHELL_RC="$HOME/.zshrc"
elif [[ -n "${BASH_VERSION:-}" ]]; then SHELL_RC="$HOME/.bashrc"
fi

if [[ -n "$SHELL_RC" ]]; then
    warn "Add to PATH so commands work from anywhere? [y/N]"
    read -r answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        if grep -qF "$SCRIPT_DIR" "$SHELL_RC" 2>/dev/null; then
            ok "Already in $SHELL_RC"
        else
            echo "" >> "$SHELL_RC"
            echo "# FileTools" >> "$SHELL_RC"
            echo "export PATH=\"$SCRIPT_DIR:\$PATH\"" >> "$SHELL_RC"
            ok "Added to $SHELL_RC"
            warn "Run: source $SHELL_RC  (or open a new terminal)"
        fi
    fi
fi

# ── 9. Финал ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗"
echo    "║      Installation complete!             ║"
echo -e "╚══════════════════════════════════════════╝${RESET}"
echo ""
echo "  ./converter input.png  output.jpg"
echo "  ./converter data.json  data.csv"
echo "  ./converter notes.txt  notes.pdf --font-size 14"
echo ""
echo "  ./searcher '*.py' ./src"
echo "  ./searcher --content 'TODO' . --ext .py"
echo "  ./searcher --regex 'report_[0-9]+' ./docs"
echo ""
echo "  Or activate: source .venv/bin/activate"
echo "  Docs:        https://github.com/your-username/filetools"
echo ""
