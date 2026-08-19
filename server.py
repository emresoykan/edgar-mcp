"""
EDGAR MCP — SEC companyfacts, frames, Form 4, 13F.

Deploy: Railway (Streamable HTTP /mcp) veya lokal stdio
Auth: EDGAR_USER_AGENT (isim + e-posta) zorunlu; Railway'de MCP_AUTH_TOKEN önerilir
Rate limit: 8 istek/sn (SEC Fair Access: max 10/sn)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from edgar_client import EdgarClient, pad_cik
from http_auth import BearerTokenMiddleware
from xbrl_map import extract_financials

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edgar-mcp")

mcp = FastMCP(
    "EDGAR MCP",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    stateless_http=True,
)
_client: EdgarClient | None = None


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> Response:
    return JSONResponse({"ok": True, "name": "EDGAR MCP"})


@mcp.custom_route("/", methods=["GET"])
async def root(_request: Request) -> Response:
    return JSONResponse({"ok": True, "mcp": "/mcp", "health": "/health"})


def client() -> EdgarClient:
    global _client
    if _client is None:
        _client = EdgarClient()
    return _client


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _err(exc: Exception) -> str:
    logger.exception("EDGAR tool error")
    return _json({"error": str(exc)})


# ══════════════════════════════════════════════════
# ŞİRKET
# ══════════════════════════════════════════════════

@mcp.tool()
def search_company(query: str, limit: int = 10) -> str:
    """Ticker, CIK veya şirket adıyla SEC kaydı arar.

    Örnek: search_company("AAPL"), search_company("320193"), search_company("NVIDIA")
    """
    try:
        hits = client().search_companies(query, limit=min(limit, 25))
        if not hits:
            return _json({"query": query, "results": [], "note": "Eşleşme yok."})
        return _json({"query": query, "results": hits})
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def get_company(query: str) -> str:
    """Şirket kimliği: CIK, sic, borsa, mali yıl sonu. Ticker veya CIK verin."""
    try:
        co = client().resolve(query)
        subs = client().get_submissions(co["cik"])
        recent = (subs.get("filings") or {}).get("recent") or {}
        last = []
        for i, form in enumerate((recent.get("form") or [])[:8]):
            last.append(
                {
                    "form": form,
                    "filed": recent.get("filingDate", [None])[i],
                    "accession": recent.get("accessionNumber", [None])[i],
                }
            )
        return _json(
            {
                "cik": pad_cik(subs.get("cik", co["cik"])),
                "name": subs.get("name") or co.get("name"),
                "tickers": subs.get("tickers") or [co.get("ticker")],
                "exchanges": subs.get("exchanges") or [co.get("exchange")],
                "sic": subs.get("sic"),
                "sic_description": subs.get("sicDescription"),
                "fiscal_year_end": subs.get("fiscalYearEnd"),
                "ein": subs.get("ein"),
                "category": subs.get("category"),
                "recent_filings": last,
            }
        )
    except Exception as exc:
        return _err(exc)


# ══════════════════════════════════════════════════
# XBRL FİNANSALLAR
# ══════════════════════════════════════════════════

@mcp.tool()
def get_financials(
    query: str,
    annual: int = 4,
    quarterly: int = 4,
) -> str:
    """Eşlenmiş gelir / bilanço / nakit akış. Kaynak: companyfacts, ham FMP değil.

    Gelir kalemlerinde 10-Q için basis=qtd (çeyrek) veya ytd (yıl başından).
    Tag şirketten şirkete değişir; alias listesi xbrl_map.py içindedir.
    """
    try:
        co = client().resolve(query)
        facts = client().get_companyfacts(co["cik"])
        mapped = extract_financials(
            facts,
            annual=min(annual, 8),
            quarterly=min(quarterly, 8),
        )
        mapped["ticker"] = co.get("ticker")
        mapped["exchange"] = co.get("exchange")
        return _json(mapped)
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def get_concept(
    query: str,
    tag: str,
    taxonomy: str = "us-gaap",
    limit: int = 20,
) -> str:
    """Tek bir XBRL kavramının ham zaman serisi. Eşleme kaçınca kaçış kapısı.

    tag: örn. RevenueFromContractWithCustomerExcludingAssessedTax, Assets
    taxonomy: us-gaap | ifrs-full | dei
    """
    try:
        co = client().resolve(query)
        data = client().get_companyconcept(co["cik"], taxonomy, tag)
        units = data.get("units") or {}
        trimmed = {}
        for unit, series in units.items():
            trimmed[unit] = series[-limit:] if isinstance(series, list) else series
        return _json(
            {
                "cik": co["cik"],
                "ticker": co.get("ticker"),
                "entity": data.get("entityName"),
                "taxonomy": taxonomy,
                "tag": data.get("tag") or tag,
                "label": data.get("label"),
                "description": data.get("description"),
                "units": trimmed,
            }
        )
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def get_frame(
    tag: str,
    period: str,
    taxonomy: str = "us-gaap",
    unit: str = "USD",
    limit: int = 30,
) -> str:
    """Kesit: aynı XBRL kavramı, aynı dönem, tüm filers. Screening için.

    period: CY2024 (yıllık), CY2024Q3 (çeyrek süre), CY2024Q3I (anlık bilanço)
    """
    try:
        data = client().get_frame(taxonomy, tag, unit, period)
        rows = data.get("data") or []
        rows_sorted = sorted(rows, key=lambda r: r.get("val") or 0, reverse=True)
        return _json(
            {
                "taxonomy": taxonomy,
                "tag": data.get("tag") or tag,
                "label": data.get("label"),
                "unit": data.get("uom") or unit,
                "period": data.get("ccp") or period,
                "total": len(rows),
                "top": rows_sorted[: min(limit, 100)],
            }
        )
    except Exception as exc:
        return _err(exc)


# ══════════════════════════════════════════════════
# FİLİNGS / INSIDER / 13F
# ══════════════════════════════════════════════════

@mcp.tool()
def list_filings(query: str, form: str = "", limit: int = 20) -> str:
    """Şirketin submissions listesi. form: 10-K, 10-Q, 8-K, 4, 13F-HR, DEF 14A..."""
    try:
        co = client().resolve(query)
        rows = client().list_filings(
            co["cik"],
            form=form or None,
            limit=min(limit, 50),
        )
        return _json({"company": co, "filings": rows})
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def get_form4(query: str, limit: int = 8) -> str:
    """Son Form 4 işlemleri (insider alım/satım). Issuer ticker veya insider CIK.

    Apple insiders: get_form4("AAPL"). Belirli kişi: o kişinin CIK'si.
    """
    try:
        co = client().resolve(query)
        rows = client().get_form4s(co["cik"], limit=min(limit, 15))
        return _json({"company": co, "form4": rows})
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def get_13f(query: str, limit_holdings: int = 50) -> str:
    """Kurumun son 13F-HR portföyü. Hisse ticker'ı değil, filer CIK/adı.

    Berkshire: get_13f("1067983") veya get_13f("BRK-B") — BRK 13F doldurur.
    Apple hissedarlarını aramak için search_filings("AAPL", forms="13F-HR").
    value_thousands_usd: SEC birimi, bin USD.
    """
    try:
        co = client().resolve(query)
        data = client().get_13f(co["cik"], limit_holdings=min(limit_holdings, 200))
        data["company"] = co
        return _json(data)
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def search_filings(
    query: str,
    forms: str = "",
    start: str = "",
    end: str = "",
    limit: int = 20,
) -> str:
    """EDGAR full-text arama (efts.sec.gov).

    query: serbest metin veya ticker:AAPL
    forms: virgülle, örn. "8-K,4,13F-HR"
    start/end: YYYY-MM-DD
    """
    try:
        data = client().search_full_text(
            query,
            forms=forms,
            start=start,
            end=end,
            limit=min(limit, 50),
        )
        return _json(data)
    except Exception as exc:
        return _err(exc)


if __name__ == "__main__":
    import uvicorn

    transport = (os.getenv("MCP_TRANSPORT") or "").strip().lower()
    if not transport:
        transport = "http" if os.getenv("PORT") else "stdio"
    if transport in {"sse", "http", "streamable-http", "streamable_http"}:
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = int(os.getenv("PORT", "8000"))
        mcp.settings.stateless_http = True
        if transport == "sse":
            app = mcp.sse_app()
            logger.info("Legacy SSE on /sse — Claude connectors should use /mcp")
        else:
            app = mcp.streamable_http_app()
            logger.info("Streamable HTTP on /mcp")
        token = (os.getenv("MCP_AUTH_TOKEN") or "").strip()
        required = os.getenv("MCP_AUTH_REQUIRED", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if required and token:
            app = BearerTokenMiddleware(app, token)
        elif required and not token:
            logger.warning("MCP_AUTH_REQUIRED açık ama MCP_AUTH_TOKEN boş.")
        elif token:
            logger.info(
                "MCP_AUTH_TOKEN var; Claude connector header göndermediği için "
                "zorunlu değil (MCP_AUTH_REQUIRED=true ile açılır)."
            )
        uvicorn.run(app, host="0.0.0.0", port=mcp.settings.port)
    else:
        mcp.run(transport="stdio")
