# infrastructure/repositories/stock_companies_repository.py
from __future__ import annotations

import json
from typing import Iterable, List, Sequence

from sqlalchemy import select

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.stock_value import CompaniesReaderPort
from domain.entities.stock_value import Company, Ticker
from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.models.company_data_model import CompanyDataModel


class SqlAlchemyCompaniesRepository(EngineSetup, CompaniesReaderPort):
    """Read-only repository that exposes companies and their tickers."""

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config.database.connection_string, logger)

    def load_companies_with_stock(self) -> Iterable[Company]:
        with self.Session() as session:
            rows = session.execute(
                select(
                    CompanyDataModel.id,
                    CompanyDataModel.company_name,
                    CompanyDataModel.ticker_codes,
                    CompanyDataModel.isin_codes,
                )
            ).all()

            for cid, name, tickers_raw, isin_raw in rows:
                tickers = self._parse_codes(tickers_raw)
                if not tickers:
                    continue

                has_isin = self._has_isin(isin_raw)
                if not has_isin:
                    continue

                yield Company(
                    id=str(cid),
                    name=name or "",
                    has_isin=has_isin,
                    tickers=frozenset(Ticker(code=code) for code in tickers),
                )

    def _parse_codes(self, raw: object) -> List[str]:
        if raw is None:
            return []
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return []
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, Sequence) and not isinstance(loaded, (str, bytes)):
                    values = loaded
                else:
                    values = raw.split(",")
            except json.JSONDecodeError:
                values = raw.split(",")
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            values = raw
        else:
            return []

        cleaned = []
        for value in values:
            if value is None:
                continue
            code = str(value).strip().upper()
            if code:
                cleaned.append(code)
        return cleaned

    def _has_isin(self, raw: object) -> bool:
        if raw is None:
            return False
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return False
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, Sequence) and not isinstance(loaded, (str, bytes)):
                    return any(str(item).strip() for item in loaded if item is not None)
            except json.JSONDecodeError:
                return True
            return True
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            return any(str(item).strip() for item in raw if item is not None)
        return bool(raw)
