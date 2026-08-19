"""us-gaap / ifrs-full / dei kavramlarını standart tablo satırlarına eşler.

SEC companyfacts ham tag yığınıdır. Aynı kalem şirketler arasında farklı
tag'lerle gelir; asıl iş bu alias listesi ve dönem seçimi.

Dönem anahtarı filing `fy`/`fp` değil, fact `start`/`end` (cari accession'ın
max `end`'i). Comparative satırlar ayrı dönem gibi listelenmez. Tarih
uymayan fact bloğa doldurulmaz.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
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
        ("ifrs-full", "SellingGeneralAndAdministrativeExpense"),
    ],
    "selling_and_marketing": [
        ("us-gaap", "SellingAndMarketingExpense"),
        ("ifrs-full", "SellingAndMarketingExpense"),
    ],
    "general_and_administrative": [
        ("us-gaap", "GeneralAndAdministrativeExpense"),
        ("ifrs-full", "AdministrativeExpense"),
        ("ifrs-full", "GeneralAndAdministrativeExpense"),
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
    "long_term_debt_total": [
        ("us-gaap", "LongTermDebt"),
    ],
    "long_term_debt_noncurrent": [
        ("us-gaap", "LongTermDebtNoncurrent"),
        ("us-gaap", "LongTermDebtAndCapitalLeaseObligations"),
        ("ifrs-full", "NoncurrentPortionOfNoncurrentLoansReceived"),
        ("ifrs-full", "LongtermBorrowings"),
    ],
    "long_term_debt_current": [
        ("us-gaap", "LongTermDebtCurrent"),
        ("ifrs-full", "CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings"),
        ("ifrs-full", "CurrentPortionOfLongtermBorrowings"),
    ],
    "short_term_borrowings": [
        ("us-gaap", "ShortTermBorrowings"),
        ("ifrs-full", "ShorttermBorrowings"),
    ],
    "commercial_paper": [
        ("us-gaap", "CommercialPaper"),
    ],
    "minority_interest": [
        ("us-gaap", "MinorityInterest"),
        ("us-gaap", "NoncontrollingInterest"),
        ("us-gaap", "EquityAttributableToNoncontrollingInterest"),
        ("ifrs-full", "NoncontrollingInterests"),
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
        ("us-gaap", "PaymentsOfDividendsCommonStock"),
        ("us-gaap", "PaymentsOfDividendsCommonStockCash"),
        ("ifrs-full", "DividendsPaid"),
        ("ifrs-full", "DividendsPaidToOwnersOfParent"),
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


def _form_kind(form: str | None) -> str | None:
    """annual | quarter — 10-K/A ve 10-Q/A aynı aile."""
    if not form:
        return None
    base = str(form).upper().split("/")[0]
    if base in {"10-K", "20-F", "40-F"}:
        return "annual"
    if base == "10-Q":
        return "quarter"
    return None


def _score_fact(
    fact: dict[str, Any],
    fy: int | None,
    fp: str | None,
    form: str | None,
    instant: bool,
) -> tuple:
    """Tarih eşleşmesinden sonra en yeni filing kazanır."""
    form_kind = _form_kind(form)
    fact_kind = _form_kind(str(fact.get("form") or ""))
    form_ok = 1 if form_kind and fact_kind == form_kind else 0
    fy_ok = 1 if fy is not None and fact.get("fy") == fy else 0
    fp_ok = 1 if fp and fact.get("fp") == fp else 0
    amendment = 1 if str(fact.get("form") or "").endswith("/A") else 0
    filed = str(fact.get("filed") or "")
    accn = str(fact.get("accn") or "")
    return (filed, amendment, form_ok, fy_ok, fp_ok, accn)


def pick_fact(
    series: list[dict[str, Any]],
    fy: int | None,
    fp: str | None,
    form: str | None,
    *,
    instant: bool,
    end: str | None = None,
    start: str | None = None,
    basis: str | None = None,
) -> dict[str, Any] | None:
    """Ekonomik tarih eşleşir; aynı tarih için en yeni `filed` kazanır."""
    candidates = [f for f in series if f.get("form") in STATEMENT_FORMS]
    if end:
        candidates = [f for f in candidates if f.get("end") == end]
    elif instant:
        return None
    if not instant and start:
        candidates = [f for f in candidates if f.get("start") == start]
    if not instant and basis:
        candidates = [
            f
            for f in candidates
            if duration_basis(f, fp or str(f.get("fp") or "")) == basis
        ]
    if not candidates:
        return None
    non_dimensional = [
        f for f in candidates if not _frame_dimensional(str(f.get("frame") or ""))
    ]
    if non_dimensional:
        candidates = non_dimensional
    candidates.sort(key=lambda f: _score_fact(f, fy, fp, form, instant), reverse=True)
    latest = candidates[0]
    preferred = next(
        (
            candidate
            for candidate in candidates
            if _form_kind(candidate.get("form")) == _form_kind(form)
        ),
        None,
    )
    # Aynı değer sonraki filing'de tekrarlandıysa denetlenmiş/blokla uyumlu
    # kaynağı koru. Değer değiştiyse en yeni filing gerçek restatement'tır.
    selected = (
        preferred
        if preferred is not None and preferred.get("val") == latest.get("val")
        else latest
    )
    chosen = dict(selected)
    prior = next(
        (
            f
            for f in candidates
            if f is not selected
            if f.get("val") != chosen.get("val")
        ),
        None,
    )
    if prior is not None:
        chosen["_restated"] = True
        chosen["_previous_value"] = prior.get("val")
        chosen["_previous_filed"] = prior.get("filed")
        chosen["_previous_accn"] = prior.get("accn")
    return chosen


def _line_item(
    facts: dict[str, Any],
    aliases: list[tuple[str, str]],
    fy: int | None,
    fp: str | None,
    form: str | None,
    *,
    instant: bool,
    end: str | None,
    start: str | None = None,
    basis: str | None = None,
) -> dict[str, Any] | None:
    for taxonomy, tag in aliases:
        concept = _concept(facts, taxonomy, tag)
        if not concept:
            continue
        unit, series = _unit_series(concept)
        chosen = pick_fact(
            series,
            fy,
            fp,
            form,
            instant=instant,
            end=end,
            start=start,
            basis=basis,
        )
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
        if chosen.get("_restated"):
            item["restated"] = True
            item["previous_value"] = chosen.get("_previous_value")
            item["previous_filed"] = chosen.get("_previous_filed")
            item["previous_accn"] = chosen.get("_previous_accn")
        if _form_kind(chosen.get("form")) != _form_kind(form):
            item["form_mismatch"] = True
        if not instant:
            item["start"] = chosen.get("start")
            item["basis"] = duration_basis(chosen, fp or str(chosen.get("fp") or ""))
        return item
    return None


def _fill_statement(
    facts: dict[str, Any],
    mapping: dict[str, list[tuple[str, str]]],
    fy: int | None,
    fp: str | None,
    form: str | None,
    *,
    instant: bool,
    end: str | None,
    start: str | None = None,
    basis: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, aliases in mapping.items():
        item = _line_item(
            facts,
            aliases,
            fy,
            fp,
            form,
            instant=instant,
            end=end,
            start=None if instant else start,
            basis=basis,
        )
        if item is not None:
            out[key] = item
    return out


def _max_end_by_accn(series_iter: list[list[dict[str, Any]]]) -> dict[str, str]:
    """Aynı accession'da en geç `end` = o filing'in cari dönemi; öncekiler comparative."""
    max_end: dict[str, str] = {}
    for series in series_iter:
        for fact in series:
            accn = str(fact.get("accn") or "")
            end = str(fact.get("end") or "")
            if not accn or not end:
                continue
            if accn not in max_end or end > max_end[accn]:
                max_end[accn] = end
    return max_end


def _is_current_period(fact: dict[str, Any], max_end: dict[str, str]) -> bool:
    accn = str(fact.get("accn") or "")
    end = str(fact.get("end") or "")
    if not end:
        return False
    if not accn:
        return True
    return end == max_end.get(accn)


def _scan_series(facts: dict[str, Any]) -> list[list[dict[str, Any]]]:
    scan_aliases = (
        INCOME_DURATION["net_income"]
        + INCOME_DURATION["revenue"]
        + BALANCE_INSTANT["assets"]
    )
    out: list[list[dict[str, Any]]] = []
    for taxonomy, tag in scan_aliases:
        concept = _concept(facts, taxonomy, tag)
        if not concept:
            continue
        _, series = _unit_series(concept)
        out.append(series)
    return out


def collect_periods(
    facts: dict[str, Any],
    *,
    annual: int = 4,
    quarterly: int = 4,
) -> list[dict[str, Any]]:
    """Cari dönem (filing max end) + ekonomik `end`. fy/fp grup anahtarı değil."""
    scanned = _scan_series(facts)
    max_end = _max_end_by_accn(scanned)
    seen: dict[tuple, dict[str, Any]] = {}
    for series in scanned:
        for fact in series:
            form = str(fact.get("form") or "")
            kind = _form_kind(form)
            end = str(fact.get("end") or "")
            if kind is None or not end or not _is_current_period(fact, max_end):
                continue
            slot = (kind, end)
            days = _duration_days(fact)
            qtd = 1 if kind == "quarter" and days is not None and days <= 100 else 0
            row = {
                "fy": int(fact["fy"]) if fact.get("fy") is not None else None,
                "fp": "FY" if kind == "annual" else str(fact.get("fp") or ""),
                "form": form,
                "end": end,
                "filed": str(fact.get("filed") or ""),
                "start": fact.get("start"),
                "kind": kind,
                "_qtd": qtd,
            }
            prev = seen.get(slot)
            if prev is None or (row["_qtd"], row["filed"]) > (
                prev.get("_qtd", 0),
                prev.get("filed", ""),
            ):
                seen[slot] = row

    def _clean(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]

    annual_rows = [p for p in seen.values() if p["kind"] == "annual"]
    quarter_rows = [p for p in seen.values() if p["kind"] == "quarter"]
    annual_rows.sort(key=lambda p: p["end"], reverse=True)
    quarter_rows.sort(key=lambda p: p["end"], reverse=True)
    return _clean(annual_rows[:annual]) + _clean(quarter_rows[:quarterly])


def _cashflow_for_period(
    facts: dict[str, Any],
    period: dict[str, Any],
) -> dict[str, Any]:
    fy, fp, form, end = period["fy"], period["fp"], period["form"], period["end"]
    start = period.get("start")
    reported = _fill_statement(
        facts,
        CASHFLOW_DURATION,
        fy,
        fp,
        form,
        instant=False,
        end=end,
        start=start,
    )
    if _form_kind(form) != "quarter":
        return reported

    ytd = _fill_statement(
        facts,
        CASHFLOW_DURATION,
        fy,
        fp,
        form,
        instant=False,
        end=end,
        basis="ytd",
    )
    # Q1 için QTD ve YTD aynı ekonomik aralıktır.
    if fp == "Q1":
        for key, item in reported.items():
            ytd.setdefault(key, item)
    for key, item in ytd.items():
        ytd_item = dict(item)
        ytd_item["basis"] = "ytd"
        ytd_item["derived"] = False
        reported[f"{key}_ytd"] = ytd_item
    return reported


def _compatible_ytd(current: dict[str, Any], previous: dict[str, Any]) -> bool:
    return (
        current.get("start")
        and current.get("start") == previous.get("start")
        and current.get("unit") == previous.get("unit")
        and current.get("taxonomy") == previous.get("taxonomy")
        and current.get("tag") == previous.get("tag")
    )


def _day_after(value: str | None) -> str | None:
    parsed = _parse_date(value)
    return (parsed + timedelta(days=1)).isoformat() if parsed else None


_NONNEGATIVE_CASHFLOW_KEYS = {
    "capex",
    "depreciation",
    "dividends",
    "buybacks",
}
_MIXED_SOURCE_LAG_DAYS = 200


def _attach_source_lag(
    item: dict[str, Any], source_filed: list[str | None]
) -> None:
    dates = [parsed for value in source_filed if (parsed := _parse_date(value))]
    if len(dates) < 2:
        return
    lag = (max(dates) - min(dates)).days
    item["source_lag_days"] = lag
    if lag > _MIXED_SOURCE_LAG_DAYS:
        item["mixed_source"] = True


def _derive_quarterly_cashflow(statements: list[dict[str, Any]]) -> None:
    quarters = sorted(
        [
            period
            for period in statements
            if _form_kind(period.get("form")) == "quarter"
        ],
        key=lambda period: period.get("end") or "",
    )
    for index, period in enumerate(quarters):
        block = period.get("cashflow") or {}
        for key in CASHFLOW_DURATION:
            if key in block:
                block[key].setdefault("derived", False)
                continue
            current = block.get(f"{key}_ytd")
            if current is None:
                continue
            previous = None
            for candidate_period in reversed(quarters[:index]):
                candidate = (candidate_period.get("cashflow") or {}).get(f"{key}_ytd")
                if candidate is not None and _compatible_ytd(current, candidate):
                    previous = candidate
                    break
            if previous is None:
                continue
            value = current["value"] - previous["value"]
            source_accns = [previous.get("accn"), current.get("accn")]
            derived = {
                "value": value,
                "unit": current.get("unit"),
                "tag": current.get("tag"),
                "taxonomy": current.get("taxonomy"),
                "start": _day_after(previous.get("end")),
                "end": current.get("end"),
                "basis": "qtd",
                "derived": True,
                "method": "ytd_diff",
                "source_periods": [previous.get("end"), current.get("end")],
                "source_accns": source_accns,
                "source_filed": [previous.get("filed"), current.get("filed")],
            }
            _attach_source_lag(derived, derived["source_filed"])
            if key in _NONNEGATIVE_CASHFLOW_KEYS and value < 0:
                derived["raw_derived_value"] = value
                derived["value"] = None
                derived["sign_anomaly"] = True
            block[key] = derived


_DEBT_COMPONENT_KEYS = (
    "long_term_debt_noncurrent",
    "long_term_debt_current",
    "short_term_borrowings",
    "commercial_paper",
)

_DEBT_SHORT_TERM_KEYS = ("short_term_borrowings", "commercial_paper")
_DEBT_OUTPUT_KEYS = (
    "long_term_debt_total",
    "long_term_debt_noncurrent",
    "long_term_debt_current",
    "short_term_borrowings",
    "commercial_paper",
    "total_debt",
)


def _derive_total_debt(balance: dict[str, Any]) -> None:
    direct = balance.get("long_term_debt_total")
    components = [
        (key, balance[key]) for key in _DEBT_COMPONENT_KEYS if key in balance
    ]
    if direct is not None:
        additive = [
            (key, balance[key]) for key in _DEBT_SHORT_TERM_KEYS if key in balance
        ]
        total = {
            **direct,
            "value": direct["value"] + sum(item["value"] for _, item in additive),
            "derived": bool(additive),
            "components": [
                str(direct.get("tag") or "LongTermDebt"),
                *[str(item.get("tag") or key) for key, item in additive],
            ],
        }
        if additive:
            total["method"] = "long_term_plus_short_term"
            total["source_accns"] = [
                direct.get("accn"),
                *[item.get("accn") for _, item in additive],
            ]
            total["source_filed"] = [
                direct.get("filed"),
                *[item.get("filed") for _, item in additive],
            ]
            _attach_source_lag(total, total["source_filed"])
        balance["total_debt"] = total
        return
    if not components:
        balance["total_debt"] = {
            "value": None,
            "derived": False,
            "warning": "insufficient_components",
            "components": [],
        }
        return
    if "long_term_debt_noncurrent" not in balance:
        balance["total_debt"] = {
            "value": None,
            "unit": components[0][1].get("unit"),
            "end": components[0][1].get("end"),
            "derived": False,
            "warning": "insufficient_components",
            "components": [
                str(item.get("tag") or key) for key, item in components
            ],
            "component_keys": [key for key, _ in components],
        }
        return
    units = {item.get("unit") for _, item in components}
    ends = {item.get("end") for _, item in components}
    if len(units) != 1 or len(ends) != 1:
        balance["total_debt_warning"] = {
            "warning": "incompatible_component_units_or_dates",
            "component_keys": [key for key, _ in components],
        }
        return
    total_debt = {
        "value": sum(item["value"] for _, item in components),
        "unit": components[0][1].get("unit"),
        "taxonomy": "derived",
        "end": components[0][1].get("end"),
        "derived": True,
        "method": "component_sum",
        "components": [str(item.get("tag") or key) for key, item in components],
        "component_keys": [key for key, _ in components],
        "source_accns": [item.get("accn") for _, item in components],
        "source_filed": [item.get("filed") for _, item in components],
    }
    _attach_source_lag(total_debt, total_debt["source_filed"])
    balance["total_debt"] = total_debt


def _normalize_debt_schema(balance: dict[str, Any]) -> None:
    for key in _DEBT_OUTPUT_KEYS:
        balance.setdefault(key, None)


def _mark_tag_changes(statements: list[dict[str, Any]]) -> None:
    ordered = sorted(statements, key=lambda p: p.get("end") or "")
    for section in ("income", "balance", "cashflow"):
        prev_tag: dict[str, str] = {}
        for period in ordered:
            block = period.get(section) or {}
            for key, item in block.items():
                if not isinstance(item, dict):
                    continue
                tag = item.get("tag")
                if not tag:
                    continue
                if key in prev_tag and prev_tag[key] != tag:
                    item["tag_changed"] = True
                prev_tag[key] = tag


def extract_financials(
    facts: dict[str, Any],
    *,
    annual: int = 4,
    quarterly: int = 4,
) -> dict[str, Any]:
    # YTD→QTD farkı, kullanıcı yalnız bir çeyrek istese bile önceki çeyreğe
    # ihtiyaç duyar. İçeride sekiz çeyrek işle, dönüş kotasını sonda uygula.
    periods = collect_periods(
        facts,
        annual=annual,
        quarterly=max(quarterly, 8) if quarterly else 0,
    )
    statements = []
    for period in periods:
        fy, fp, form, end = period["fy"], period["fp"], period["form"], period["end"]
        start = period.get("start")
        income = _fill_statement(
            facts,
            INCOME_DURATION,
            fy,
            fp,
            form,
            instant=False,
            end=end,
            start=start,
        )
        cashflow = _cashflow_for_period(facts, period)
        balance = _fill_statement(
            facts, BALANCE_INSTANT, fy, fp, form, instant=True, end=end
        )
        _derive_total_debt(balance)
        _normalize_debt_schema(balance)
        statements.append(
            {
                **{k: v for k, v in period.items() if k != "kind"},
                "income": income,
                "balance": balance,
                "cashflow": cashflow,
            }
        )
    statements.sort(key=lambda p: p["end"], reverse=True)
    _derive_quarterly_cashflow(statements)
    _mark_tag_changes(statements)
    annual_statements = [
        period for period in statements if _form_kind(period.get("form")) == "annual"
    ][:annual]
    quarter_statements = [
        period for period in statements if _form_kind(period.get("form")) == "quarter"
    ][:quarterly]
    statements = sorted(
        annual_statements + quarter_statements,
        key=lambda period: period["end"],
        reverse=True,
    )
    return {
        "cik": facts.get("cik"),
        "entity": facts.get("entityName"),
        "periods": statements,
    }
