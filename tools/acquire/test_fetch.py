import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import archive_digest, looks_right, select  # noqa: E402


class Fetch(unittest.TestCase):
    def test_digest_is_base32_sha1(self):
        self.assertEqual(archive_digest(b''), '3I42H3S6NNFQ2MSVX7XZKYAYSCX5QBYJ')   # SHA-1 of empty input

    def test_looks_right(self):
        self.assertTrue(looks_right('pdf', b'%PDF-1.4 ... %%EOF\n'))
        self.assertFalse(looks_right('pdf', b'%PDF-1.4 truncated mid-stream'))
        self.assertFalse(looks_right('pdf', b'<html>'))
        self.assertFalse(looks_right('txt', b'  <!DOCTYPE html><html>'))
        self.assertTrue(looks_right('txt', b'PREVIEWS JAN VOL 19'))

    def test_select_earliest_per_digest(self):
        base = {'month': 'JAN13', 'kind': 'txt', 'plausible': '1'}
        rows = [dict(base, digest='A', timestamp='2013'), dict(base, digest='A', timestamp='2012'),
                dict(base, digest='B', timestamp='2014'), dict(base, digest='C', timestamp='2011', plausible='0')]
        got = select(rows, {'JAN13'}, {'txt'})
        self.assertEqual(sorted((r['digest'], r['timestamp']) for r in got), [('A', '2012'), ('B', '2014')])


if __name__ == '__main__':
    unittest.main()
