"""Small static development server that never exposes checkout internals."""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

BLOCKED_PARTS = {"__pycache__", "node_modules", "_site", "build", "dist"}
BLOCKED_SUFFIXES = {".py", ".pyc", ".pyo", ".toml", ".yaml", ".yml", ".sh", ".log", ".zip", ".db", ".sqlite"}


class PublicFilesHandler(SimpleHTTPRequestHandler):
    """Serve public files, not dotfiles, source code, credentials or listings."""

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        parts = [unquote(part) for part in path.split("/") if part]
        if any(part.startswith(".") or part in BLOCKED_PARTS or part.endswith(".egg-info") for part in parts):
            self.send_error(404, "File not found")
            return None
        if Path(path).suffix.lower() in BLOCKED_SUFFIXES:
            self.send_error(404, "File not found")
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404, "Directory listing is disabled")
        return None


def serve(root: Path, host: str, port: int, name: str) -> None:
    root = root.resolve()
    if not (root / "index.html").is_file():
        raise ValueError("serve requires a repository checkout with index.html")
    handler = partial(PublicFilesHandler, directory=str(root))
    with ThreadingHTTPServer((host, port), handler) as server:
        display_host = "127.0.0.1" if host == "0.0.0.0" else host
        print(f"{name}: http://{display_host}:{server.server_port} — listening on {host}; Ctrl+C to stop", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.", flush=True)
