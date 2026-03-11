import os
import sys
import unittest

# add project root to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scraper import extract_price


class ExtractPriceTest(unittest.TestCase):
    def test_simple_dollar_price(self):
        self.assertEqual(extract_price("$29.99"), 29.99)

    def test_euro_comma_price(self):
        self.assertEqual(extract_price("29,99 €"), 29.99)

    def test_thousands_dot_decimal_comma(self):
        self.assertEqual(extract_price("1.299,99 €"), 1299.99)

    def test_thousands_comma_decimal_dot(self):
        self.assertEqual(extract_price("1,299.99"), 1299.99)

    def test_invalid_text_returns_none(self):
        self.assertIsNone(extract_price("no price here"))

    def test_none_input_returns_none(self):
        self.assertIsNone(extract_price(None))


if __name__ == "__main__":
    unittest.main()

