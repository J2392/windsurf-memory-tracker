import unittest
from ultis import format_time, slugify, validate_email
from datetime import datetime

class TestUtils(unittest.TestCase):
    def test_format_time(self):
        dt = datetime(2025, 4, 20, 22, 0, 0)
        self.assertEqual(format_time(dt), '2025-04-20 22:00:00')

    def test_slugify(self):
        self.assertEqual(slugify('Hello World!'), 'hello-world')
        self.assertEqual(slugify('Python_123'), 'python-123')

    def test_validate_email(self):
        self.assertTrue(validate_email('a@b.com'))
        self.assertFalse(validate_email('a@b'))
        self.assertFalse(validate_email('abc.com'))

if __name__ == "__main__":
    unittest.main()
