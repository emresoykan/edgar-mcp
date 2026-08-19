import unittest

from xbrl_map import (
    _add_balance_check,
    _attach_source_lag,
    collect_periods,
    duration_basis,
    extract_financials,
    pick_fact,
)


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
                            accn="k2024",
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
                        _fact(val=93736000000, start="2023-10-01", frame="CY2024", accn="k2024"),
                        _fact(
                            val=21448000000,
                            fy=2025,
                            fp="Q1",
                            form="10-Q",
                            end="2024-12-28",
                            start="2024-09-29",
                            filed="2025-01-31",
                            frame="CY2025Q1",
                            accn="q12025",
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
                            accn="q12025",
                        ),
                    ]
                }
            },
            "Assets": {
                "units": {
                    "USD": [
                        _fact(val=364980000000, frame="CY2024Q4I", accn="k2024"),
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


class PeriodIntegrityTests(unittest.TestCase):
    def test_comparative_10k_does_not_duplicate_fy(self):
        facts = {
            "cik": 1296445,
            "entityName": "ORMAT TECHNOLOGIES INC",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=879654,
                                    fy=2024,
                                    fp="FY",
                                    end="2024-12-31",
                                    start="2024-01-01",
                                    filed="2025-02-27",
                                    accn="k24",
                                    frame="CY2024",
                                ),
                                _fact(
                                    val=879654,
                                    fy=2025,
                                    fp="FY",
                                    end="2024-12-31",
                                    start="2024-01-01",
                                    filed="2026-02-27",
                                    accn="k25",
                                    frame="CY2024",
                                ),
                                _fact(
                                    val=989543,
                                    fy=2025,
                                    fp="FY",
                                    end="2025-12-31",
                                    start="2025-01-01",
                                    filed="2026-02-27",
                                    accn="k25",
                                    frame="CY2025",
                                ),
                            ]
                        }
                    },
                    "NetIncomeLoss": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=1,
                                    fy=2024,
                                    fp="FY",
                                    end="2024-12-31",
                                    start="2024-01-01",
                                    filed="2025-02-27",
                                    accn="k24",
                                ),
                                _fact(
                                    val=2,
                                    fy=2025,
                                    fp="FY",
                                    end="2025-12-31",
                                    start="2025-01-01",
                                    filed="2026-02-27",
                                    accn="k25",
                                ),
                            ]
                        }
                    },
                    "Assets": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=10,
                                    fy=2024,
                                    fp="FY",
                                    end="2024-12-31",
                                    filed="2025-02-27",
                                    accn="k24",
                                ),
                                _fact(
                                    val=20,
                                    fy=2025,
                                    fp="FY",
                                    end="2025-12-31",
                                    filed="2026-02-27",
                                    accn="k25",
                                ),
                            ]
                        }
                    },
                    "LongTermDebt": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=2344746,
                                    fy=2024,
                                    fp="FY",
                                    end="2024-12-31",
                                    filed="2025-02-27",
                                    accn="k24",
                                ),
                                _fact(
                                    val=2344746,
                                    fy=2025,
                                    fp="FY",
                                    end="2024-12-31",
                                    filed="2026-02-27",
                                    accn="k25",
                                ),
                                _fact(
                                    val=2660570,
                                    fy=2025,
                                    fp="FY",
                                    end="2025-12-31",
                                    filed="2026-02-27",
                                    accn="k25",
                                ),
                            ]
                        }
                    },
                    "CashAndCashEquivalentsAtCarryingValue": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=94395,
                                    fy=2024,
                                    fp="FY",
                                    end="2024-12-31",
                                    filed="2025-02-27",
                                    accn="k24",
                                ),
                                _fact(
                                    val=100000,
                                    fy=2025,
                                    fp="FY",
                                    end="2025-12-31",
                                    filed="2026-02-27",
                                    accn="k25",
                                ),
                            ]
                        }
                    },
                }
            },
        }
        out = extract_financials(facts, annual=4, quarterly=0)
        fy_periods = [p for p in out["periods"] if p["fp"] == "FY"]
        self.assertEqual(len(fy_periods), 2)
        by_end = {p["end"]: p for p in fy_periods}
        self.assertEqual(set(by_end), {"2024-12-31", "2025-12-31"})
        self.assertEqual(by_end["2024-12-31"]["income"]["revenue"]["value"], 879654)
        self.assertNotIn(
            "restated", by_end["2024-12-31"]["income"]["revenue"]
        )
        self.assertEqual(
            by_end["2024-12-31"]["balance"]["long_term_debt_total"]["value"],
            2344746,
        )
        self.assertEqual(by_end["2024-12-31"]["balance"]["cash"]["value"], 94395)
        self.assertEqual(by_end["2025-12-31"]["income"]["revenue"]["value"], 989543)
        self.assertEqual(
            by_end["2025-12-31"]["balance"]["total_debt"]["value"], 2660570
        )
        self.assertNotEqual(
            by_end["2024-12-31"]["balance"]["long_term_debt_total"]["end"],
            "2025-12-31",
        )

    def test_pick_fact_does_not_backfill_other_end(self):
        series = [_fact(val=2660570, fy=2025, fp="FY", end="2025-12-31")]
        chosen = pick_fact(series, 2025, "FY", "10-K", instant=True, end="2024-12-31")
        self.assertIsNone(chosen)

    def test_duration_requires_start_match(self):
        series = [
            _fact(
                val=100,
                fy=2026,
                fp="Q2",
                form="10-Q",
                end="2025-06-30",
                start="2025-01-01",
                filed="2025-08-01",
            )
        ]
        chosen = pick_fact(
            series,
            2026,
            "Q2",
            "10-Q",
            instant=False,
            end="2025-06-30",
            start="2025-04-01",
        )
        self.assertIsNone(chosen)

    def test_sg_and_a_does_not_use_selling_and_marketing(self):
        facts = {
            "cik": 1,
            "entityName": "X",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=10,
                                    start="2024-01-01",
                                    end="2024-12-31",
                                    accn="k",
                                )
                            ]
                        }
                    },
                    "Assets": {
                        "units": {
                            "USD": [_fact(val=1, end="2024-12-31", accn="k")]
                        }
                    },
                    "SellingAndMarketingExpense": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=18898,
                                    start="2024-01-01",
                                    end="2024-12-31",
                                    accn="k",
                                )
                            ]
                        }
                    },
                    "GeneralAndAdministrativeExpense": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=50000,
                                    start="2024-01-01",
                                    end="2024-12-31",
                                    accn="k",
                                )
                            ]
                        }
                    },
                }
            },
        }
        out = extract_financials(facts, annual=1, quarterly=0)
        fy = out["periods"][0]
        self.assertNotIn("sg_and_a", fy["income"])
        self.assertEqual(fy["income"]["selling_and_marketing"]["value"], 18898)
        self.assertEqual(fy["income"]["general_and_administrative"]["value"], 50000)

    def test_tag_changed_on_interest_alias_shift(self):
        facts = {
            "cik": 1,
            "entityName": "X",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=1,
                                    fy=2023,
                                    end="2023-12-31",
                                    start="2023-01-01",
                                    filed="2024-02-01",
                                    accn="k23",
                                ),
                                _fact(
                                    val=2,
                                    fy=2024,
                                    end="2024-12-31",
                                    start="2024-01-01",
                                    filed="2025-02-01",
                                    accn="k24",
                                ),
                            ]
                        }
                    },
                    "Assets": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=1,
                                    fy=2023,
                                    end="2023-12-31",
                                    filed="2024-02-01",
                                    accn="k23",
                                ),
                                _fact(
                                    val=2,
                                    fy=2024,
                                    end="2024-12-31",
                                    filed="2025-02-01",
                                    accn="k24",
                                ),
                            ]
                        }
                    },
                    "InterestExpense": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=10,
                                    fy=2023,
                                    end="2023-12-31",
                                    start="2023-01-01",
                                    filed="2024-02-01",
                                    accn="k23",
                                )
                            ]
                        }
                    },
                    "InterestExpenseNonoperating": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=11,
                                    fy=2024,
                                    end="2024-12-31",
                                    start="2024-01-01",
                                    filed="2025-02-01",
                                    accn="k24",
                                )
                            ]
                        }
                    },
                }
            },
        }
        out = extract_financials(facts, annual=2, quarterly=0)
        by_end = {p["end"]: p for p in out["periods"]}
        self.assertEqual(
            by_end["2023-12-31"]["income"]["interest_expense"]["tag"],
            "InterestExpense",
        )
        later = by_end["2024-12-31"]["income"]["interest_expense"]
        self.assertEqual(later["tag"], "InterestExpenseNonoperating")
        self.assertTrue(later.get("tag_changed"))


