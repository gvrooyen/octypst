#!/usr/bin/env python3
"""Build and serve a live, scroll-preserving preview of an Octypst report."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIRECTORY = ROOT / ".amp" / "preview"
OUTPUT = OUTPUT_DIRECTORY / "report.pdf"
PAGES_DIRECTORY = OUTPUT_DIRECTORY / "pages"
WATCH_PATTERNS = (
    "**/*.typ",
    "Makefile",
    "assets/**/*",
)

VIEWER_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__REPORT_NAME__ — live PDF preview</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; background: #202124; }
    body { display: grid; grid-template-rows: 40px minmax(0, 1fr); }
    header {
      display: flex; align-items: center; gap: 10px; padding: 0 14px;
      color: #eef3ff; background: #15213d; border-bottom: 1px solid #385588;
      font-size: 13px;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #65d48a; }
    .building .dot { background: #f3c969; }
    .error .dot { background: #ff6b6b; }
    #status { opacity: 0.85; }
    header a { margin-left: auto; color: #dce8ff; }
    main {
      overflow: auto; display: flex; flex-direction: column; align-items: center;
      gap: 18px; padding: 24px; background: #525659; scrollbar-gutter: stable;
    }
    .page {
      display: block; width: min(100%, 900px); aspect-ratio: 210 / 297;
      background: white; box-shadow: 0 2px 10px #0008;
    }
  </style>
</head>
<body>
  <header id="header"><span class="dot"></span><strong>__REPORT_NAME__ preview</strong><span id="status">Connecting…</span><a href="/report.pdf" target="_blank">Open PDF</a></header>
  <main id="pages" aria-label="Report pages"></main>
  <script>
    const header = document.querySelector('#header');
    const status = document.querySelector('#status');
    const pages = document.querySelector('#pages');
    let version = null;

    function showPages(count, nextVersion) {
      const scrollPosition = pages.scrollTop;
      while (pages.children.length < count) {
        const image = document.createElement('img');
        image.className = 'page';
        image.alt = `Report page ${pages.children.length + 1}`;
        pages.appendChild(image);
      }
      while (pages.children.length > count) pages.lastElementChild.remove();
      [...pages.children].forEach((image, index) => {
        image.src = `/page/${index + 1}.png?v=${encodeURIComponent(nextVersion)}`;
      });
      requestAnimationFrame(() => { pages.scrollTop = scrollPosition; });
    }

    async function refresh() {
      try {
        const response = await fetch('/api/version', { cache: 'no-store' });
        const state = await response.json();
        header.className = state.status;
        status.textContent = state.message;
        if (state.version && state.version !== version) {
          version = state.version;
          showPages(state.page_count, version);
        }
      } catch (_) {
        header.className = 'error';
        status.textContent = 'Preview service disconnected; retrying…';
      }
    }

    refresh();
    setInterval(refresh, 750);
  </script>
</body>
</html>
"""


class BuildState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.status = "building"
        self.message = "Building report…"
        self.version: str | None = None
        self.page_count = 0

    def snapshot(self) -> dict[str, str | int | None]:
        with self.lock:
            return {
                "status": self.status,
                "message": self.message,
                "version": self.version,
                "page_count": self.page_count,
            }

    def building(self) -> None:
        with self.lock:
            self.status = "building"
            self.message = "Rebuilding report…"

    def ready(self, page_count: int) -> None:
        with self.lock:
            self.status = "ready"
            self.message = "Up to date — scroll position is retained"
            self.version = str(time.time_ns())
            self.page_count = page_count

    def failed(self) -> None:
        with self.lock:
            self.status = "error"
            self.message = "Build failed — see the service logs"


STATE = BuildState()
SOURCE: Path
REPORT_NAME: str


def input_signature() -> tuple[tuple[str, int, int], ...]:
    files: set[Path] = set()
    for pattern in WATCH_PATTERNS:
        files.update(path for path in ROOT.glob(pattern) if path.is_file())
    return tuple(
        (str(path.relative_to(ROOT)), path.stat().st_mtime_ns, path.stat().st_size)
        for path in sorted(files)
    )


