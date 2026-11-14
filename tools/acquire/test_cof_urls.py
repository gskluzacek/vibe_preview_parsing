import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cof_urls import classify, months_between, CofUrl  # noqa: E402


class Classify(unittest.TestCase):
    def test_era1(self):
        self.assertEqual(classify('http://www.previewsworld.com/support/previews_docs/orderforms/MAR13_COF.txt'),
                         CofUrl('MAR13', 'txt', 1))

    def test_era2_year_folder(self):
        self.assertEqual(classify('http://www.previewsworld.com/support/previews_docs/orderforms/archive/2013/JAN13_COF.pdf'),
                         CofUrl('JAN13', 'pdf', 2))

    def test_era2_2009_month_folder(self):
        self.assertEqual(classify('http://www.previewsworld.com/support/previews_docs/orderforms/archive/2009/JAN09/JAN09_COF.txt'),
                         CofUrl('JAN09', 'txt', 2))

    def test_era3_and_case_and_host(self):
        self.assertEqual(classify('https://www.previewsworld.com/Catalog/CustomerOrderForm/TXT/jul23'), CofUrl('JUL23', 'txt', 3))
        self.assertEqual(classify('https://previewsworld.com/Catalog/CustomerOrderForm/PDF/JAN18?x=1'), CofUrl('JAN18', 'pdf', 3))

    def test_rejects(self):
        for u in ['http://www.previewsworld.com/support/previews_docs/orderforms/archive/2009/APR09/',
                  'https://www.previewsworld.com/Catalog/CustomerOrderForm/PDF/%CE%9C%CE%91%CE%A521',
                  'https://www.previewsworld.com/Catalog/CustomerOrderForm/TXT/',
                  'https://example.com/MAR13_COF.txt',
                  'https://previewsworld.com/Catalog/CustomerOrderForm/TXT/XXX13']:
            self.assertIsNone(classify(u), u)


class Months(unittest.TestCase):
    def test_range(self):
        self.assertEqual(months_between('NOV09', 'FEB10'), ['NOV09', 'DEC09', 'JAN10', 'FEB10'])
        self.assertEqual(len(months_between('JAN09', 'DEC25')), 204)


if __name__ == '__main__':
    unittest.main()
