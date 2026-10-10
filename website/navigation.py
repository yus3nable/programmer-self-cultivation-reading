"""Use one canonical body sequence, independent of guides and chapter copies."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def on_nav(nav, config, files):
    order=json.loads((ROOT/'maintenance/reading-order.json').read_text())['chapters']
    pages=[files.get_file_from_path(f"{c['directory']}/{s['path']}").page for c in order for s in c['sections']]
    for page in nav.pages:
        page.previous_page=page.next_page=None
    for i,page in enumerate(pages):
        page.previous_page=pages[i-1] if i else None
        page.next_page=pages[i+1] if i+1<len(pages) else None
    return nav
