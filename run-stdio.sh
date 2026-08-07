#!/bin/sh
DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="/Library/TeX/texbin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec uv run --project "$DIR" server.py
