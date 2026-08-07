# Tafel

A personal MCP server for Claude Code that turns "explain X with an animation"
into a rendered explainer video on a chalkboard-style viewer page: the video
plays muted on a loop, with a title, a summary and detailed, click-to-seek
explanation blocks beneath it. Pages are single self-contained HTML files -
send one to anybody and it plays offline in their browser.

Claude writes the animation code; your Mac renders it. No tokens are spent on
pixels - only on the scene script and the explanation text.

## Requirements

- macOS with [Homebrew](https://brew.sh)
- [Claude Code](https://claude.com/claude-code)
- Optional: LaTeX for mathematical formulas (`brew install --cask mactex-no-gui`, ~5 GB)

## Install

Unpack this folder anywhere permanent (e.g. `~/Documents/tafel`), then:

```sh
cd tafel
./install.sh
```

The script installs the Homebrew dependencies (ffmpeg, cairo, pango,
python 3.12), creates a local `venv`, installs the Python packages, and
registers the server with Claude Code as `tafel` (user scope, all projects).

Manual equivalent, if you prefer:

```sh
brew install ffmpeg cairo pango python@3.12
python3.12 -m venv venv
./venv/bin/pip install -r requirements.txt
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

The viewer page opens in your browser automatically when the render finishes.
Iterate conversationally: "slow down step 3", "make the arrows curved" -
Claude edits the scene and re-renders.

## Output and sharing

Renders land in `~/.tafel/renders/` (override with the `TAFEL_OUTPUT_DIR`
environment variable) as `<timestamp>_<Scene>.mp4` plus a matching `.html`
viewer page. The `.html` embeds the video, so that single file is the whole
deliverable - share it by sending it.

## Troubleshooting

- **Tool missing in a session** - servers load at session start; run `/mcp`
  to reconnect or open a new session. Same after updating `server.py`.
- **Formula scenes fail** ("latex: command not found" in the error) - install
  MacTeX (see Requirements); the wrapper already puts `/Library/TeX/texbin`
  on the PATH.
- **Render timeout** - default limit is 300s per render (600s for deep dives).
  Raise it via the `TAFEL_TIMEOUT` environment variable if 4K renders need more.
