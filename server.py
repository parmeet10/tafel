#!/usr/bin/env python3
"""Tafel - render explanatory animations and present them on a chalkboard viewer page."""

import base64
import html
import os
import shutil
import subprocess
import tempfile
import time
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from mcp.server import MCPServer

OUTPUT_DIR = os.path.expanduser(os.environ.get("TAFEL_OUTPUT_DIR", "~/.tafel/renders"))
RENDER_TIMEOUT = int(os.environ.get("TAFEL_TIMEOUT", "300"))
STDERR_TAIL = 2500

mcp = MCPServer("Tafel")


class Point(BaseModel):
    heading: str = Field(description="Short label naming the part of the animation this point belongs to.")
    detail: str = Field(description=(
        "Detailed explanation, 2-4 sentences. The video carries the visuals; this carries the depth - "
        "explain why it works this way, what happens under the hood, edge cases the animation cannot show."
    ))
    at: float | None = Field(
        default=None,
        description="Optional timestamp in seconds. The point highlights while the video passes it and clicking it seeks there.",
    )


class RenderResult(BaseModel):
    video_path: str
    page_path: str
    scene: str
    duration_seconds: float | None
    size_bytes: int
    quality: str
    format: str


QUALITY_FLAGS = {"low": "-ql", "medium": "-qm", "high": "-qh", "fourk": "-qk"}


def _probe_duration(path: str) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30,
        )
        return round(float(out.stdout.strip()), 2)
    except Exception:
        return None


MIME = {"mp4": "video/mp4", "webm": "video/webm", "gif": "image/gif"}


