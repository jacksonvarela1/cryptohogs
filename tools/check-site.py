"""Check publishing guardrails with Python's standard library. Exit 1 on failure."""
import argparse
import json
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = False
        self.footer = []
        self.in_footer = False

    def handle_starttag(self, tag, attrs):
        self.h1 |= tag == 'h1'
        if tag == 'footer':
            self.in_footer = True

    def handle_endtag(self, tag):
        if tag == 'footer':
            self.in_footer = False

    def handle_data(self, data):
        if self.in_footer:
            self.footer.append(data)


def check(root):
    errors = []
    pages = sorted(root.rglob('*.html'))
    pages = [p for p in pages if not any(x.startswith('.') or x in
             ('node_modules', '__pycache__') for x in p.relative_to(root).parts)]
    if not pages:
        errors.append('No HTML pages found')
    for path in pages:
        name = path.relative_to(root).as_posix()
        source = path.read_text(encoding='utf-8-sig')
        parser = Page()
        parser.feed(source)
        for bad in ('\u2014', '839-4755', 'AG10468', 'ANVIL Research', '\x08'):
            if bad.casefold() in unescape(source).casefold():
                errors.append(f'{name}: forbidden text {ascii(bad)}')
        if not parser.h1:
            errors.append(f'{name}: missing h1')
        # Standalone print/social assets and the compact 404 have no site footer.
        exempt = name in ('flyer.html', '404.html', 'assets/social/speaker-card.html')
        footer = ' '.join(' '.join(parser.footer).split()).casefold()
        if not exempt and 'not an official unit of the university' not in footer:
            errors.append(f'{name}: missing footer non-endorsement')
    try:
        rows = json.loads((root / 'assets/schedule.json').read_text(encoding='utf-8-sig'))['rows']
        orgs = {r.get('org', '').strip().casefold() for r in rows} - {''}
        for row in rows:
            for field in ('title', 'short', 'hero'):
                value = row.get(field, '').casefold()
                if any(org in value for org in orgs):
                    errors.append(f"schedule {row.get('date')}: company in {field}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f'schedule unreadable or invalid: {type(exc).__name__}')
    return errors


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = cli.parse_args()
    failures = check(args.root)
    for failure in failures:
        print('FAIL:', failure)
    print(f'{len(failures)} guardrail failures' if failures else 'PASS: site guardrails')
    raise SystemExit(bool(failures))
