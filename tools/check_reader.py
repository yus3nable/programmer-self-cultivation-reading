#!/usr/bin/env python3
"""Check static reading-site links and canonical prev/next order, without network access."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.refs = []
        self.reading = {'prev': [], 'next': []}
        self.missing_alt = 0
        self.h1 = 0
        self.has_base = False
        self.feed(text)

    def handle_starttag(self, tag, pairs):
        a = dict(pairs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'a' and 'name' in a:
            self.ids.add(a['name'])
        self.h1 += tag == 'h1'
        self.has_base |= tag == 'base' and 'href' in a
        for key in ('href', 'src'):
            if a.get(key):
                self.refs.append(a[key])
        if tag == 'img' and 'alt' not in a:
            self.missing_alt += 1
        if tag == 'a':
            for direction in self.reading:
                if (direction in a.get('rel', '').split()
                        or a.get('data-reading') == direction
                        or f'md-footer__link--{direction}' in a.get('class', '').split()):
                    self.reading[direction].append(a.get('href', ''))


def local_target(root, current, ref, prefix):
    url = urlsplit(ref)
    if url.scheme or url.netloc:
        return None, ''
    path = unquote(url.path)
    if path.startswith('/'):
        if not path.startswith(prefix):
            raise ValueError(f'root link outside deployment base: {ref}')
        target = root / path[len(prefix):]
    else:
        target = current.parent / path if path else current
    target = target.resolve()
    if not target.is_relative_to(root):
        raise ValueError(f'link escapes site directory: {ref}')
    if target.is_dir():
        target = (target / 'index.html').resolve()
    return target, unquote(url.fragment)


def check(root, order, base_path='/'):
    root = root.resolve()
    prefix = '/' + base_path.strip('/') + '/' if base_path.strip('/') else '/'
    pages = {p.resolve(): Page(p.read_text(encoding='utf-8')) for p in root.rglob('*.html')}
    errors = []
    if not pages:
        errors.append('No HTML pages found.')
    for path, page in pages.items():
        label = path.relative_to(root).as_posix()
        if page.has_base:
            errors.append(f'{label}: HTML base href requires a separate resolver; not checked as a normal site.')
        if page.missing_alt:
            errors.append(f'{label}: {page.missing_alt} image(s) missing alt attribute.')
        for ref in page.refs:
            try:
                target, fragment = local_target(root, path, ref, prefix)
                if target is None:
                    continue
                if not target.exists():
                    errors.append(f'{label}: missing target {ref}')
                elif fragment and target in pages and fragment not in pages[target].ids:
                    errors.append(f'{label}: missing anchor {ref}')
            except ValueError as exc:
                errors.append(f'{label}: {exc}')
    canonical = []
    if not isinstance(order, dict) or not isinstance(order.get('pages'), list) or not order['pages']:
        errors.append('Reading order must be an object with a nonempty pages list.')
    else:
        for route in order['pages']:
            if not isinstance(route, str) or urlsplit(route).scheme or urlsplit(route).netloc or route.startswith('/') or '#' in route or '?' in route:
                errors.append(f'Invalid canonical HTML path: {route!r}')
                continue
            target = (root / unquote(route)).resolve()
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_relative_to(root) or target not in pages:
                errors.append(f'Canonical page missing or outside site: {route}')
                continue
            canonical.append(target)
        if len(canonical) != len(set(canonical)):
            errors.append('Duplicate canonical reading pages.')
    for i, path in enumerate(canonical):
        label = path.relative_to(root).as_posix()
        if pages[path].h1 != 1:
            errors.append(f'{label}: canonical page must have one h1, found {pages[path].h1}.')
        for direction, offset in [('prev', -1), ('next', 1)]:
            expected = canonical[i + offset] if 0 <= i + offset < len(canonical) else None
            refs = pages[path].reading[direction]
            if len(refs) != (1 if expected else 0):
                errors.append(f'{label}: {direction} link count is {len(refs)}, expected {1 if expected else 0}.')
                continue
            if refs:
                try:
                    actual, _ = local_target(root, path, refs[0], prefix)
                    if not refs[0] or actual != expected:
                        errors.append(f'{label}: {direction} leads outside canonical reading order: {refs[0]}')
                except ValueError as exc:
                    errors.append(f'{label}: {exc}')
    return {'status': 'failed' if errors else 'passed', 'html_pages': len(pages),
            'reading_pages': len(canonical), 'errors': errors,
            'scope': 'Static href/src, HTML anchors, image alt presence, canonical h1 and prev/next paths. Excludes remote URLs, CSS URLs, srcset, JavaScript behavior and content accuracy.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site', type=Path)
    parser.add_argument('--reading-order', required=True, type=Path)
    parser.add_argument('--base-path', default='/')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = check(args.site, json.loads(args.reading_order.read_text(encoding='utf-8')), args.base_path)
    result = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(result, encoding='utf-8')
        summary = {key: report[key] for key in ('status', 'html_pages', 'reading_pages')}
        summary.update(error_count=len(report['errors']), first_errors=report['errors'][:10], report=str(args.report))
        result = json.dumps(summary, ensure_ascii=False, indent=2) + '\n'
    print(result, end='')
    raise SystemExit(bool(report['errors']))


if __name__ == '__main__':
    main()