def _viewer_page(video_path: str, fmt: str, title: str, summary: str, points: list[Point], meta: str) -> str:
    with open(video_path, "rb") as f:
        data_uri = f"data:{MIME[fmt]};base64,{base64.b64encode(f.read()).decode()}"
    if fmt == "gif":
        media = f'<img src="{data_uri}" alt="">'
    else:
        media = f'<video id="v" src="{data_uri}" autoplay loop muted playsinline controls></video>'

    items = []
    for p in points:
        at = "" if p.at is None else f' data-at="{p.at}"'
        items.append(f"<li{at}><h3>{html.escape(p.heading)}</h3><p>{html.escape(p.detail)}</p></li>")
    points_html = f'<ul id="points">{"".join(items)}</ul>' if items else ""
    summary_html = f'<p class="summary">{html.escape(summary)}</p>' if summary else ""
    speed_html = "" if fmt == "gif" else (
        '<div class="speed">Speed '
        + "".join(f'<button data-rate="{r}"{" class=on" if r == 1 else ""}>{r}&times;</button>' for r in (0.5, 1, 1.5, 2))
        + "</div>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title) or "Tafel"}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #14171a; color: #e9e7e1; font: 16px/1.6 system-ui, sans-serif;
         display: flex; justify-content: center; padding: 40px 20px; }}
  main {{ width: 100%; max-width: 960px; }}
  h1 {{ font-size: 1.6em; font-weight: 600; padding-bottom: 12px; margin-bottom: 20px;
       border-bottom: 2px solid #3a4046; }}
  video, img {{ width: 100%; border-radius: 8px; background: #000; display: block; }}
  .speed {{ margin-top: 10px; color: #9aa0a6; font-size: .85em; }}
  .speed button {{ background: none; border: 1px solid #3a4046; color: #9aa0a6; border-radius: 5px;
                  padding: 2px 10px; margin-left: 6px; cursor: pointer; font: inherit; }}
  .speed button.on {{ color: #f2d479; border-color: #f2d479; }}
  .summary {{ margin-top: 24px; color: #c7c5bf; }}
  #points {{ margin-top: 20px; list-style: none; }}
  #points li {{ padding: 12px 16px; border-left: 3px solid #3a4046; margin-bottom: 10px;
               border-radius: 0 6px 6px 0; }}
  #points li[data-at] {{ cursor: pointer; }}
  #points li.on {{ border-left-color: #f2d479; background: #1b1f23; }}
  #points h3 {{ font-size: .95em; font-weight: 600; margin-bottom: 4px; }}
  #points li.on h3 {{ color: #f2d479; }}
  #points p {{ color: #c7c5bf; font-size: .95em; }}
  footer {{ margin-top: 28px; color: #6b7075; font-size: .8em; }}
</style>
</head>
<body>
<main>
  {f"<h1>{html.escape(title)}</h1>" if title else ""}
  {media}
  {speed_html}
  {summary_html}
  {points_html}
  <footer>{html.escape(meta)}</footer>
</main>
<script>
  const v = document.getElementById("v");
  if (v) {{
    const lis = [...document.querySelectorAll("#points li[data-at]")];
    lis.forEach(li => li.addEventListener("click", () => {{ v.currentTime = +li.dataset.at; v.play(); }}));
    v.addEventListener("timeupdate", () => {{
      let active = null;
      for (const li of lis) if (+li.dataset.at <= v.currentTime) active = li;
      lis.forEach(li => li.classList.toggle("on", li === active));
    }});
    document.querySelectorAll(".speed button").forEach(b => b.addEventListener("click", () => {{
      v.playbackRate = +b.dataset.rate;
      document.querySelectorAll(".speed button").forEach(x => x.classList.toggle("on", x === b));
    }}));
  }}
</script>
</body>
</html>
"""


@mcp.tool()
def render_animation(
    script: Annotated[str, Field(description=(
        "Python script using the manim library: `from manim import *` and one Scene subclass with a "
        "construct() method. LaTeX is available, so Tex/MathTex work. Prefer elaborate, self-explanatory "
        "scenes: step-by-step buildup with labels, section headings between parts, and a closing summary "
        "frame - not a single quick diagram. Never open with a title or intro card: start directly with "
        "the main content, since the viewer page already shows the title above the video."
    ))],
    title: Annotated[str, Field(description="Heading shown above the video on the viewer page.")] = "",
    summary: Annotated[str, Field(description="One short paragraph shown under the video.")] = "",
    points: Annotated[list[Point], Field(description=(
        "Explanation blocks listed under the video, one per part of the animation. Each has a short "
        "heading and a detailed multi-sentence explanation going beyond what the video shows. Give each "
        "the timestamp (seconds) where its part starts; the page highlights the active block in sync "
        "and clicking one seeks the video there."
    ))] = [],
    depth: Annotated[Literal["overview", "standard", "deep_dive"], Field(description=(
        "How thorough the explanation must be - match the script and points to the chosen level. "
        "overview: ~30s animation, 2-3 points, the core idea only. "
        "standard: ~60s, 4-6 points, step-by-step mechanics. "
        "deep_dive: 90-180s animation with 8+ points that also cover edge cases, failure modes and "
        "the underlying math or internals."
    ))] = "standard",
    quality: Literal["low", "medium", "high", "fourk"] = "medium",
    output_format: Literal["mp4", "webm", "gif"] = "mp4",
    scene_name: Annotated[str, Field(description="Scene class to render if the script defines several.")] = "",
) -> RenderResult:
    """Render an animation onto a chalkboard-style viewer page: the video plays muted on a loop, with
    a title, summary and explanation points beneath it. Write all viewer-page text (title, summary,
    points) and all text inside the animation in English. Returns file paths and video metadata -
    verify duration_seconds roughly matches the scene you wrote.

    This tool only renders to local files - it does not open a browser or publish anywhere. Next
    steps for the calling assistant: publish page_path with the Artifact tool to give the user a
    shareable link (the page is a single self-contained .html with the video embedded as a data URI,
    so it needs no other files), then call cleanup_render(page_path) to delete the local video/html
    once the artifact is published, so renders do not pile up on disk."""
    render_dir = tempfile.mkdtemp(prefix="tafel_")
    try:
        script_path = os.path.join(render_dir, "scene.py")
        with open(script_path, "w") as f:
            f.write(script)

        cmd = [
            "manim", "render", "--media_dir", render_dir,
            QUALITY_FLAGS[quality], "--format", output_format, script_path,
        ]
        if scene_name:
            cmd.append(scene_name)

        timeout = RENDER_TIMEOUT * 2 if depth == "deep_dive" else RENDER_TIMEOUT
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False,
                stdin=subprocess.DEVNULL, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Render timed out after {timeout}s - the script may contain an endless loop or be too heavy.")

        if result.returncode != 0:
            tail = (result.stderr or result.stdout or "render failed")[-STDERR_TAIL:]
            raise RuntimeError(f"Render failed:\n{tail}")

        found = None
        for root, _dirs, files in os.walk(render_dir):
            if "partial_movie_files" in root:
                continue
            for file in files:
                if file.endswith(f".{output_format}"):
                    found = os.path.join(root, file)
                    break
            if found:
                break
        if not found:
            raise RuntimeError("Render reported success but produced no output file.")

        scene = os.path.splitext(os.path.basename(found))[0]
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        stem = f"{time.strftime('%Y%m%d-%H%M%S')}_{scene}"
        video_path = os.path.join(OUTPUT_DIR, f"{stem}.{output_format}")
        shutil.copy(found, video_path)

        duration = _probe_duration(video_path) if output_format != "gif" else None
        size = os.path.getsize(video_path)
        meta = f"{scene} · {quality} · " + (f"{duration}s · " if duration else "") + time.strftime("%Y-%m-%d %H:%M")

        page_path = os.path.join(OUTPUT_DIR, f"{stem}.html")
        with open(page_path, "w") as f:
            f.write(_viewer_page(video_path, output_format, title, summary, points, meta))

        return RenderResult(
            video_path=video_path, page_path=page_path, scene=scene,
            duration_seconds=duration, size_bytes=size,
            quality=quality, format=output_format,
        )
    finally:
        shutil.rmtree(render_dir, ignore_errors=True)


@mcp.tool()
def cleanup_render(page_path: str) -> bool:
    """Delete the local video and viewer-page files for a previous render_animation call, identified
    by its page_path. Call this after the page has been published with the Artifact tool, so rendered
    videos do not accumulate in the output directory. Returns True if any file was removed."""
    real_dir = os.path.realpath(OUTPUT_DIR)
    real_page = os.path.realpath(page_path)
    if os.path.dirname(real_page) != real_dir or not real_page.endswith(".html"):
        raise ValueError("page_path must be an .html file directly inside the Tafel output directory.")

    stem = os.path.splitext(real_page)[0]
    removed = False
    for entry in os.listdir(real_dir):
        entry_path = os.path.join(real_dir, entry)
        if os.path.splitext(entry_path)[0] == stem:
            os.remove(entry_path)
            removed = True
    return removed


if __name__ == "__main__":
    mcp.run()
