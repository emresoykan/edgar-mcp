import unittest
from unittest.mock import Mock, patch

import httpx

from edgar_client import EdgarClient, EdgarHTTPError, form_matches, pad_cik


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


class HttpErrorTests(unittest.TestCase):
    def setUp(self):
        self.client = EdgarClient("Test User test@example.com")
        self.client.http.close()
        self.client.http = Mock()
        self.client.rate.wait_if_needed = Mock()
        self.url = "https://data.sec.gov/test"

    def _response(self, status, text="", headers=None):
        return httpx.Response(
            status,
            text=text,
            headers=headers,
            request=httpx.Request("GET", self.url),
        )

    def test_404_is_not_retried(self):
        self.client.http.get.return_value = self._response(404)
        with self.assertRaises(EdgarHTTPError) as caught:
            self.client._get(self.url)
        self.assertEqual(caught.exception.status, 404)
        self.assertEqual(caught.exception.url, self.url)
        self.client.http.get.assert_called_once_with(self.url)

    @patch("edgar_client.time.sleep")
    def test_429_retries_with_exponential_backoff(self, sleep):
        self.client.http.get.return_value = self._response(429)
        with self.assertRaises(EdgarHTTPError) as caught:
            self.client._get(self.url)
        self.assertEqual(caught.exception.status, 429)
        self.assertEqual(caught.exception.message, "rate limit exceeded")
        self.assertEqual(self.client.http.get.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.5, 1.0])

    @patch("edgar_client.time.sleep")
    def test_5xx_retries_with_exponential_backoff(self, sleep):
        self.client.http.get.return_value = self._response(503, "upstream unavailable")
        with self.assertRaises(EdgarHTTPError) as caught:
            self.client._get(self.url)
        self.assertEqual(caught.exception.status, 503)
        self.assertEqual(caught.exception.message, "upstream unavailable")
        self.assertEqual(self.client.http.get.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.5, 1.0])


if __name__ == "__main__":
    unittest.main()
