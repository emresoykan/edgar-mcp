import json
import unittest
from unittest.mock import patch

from edgar_client import EdgarHTTPError
from server import get_concept


class ConceptErrorTests(unittest.TestCase):
    def test_get_concept_returns_structured_404(self):
        url = (
            "https://data.sec.gov/api/xbrl/companyconcept/"
            "CIK0001296445/us-gaap/LongTermDebtCurrent.json"
        )

        class FakeClient:
            def resolve(self, _query):
                return {"cik": "0001296445", "ticker": "ORA"}

            def get_companyconcept(self, _cik, _taxonomy, _tag):
                raise EdgarHTTPError(404, "not found", url)

        with patch("server.client", return_value=FakeClient()):
            payload = json.loads(
                get_concept("ORA", "LongTermDebtCurrent", "us-gaap")
            )

        self.assertEqual(
            payload,
            {
                "error": {
                    "status": 404,
                    "message": "concept not found",
                    "url": url,
                    "taxonomy": "us-gaap",
                    "tag": "LongTermDebtCurrent",
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
