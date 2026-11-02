#!/usr/bin/env python3
"""Serve an explicit-save browser editor for an Octypst report."""

import argparse
import hashlib
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import threading
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / ("report.typ" if (ROOT / "report.typ").is_file() else "sample_report.typ")
PAGE = ROOT / "editor" / "index.html"
BUNDLE = ROOT / "editor" / "app.bundle.js"
PREVIEW = ROOT / ".amp" / "preview" / "editor" / "report.pdf"
PREVIEW_PAGES = PREVIEW.parent / "pages"
SAVE_LOCK = threading.Lock()
preview_revision = None
preview_page_count = 0


def revision(data):
    return hashlib.sha256(data).hexdigest()


def render_preview(data):
    global preview_revision, preview_page_count
    current_revision = revision(data)
    if current_revision == preview_revision and PREVIEW.is_file() and PREVIEW_PAGES.is_dir():
        return {"ok": True, "version": current_revision, "pageCount": preview_page_count}

    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=PREVIEW.parent) as directory:
        temporary = Path(directory)
        try:
            pdf = subprocess.run(
                ["typst", "compile", "--root", str(ROOT), str(SOURCE), str(temporary / "report.pdf")],
                cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
            )
            pages = subprocess.run(
                ["typst", "compile", "--root", str(ROOT), "--ppi", "144", str(SOURCE), str(temporary / "page-{p}.png")],
                cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
            ) if pdf.returncode == 0 else pdf
        except subprocess.TimeoutExpired:
            return {"ok": False, "message": "Preview build timed out."}
        rendered = sorted(temporary.glob("page-*.png"))
        if pdf.returncode or pages.returncode or not rendered:
            return {"ok": False, "message": (pdf.stderr or pages.stderr).strip() or "Typst could not render the report."}
        os.replace(temporary / "report.pdf", PREVIEW)
        previous = PREVIEW.parent / "pages-previous"
        shutil.rmtree(previous, ignore_errors=True)
        if PREVIEW_PAGES.exists():
            os.replace(PREVIEW_PAGES, previous)
        os.replace(temporary, PREVIEW_PAGES)
        shutil.rmtree(previous, ignore_errors=True)
        preview_revision = current_revision
        preview_page_count = len(rendered)
        return {"ok": True, "version": current_revision, "pageCount": preview_page_count}


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        if urlsplit(self.path).path in {"/", "/app.js", "/document", "/preview/status", "/healthz"} or (
            urlsplit(self.path).path == "/preview.pdf" and PREVIEW.is_file()
        ):
            self.send_response(200)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
        else:
            self.send_error(404)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            page = PAGE.read_text().replace("__REPORT_NAME__", html.escape(SOURCE.relative_to(ROOT).as_posix()))
            self.respond(200, page.encode(), "text/html; charset=utf-8")
        elif path == "/app.js":
            self.respond(200, BUNDLE.read_bytes(), "text/javascript; charset=utf-8")
        elif path == "/document":
            data = SOURCE.read_bytes()
            self.json(200, {"text": data.decode("utf-8"), "revision": revision(data)})
        elif path == "/preview/status":
            with SAVE_LOCK:
                self.json(200, render_preview(SOURCE.read_bytes()))
        elif path == "/preview.pdf" and PREVIEW.is_file():
            self.respond(200, PREVIEW.read_bytes(), "application/pdf")
        elif match := re.fullmatch(r"/preview/page/(\d+)\.png", path):
            page = PREVIEW_PAGES / f"page-{int(match.group(1))}.png"
            if page.is_file():
                self.respond(200, page.read_bytes(), "image/png")
            else:
                self.send_error(404)
        elif path == "/healthz":
            self.respond(200, b"ok\n", "text/plain; charset=utf-8")
        elif path == "/favicon.ico":
            self.respond(204, b"", "text/plain")
        else:
            self.send_error(404)

    def do_POST(self):
        if urlsplit(self.path).path != "/document":
            self.send_error(404)
            return
        if (self.headers.get("Content-Type", "").split(";")[0] != "application/json"
                or self.headers.get("X-Editor-Save") != "1"):
            self.send_error(415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if not 0 < length <= 512_000:
            self.send_error(413)
            return
        try:
            request = json.loads(self.rfile.read(length))
            text, expected = request["text"], request["revision"]
            if not isinstance(text, str) or not isinstance(expected, str):
                raise ValueError("Invalid document")
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            self.send_error(400)
            return

        with SAVE_LOCK:
            current = SOURCE.read_bytes()
            if revision(current) != expected:
                self.json(409, {"error": "The file changed on the server. Reload before saving."})
                return
            data = text.encode("utf-8")
            if data != current:
                fd, temporary = tempfile.mkstemp(prefix=".report-save-", dir=SOURCE.parent)
                try:
                    os.fchmod(fd, stat.S_IMODE(SOURCE.stat().st_mode))
                    with os.fdopen(fd, "wb") as file:
                        file.write(data)
                        file.flush()
                        os.fsync(file.fileno())
                    os.replace(temporary, SOURCE)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
            self.json(200, {"revision": revision(data), "preview": render_preview(data)})

    def json(self, status, value):
        self.respond(status, json.dumps(value).encode(), "application/json; charset=utf-8")

    def respond(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=os.environ.get("OCTYPST_EDITOR_SOURCE") or SOURCE.name,
        help="Typst source relative to the project root (default: report.typ or sample_report.typ)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    SOURCE = (ROOT / args.source).resolve()
    if not SOURCE.is_file() or not SOURCE.is_relative_to(ROOT) or SOURCE.suffix != ".typ":
        parser.error("--source must be an existing .typ file inside the project")
    if not BUNDLE.is_file():
        parser.error("editor/app.bundle.js is missing; run npm ci && npm run build:editor")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
