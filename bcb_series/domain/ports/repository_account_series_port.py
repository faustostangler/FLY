from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List

from application.ports.uow_port import Uow
from domain.entities.account_series import AccountPoint
from domain.value_objects.account_code import AccountCode


class RepositoryAccountSeriesPort(ABC):
    """Porta de repositório para séries temporais de contas contábeis."""

    @abstractmethod
    def get_account_series(
        self,
        *,
        ticker: str,
        account: AccountCode,
        uow: Uow,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> List[AccountPoint]:
        """Retorna série temporal de uma conta para um ticker."""
