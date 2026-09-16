"""Regression tests for the publishing guardrails, using isolated fixtures."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('check_site', Path(__file__).with_name('check-site.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Guardrails(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'assets').mkdir()
        self.page = self.root / 'index.html'
        self.good = '<h1>Club</h1><footer>Not an official unit of the university</footer>'
        self.page.write_text(self.good, encoding='utf-8')
        self.schedule = self.root / 'assets/schedule.json'
        self.schedule.write_text(json.dumps({'rows': [{'date': '2026-09-22',
            'title': 'Learning together', 'org': 'Example Labs'}]}), encoding='utf-8')

    def test_valid_site(self):
        self.assertEqual(module.check(self.root), [])

    def test_missing_heading_and_footer(self):
        self.page.write_text('<p>Not an official unit of the university</p>')
        self.assertEqual(len(module.check(self.root)), 2)

    def test_forbidden_text_and_entity_decoding(self):
        self.page.write_text(self.good + '&mdash; AG10468', encoding='utf-8')
        self.assertEqual(len(module.check(self.root)), 2)

    def test_company_in_title(self):
        self.schedule.write_text(json.dumps({'rows': [{'title': 'Visit EXAMPLE LABS',
            'org': 'Example Labs'}]}))
        self.assertTrue(any('company in title' in e for e in module.check(self.root)))

    def test_missing_schedule(self):
        self.schedule.unlink()
        self.assertTrue(any('schedule unreadable' in e for e in module.check(self.root)))

    def test_print_exemption_still_requires_heading(self):
        (self.root / 'flyer.html').write_text('<h1>Print</h1>')
        self.assertEqual(module.check(self.root), [])


if __name__ == '__main__':
    unittest.main()
