"""Form 4 (ownership XML) ve 13F information table parse."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


FORM4_CODES = {
    "P": "open market purchase",
    "S": "open market sale",
    "A": "award / grant",
    "M": "option/derivative exercise",
    "G": "gift",
    "F": "tax withholding / payment",
    "D": "disposition to issuer",
    "C": "conversion",
    "J": "other",
    "I": "discretionary",
    "X": "option exercise (expired code)",
    "V": "voluntary report",
}


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _child(el: ET.Element | None, name: str) -> ET.Element | None:
    if el is None:
        return None
    for child in el:
        if _local(child.tag) == name:
            return child
    return None


def _find(el: ET.Element | None, *names: str) -> ET.Element | None:
    cur = el
    for name in names:
        cur = _child(cur, name)
        if cur is None:
            return None
    return cur


def _text(el: ET.Element | None) -> str | None:
    if el is None:
        return None
    for node in el.iter():
        if _local(node.tag) == "value" and (node.text or "").strip():
            return node.text.strip()
    text = (el.text or "").strip()
    return text or None


def _num(el: ET.Element | None) -> float | None:
    raw = _text(el)
    if raw is None:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def parse_form4(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    issuer = _child(root, "issuer")
    owner = _child(root, "reportingOwner")
    owner_id = _child(owner, "reportingOwnerId")
    rel = _child(owner, "reportingOwnerRelationship")

    transactions: list[dict[str, Any]] = []
    for table_name, derivative in (
        ("nonDerivativeTable", False),
        ("derivativeTable", True),
    ):
        table = _child(root, table_name)
        if table is None:
            continue
        for node in table:
            local = _local(node.tag)
            if local not in {"nonDerivativeTransaction", "derivativeTransaction"}:
                continue
            code = _text(_find(node, "transactionCoding", "transactionCode"))
            transactions.append(
                {
                    "derivative": derivative,
                    "security": _text(_find(node, "securityTitle")),
                    "date": _text(_find(node, "transactionDate")),
                    "code": code,
                    "code_label": FORM4_CODES.get(code or "", ""),
                    "shares": _num(_find(node, "transactionAmounts", "transactionShares")),
                    "price": _num(
                        _find(node, "transactionAmounts", "transactionPricePerShare")
                    ),
                    "acquired_or_disposed": _text(
                        _find(node, "transactionAmounts", "transactionAcquiredDisposedCode")
                    ),
                    "shares_after": _num(
                        _find(
                            node,
                            "postTransactionAmounts",
                            "sharesOwnedFollowingTransaction",
                        )
                    ),
                }
            )

    return {
        "period_of_report": _text(_child(root, "periodOfReport")),
        "issuer": {
            "cik": _text(_child(issuer, "issuerCik")),
            "name": _text(_child(issuer, "issuerName")),
            "ticker": _text(_child(issuer, "issuerTradingSymbol")),
        },
        "reporting_owner": {
            "cik": _text(_child(owner_id, "rptOwnerCik")),
            "name": _text(_child(owner_id, "rptOwnerName")),
            "is_director": _text(_child(rel, "isDirector")),
            "is_officer": _text(_child(rel, "isOfficer")),
            "is_ten_percent": _text(_child(rel, "isTenPercentOwner")),
            "officer_title": _text(_child(rel, "officerTitle")),
        },
        "transactions": transactions,
    }


def parse_13f_table(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, Any]] = []
    for node in root.iter():
        if _local(node.tag) != "infoTable":
            continue
        voting = _child(node, "votingAuthority")
        shrs = _child(node, "shrsOrPrnAmt")
        rows.append(
            {
                "issuer": _text(_child(node, "nameOfIssuer")),
                "class": _text(_child(node, "titleOfClass")),
                "cusip": _text(_child(node, "cusip")),
                "value_thousands_usd": _num(_child(node, "value")),
                "shares": _num(_child(shrs, "sshPrnamt")),
                "share_type": _text(_child(shrs, "sshPrnamtType")),
                "discretion": _text(_child(node, "investmentDiscretion")),
                "voting_sole": _num(_child(voting, "Sole")),
                "voting_shared": _num(_child(voting, "Shared")),
                "voting_none": _num(_child(voting, "None")),
            }
        )
    return rows
