#!/bin/sh
DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$DIR/venv/bin:/Library/TeX/texbin:/opt/homebrew/bin:$PATH"
exec "$DIR/venv/bin/python" "$DIR/server.py"
