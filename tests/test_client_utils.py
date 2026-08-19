import unittest

from edgar_client import form_matches, pad_cik


class FormMatchTests(unittest.TestCase):
    def test_form4_does_not_match_424(self):
        self.assertTrue(form_matches("4", "4"))
        self.assertTrue(form_matches("4/A", "4"))
        self.assertFalse(form_matches("424B2", "4"))
        self.assertFalse(form_matches("40-F", "4"))

    def test_10k_amendment(self):
        self.assertTrue(form_matches("10-K", "10-K"))
        self.assertTrue(form_matches("10-K/A", "10-K"))
        self.assertFalse(form_matches("10-Q", "10-K"))


class CikTests(unittest.TestCase):
    def test_pad(self):
        self.assertEqual(pad_cik("320193"), "0000320193")
        self.assertEqual(pad_cik("0000320193"), "0000320193")


if __name__ == "__main__":
    unittest.main()
