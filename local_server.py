#!/usr/bin/env python3
"""Serve a static clone while mapping extensionless SPA routes to .html files."""

import argparse
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SPARequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        translated = Path(super().translate_path(path))
        if translated.exists():
            return str(translated)
        html_path = translated.with_name(translated.name + ".html")
        if html_path.is_file():
            return str(html_path)
        return str(translated)

    def guess_type(self, path):
        if Path(path).suffix == "" and Path(path + ".html").is_file():
            return "text/html"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"


def main():
    parser = argparse.ArgumentParser(description="Serve a cloned SPA locally")
    parser.add_argument("directory", nargs="?", default="cloned_site")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    handler = lambda *handler_args: SPARequestHandler(*handler_args, directory=str(directory))
    server = ThreadingHTTPServer(("localhost", args.port), handler)
    print(f"Serving {directory} at http://localhost:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
