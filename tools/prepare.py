#!/usr/bin/env python3
"""Recreate cached scan images and local Apple Vision OCR for this PDF edition."""
import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('pdf', type=Path)
parser.add_argument('--jobs', type=int, choices=(1, 2), default=2)
args = parser.parse_args()
inventory = json.loads((ROOT / 'maintenance/pdf-inventory.json').read_text())
if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != inventory['sha256']:
    raise SystemExit('PDF differs from this edition. Page mapping must be reviewed before conversion.')
scans, ocr = ROOT / 'tmp/scans', ROOT / 'tmp/ocr'
scans.mkdir(parents=True, exist_ok=True)
ocr.mkdir(parents=True, exist_ok=True)
with fitz.open(args.pdf) as doc:
    (ROOT / 'tmp/toc.json').write_text(json.dumps(doc.get_toc(), ensure_ascii=False))
    count = len(doc)
    for number, page in enumerate(doc, 1):
        out = scans / f'p{number:04d}.png'
        if out.exists():
            continue
        images = page.get_images(full=True)
        if len(images) != 1:
            raise SystemExit(f'Unexpected raster layout on page {number}')
        image = fitz.Pixmap(doc, images[0][0])
        if image.n - image.alpha > 3:
            image = fitz.Pixmap(fitz.csRGB, image)
        image.save(out)
binary = ROOT / 'tmp/recognize'
subprocess.run(['swiftc', '-O', str(ROOT / 'tools/recognize.swift'), '-o', str(binary)], check=True)
def recognize(span):
    subprocess.run([str(binary), str(scans), str(ocr), str(span[0]), str(span[1])], check=True)
spans = [(1, count)] if args.jobs == 1 else [(1, count // 2), (count // 2 + 1, count)]
with ThreadPoolExecutor(max_workers=args.jobs) as pool:
    list(pool.map(recognize, spans))
print('OCR cache ready. Existing Markdown has not been changed.')
