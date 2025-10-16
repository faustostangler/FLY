from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos.statement_ratio_dto import StatementRatioDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementRatioPort(RepositoryBasePort[StatementRatioDTO, int], Protocol):
    """Port definition for persisting Ratio financial statements.

    Extends RepositoryBasePort with methods specific to handling Ratio
    financial statements associated with companies.
    """

