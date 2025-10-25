# infrastructure/repositories/repository_ratios.py
from __future__ import annotations

from typing import List, Tuple
import time
from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.statement_ratio_dto import StatementRatioDTO
from domain.ports.repository_statements_ratio_port import RepositoryStatementRatioPort 
from infrastructure.models.statements_ratio_model import StatementRatioModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener


class StatementRatioRepository(
    RepositoryBase[StatementRatioDTO, int],
    RepositoryStatementRatioPort,
):
    """SQLite-backed repository for ``StatementRatioDTO`` objects."""

    def __init__(
        self, config: ConfigPort, logger: LoggerPort
    ) -> None:
        """Initialize repository with ``config`` and ``logger``."""
        super().__init__(config, logger)
        self.config = config
        self.logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return StatementRatioModel, (StatementRatioModel.id,)

    def save_all(self, items: List[StatementRatioDTO], *, uow: Uow) -> None:
        """Persist Ratio statements using SQLite upserts."""

        session = uow.session
        model, _ = self.get_model_class()

        flat_items = ListFlattener.flatten(items)
        valid_items = [item for item in flat_items if item is not None]
        if not valid_items:
            return

        chunk_size = 10000
        start_time = time.perf_counter()
        for i, dto in enumerate(valid_items):
            if i % chunk_size == 0:
                position = i+chunk_size
                extra_info = {} # {"Item": i, "Total": len(valid_items)}

                # Log Progress
                self.logger.log(
                f"Item {position}",
                    level="info",
                    progress={"index": position, "size": len(valid_items),"start_time": start_time,},
                    extra=extra_info,
                )
            obj = model.from_dto(dto)
            data = {column.name: getattr(obj, column.name) for column in model.__table__.columns}

            stmt = insert(model).values(**data)
            update_dict = {
                column.name: getattr(stmt.excluded, column.name)
                for column in model.__table__.columns
                if column.name != "id"
            }

            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    "nsd",
                    "company_name",
                    "ticker",
                    "date",
                    "grupo",
                    "quadro",
                    "account",
                    "version",
                ],
                set_=update_dict,
            )

            session.execute(stmt)

    def get_by_company_name(
        self, company_name: str, *, uow: Uow
    ) -> list[StatementRatioDTO]:
        """Return Ratio statement rows for the given company."""

        session = uow.session
        results = (
            session.query(StatementRatioModel)
            .filter(StatementRatioModel.company_name == company_name)
            .all()
        )
        return [r.to_dto() for r in results]

