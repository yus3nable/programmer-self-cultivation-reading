#!/usr/bin/env python3
"""Serve the built reader on this computer only."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8766)
args = parser.parse_args()
site = root / 'website/build/site'
if not (site / 'index.html').exists():
    raise SystemExit('Build first: python website/build.py')
server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(site)))
print(f'Local reader: http://127.0.0.1:{args.port}/', flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
