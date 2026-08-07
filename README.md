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

Steer it with plain words - they map to the tool's settings below. Say
things like "quick overview", "deep dive", "low quality, I'm iterating", or
"give me a gif" and Claude picks the matching value; it defaults to
`standard` depth and `medium` quality if you don't specify.

### Settings

| Setting | Values | Effect |
|---|---|---|
| **depth** | `overview` / `standard` (default) / `deep_dive` | Animation length and explanation depth. `overview`: ~30s, 2-3 points, core idea only. `standard`: ~60s, 4-6 points, step-by-step. `deep_dive`: 90-180s, 8+ points, edge cases, failure modes, underlying internals. |
| **quality** | `low` / `medium` (default) / `high` / `fourk` | Render resolution: 480p / 720p / 1080p / 4K. Higher quality renders noticeably slower - use `low` while iterating on a scene, bump it up for the final version. |
| **format** | `mp4` (default) / `webm` / `gif` | Output video container. `gif` has no audio/speed controls on the viewer page. |
| **scene_name** | - | Only needed if the animation script defines more than one `Scene` class and a specific one should render. |

When the render finishes, Claude publishes the viewer page as a claude.ai
artifact and shares the link - it does not open a local browser window.
Iterate conversationally: "slow down step 3", "make the arrows curved",
"redo this in high quality" - Claude edits the scene or settings and
re-renders.

### Environment variables

| Variable | Default | Effect |
|---|---|---|
| `TAFEL_OUTPUT_DIR` | `~/.tafel/renders` | Where finished renders land before being published and cleaned up. |
| `TAFEL_TIMEOUT` | `300` (seconds) | Per-render timeout; doubled automatically for `deep_dive`. Raise it if `high`/`fourk` renders are timing out. |

Set these before running `install.sh`, or edit them into `run-stdio.sh`
after install (`export TAFEL_TIMEOUT=600` before the `exec uv run` line),
then reconnect the server with `/mcp`.

## Output and cleanup

Each render briefly lands in the output directory (`TAFEL_OUTPUT_DIR` above)
as `<timestamp>_<Scene>.mp4` plus a matching self-contained `.html` viewer
page (video embedded as a data URI). Claude deletes both right after
publishing the artifact, so nothing accumulates on disk under normal use. If
a session ends before cleanup runs, stale files may be left behind - safe to
delete the directory's contents manually at any time.

## Troubleshooting

- **Tool missing in a session** - servers load at session start; run `/mcp`
  to reconnect or open a new session. Same after updating `server.py`.
- **Formula scenes fail** ("latex: command not found" in the error) - install
  LaTeX: `brew install --cask mactex-no-gui` on macOS (~5 GB), or
  `sudo apt-get install texlive texlive-latex-extra texlive-fonts-extra` on
  Linux. Optional - only needed for `Tex`/`MathTex` formulas, not plain
  animations.
- **Render timeout** - see `TAFEL_TIMEOUT` under Environment variables above;
  raise it if `high`/`fourk` or `deep_dive` renders are cutting off.
