#!/usr/bin/env python3
"""Serve the saved benchmark explorer locally, without rebuilding its data."""

import argparse
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


def port_number(value):
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


class ExplorerHandler(SimpleHTTPRequestHandler):
    def route(self):
        path = urlsplit(self.path).path
        if path in ("/", "/benchmarks"):
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/benchmarks/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return False
        if not path.startswith("/benchmarks/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return False
        return True

    def translate_path(self, path):
        return super().translate_path(path[len("/benchmarks"):])

    def do_GET(self):
        if self.route():
            super().do_GET()

    def do_HEAD(self):
        if self.route():
            super().do_HEAD()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=port_number, default=8766)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    dist = repo / "benchmarks/clbg/overview/explorer/dist"
    if not all((dist / name).is_file() for name in ("index.html", "data.json")):
        parser.error(f"saved explorer is missing from {dist}")
    handler = partial(ExplorerHandler, directory=str(dist))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Saved chart: http://127.0.0.1:{args.port}/benchmarks/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
