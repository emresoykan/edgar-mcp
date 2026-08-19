import unittest

from xbrl_map import collect_periods, duration_basis, extract_financials, pick_fact


def _fact(**kwargs):
    base = {
        "end": "2024-09-28",
        "val": 1,
        "fy": 2024,
        "fp": "FY",
        "form": "10-K",
        "filed": "2024-11-01",
        "accn": "0001",
    }
    base.update(kwargs)
    return base


FACTS = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {
                    "USD": [
                        _fact(
                            val=391035000000,
                            start="2023-10-01",
                            frame="CY2024",
                        ),
                        _fact(
                            val=999,
                            start="2023-10-01",
                            form="8-K",
                        ),
                    ]
                }
            },
            "NetIncomeLoss": {
                "units": {
                    "USD": [
                        _fact(val=93736000000, start="2023-10-01", frame="CY2024"),
                        _fact(
                            val=21448000000,
                            fy=2025,
                            fp="Q1",
                            form="10-Q",
                            end="2024-12-28",
                            start="2024-09-29",
                            filed="2025-01-31",
                            frame="CY2025Q1",
                        ),
                        _fact(
                            val=60000000000,
                            fy=2025,
                            fp="Q1",
                            form="10-Q",
                            end="2024-12-28",
                            start="2024-09-29",
                            filed="2025-01-31",
                            frame="CY2025Q1-us_gaap_ProductMember",
                        ),
                    ]
                }
            },
            "Assets": {
                "units": {
                    "USD": [
                        _fact(val=364980000000, frame="CY2024Q4I"),
                    ]
                }
            },
        }
    },
}


class PickFactTests(unittest.TestCase):
    def test_prefers_10k_over_8k(self):
        series = [
            _fact(val=1, form="8-K"),
            _fact(val=2, form="10-K"),
        ]
        chosen = pick_fact(series, 2024, "FY", "10-K", instant=False)
        self.assertEqual(chosen["val"], 2)

    def test_prefers_qtd_over_dimensional(self):
        series = [
            _fact(
                val=10,
                fy=2025,
                fp="Q1",
                form="10-Q",
                end="2024-12-28",
                start="2024-09-29",
                frame="CY2025Q1-us_gaap_ProductMember",
            ),
            _fact(
                val=20,
                fy=2025,
                fp="Q1",
                form="10-Q",
                end="2024-12-28",
                start="2024-09-29",
                frame="CY2025Q1",
            ),
        ]
        chosen = pick_fact(series, 2025, "Q1", "10-Q", instant=False)
        self.assertEqual(chosen["val"], 20)

    def test_ytd_flag(self):
        fact = _fact(fp="Q2", start="2024-01-01", end="2024-06-30")
        self.assertEqual(duration_basis(fact, "Q2"), "ytd")
        qtd = _fact(fp="Q2", start="2024-04-01", end="2024-06-30")
        self.assertEqual(duration_basis(qtd, "Q2"), "qtd")


class ExtractTests(unittest.TestCase):
    def test_maps_revenue_and_assets(self):
        out = extract_financials(FACTS, annual=1, quarterly=1)
        self.assertEqual(out["entity"], "Apple Inc.")
        fy = next(p for p in out["periods"] if p["fp"] == "FY")
        self.assertEqual(fy["income"]["revenue"]["value"], 391035000000)
        self.assertEqual(
            fy["income"]["revenue"]["tag"],
            "RevenueFromContractWithCustomerExcludingAssessedTax",
        )
        self.assertEqual(fy["balance"]["assets"]["value"], 364980000000)
        q1 = next(p for p in out["periods"] if p["fp"] == "Q1")
        self.assertEqual(q1["income"]["net_income"]["value"], 21448000000)
        self.assertEqual(q1["income"]["net_income"]["basis"], "qtd")

    def test_collect_skips_8k(self):
        periods = collect_periods(FACTS, annual=4, quarterly=4)
        forms = {p["form"] for p in periods}
        self.assertNotIn("8-K", forms)


if __name__ == "__main__":
    unittest.main()
