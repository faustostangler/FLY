from __future__ import annotations

from datetime import date, datetime, time
from typing import List

from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.entities.account_series import AccountPoint
from domain.ports.repository_account_series_port import RepositoryAccountSeriesPort
from domain.value_objects.account_code import AccountCode
from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.models.account_series_model import FinancialStatementModel


class RepositoryAccountSeries(EngineSetup, RepositoryAccountSeriesPort):
    """Repositório SQLAlchemy para séries temporais de contas contábeis."""

    def __init__(self, *, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config.database.connection_string, logger)

    def get_account_series(
        self,
        *,
        ticker: str,
        account: AccountCode,
        uow: Uow,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> List[AccountPoint]:
        session: Session = uow.session

        query = (
            session.query(FinancialStatementModel)
            .filter(FinancialStatementModel.ticker == ticker)
            .filter(FinancialStatementModel.account_code == account.value)
            .order_by(FinancialStatementModel.reference_date.asc())
        )

        if start_date is not None:
            query = query.filter(
                FinancialStatementModel.reference_date
                >= datetime.combine(start_date, time.min)
            )
        if end_date is not None:
            query = query.filter(
                FinancialStatementModel.reference_date
                <= datetime.combine(end_date, time.max)
            )

        rows = query.all()

        return [
            AccountPoint(
                date=row.reference_date.date()
                if isinstance(row.reference_date, datetime)
                else row.reference_date,
                value=float(row.value) if row.value is not None else 0.0,
            )
            for row in rows
        ]
