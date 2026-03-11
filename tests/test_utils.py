import os
import sys
import unittest

# add project root to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import check_password, generate_otp, hash_password, is_price_drop


class UtilsTest(unittest.TestCase):
    def test_hash_and_check(self):
        pwd = "secret123"
        h = hash_password(pwd)
        self.assertTrue(check_password(pwd, h))
        self.assertFalse(check_password("wrong", h))

    def test_generate_otp_length(self):
        otp = generate_otp()
        self.assertTrue(otp.isdigit())
        self.assertEqual(len(otp), 4)

    def test_is_price_drop_equal_values_do_not_drop(self):
        # Same numeric value with different formatting should not trigger a drop
        self.assertFalse(is_price_drop(29.90, 29.9))
        self.assertFalse(is_price_drop("29.90", "29.9"))

    def test_is_price_drop_real_decrease(self):
        self.assertTrue(is_price_drop(30, 29.99))
        self.assertTrue(is_price_drop("30.00", "29.99"))


if __name__ == "__main__":
    unittest.main()
