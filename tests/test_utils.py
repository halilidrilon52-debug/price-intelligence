import os
import sys
import unittest

# add project root to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import hash_password, check_password, generate_otp


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


if __name__ == "__main__":
    unittest.main()
