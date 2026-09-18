"""Recaps must not invent attendance or publish before a meeting finishes."""
import datetime as dt
import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('schedule_builder', pathlib.Path(__file__).with_name('build-schedule.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

class Recaps(unittest.TestCase):
    def row(self, **changes):
        r = {'_date': dt.date(2026, 9, 22), 'status': 'done', 'title': 'A real talk', 'recap': 'Officer supplied notes.'}
        r.update(changes)
        return r

    def test_past_completed(self):
        self.assertIn('Officer supplied notes.', '\n'.join(B.recap_region([self.row()], dt.date(2026, 9, 23))))

    def test_future_today_and_unfinished_hidden(self):
        for day in [dt.date(2026, 9, 21), dt.date(2026, 9, 22)]:
            self.assertEqual(B.recap_region([self.row()], day), [])
        self.assertEqual(B.recap_region([self.row(status='confirmed')], dt.date(2026, 9, 23)), [])

    def test_optional_and_escaped(self):
        self.assertEqual(B.recap_region([self.row(recap=None)], dt.date(2026, 9, 23)), [])
        html = '\n'.join(B.recap_region([self.row(title='<script>', recap='<img onerror=x> & notes')], dt.date(2026, 9, 23)))
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img', html)
        self.assertIn('&amp; notes', html)

    def test_latest_first(self):
        html = '\n'.join(B.recap_region([self.row(title='Older'), self.row(title='Newer', _date=dt.date(2026, 9, 23))], dt.date(2026, 9, 24)))
        self.assertLess(html.index('Newer'), html.index('Older'))

if __name__ == '__main__':
    unittest.main()
