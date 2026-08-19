"""SEC EDGAR HTTP client — companyfacts, frames, submissions, archives, EFTS.

Fair Access: User-Agent zorunlu, en fazla ~10 istek/sn.
https://www.sec.gov/os/webmaster-faq#code-support
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any
from urllib.parse import urlencode

import httpx
from cachetools import TTLCache

from form_parsers import parse_13f_table, parse_form4

log = logging.getLogger("edgar")

DATA_BASE = "https://data.sec.gov"
WWW_BASE = "https://www.sec.gov"
EFTS_BASE = "https://efts.sec.gov"
MAX_RPS = 8
TIMEOUT = 30.0
CIK_RE = re.compile(r"^\d{1,10}$")


class EdgarHTTPError(RuntimeError):
    def __init__(self, status: int, message: str, url: str):
        super().__init__(f"SEC {status}: {message} ({url})")
        self.status = status
        self.message = message
        self.url = url

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "url": self.url,
        }


class RateLimiter:
    def __init__(self, max_calls: int = MAX_RPS, window: float = 1.0):
        self.max_calls = max_calls
        self.window = window
        self.calls: list[float] = []

    def wait_if_needed(self) -> None:
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.window]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.window - (now - self.calls[0]) + 0.05
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.calls.append(time.time())


def pad_cik(cik: str | int) -> str:
    return f"{int(str(cik).lstrip('0') or '0'):010d}"


def bare_cik(cik: str | int) -> str:
    return str(int(pad_cik(cik)))


def accession_nodash(accession: str) -> str:
    return accession.replace("-", "")


def form_matches(ftype: str, wanted: str) -> bool:
    """'4' 424B2'ye yapışmasın; 4 ve 4/A kabul."""
    if not wanted:
        return True
    a, b = ftype.upper(), wanted.upper()
    return a == b or a == f"{b}/A"


