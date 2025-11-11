from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import pandas as pd

from application.dtos.account_series_dto import AccountSeriesDTO, AccountSeriesPointDTO
from application.dtos.company_accounts_series_dto import CompanyAccountsSeriesDTO
from application.usecases.get_company_ratios_frame import GetCompanyRatiosFrameUseCase
from domain import DomainError
from domain.value_objects import SearchFilterTree


@dataclass
class GetCompanyAccountsChartUseCase:
    ratios_frame_usecase: GetCompanyRatiosFrameUseCase
    account_labels: Optional[dict[str, str]] = None

    def __call__(
        self,
        *,
        company_name: str,
        accounts: Sequence[str],
        filters: Optional[SearchFilterTree] = None,
    ) -> CompanyAccountsSeriesDTO:
        return self.run(company_name=company_name, accounts=accounts, filters=filters)

    def run(
        self,
        *,
        company_name: str,
        accounts: Sequence[str],
        filters: Optional[SearchFilterTree] = None,
    ) -> CompanyAccountsSeriesDTO:
        normalized_company = (company_name or "").strip()
        if not normalized_company:
            raise DomainError("company_name é obrigatório para gerar séries de gráfico.")

        account_codes = [code.strip() for code in accounts if str(code).strip()]
        if not account_codes:
            raise DomainError("Informe ao menos um código de conta para gerar o gráfico.")

        ratios_frame = self.ratios_frame_usecase(
            company_name=normalized_company,
            filters=filters,
        )
        df = ratios_frame.frame

        if df is None or df.empty:
            raise DomainError(
                f"Nenhum dado de ratios disponível para '{ratios_frame.company_name}'."
            )

        df = self._ensure_datetime_index(df)
        df_selected = self._select_accounts(df, account_codes, ratios_frame.company_name)
        series = self._build_series(df_selected, ratios_frame)

        meta = dict(ratios_frame.meta)

        return CompanyAccountsSeriesDTO(
            company_name=ratios_frame.company_name,
            ticker=ratios_frame.ticker,
            series=series,
            cache_info=ratios_frame.cache_info,
            meta=meta,
        )

    def _ensure_datetime_index(self, df: pd.DataFrame) -> pd.DataFrame:
        if isinstance(df.index, (pd.DatetimeIndex, pd.PeriodIndex)):
            return df.sort_index()

        df = df.copy()
        if "date" in df.columns:
            df.index = pd.to_datetime(df["date"], errors="coerce")
            df.drop(columns=["date"], inplace=True)
        else:
            df.index = pd.to_datetime(df.index, errors="coerce")
        df.sort_index(inplace=True)
        return df

    def _select_accounts(
        self,
        df: pd.DataFrame,
        accounts: Sequence[str],
        company_name: str,
    ) -> pd.DataFrame:
        missing = [code for code in accounts if code not in df.columns]
        if missing:
            raise DomainError(
                f"As seguintes contas não foram encontradas para '{company_name}': {missing}."
            )
        return df.loc[:, list(accounts)].sort_index()

    def _build_series(
        self,
        df: pd.DataFrame,
        ratios_frame,
    ) -> List[AccountSeriesDTO]:
        labels = self._build_labels(df.columns)
        series_list: List[AccountSeriesDTO] = []
        ticker = ratios_frame.ticker or ratios_frame.company_name

        for account_code in df.columns:
            column = df[account_code]
            points: List[AccountSeriesPointDTO] = []
            for index, value in column.items():
                if pd.isna(value):
                    point_value: Optional[float] = None
                else:
                    point_value = float(value)
                if hasattr(index, "date"):
                    date_value = index.date()
                else:
                    date_value = index
                points.append(
                    AccountSeriesPointDTO(
                        date=date_value,
                        value=point_value,
                    )
                )

            series_list.append(
                AccountSeriesDTO(
                    ticker=ticker,
                    account_code=account_code,
                    label=labels.get(account_code, account_code),
                    points=points,
                )
            )

        return series_list

    def _build_labels(self, account_codes: Iterable[str]) -> dict[str, str]:
        if not self.account_labels:
            return {code: code for code in account_codes}
        return {code: self.account_labels.get(code, code) for code in account_codes}
