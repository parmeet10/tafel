# Tafel

An MCP server for Claude Code that turns "explain X with an animation" into
a rendered explainer video on a chalkboard-style viewer page: the video plays
muted on a loop, with a title, a summary and detailed, click-to-seek
explanation blocks beneath it. Claude publishes the page as a claude.ai
artifact, so you get a shareable link - no local file to manage.

Claude writes the animation code; your machine renders it. No tokens are
spent on pixels - only on the scene script and the explanation text.

## Requirements

- macOS or Linux (Windows: install inside [WSL2](https://learn.microsoft.com/windows/wsl/install) and follow the Linux steps there)
- [Claude Code](https://claude.com/claude-code)
- Optional: LaTeX for mathematical formulas (several GB - see Troubleshooting)

## Install

Unpack this folder anywhere permanent (e.g. `~/Documents/tafel`), then:

```sh
cd tafel
./install.sh
```

The script installs the native dependencies (ffmpeg, cairo, pango) via
Homebrew on macOS or your Linux package manager (apt/dnf/pacman), installs
[`uv`](https://docs.astral.sh/uv/) if missing, and registers the server with
Claude Code as `tafel` (user scope, all projects). `uv` resolves the right
Python version and the project's Python packages itself - no manual venv or
Python install needed.

Manual equivalent, if you prefer:

```sh
# macOS
brew install ffmpeg cairo pango uv
# Linux (Debian/Ubuntu)
sudo apt-get install ffmpeg libcairo2-dev libpango1.0-dev pkg-config
curl -LsSf https://astral.sh/uv/install.sh | sh

chmod +x run-stdio.sh
claude mcp add tafel -s user -- "$PWD/run-stdio.sh"
```

Then open a **new** Claude Code session (servers load at session start) and
check with `/mcp` that `tafel` shows as connected.

## Usage

Just ask in any session:

> explain how an SSL/TLS handshake works with an animation

Steer it with plain words - they map to the tool's parameters:

- **depth**: "quick overview" (~30s, core idea) / default (~60s, step by step) /
  "deep dive" (90-180s, edge cases and internals)
- **quality**: "low" 480p (fast, for iterating) / default 720p / "high" 1080p
  (presentations) / "fourk" 4K
- **format**: mp4 (default), webm or gif

When the render finishes, Claude publishes the viewer page as a claude.ai
artifact and shares the link - it does not open a local browser window.
Iterate conversationally: "slow down step 3", "make the arrows curved" -
Claude edits the scene and re-renders.

## Output and cleanup

Each render briefly lands in `~/.tafel/renders/` (override with the
`TAFEL_OUTPUT_DIR` environment variable) as `<timestamp>_<Scene>.mp4` plus a
matching self-contained `.html` viewer page (video embedded as a data URI).
Claude deletes both right after publishing the artifact, so nothing
accumulates on disk under normal use. If a session ends before cleanup runs,
stale files may be left behind - safe to delete the directory's contents
manually at any time.

## Troubleshooting

- **Tool missing in a session** - servers load at session start; run `/mcp`
  to reconnect or open a new session. Same after updating `server.py`.
- **Formula scenes fail** ("latex: command not found" in the error) - install
  LaTeX: `brew install --cask mactex-no-gui` on macOS (~5 GB), or
  `sudo apt-get install texlive texlive-latex-extra texlive-fonts-extra` on
  Linux. Optional - only needed for `Tex`/`MathTex` formulas, not plain
  animations.
- **Render timeout** - default limit is 300s per render (600s for deep dives).
  Raise it via the `TAFEL_TIMEOUT` environment variable if 4K renders need more.