def build() -> None:
    STATE.building()
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    temporary_pdf = OUTPUT_DIRECTORY / "report-next.pdf"
    temporary_pages = OUTPUT_DIRECTORY / "pages-next"
    previous_pages = OUTPUT_DIRECTORY / "pages-previous"
    shutil.rmtree(temporary_pages, ignore_errors=True)
    shutil.rmtree(previous_pages, ignore_errors=True)
    temporary_pages.mkdir()

    pdf_result = subprocess.run(
        ["typst", "compile", "--root", str(ROOT), str(SOURCE), str(temporary_pdf)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    pages_result = subprocess.run(
        [
            "typst",
            "compile",
            "--root",
            str(ROOT),
            "--ppi",
            "144",
            str(SOURCE),
            str(temporary_pages / "page-{p}.png"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    rendered_pages = sorted(temporary_pages.glob("page-*.png"))
    if pdf_result.returncode == 0 and pages_result.returncode == 0 and rendered_pages:
        os.replace(temporary_pdf, OUTPUT)
        if PAGES_DIRECTORY.exists():
            os.replace(PAGES_DIRECTORY, previous_pages)
        os.replace(temporary_pages, PAGES_DIRECTORY)
        shutil.rmtree(previous_pages, ignore_errors=True)
        STATE.ready(len(rendered_pages))
        print(f"{REPORT_NAME} preview rebuilt ({len(rendered_pages)} pages)", flush=True)
        return

    temporary_pdf.unlink(missing_ok=True)
    shutil.rmtree(temporary_pages, ignore_errors=True)
    STATE.failed()
    diagnostics = (
        pdf_result.stderr
        or pdf_result.stdout
        or pages_result.stderr
        or pages_result.stdout
        or "Typst build failed"
    )
    print(diagnostics, flush=True)


def watch() -> None:
    signature = input_signature()
    build()
    while True:
        time.sleep(0.5)
        current = input_signature()
        if current != signature:
            signature = current
            build()


class PreviewHandler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path in {"/", "/healthz", "/api/version"} or (
            path == "/report.pdf" and OUTPUT.is_file()
        ):
            self.send_response(200)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
        else:
            self.send_error(404)

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path == "/":
            self.respond(
                VIEWER_HTML.replace("__REPORT_NAME__", html.escape(REPORT_NAME)).encode(),
                "text/html; charset=utf-8",
            )
        elif path == "/healthz":
            self.respond(b"ok\n", "text/plain; charset=utf-8")
        elif path == "/api/version":
            self.respond(
                json.dumps(STATE.snapshot()).encode(),
                "application/json; charset=utf-8",
            )
        elif path == "/report.pdf" and OUTPUT.is_file():
            self.respond(OUTPUT.read_bytes(), "application/pdf")
        elif match := re.fullmatch(r"/page/(\d+)\.png", path):
            page = PAGES_DIRECTORY / f"page-{int(match.group(1))}.png"
            if page.is_file():
                self.respond(page.read_bytes(), "image/png")
            else:
                self.send_error(404)
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)

    def respond(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        if args and args[1] != "200":
            super().log_message(format, *args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=os.environ.get("OCTYPST_PREVIEW_SOURCE") or (
            "report.typ" if (ROOT / "report.typ").is_file() else "sample_report.typ"
        ),
        help="Typst source relative to the project root (default: report.typ or sample_report.typ)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    global SOURCE, REPORT_NAME
    SOURCE = (ROOT / args.source).resolve()
    if not SOURCE.is_file() or not SOURCE.is_relative_to(ROOT) or SOURCE.suffix != ".typ":
        parser.error("--source must be an existing .typ file inside the project")
    REPORT_NAME = SOURCE.relative_to(ROOT).as_posix()

    threading.Thread(target=watch, daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.port), PreviewHandler)
    print(f"PDF preview listening on {args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
