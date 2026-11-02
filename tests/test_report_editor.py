"""Exercise the report editor's explicit saves and last-good preview through HTTP."""

import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from scripts import report_editor


class ReportEditorPreviewTest(unittest.TestCase):
    def test_preview_tracks_successful_saves_and_retains_last_good_render(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            original = (report_editor.ROOT, report_editor.SOURCE, report_editor.PREVIEW,
                        report_editor.PREVIEW_PAGES, report_editor.preview_revision,
                        report_editor.preview_page_count)
            report_editor.ROOT = root
            report_editor.SOURCE = root / "report.typ"
            report_editor.PREVIEW = root / "report.pdf"
            report_editor.PREVIEW_PAGES = root / "pages"
            report_editor.preview_revision = None
            report_editor.preview_page_count = 0
            report_editor.SOURCE.write_text("= Original\n")
            server = ThreadingHTTPServer(("127.0.0.1", 0), report_editor.Handler)
            Thread(target=server.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{server.server_port}"

            def get(path):
                with urlopen(base + path) as response:
                    return response.read()

            def save(text, revision):
                request = Request(
                    base + "/document",
                    data=json.dumps({"text": text, "revision": revision}).encode(),
                    headers={"Content-Type": "application/json", "X-Editor-Save": "1"},
                )
                with urlopen(request) as response:
                    return json.load(response)

            try:
                initial = json.loads(get("/preview/status"))
                self.assertTrue(initial["ok"])
                self.assertEqual(initial["pageCount"], 1)
                self.assertTrue(get("/preview/page/1.png").startswith(b"\x89PNG"))
                first_pdf = hashlib.sha256(get("/preview.pdf")).digest()

                updated = save("= Updated\n", initial["version"])
                self.assertTrue(updated["preview"]["ok"])
                self.assertNotEqual(updated["preview"]["version"], initial["version"])
                with self.assertRaises(HTTPError) as error:
                    save("= Stale\n", initial["version"])
                self.assertEqual(error.exception.code, 409)
                last_good = hashlib.sha256(get("/preview.pdf")).digest()
                self.assertNotEqual(first_pdf, last_good)

                invalid = save("#let =\n", updated["revision"])
                self.assertFalse(invalid["preview"]["ok"])
                self.assertEqual(report_editor.SOURCE.read_text(), "#let =\n")
                self.assertEqual(hashlib.sha256(get("/preview.pdf")).digest(), last_good)

                recovered = save("= Recovered\n", invalid["revision"])
                self.assertTrue(recovered["preview"]["ok"])
                self.assertTrue(get("/preview/page/1.png").startswith(b"\x89PNG"))
            finally:
                server.shutdown()
                server.server_close()
                (report_editor.ROOT, report_editor.SOURCE, report_editor.PREVIEW,
                 report_editor.PREVIEW_PAGES, report_editor.preview_revision,
                 report_editor.preview_page_count) = original


if __name__ == "__main__":
    unittest.main()