class ProductionMappingTests(unittest.TestCase):
    def test_redeemable_nci_closes_balance_sheet(self):
        period = dict(
            fy=2025,
            end="2025-12-31",
            filed="2026-02-26",
            accn="k25",
        )

        def instant(value):
            return _fact(val=value, **period)

        facts = {
            "cik": 1296445,
            "entityName": "ORMAT TECHNOLOGIES INC",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=1,
                                    start="2025-01-01",
                                    **period,
                                )
                            ]
                        }
                    },
                    "Assets": {"units": {"USD": [instant(6246508)]}},
                    "Liabilities": {"units": {"USD": [instant(3555232)]}},
                    "StockholdersEquity": {
                        "units": {"USD": [instant(2543943)]}
                    },
                    "MinorityInterest": {
                        "units": {"USD": [instant(136931)]}
                    },
                    "RedeemableNoncontrollingInterestEquityCarryingAmount": {
                        "units": {"USD": [instant(10402)]}
                    },
                }
            },
        }
        out = extract_financials(facts, annual=1, quarterly=0)
        balance = out["periods"][0]["balance"]
        redeemable = balance["redeemable_noncontrolling_interest"]
        self.assertEqual(redeemable["value"], 10402)
        self.assertEqual(
            redeemable["tag"],
            "RedeemableNoncontrollingInterestEquityCarryingAmount",
        )
        self.assertEqual(balance["balance_check"]["residual"], 0)
        self.assertEqual(balance["balance_check"]["residual_pct_assets"], 0)
        self.assertTrue(balance["balance_check"]["ok"])

    def test_balance_check_lists_missing_components(self):
        balance = {
            "assets": {"value": 100},
            "liabilities": {"value": 60},
            "stockholders_equity": {"value": 40},
        }
        _add_balance_check(balance)
        check = balance["balance_check"]
        self.assertFalse(check["ok"])
        self.assertEqual(check["reason"], "missing_component")
        self.assertEqual(
            check["missing_components"],
            ["minority_interest", "redeemable_noncontrolling_interest"],
        )
        self.assertIsNone(check["residual"])
        self.assertIsNone(check["residual_pct_assets"])

    def test_balance_check_accepts_rounding_residual(self):
        balance = {
            "assets": {"value": 6788245},
            "liabilities": {"value": 4044260},
            "stockholders_equity": {"value": 2597579},
            "minority_interest": {"value": 136501},
            "redeemable_noncontrolling_interest": {"value": 9906},
        }
        _add_balance_check(balance)
        check = balance["balance_check"]
        self.assertEqual(check["residual"], -1)
        self.assertAlmostEqual(check["residual_pct_assets"], -1 / 6788245)
        self.assertEqual(check["tolerance_pct"], 0.001)
        self.assertTrue(check["ok"])

    def test_mixed_source_requires_more_than_200_days(self):
        short_lag = {}
        _attach_source_lag(short_lag, ["2026-05-07", "2026-08-06"])
        self.assertEqual(short_lag["source_lag_days"], 91)
        self.assertNotIn("mixed_source", short_lag)

        long_lag = {}
        _attach_source_lag(long_lag, ["2025-11-05", "2026-08-06"])
        self.assertEqual(long_lag["source_lag_days"], 274)
        self.assertTrue(long_lag["mixed_source"])

    def test_latest_filed_instant_fact_wins_and_is_marked_restated(self):
        facts = {
            "cik": 1296445,
            "entityName": "ORMAT TECHNOLOGIES INC",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=989543,
                                    fy=2025,
                                    end="2025-12-31",
                                    start="2025-01-01",
                                    filed="2026-02-26",
                                    accn="k25",
                                ),
                                _fact(
                                    val=1,
                                    fy=2026,
                                    fp="Q1",
                                    form="10-Q",
                                    end="2025-12-31",
                                    filed="2026-05-07",
                                    accn="q126",
                                ),
                                _fact(
                                    val=1,
                                    fy=2026,
                                    fp="Q2",
                                    form="10-Q",
                                    end="2025-12-31",
                                    filed="2026-08-06",
                                    accn="q226",
                                ),
                            ]
                        }
                    },
                    "Assets": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=1,
                                    fy=2025,
                                    end="2025-12-31",
                                    filed="2026-02-26",
                                    accn="k25",
                                )
                            ]
                        }
                    },
                    "CommonStockSharesOutstanding": {
                        "units": {
                            "shares": [
                                _fact(
                                    val=60500580,
                                    fy=2025,
                                    end="2025-12-31",
                                    filed="2026-02-26",
                                    accn="k25",
                                ),
                                _fact(
                                    val=60845411,
                                    fy=2026,
                                    fp="Q1",
                                    form="10-Q",
                                    end="2025-12-31",
                                    filed="2026-05-07",
                                    accn="q126",
                                ),
                                _fact(
                                    val=60845411,
                                    fy=2026,
                                    fp="Q2",
                                    form="10-Q",
                                    end="2025-12-31",
                                    filed="2026-08-06",
                                    accn="q226",
                                ),
                            ]
                        }
                    },
                }
            },
        }
        out = extract_financials(facts, annual=1, quarterly=0)
        shares = out["periods"][0]["balance"]["shares_outstanding"]
        self.assertEqual(shares["value"], 60845411)
        self.assertEqual(shares["filed"], "2026-08-06")
        self.assertTrue(shares["restated"])
        self.assertEqual(shares["previous_value"], 60500580)
        self.assertEqual(shares["previous_accn"], "k25")
        self.assertTrue(shares["form_mismatch"])
        assets = out["periods"][0]["balance"]["assets"]
        self.assertEqual(assets["form"], "10-K")
        self.assertEqual(assets["accn"], "k25")
        self.assertNotIn("restated", assets)
        self.assertNotIn("form_mismatch", assets)

    def test_ytd_cashflow_is_preserved_and_qtd_is_derived(self):
        q1 = dict(
            fy=2026,
            fp="Q1",
            form="10-Q",
            end="2026-03-31",
            start="2026-01-01",
            filed="2026-05-07",
            accn="q126",
        )
        q2 = dict(
            fy=2026,
            fp="Q2",
            form="10-Q",
            end="2026-06-30",
            start="2026-04-01",
            filed="2026-08-06",
            accn="q226",
        )
        facts = {
            "cik": 1296445,
            "entityName": "ORMAT TECHNOLOGIES INC",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                _fact(val=1, **q1),
                                _fact(val=2, **q2),
                            ]
                        }
                    },
                    "Assets": {
                        "units": {
                            "USD": [
                                _fact(val=1, **{k: v for k, v in q1.items() if k != "start"}),
                                _fact(val=2, **{k: v for k, v in q2.items() if k != "start"}),
                            ]
                        }
                    },
                    "NetCashProvidedByUsedInOperatingActivities": {
                        "units": {
                            "USD": [
                                _fact(val=78579, **q1),
                                _fact(
                                    val=184907,
                                    **{**q2, "start": "2026-01-01"},
                                ),
                            ]
                        }
                    },
                    "PaymentsForRepurchaseOfCommonStock": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=24400,
                                    **{**q1, "filed": "2026-08-06", "accn": "q226"},
                                ),
                                _fact(
                                    val=24395,
                                    **{**q2, "start": "2026-01-01"},
                                ),
                            ]
                        }
                    },
                }
            },
        }
        # Dönüş kotası 1 olsa da türetme için Q1 içeride okunmalı.
        out = extract_financials(facts, annual=0, quarterly=1)
        self.assertEqual(len(out["periods"]), 1)
        by_end = {period["end"]: period for period in out["periods"]}
        q2_cashflow = by_end["2026-06-30"]["cashflow"]
        self.assertEqual(q2_cashflow["cfo_ytd"]["value"], 184907)
        self.assertEqual(q2_cashflow["cfo_ytd"]["basis"], "ytd")
        self.assertFalse(q2_cashflow["cfo_ytd"]["derived"])
        self.assertEqual(q2_cashflow["cfo"]["value"], 106328)
        self.assertEqual(q2_cashflow["cfo"]["basis"], "qtd")
        self.assertTrue(q2_cashflow["cfo"]["derived"])
        self.assertEqual(q2_cashflow["cfo"]["method"], "ytd_diff")
        self.assertEqual(q2_cashflow["cfo"]["start"], "2026-04-01")
        self.assertEqual(q2_cashflow["cfo"]["source_accns"], ["q126", "q226"])
        self.assertEqual(q2_cashflow["cfo"]["source_lag_days"], 91)
        self.assertNotIn("mixed_source", q2_cashflow["cfo"])
        buybacks = q2_cashflow["buybacks"]
        self.assertIsNone(buybacks["value"])
        self.assertEqual(buybacks["raw_derived_value"], -5)
        self.assertTrue(buybacks["sign_anomaly"])
        self.assertNotIn("mixed_source", buybacks)

    def test_total_debt_prefers_total_and_falls_back_to_components(self):
        periods = [
            dict(
                fy=2023,
                end="2023-12-31",
                start="2023-01-01",
                filed="2024-02-01",
                accn="k23",
            ),
            dict(
                fy=2024,
                end="2024-12-31",
                start="2024-01-01",
                filed="2025-02-01",
                accn="k24",
            ),
        ]

        def duration_series(values):
            return [
                _fact(val=value, **period)
                for value, period in zip(values, periods)
            ]

        def instant_series(values):
            return [
                _fact(
                    val=value,
                    **{k: v for k, v in period.items() if k != "start"},
                )
                for value, period in zip(values, periods)
            ]

        facts = {
            "cik": 1,
            "entityName": "X",
            "facts": {
                "us-gaap": {
                    "Revenues": {"units": {"USD": duration_series([1, 2])}},
                    "Assets": {"units": {"USD": instant_series([10, 20])}},
                    "LongTermDebt": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=1000,
                                    **{
                                        k: v
                                        for k, v in periods[1].items()
                                        if k != "start"
                                    },
                                )
                            ]
                        }
                    },
                    "LongTermDebtNoncurrent": {
                        "units": {"USD": instant_series([600, 700])}
                    },
                    "LongTermDebtCurrent": {
                        "units": {"USD": instant_series([100, 110])}
                    },
                    "ShortTermBorrowings": {
                        "units": {"USD": instant_series([50, 60])}
                    },
                    "CommercialPaper": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=40,
                                    **{
                                        k: v
                                        for k, v in periods[0].items()
                                        if k != "start"
                                    },
                                ),
                                _fact(
                                    val=45,
                                    **{
                                        **{
                                            k: v
                                            for k, v in periods[1].items()
                                            if k != "start"
                                        },
                                        "filed": "2025-10-01",
                                        "accn": "k24-later",
                                    },
                                ),
                            ]
                        }
                    },
                }
            },
        }
        out = extract_financials(facts, annual=2, quarterly=0)
        by_end = {period["end"]: period for period in out["periods"]}
        direct = by_end["2024-12-31"]["balance"]
        self.assertNotIn("debt_current", direct)
        self.assertEqual(direct["commercial_paper"]["value"], 45)
        self.assertEqual(direct["total_debt"]["value"], 1105)
        self.assertTrue(direct["total_debt"]["derived"])
        self.assertEqual(
            direct["total_debt"]["components"],
            ["LongTermDebt", "ShortTermBorrowings", "CommercialPaper"],
        )
        self.assertEqual(
            direct["total_debt"]["method"], "long_term_plus_short_term"
        )
        self.assertEqual(direct["total_debt"]["source_lag_days"], 242)
        self.assertTrue(direct["total_debt"]["mixed_source"])

        fallback = by_end["2023-12-31"]["balance"]["total_debt"]
        self.assertEqual(fallback["value"], 790)
        self.assertTrue(fallback["derived"])
        self.assertEqual(fallback["method"], "component_sum")
        self.assertEqual(
            fallback["component_keys"],
            [
                "long_term_debt_noncurrent",
                "long_term_debt_current",
                "short_term_borrowings",
                "commercial_paper",
            ],
        )

    def test_total_debt_is_null_when_only_short_term_component_is_known(self):
        period = dict(
            fy=2026,
            fp="Q2",
            form="10-Q",
            end="2026-06-30",
            filed="2026-08-06",
            accn="q226",
        )
        facts = {
            "cik": 1296445,
            "entityName": "ORMAT TECHNOLOGIES INC",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                _fact(
                                    val=1,
                                    start="2026-04-01",
                                    **period,
                                )
                            ]
                        }
                    },
                    "Assets": {
                        "units": {"USD": [_fact(val=1, **period)]}
                    },
                    "CommercialPaper": {
                        "units": {"USD": [_fact(val=99986, **period)]}
                    },
                }
            },
        }
        out = extract_financials(facts, annual=0, quarterly=1)
        balance = out["periods"][0]["balance"]
        self.assertIsNone(balance["long_term_debt_total"])
        self.assertEqual(balance["commercial_paper"]["value"], 99986)
        self.assertIsNone(balance["total_debt"]["value"])
        self.assertEqual(
            balance["total_debt"]["warning"], "insufficient_components"
        )
        self.assertEqual(balance["total_debt"]["components"], ["CommercialPaper"])


if __name__ == "__main__":
    unittest.main()
