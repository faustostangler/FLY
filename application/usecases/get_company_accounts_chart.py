from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional, Sequence

import pandas as pd

from application.dtos.account_series_dto import AccountSeriesDTO, AccountSeriesPointDTO
from application.dtos.company_accounts_series_dto import CompanyAccountsSeriesDTO
from domain.exceptions import DomainError
from domain.value_objects import SearchFilterTree

from .get_company_ratios_frame import (
    GetCompanyRatiosFrameRequest,
    GetCompanyRatiosFrameUseCase,
)


@dataclass
class GetCompanyAccountsChartUseCase:
    ratios_frame_usecase: GetCompanyRatiosFrameUseCase
    account_labels: dict[str, str] | None = None

    def __call__(
        self,
        *,
        company_name: str,
        accounts: Sequence[str],
        filters: Optional[SearchFilterTree] = None,
    ) -> CompanyAccountsSeriesDTO:
        return self.run(
            company_name=company_name,
            accounts=accounts,
            filters=filters,
        )

    def run(
        self,
        *,
        company_name: str,
        accounts: Sequence[str],
        filters: Optional[SearchFilterTree] = None,
    ) -> CompanyAccountsSeriesDTO:
        name = (company_name or "").strip()
        if not name:
            raise DomainError("company_name is required")

        requested_accounts = [str(a).strip() for a in (accounts or []) if str(a).strip()]
        if not requested_accounts:
            raise DomainError("At least one account must be provided")

        ratios_request = GetCompanyRatiosFrameRequest(
            company_name=name,
            filters=filters,
        )
        ratios_result = self.ratios_frame_usecase(ratios_request)
        df = self._prepare_frame(ratios_result.frame)

        missing = [acc for acc in requested_accounts if acc not in df.columns]
        if missing:
            raise DomainError(
                f"Accounts not found in ratios frame for {ratios_result.company_name}: {missing}"
            )

        df_selected = df[requested_accounts]
        series = self._build_series(
            df_selected,
            company_name=ratios_result.company_name,
            ticker=ratios_result.ticker,
        )

        cache_info = {
            "cache_key": ratios_result.cache_info.cache_key,
            "hit": ratios_result.cache_info.hit,
        }

        meta = {**ratios_result.meta}

        return CompanyAccountsSeriesDTO(
            company_name=ratios_result.company_name,
            ticker=ratios_result.ticker,
            series=series,
            meta=meta,
            cache_info=cache_info,
        )

    def _prepare_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame is None or frame.empty:
            raise DomainError("Ratios frame is empty")

        df = frame.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.set_index("date")
            else:
                df.index = pd.to_datetime(df.index, errors="coerce")
        df = df.sort_index()
        df.index = df.index.tz_localize(None)
        return df

    def _build_series(
        self,
        df: pd.DataFrame,
        *,
        company_name: str,
        ticker: Optional[str],
    ) -> List[AccountSeriesDTO]:
        labels_map = self._labels_for(df.columns)
        series_list: List[AccountSeriesDTO] = []
        for account_code in df.columns:
            points = self._build_points(df.index, df[account_code])
            label = labels_map.get(account_code, account_code)
            series_list.append(
                AccountSeriesDTO(
                    ticker=ticker or company_name,
                    account_code=account_code,
                    label=label,
                    points=points,
                )
            )
        return series_list

    def _build_points(
        self,
        index: Iterable[pd.Timestamp],
        series: pd.Series,
    ) -> List[AccountSeriesPointDTO]:
        points: List[AccountSeriesPointDTO] = []
        for idx, value in series.items():
            if pd.isna(value):
                y = None
            else:
                y = float(value)
            if isinstance(idx, pd.Timestamp):
                x: date = idx.date()
            else:
                x = idx
            points.append(AccountSeriesPointDTO(date=x, value=y))
        return points

    def _labels_for(self, account_codes: Iterable[str]) -> dict[str, str]:
        if not self.account_labels:
            return {code: code for code in account_codes}
        return {code: self.account_labels.get(code, code) for code in account_codes}
