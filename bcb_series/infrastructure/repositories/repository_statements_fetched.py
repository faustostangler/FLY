"""SQLAlchemy adapter for fetched statement persistence."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import Integer, func
from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from infrastructure.models.statements_fetched_model import StatementFetchedModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener


class StatementFetchedRepository(
    RepositoryBase[StatementFetchedDTO, int],
    RepositoryStatementFetchedPort,
):
    """SQLite-backed repository for ``StatementFetchedDTO`` objects."""

    def __init__(
        self, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(config, logger)
        self._config = config
        self._logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return StatementFetchedModel, (StatementFetchedModel.id,)

    def save_all(self, items: List[StatementFetchedDTO], *, uow: Uow) -> None:
        """Persist fetched statements using SQLite upserts."""
        session = uow.session
        model, _ = self.get_model_class()
        flat_items = ListFlattener.flatten(items)
        valid_items = [i for i in flat_items if i is not None]
        for dto in valid_items:
            obj = model.from_dto(dto)
            data = {c.name: getattr(obj, c.name) for c in model.__table__.columns}
            stmt = insert(model).values(**data)
            update_dict = {
                c.name: getattr(stmt.excluded, c.name)
                for c in model.__table__.columns
                if c.name != "id"
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    "nsd",
                    "company_name",
                    "quarter",
                    "version",
                    "grupo",
                    "quadro",
                    "account",
                ],
                set_=update_dict,
            )
            session.execute(stmt)

    def get_by_company_name(self, company_name: str) -> list[StatementFetchedDTO]:
        """Return fetched statement rows for the given company."""
        with self.Session() as session:
            results = (
                session.query(StatementFetchedModel)
                .filter(StatementFetchedModel.company_name == company_name)
                .all()
            )
            return [r.to_dto() for r in results]

    def get_head(self, company: str, *, uow: Uow) -> Optional[tuple[datetime, int]]:
        s = uow.session

        latest_q = (
            s.query(func.max(StatementFetchedModel.quarter))
            .filter(StatementFetchedModel.company_name == company)
            .scalar()
        )
        if latest_q is None:
            return None

        ver_num = func.coalesce(
            func.nullif(StatementFetchedModel.version, ""), "-1"
        ).cast(Integer)

        latest_v = (
            s.query(func.max(ver_num))
            .filter(
                StatementFetchedModel.company_name == company,
                StatementFetchedModel.quarter == latest_q,
            )
            .scalar()
        ) or -1

        return latest_q, int(latest_v)