class EdgarClient:
    def __init__(self, user_agent: str | None = None):
        self.user_agent = (user_agent or os.getenv("EDGAR_USER_AGENT", "")).strip()
        if not self.user_agent or "@" not in self.user_agent:
            raise RuntimeError(
                "EDGAR_USER_AGENT tanımlı değil veya e-posta içermiyor. "
                "SEC Fair Access için 'İsim eposta@alan.com' formatı zorunlu. "
                ".env.example dosyasına bakın."
            )
        self.rate = RateLimiter()
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json, text/plain, */*",
        }
        self.http = httpx.Client(timeout=TIMEOUT, headers=headers, follow_redirects=True)
        self._tickers_cache: TTLCache = TTLCache(maxsize=1, ttl=24 * 3600)
        self._facts_cache: TTLCache = TTLCache(maxsize=64, ttl=3600)
        self._subs_cache: TTLCache = TTLCache(maxsize=64, ttl=900)
        self._doc_cache: TTLCache = TTLCache(maxsize=32, ttl=3600)

    def close(self) -> None:
        self.http.close()

    def _get(self, url: str, *, json: bool = True, retries: int = 3) -> Any:
        last_exc: Exception | None = None
        last_status = 0
        last_message = "request failed"
        for attempt in range(retries):
            self.rate.wait_if_needed()
            try:
                resp = self.http.get(url)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < retries - 1:
                    time.sleep(0.5 * (2**attempt))
                continue
            last_status = resp.status_code
            if resp.status_code == 429:
                last_message = "rate limit exceeded"
                try:
                    retry_after = float(resp.headers.get("Retry-After", "0"))
                except ValueError:
                    retry_after = 0
                wait = max(retry_after, 0.5 * (2**attempt))
                log.info("SEC 429, %.1fs bekleniyor", wait)
                if attempt < retries - 1:
                    time.sleep(wait)
                continue
            if resp.status_code == 403:
                raise EdgarHTTPError(
                    403,
                    "forbidden; EDGAR_USER_AGENT may have been rejected",
                    url,
                )
            if resp.status_code == 404:
                raise EdgarHTTPError(404, "not found", url)
            if resp.status_code >= 500:
                last_message = (resp.text or "SEC upstream error")[:300]
                if attempt < retries - 1:
                    time.sleep(0.5 * (2**attempt))
                continue
            if resp.status_code >= 400:
                raise EdgarHTTPError(
                    resp.status_code,
                    (resp.text or "request rejected")[:300],
                    url,
                )
            return resp.json() if json else resp.text
        if last_status:
            raise EdgarHTTPError(last_status, last_message, url)
        raise RuntimeError(f"SEC isteği başarısız ({url}): {last_exc}")

    def _tickers(self) -> list[dict[str, Any]]:
        cached = self._tickers_cache.get("all")
        if cached is not None:
            return cached
        url = f"{WWW_BASE}/files/company_tickers_exchange.json"
        payload = self._get(url)
        rows: list[dict[str, Any]] = []
        if isinstance(payload, dict) and "data" in payload:
            fields = payload.get("fields") or ["cik", "name", "ticker", "exchange"]
            for item in payload["data"]:
                row = dict(zip(fields, item))
                rows.append(
                    {
                        "cik": pad_cik(row.get("cik", 0)),
                        "ticker": str(row.get("ticker") or "").upper(),
                        "name": row.get("name") or "",
                        "exchange": row.get("exchange") or "",
                    }
                )
        else:
            for item in (payload or {}).values():
                rows.append(
                    {
                        "cik": pad_cik(item.get("cik_str", 0)),
                        "ticker": str(item.get("ticker") or "").upper(),
                        "name": item.get("title") or "",
                        "exchange": "",
                    }
                )
        self._tickers_cache["all"] = rows
        return rows

    def search_companies(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        rows = self._tickers()
        if CIK_RE.match(q):
            cik = pad_cik(q)
            return [r for r in rows if r["cik"] == cik][:limit]

        needle = q.upper().replace(".", "-")
        exact: list[dict[str, Any]] = []
        starts: list[dict[str, Any]] = []
        named: list[dict[str, Any]] = []
        for row in rows:
            if row["ticker"] == needle:
                exact.append(row)
            elif row["ticker"].startswith(needle):
                starts.append(row)
            elif needle in row["name"].upper():
                named.append(row)
        out: list[dict[str, Any]] = []
        for bucket in (exact, starts, named):
            for row in bucket:
                if row not in out:
                    out.append(row)
                if len(out) >= limit:
                    return out
        return out

    def resolve(self, query: str) -> dict[str, Any]:
        raw = (query or "").strip()
        if not raw:
            raise FileNotFoundError("Boş sorgu.")
        if CIK_RE.match(raw):
            cik = pad_cik(raw)
            hits = self.search_companies(raw, limit=5)
            return hits[0] if hits else {"cik": cik, "ticker": "", "name": "", "exchange": ""}
        hits = self.search_companies(raw, limit=5)
        if not hits:
            raise FileNotFoundError(
                f"'{query}' için CIK/ticker bulunamadı. Örn. AAPL, 320193, Apple."
            )
        q = raw.upper()
        for hit in hits:
            if hit["ticker"] == q:
                return hit
        return hits[0]

    def get_submissions(self, cik: str) -> dict[str, Any]:
        cik = pad_cik(cik)
        cached = self._subs_cache.get(cik)
        if cached is not None:
            return cached
        data = self._get(f"{DATA_BASE}/submissions/CIK{cik}.json")
        self._subs_cache[cik] = data
        return data

    def get_companyfacts(self, cik: str) -> dict[str, Any]:
        cik = pad_cik(cik)
        cached = self._facts_cache.get(cik)
        if cached is not None:
            return cached
        data = self._get(f"{DATA_BASE}/api/xbrl/companyfacts/CIK{cik}.json")
        self._facts_cache[cik] = data
        return data

    def get_companyconcept(self, cik: str, taxonomy: str, tag: str) -> dict[str, Any]:
        cik = pad_cik(cik)
        return self._get(
            f"{DATA_BASE}/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json"
        )

    def get_frame(self, taxonomy: str, tag: str, unit: str, period: str) -> dict[str, Any]:
        return self._get(
            f"{DATA_BASE}/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json"
        )

    def list_filings(
        self,
        cik: str,
        form: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        subs = self.get_submissions(cik)
        recent = (subs.get("filings") or {}).get("recent") or {}
        forms = recent.get("form") or []
        wanted = (form or "").strip().upper()
        rows: list[dict[str, Any]] = []
        for i, ftype in enumerate(forms):
            if wanted and not form_matches(ftype, wanted):
                continue
            accn = recent.get("accessionNumber", [None])[i]
            primary = recent.get("primaryDocument", [None])[i]
            rows.append(
                {
                    "form": ftype,
                    "accession": accn,
                    "filed": recent.get("filingDate", [None])[i],
                    "report_date": recent.get("reportDate", [None])[i],
                    "primary_document": primary,
                    "description": recent.get("primaryDocDescription", [None])[i],
                    "url": self.archive_url(cik, accn, primary) if accn and primary else None,
                }
            )
            if len(rows) >= limit:
                break
        return rows

    def archive_url(self, cik: str, accession: str, filename: str) -> str:
        return (
            f"{WWW_BASE}/Archives/edgar/data/{bare_cik(cik)}/"
            f"{accession_nodash(accession)}/{filename}"
        )

    def get_filing_index(self, cik: str, accession: str) -> dict[str, Any]:
        url = (
            f"{WWW_BASE}/Archives/edgar/data/{bare_cik(cik)}/"
            f"{accession_nodash(accession)}/index.json"
        )
        return self._get(url)

    def get_text(self, url: str) -> str:
        cached = self._doc_cache.get(url)
        if cached is not None:
            return cached
        text = self._get(url, json=False)
        self._doc_cache[url] = text
        return text

    def _index_files(self, cik: str, accession: str) -> list[dict[str, Any]]:
        index = self.get_filing_index(cik, accession)
        directory = index.get("directory") or {}
        items = directory.get("item") or []
        if isinstance(items, dict):
            items = [items]
        return items

    def _pick_xml(self, files: list[dict[str, Any]], *, kind: str) -> str | None:
        names = [str(f.get("name") or "") for f in files]
        xmls = [
            n
            for n in names
            if n.lower().endswith(".xml")
            and not n.lower().startswith("r")
            and "xsl" not in n.lower()
            and n.lower() not in {"filingSummary.xml".lower(), "Metalinks.xml".lower()}
        ]
        if not xmls:
            return None
        if kind == "form4":
            for n in xmls:
                low = n.lower()
                if "ownership" in low or low.endswith(".xml"):
                    return n
            return xmls[0]
        if kind == "13f":
            for n in xmls:
                low = n.lower()
                if "info" in low or "13f" in low or "infotable" in low:
                    return n
            # Kapak XML'i değil, en büyük tablo genelde infotable
            sized = sorted(
                files,
                key=lambda f: int(f.get("size") or 0),
                reverse=True,
            )
            for f in sized:
                n = str(f.get("name") or "")
                if n in xmls:
                    return n
        return xmls[0]

    def get_form4s(self, cik: str, limit: int = 10) -> list[dict[str, Any]]:
        filings = self.list_filings(cik, form="4", limit=limit)
        out: list[dict[str, Any]] = []
        for filing in filings:
            accn = filing.get("accession")
            if not accn:
                continue
            try:
                files = self._index_files(cik, accn)
                name = self._pick_xml(files, kind="form4")
                if not name:
                    name = filing.get("primary_document")
                if not name:
                    continue
                xml_text = self.get_text(self.archive_url(cik, accn, name))
                parsed = parse_form4(xml_text)
                parsed["filing"] = filing
                out.append(parsed)
            except Exception as exc:
                log.warning("Form 4 parse hatası %s: %s", accn, exc)
                out.append({"filing": filing, "error": str(exc)})
        return out

    def get_13f(self, cik: str, limit_holdings: int = 100) -> dict[str, Any]:
        filings = self.list_filings(cik, form="13F-HR", limit=5)
        if not filings:
            return {
                "cik": pad_cik(cik),
                "filings": [],
                "holdings": [],
                "note": (
                    "Bu CIK için 13F-HR yok. 13F'i hisse değil, kurum (fon, investment "
                    "adviser) doldurur. Örn. Berkshire Hathaway CIK 1067983. Bir hissenin "
                    "sahiplerini aramak için search_filings kullanın."
                ),
            }
        filing = filings[0]
        accn = filing["accession"]
        files = self._index_files(cik, accn)
        name = self._pick_xml(files, kind="13f")
        if not name:
            raise RuntimeError(f"13F XML bulunamadı ({accn})")
        xml_text = self.get_text(self.archive_url(cik, accn, name))
        holdings = parse_13f_table(xml_text)
        holdings.sort(key=lambda r: r.get("value_thousands_usd") or 0, reverse=True)
        return {
            "cik": pad_cik(cik),
            "filing": filing,
            "holdings_total": len(holdings),
            "holdings": holdings[:limit_holdings],
            "value_unit": "thousands of USD (SEC 13F convention)",
        }

    def search_full_text(
        self,
        query: str,
        *,
        forms: str = "",
        start: str = "",
        end: str = "",
        limit: int = 20,
    ) -> dict[str, Any]:
        params: list[tuple[str, str]] = [
            ("q", query),
            ("dateRange", "custom" if start or end else "all"),
        ]
        if start:
            params.append(("startdt", start))
        if end:
            params.append(("enddt", end))
        if forms:
            params.append(("forms", forms))
        url = f"{EFTS_BASE}/LATEST/search-index?{urlencode(params)}"
        data = self._get(url)
        hits_in = data.get("hits", {}).get("hits", []) if isinstance(data, dict) else []
        hits = []
        for hit in hits_in[:limit]:
            src = hit.get("_source") or {}
            hits.append(
                {
                    "id": hit.get("_id"),
                    "form": src.get("file_type") or src.get("form"),
                    "filed": src.get("file_date"),
                    "period_ending": src.get("period_ending"),
                    "display_names": src.get("display_names"),
                    "tickers": src.get("tickers"),
                    "ciks": src.get("ciks"),
                    "items": src.get("items"),
                }
            )
        total = (
            (data.get("hits") or {}).get("total", {})
            if isinstance(data, dict)
            else {}
        )
        if isinstance(total, dict):
            total = total.get("value", len(hits))
        return {"query": query, "total": total, "hits": hits}
