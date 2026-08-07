#!/bin/sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "== Tafel setup =="

OS="$(uname -s)"

install_deps_macos() {
    command -v brew >/dev/null 2>&1 || { echo "Homebrew is required first: https://brew.sh"; exit 1; }
    for pkg in ffmpeg cairo pango; do
        brew list --versions "$pkg" >/dev/null 2>&1 || brew install "$pkg"
    done
    command -v uv >/dev/null 2>&1 || brew install uv
    LATEX_HINT="brew install --cask mactex-no-gui   (~5 GB, optional)"
    LATEX_BIN="/Library/TeX/texbin/latex"
}

install_deps_linux() {
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev pkg-config
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y ffmpeg cairo-devel pango-devel pkgconf-pkg-config
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --needed --noconfirm ffmpeg cairo pango pkgconf
    else
        echo "Unrecognized package manager - install ffmpeg, cairo, and pango (with headers) manually, then re-run."
        exit 1
    fi
    command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
    LATEX_HINT="sudo apt-get install texlive texlive-latex-extra texlive-fonts-extra   (optional, several GB)"
    LATEX_BIN="$(command -v latex || true)"
}

case "$OS" in
    Darwin) install_deps_macos ;;
    Linux) install_deps_linux ;;
    *)
        echo "Unsupported OS: $OS"
        echo "On Windows, install inside WSL2 (https://learn.microsoft.com/windows/wsl/install) and re-run this script there."
        exit 1
        ;;
esac

export PATH="$HOME/.local/bin:$PATH"
chmod +x "$DIR/run-stdio.sh"

echo "Resolving Python environment (uv picks/downloads a suitable interpreter automatically)..."
uv sync --project "$DIR"

if [ -z "${LATEX_BIN:-}" ] || [ ! -x "${LATEX_BIN:-/nonexistent}" ]; then
    echo "Note: no LaTeX found - animations work, but Tex/MathTex formulas need it:"
    echo "      $LATEX_HINT"
fi

if command -v claude >/dev/null 2>&1; then
    claude mcp add tafel -s user -- "$DIR/run-stdio.sh"
    echo "Registered. Open a NEW Claude Code session and ask for an animation."
else
    echo "claude CLI not found - register manually once it is installed:"
    echo "  claude mcp add tafel -s user -- $DIR/run-stdio.sh"
fi
