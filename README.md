# EDGAR MCP — SEC companyfacts, frames, Form 4, 13F

SEC EDGAR'a User-Agent ile bağlanan MCP sunucusu. API key yok. Finansallar FMP değil, `companyfacts` / `frames` üzerinden okunur; XBRL tag eşlemesi `xbrl_map.py` içindedir.

## Tool'lar

| Tool | Ne işe yarar |
|------|----------------|
| `search_company` | Ticker / CIK / ad |
| `get_company` | SIC, borsa, mali yıl sonu |
| `get_financials` | Eşlenmiş gelir, bilanço, nakit akış |
| `get_concept` | Tek us-gaap/ifrs/dei tag'inin ham serisi |
| `get_frame` | Aynı kavram + dönem, tüm filers (kesit) |
| `list_filings` | 10-K, 10-Q, 8-K, 4, 13F-HR... |
| `get_form4` | Insider işlemleri (issuer ticker veya kişi CIK) |
| `get_13f` | Kurumun 13F-HR portföyü (hisse ticker'ı değil) |
| `search_filings` | Full-text (efts.sec.gov) |

## Kurulum

```bash
cd edgar-mcp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`.env` içinde `EDGAR_USER_AGENT` gerçek isim + e-posta olmalı. SEC generic `python-requests` ajanlarını 403 ile keser.

```
EDGAR_USER_AGENT=Your Name your.email@example.com
MCP_TRANSPORT=stdio
```

### Cursor (stdio)

`%USERPROFILE%\.cursor\mcp.json`:

```json
{
  "mcpServers": {
    "edgar": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "C:\\Users\\yunus\\Documents\\dev\\edgar-mcp",
      "env": {
        "MCP_TRANSPORT": "stdio",
        "EDGAR_USER_AGENT": "Your Name your.email@example.com"
      }
    }
  }
}
```

### Railway → Claude (Streamable HTTP)

`PORT` varsa varsayılan transport `http` ve endpoint `https://<railway-host>/mcp`. **`MCP_TRANSPORT=stdio` koyma** — süreç dinlemez, Railway "online" görünür ama Claude bağlanamaz.

**Variables**

| Key | Değer |
|-----|--------|
| `EDGAR_USER_AGENT` | `Ad Soyad you@email.com` (SEC 403 olmasın diye gerçek) |
| `MCP_TRANSPORT` | `http` (veya hiç ekleme) |
| `MCP_AUTH_TOKEN` | Claude.ai için **koyma**. Connector formu header göndermez; token 401 + "Authentication failed" üretir. |

**Kontrol:** `https://<host>/health` → `{"ok": true, ...}`

**Claude (claude.ai / Desktop Connectors)**

1. Customize → Connectors → Add custom connector
2. URL: `https://<host>/mcp`  (sonunda `/sse` değil)
3. OAuth alanlarını boş bırak, Individual sign-in kapalı
4. Add, sohbette `+` → Connectors ile aç

Claude Code header gönderebiliyorsa `MCP_AUTH_REQUIRED=true` ve `Authorization: Bearer <token>`.

Eski `/sse` için `MCP_TRANSPORT=sse` (Claude connector için tercih etme).

## Test

```bash
python -m unittest tests.test_xbrl_map tests.test_form_parsers tests.test_http_auth tests.test_client_utils
```

## Kaynaklar

- companyfacts / concept / frames: https://data.sec.gov
- submissions: https://data.sec.gov/submissions
- archives: https://www.sec.gov/Archives/edgar
- full-text: https://efts.sec.gov/LATEST/search-index
- Fair Access: https://www.sec.gov/os/webmaster-faq#code-support (max 10 req/s, User-Agent zorunlu)

13F değerleri SEC konvansiyonuyla **bin USD**. 13F'i hisse değil, kurum doldurur.
