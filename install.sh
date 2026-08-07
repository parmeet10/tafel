#!/bin/sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "== Tafel setup =="

command -v brew >/dev/null 2>&1 || { echo "Homebrew is required first: https://brew.sh"; exit 1; }

for pkg in ffmpeg cairo pango python@3.12; do
    brew list --versions "$pkg" >/dev/null 2>&1 || brew install "$pkg"
done

PY="$(brew --prefix python@3.12)/bin/python3.12"
[ -d "$DIR/venv" ] || "$PY" -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install --quiet --upgrade pip
"$DIR/venv/bin/pip" install --quiet -r "$DIR/requirements.txt"
chmod +x "$DIR/run-stdio.sh"

if [ ! -x /Library/TeX/texbin/latex ]; then
    echo "Note: no LaTeX found - animations work, but Tex/MathTex formulas need it:"
    echo "      brew install --cask mactex-no-gui   (~5 GB, optional)"
fi

if command -v claude >/dev/null 2>&1; then
    claude mcp add tafel -s user -- "$DIR/run-stdio.sh"
    echo "Registered. Open a NEW Claude Code session and ask for an animation."
else
    echo "claude CLI not found - register manually once it is installed:"
    echo "  claude mcp add tafel -s user -- $DIR/run-stdio.sh"
fi
