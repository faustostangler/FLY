from __future__ import annotations

from datetime import datetime
from typing import Tuple

from sqlalchemy import select

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.quarter_price_dto import QuarterPriceDTO
from domain.ports.repository_quarter_price_port import RepositoryQuarterPricePort
from infrastructure.models.quarter_price_model import QuarterPriceModel
from infrastructure.repositories.repository_base import RepositoryBase


class QuarterPriceRepository(
    RepositoryBase[QuarterPriceDTO, int], RepositoryQuarterPricePort
):
    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config, logger)
        self.config = config
        self.logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        return QuarterPriceModel, (QuarterPriceModel.id,)

    def insert_or_update(self, dto: QuarterPriceDTO, *, uow: Uow) -> QuarterPriceDTO:
        session = uow.session
        model, _ = self.get_model_class()
        existing = (
            session.query(model)
            .filter(model.company_name == dto.company_name)
            .filter(model.quarter == dto.quarter)
            .filter(model.method == dto.method)
            .one_or_none()
        )
        if existing is None:
            obj = model.from_dto(dto)
            session.add(obj)
            session.flush()
            return obj.to_dto()

        updated = False
        if existing.price != dto.price:
            existing.price = dto.price
            updated = True
        if existing.asof != dto.asof:
            existing.asof = dto.asof
            updated = True
        if existing.currency != dto.currency:
            existing.currency = dto.currency
            updated = True
        if updated:
            existing.version = (existing.version or 0) + 1
        session.flush()
        return existing.to_dto()

    def get_for_quarter(
        self,
        *,
        company_name: str,
        quarter: datetime,
        method: str,
        uow: Uow,
    ) -> QuarterPriceDTO | None:
        session = uow.session
        model, _ = self.get_model_class()
        stmt = (
            select(model)
            .where(model.company_name == company_name)
            .where(model.quarter == quarter)
            .where(model.method == method)
        )
        result = session.execute(stmt).scalar_one_or_none()
        return result.to_dto() if result is not None else None
