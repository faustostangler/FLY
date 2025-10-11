from __future__ import annotations

from typing import Iterable, List, Tuple, TypeVar

from sqlalchemy import update
from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.ratio_result_dto import RatioResultDTO
from domain.ports.repository_ratios_port import RepositoryRatiosPort
from infrastructure.models.ratio_metric_model import RatioMetricModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener

T = TypeVar("T")


class RepositoryRatios(RepositoryBase[RatioResultDTO, int], RepositoryRatiosPort):
    """SQLite-backed repository for ratio metrics."""

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config, logger)
        self.config = config
        self.logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        return RatioMetricModel, (RatioMetricModel.id,)

    def save_all(self, items: List[T], *, uow: Uow) -> None:
        if uow is None:
            raise RuntimeError("Ratio repository requires an explicit unit of work")

        session = uow.session
        model, _ = self.get_model_class()
        flat_items = ListFlattener.flatten(items)
        valid_items: Iterable[RatioResultDTO] = [
            i for i in flat_items if isinstance(i, RatioResultDTO)
        ]

        for dto in valid_items:
            obj = model.from_dto(dto)
            data = {c.name: getattr(obj, c.name) for c in model.__table__.columns}

            stmt = insert(model).values(**data)
            update_payload = {
                c.name: getattr(stmt.excluded, c.name)
                for c in model.__table__.columns
                if c.name not in {"id", "version"}
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["company_name", "ratio_code", "date", "version"],
                set_=update_payload,
            )
            session.execute(stmt)

            session.execute(
                update(model)
                .where(
                    model.company_name == dto.company_id,
                    model.ratio_code == dto.ratio_code,
                    model.date == dto.date,
                    model.version != dto.version,
                    model.is_current.is_(True),
                )
                .values(is_current=False)
            )
