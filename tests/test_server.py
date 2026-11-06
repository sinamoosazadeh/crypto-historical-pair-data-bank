import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import urlopen

from pairatlas.server import PublicFilesHandler


class PublicServerTests(unittest.TestCase):
    def test_public_files_work_but_checkout_internals_do_not(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<h1>PairAtlas</h1>")
            (root / ".env").write_text("PRIVATE=not-for-http")
            (root / "pyproject.toml").write_text("[project]")
            (root / ".git").mkdir()
            (root / ".git/config").write_text("private configuration")
            (root / "docs").mkdir()
            with ThreadingHTTPServer(("127.0.0.1", 0), partial(PublicFilesHandler, directory=directory)) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    with urlopen(base + "/", timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertIn(b"PairAtlas", response.read())
                        self.assertEqual(response.headers["Cache-Control"], "no-cache")
                    for path in ("/.env", "/.git/config", "/%2egit/config", "/pyproject.toml", "/docs/", "/missing"):
                        with self.assertRaises(HTTPError) as raised:
                            urlopen(base + path, timeout=5)
                        self.assertEqual(raised.exception.code, 404, path)
                finally:
                    server.shutdown()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
