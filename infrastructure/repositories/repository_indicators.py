"""SQLite-backed repository implementation for NSD data."""

from __future__ import annotations

from typing import List, Set, Tuple, TypeVar

from sqlalchemy import func
from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.indicators_dto import IndicatorsDTO
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from infrastructure.models.indicators_model import IndicatorModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener

T = TypeVar("T")


class RepositoryIndicators(RepositoryBase[IndicatorsDTO, int], RepositoryIndicatorsPort):
    """Concrete repository for DTO using SQLite via SQLAlchemy."""

    def __init__(
        self, config: ConfigPort, logger: LoggerPort
    ) -> None:
        super().__init__(config, logger)

        self.config = config
        self.logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return IndicatorModel, (IndicatorModel.id,)

    def save_all(self, items: List[T], *, uow: Uow) -> None:
        """Persist ``NsdDTO`` objects using SQLite upserts.
        Se receber uma sessão externa, participa dela sem dar commit próprio.
        """
        try:
            session = uow.session
            model, pk_columns = self.get_model_class()

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
                    index_elements=["ticker", "date"],
                    set_=update_dict,
                )
                session.execute(stmt)
        except Exception as e:
            self.logger.log(f"Error saving NSD data: {e}", level="error")
            raise

