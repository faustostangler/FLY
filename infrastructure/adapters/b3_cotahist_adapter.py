from __future__ import annotations

import re
from datetime import date
from typing import Dict, Iterable, List, Sequence

import requests
from bs4 import BeautifulSoup

from application.ports.market_data_port import MarketDataPort
from domain.dtos.market_quote_dto import MarketQuoteDTO


class B3CotahistAdapter(MarketDataPort):
    """Adapter that fetches historical quotes from the B3 COTAHIST website."""

    def __init__(
        self,
        *,
        provider: str = "b3-cotahist",
        currency: str = "BRL",
        timeout: int = 15,
        session: requests.Session | None = None,
    ) -> None:
        self.provider = provider
        self.currency = currency
        self.timeout = timeout
        self.session = session or requests.Session()

    def fetch_window(
        self, symbol: str, start: date, end: date
    ) -> Sequence[MarketQuoteDTO]:
        canonical = (symbol or "").strip().upper()
        if not canonical or start > end:
            return []

        issuer_root = self._issuer_root(canonical)
        months = list(self._iter_months(start, end))
        quotes_by_day: Dict[date, MarketQuoteDTO] = {}

        for year, month in months:
            month_quotes = self._fetch_month(issuer_root, year, month)
            if not month_quotes:
                continue

            daily_quotes = month_quotes.get(canonical)
            if daily_quotes is None and canonical.endswith("F"):
                daily_quotes = month_quotes.get(canonical[:-1])
            if daily_quotes is None and canonical not in month_quotes:
                alt = canonical.rstrip("F")
                daily_quotes = month_quotes.get(alt)
            if not daily_quotes:
                continue

            for quote in daily_quotes:
                if start <= quote.day <= end:
                    quotes_by_day[quote.day] = quote

        return [quotes_by_day[d] for d in sorted(quotes_by_day)]

    @staticmethod
    def _issuer_root(symbol: str) -> str:
        for idx, char in enumerate(symbol):
            if char.isdigit():
                return symbol[:idx] or symbol
        return symbol

    @staticmethod
    def _iter_months(start: date, end: date) -> Iterable[tuple[int, int]]:
        current = date(start.year, start.month, 1)
        limit = date(end.year, end.month, 1)
        while current <= limit:
            yield current.year, current.month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

    def _fetch_month(
        self, root: str, year: int, month: int
    ) -> Dict[str, List[MarketQuoteDTO]]:
        if not root:
            return {}
        url = (
            "https://bvmf.bmfbovespa.com.br/sig/FormConsultaMercVista.asp?"
            f"strTipoResumo=RES_MERC_VISTA&strSocEmissora={root}&strDtReferencia={month:02d}-{year}"
            "&strIdioma=P&intCodNivel=2&intCodCtrl=160"
        )
        try:
            response = self.session.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException:
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("table", id="tblResDiario")
        if not container:
            return {}

        quotes: Dict[str, List[MarketQuoteDTO]] = {}
        for table in container.find_all("table"):
            if "Nome da Ação" not in table.get_text():
                continue
            ticker = self._extract_symbol(table)
            if not ticker:
                continue
            rows = self._parse_rows(table, ticker, year, month)
            if rows:
                quotes[ticker] = rows
        return quotes

    @staticmethod
    def _extract_symbol(table) -> str | None:
        header = table.find("tr")
        if not header:
            return None
        text = header.get_text(" ", strip=True)
        match = re.search(r"\(([^)]+)\)", text)
        return match.group(1).upper() if match else None

    def _parse_rows(
        self, table, ticker: str, year: int, month: int
    ) -> List[MarketQuoteDTO]:
        rows: List[MarketQuoteDTO] = []
        for row in table.find_all("tr"):
            cells = [col.get_text(strip=True) for col in row.find_all("td")]
            if len(cells) < 12:
                continue
            day_digits = "".join(ch for ch in cells[0] if ch.isdigit())
            if not day_digits:
                continue
            try:
                day = int(day_digits)
                when = date(year, month, day)
            except ValueError:
                continue

            close = self._parse_decimal(cells[-1])
            if close is None:
                continue
            rows.append(
                MarketQuoteDTO(
                    provider=self.provider,
                    symbol=ticker,
                    day=when,
                    close=close,
                    adjusted_close=close,
                    currency=self.currency,
                )
            )
        rows.sort(key=lambda q: q.day)
        return rows

    @staticmethod
    def _parse_decimal(raw: str) -> float | None:
        if not raw:
            return None
        cleaned = re.sub(r"[^0-9,.-]", "", raw)
        cleaned = cleaned.replace(".", "").replace(",", ".").strip()
        if cleaned in {"", "-", "--"}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
