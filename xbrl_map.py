"""us-gaap / ifrs-full / dei kavramlarını standart tablo satırlarına eşler.

SEC companyfacts ham tag yığınıdır. Aynı kalem şirketler arasında farklı
tag'lerle gelir; asıl iş bu alias listesi ve dönem seçimi.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

_CLEAN_FRAME = re.compile(r"CY\d{4}(?:Q[1-4])?I?")


# Her satır: (taxonomy, tag). İlk bulunan, dönemle uyuşan değer kazanır.
INCOME_DURATION: dict[str, list[tuple[str, str]]] = {
    "revenue": [
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
        ("us-gaap", "Revenues"),
        ("us-gaap", "SalesRevenueNet"),
        ("us-gaap", "SalesRevenueGoodsNet"),
        ("us-gaap", "SalesRevenueServicesNet"),
        ("ifrs-full", "Revenue"),
        ("ifrs-full", "RevenueFromContractsWithCustomers"),
    ],
    "cost_of_revenue": [
        ("us-gaap", "CostOfRevenue"),
        ("us-gaap", "CostOfGoodsAndServicesSold"),
        ("us-gaap", "CostOfGoodsSold"),
        ("us-gaap", "CostOfSales"),
        ("ifrs-full", "CostOfSales"),
    ],
    "gross_profit": [
        ("us-gaap", "GrossProfit"),
        ("ifrs-full", "GrossProfit"),
    ],
    "operating_income": [
        ("us-gaap", "OperatingIncomeLoss"),
        ("ifrs-full", "ProfitLossFromOperatingActivities"),
    ],
    "net_income": [
        ("us-gaap", "NetIncomeLoss"),
        ("us-gaap", "ProfitLoss"),
        ("us-gaap", "NetIncomeLossAvailableToCommonStockholdersBasic"),
        ("ifrs-full", "ProfitLoss"),
        ("ifrs-full", "ProfitLossAttributableToOwnersOfParent"),
    ],
    "eps_basic": [
        ("us-gaap", "EarningsPerShareBasic"),
        ("ifrs-full", "BasicEarningsLossPerShare"),
    ],
    "eps_diluted": [
        ("us-gaap", "EarningsPerShareDiluted"),
        ("ifrs-full", "DilutedEarningsLossPerShare"),
    ],
    "research_and_development": [
        ("us-gaap", "ResearchAndDevelopmentExpense"),
    ],
    "sg_and_a": [
        ("us-gaap", "SellingGeneralAndAdministrativeExpense"),
        ("us-gaap", "SellingAndMarketingExpense"),
    ],
    "interest_expense": [
        ("us-gaap", "InterestExpense"),
        ("us-gaap", "InterestExpenseNonoperating"),
        ("ifrs-full", "InterestExpense"),
    ],
    "income_tax": [
        ("us-gaap", "IncomeTaxExpenseBenefit"),
        ("ifrs-full", "IncomeTaxExpenseContinuingOperations"),
    ],
    "shares_basic": [
        ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic"),
        ("ifrs-full", "WeightedAverageShares"),
    ],
    "shares_diluted": [
        ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
        ("ifrs-full", "WeightedAverageSharesDiluted"),
    ],
}

BALANCE_INSTANT: dict[str, list[tuple[str, str]]] = {
    "assets": [
        ("us-gaap", "Assets"),
        ("ifrs-full", "Assets"),
    ],
    "assets_current": [
        ("us-gaap", "AssetsCurrent"),
        ("ifrs-full", "CurrentAssets"),
    ],
    "cash": [
        ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
        ("us-gaap", "Cash"),
        ("ifrs-full", "CashAndCashEquivalents"),
    ],
    "inventory": [
        ("us-gaap", "InventoryNet"),
        ("us-gaap", "InventoryFinishedGoodsNetOfReserves"),
        ("ifrs-full", "Inventories"),
    ],
    "receivables": [
        ("us-gaap", "AccountsReceivableNetCurrent"),
        ("us-gaap", "AccountsReceivableNet"),
        ("ifrs-full", "TradeAndOtherCurrentReceivables"),
    ],
    "liabilities": [
        ("us-gaap", "Liabilities"),
        ("ifrs-full", "Liabilities"),
    ],
    "liabilities_current": [
        ("us-gaap", "LiabilitiesCurrent"),
        ("ifrs-full", "CurrentLiabilities"),
    ],
    "long_term_debt": [
        ("us-gaap", "LongTermDebt"),
        ("us-gaap", "LongTermDebtNoncurrent"),
        ("us-gaap", "LongTermDebtAndCapitalLeaseObligations"),
        ("ifrs-full", "NoncurrentPortionOfNoncurrentLoansReceived"),
        ("ifrs-full", "LongtermBorrowings"),
    ],
    "stockholders_equity": [
        ("us-gaap", "StockholdersEquity"),
        ("us-gaap", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
        ("ifrs-full", "Equity"),
        ("ifrs-full", "EquityAttributableToOwnersOfParent"),
    ],
    "retained_earnings": [
        ("us-gaap", "RetainedEarningsAccumulatedDeficit"),
        ("ifrs-full", "RetainedEarnings"),
    ],
    "shares_outstanding": [
        ("dei", "EntityCommonStockSharesOutstanding"),
        ("us-gaap", "CommonStockSharesOutstanding"),
        ("us-gaap", "CommonStockSharesIssued"),
    ],
}

CASHFLOW_DURATION: dict[str, list[tuple[str, str]]] = {
    "cfo": [
        ("us-gaap", "NetCashProvidedByUsedInOperatingActivities"),
        ("ifrs-full", "CashFlowsFromUsedInOperatingActivities"),
    ],
    "cfi": [
        ("us-gaap", "NetCashProvidedByUsedInInvestingActivities"),
        ("ifrs-full", "CashFlowsFromUsedInInvestingActivities"),
    ],
    "cff": [
        ("us-gaap", "NetCashProvidedByUsedInFinancingActivities"),
        ("ifrs-full", "CashFlowsFromUsedInFinancingActivities"),
    ],
    "capex": [
        ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
        ("ifrs-full", "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"),
    ],
    "depreciation": [
        ("us-gaap", "DepreciationDepletionAndAmortization"),
        ("us-gaap", "Depreciation"),
        ("ifrs-full", "DepreciationAndAmortisationExpense"),
    ],
    "dividends": [
        ("us-gaap", "PaymentsOfDividends"),
        ("us-gaap", "PaymentsOfOrdinaryDividends"),
        ("ifrs-full", "DividendsPaid"),
    ],
    "buybacks": [
        ("us-gaap", "PaymentsForRepurchaseOfCommonStock"),
        ("ifrs-full", "PurchaseOfTreasuryShares"),
    ],
}

STATEMENT_FORMS = {
    "10-K",
    "10-K/A",
    "10-Q",
    "10-Q/A",
    "20-F",
    "20-F/A",
    "40-F",
    "40-F/A",
}

_PREFERRED_UNITS = ("USD", "USD/shares", "shares", "pure", "ISO4217:USD")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _duration_days(fact: dict[str, Any]) -> int | None:
    start = _parse_date(fact.get("start"))
    end = _parse_date(fact.get("end"))
    if not start or not end:
        return None
    return (end - start).days


def duration_basis(fact: dict[str, Any], fp: str) -> str:
    """qtd / ytd / annual / unknown — 10-Q gelir kalemleri çoğu zaman YTD gelir."""
    days = _duration_days(fact)
    if days is None:
        frame = str(fact.get("frame") or "")
        if fp == "FY":
            return "annual"
        if frame.endswith("Q1") or frame.endswith("Q2") or frame.endswith("Q3") or frame.endswith("Q4"):
            return "qtd"
        return "unknown"
    if fp == "FY":
        return "annual" if days >= 300 else "other"
    if days <= 100:
        return "qtd"
    return "ytd"


def _frame_dimensional(frame: str) -> bool:
    """Segment/member boyutlu frame. Örn. CY2024Q4I-us_gaap_ProductMember."""
    if not frame:
        return False
    return _CLEAN_FRAME.fullmatch(frame) is None


def _concept(facts: dict[str, Any], taxonomy: str, tag: str) -> dict[str, Any] | None:
    block = (facts.get("facts") or {}).get(taxonomy) or {}
    return block.get(tag)


def _unit_series(concept: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    units = concept.get("units") or {}
    for unit in _PREFERRED_UNITS:
        if unit in units:
            return unit, units[unit]
    if units:
        unit = next(iter(units))
        return unit, units[unit]
    return "", []


def _score_fact(fact: dict[str, Any], fy: int, fp: str, form: str, instant: bool) -> tuple:
    """Yüksek skor kazanır. tuple karşılaştırması ile sıralanır."""
    form_ok = 1 if fact.get("form") == form else 0
    fy_ok = 1 if fact.get("fy") == fy else 0
    fp_ok = 1 if fact.get("fp") == fp else 0
    dimensional = 1 if _frame_dimensional(str(fact.get("frame") or "")) else 0
    amendment = 1 if str(fact.get("form") or "").endswith("/A") else 0
    basis_rank = 0
    if not instant:
        basis = duration_basis(fact, fp)
        if fp == "FY" and basis == "annual":
            basis_rank = 2
        elif fp != "FY" and basis == "qtd":
            basis_rank = 2
        elif fp != "FY" and basis == "ytd":
            basis_rank = 1
    filed = str(fact.get("filed") or "")
    return (fy_ok, fp_ok, form_ok, basis_rank, 0 if dimensional else 1, amendment, filed)


def pick_fact(
    series: list[dict[str, Any]],
    fy: int,
    fp: str,
    form: str,
    *,
    instant: bool,
    end: str | None = None,
) -> dict[str, Any] | None:
    candidates = [
        f
        for f in series
        if f.get("fy") == fy and f.get("fp") == fp and f.get("form") in STATEMENT_FORMS
    ]
    if end:
        ended = [f for f in candidates if f.get("end") == end]
        if ended:
            candidates = ended
    if not candidates:
        return None
    candidates.sort(key=lambda f: _score_fact(f, fy, fp, form, instant), reverse=True)
    return candidates[0]


def _line_item(
    facts: dict[str, Any],
    aliases: list[tuple[str, str]],
    fy: int,
    fp: str,
    form: str,
    *,
    instant: bool,
    end: str | None,
) -> dict[str, Any] | None:
    for taxonomy, tag in aliases:
        concept = _concept(facts, taxonomy, tag)
        if not concept:
            continue
        unit, series = _unit_series(concept)
        chosen = pick_fact(series, fy, fp, form, instant=instant, end=end)
        if chosen is None or chosen.get("val") is None:
            continue
        item: dict[str, Any] = {
            "value": chosen["val"],
            "unit": unit,
            "tag": tag,
            "taxonomy": taxonomy,
            "end": chosen.get("end"),
            "filed": chosen.get("filed"),
            "accn": chosen.get("accn"),
            "form": chosen.get("form"),
        }
        if not instant:
            item["start"] = chosen.get("start")
            item["basis"] = duration_basis(chosen, fp)
        return item
    return None


def _fill_statement(
    facts: dict[str, Any],
    mapping: dict[str, list[tuple[str, str]]],
    fy: int,
    fp: str,
    form: str,
    *,
    instant: bool,
    end: str | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, aliases in mapping.items():
        item = _line_item(facts, aliases, fy, fp, form, instant=instant, end=end)
        if item is not None:
            out[key] = item
    return out


def _period_key(fact: dict[str, Any]) -> tuple | None:
    fy, fp, form, end = fact.get("fy"), fact.get("fp"), fact.get("form"), fact.get("end")
    if fy is None or not fp or form not in STATEMENT_FORMS or not end:
        return None
    return (int(fy), str(fp), str(form), str(end), str(fact.get("filed") or ""))


def collect_periods(
    facts: dict[str, Any],
    *,
    annual: int = 4,
    quarterly: int = 4,
) -> list[dict[str, Any]]:
    """Gelir ve bilanço tag'lerinden 10-K / 10-Q dönemlerini toplar."""
    scan_aliases = (
        INCOME_DURATION["net_income"]
        + INCOME_DURATION["revenue"]
        + BALANCE_INSTANT["assets"]
    )
    seen: dict[tuple, dict[str, Any]] = {}
    for taxonomy, tag in scan_aliases:
        concept = _concept(facts, taxonomy, tag)
        if not concept:
            continue
        _, series = _unit_series(concept)
        for fact in series:
            key = _period_key(fact)
            if key is None:
                continue
            fy, fp, form, end, filed = key
            slot = (fy, fp, end)
            prev = seen.get(slot)
            row = {
                "fy": fy,
                "fp": fp,
                "form": form,
                "end": end,
                "filed": filed,
                "start": fact.get("start"),
            }
            if prev is None or filed >= prev.get("filed", ""):
                # 10-K/A, 10-Q/A son filed ile kazansın
                seen[slot] = row

    annual_rows = [p for p in seen.values() if p["fp"] == "FY"]
    quarter_rows = [p for p in seen.values() if p["fp"] in {"Q1", "Q2", "Q3", "Q4"}]
    annual_rows.sort(key=lambda p: p["end"], reverse=True)
    quarter_rows.sort(key=lambda p: p["end"], reverse=True)
    # Aynı yıl için hem FY hem Q4 varsa ikisini de bırak — farklı formlar
    return annual_rows[:annual] + quarter_rows[:quarterly]


def extract_financials(
    facts: dict[str, Any],
    *,
    annual: int = 4,
    quarterly: int = 4,
) -> dict[str, Any]:
    periods = collect_periods(facts, annual=annual, quarterly=quarterly)
    statements = []
    for period in periods:
        fy, fp, form, end = period["fy"], period["fp"], period["form"], period["end"]
        income = _fill_statement(
            facts, INCOME_DURATION, fy, fp, form, instant=False, end=end
        )
        cashflow = _fill_statement(
            facts, CASHFLOW_DURATION, fy, fp, form, instant=False, end=end
        )
        balance = _fill_statement(
            facts, BALANCE_INSTANT, fy, fp, form, instant=True, end=end
        )
        statements.append(
            {
                **period,
                "income": income,
                "balance": balance,
                "cashflow": cashflow,
            }
        )
    statements.sort(key=lambda p: p["end"], reverse=True)
    return {
        "cik": facts.get("cik"),
        "entity": facts.get("entityName"),
        "periods": statements,
    }
