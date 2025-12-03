from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from application.dtos.account_series_dto import (
    AccountSeriesDTO,
    AccountSeriesPointDTO,
)
from application.ports.uow_port import UowFactoryPort
from domain.ports.repository_account_series_port import RepositoryAccountSeriesPort
from domain.value_objects.account_code import AccountCode


@dataclass
class GetAccountSeriesUseCase:
    repository: RepositoryAccountSeriesPort
    uow_factory: UowFactoryPort

    def __call__(
        self,
        *,
        ticker: str,
        account_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> AccountSeriesDTO:
        account = AccountCode(account_code)

        with self.uow_factory() as uow:
            points = self.repository.get_account_series(
                ticker=ticker,
                account=account,
                uow=uow,
                start_date=start_date,
                end_date=end_date,
            )
            uow.commit()

        dto_points: List[AccountSeriesPointDTO] = [
            AccountSeriesPointDTO(date=p.date, value=float(p.value)) for p in points
        ]
        dto_points.sort(key=lambda p: p.date)

        label = f"Conta {account.value}"

        return AccountSeriesDTO(
            ticker=ticker,
            account_code=account.value,
            label=label,
            points=dto_points,
        )
