"""SQLite-backed repository implementation for NSD data."""

from __future__ import annotations

from typing import List, Set, Tuple, TypeVar

from sqlalchemy import func
from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from infrastructure.models.stock_quote_model import StockQuoteModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener

T = TypeVar("T")


class RepositoryStockQuote(RepositoryBase[StockQuoteDTO, int], RepositoryStockQuotePort):
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
        return StockQuoteModel, (StockQuoteModel.id,)

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

    def get_last_date(self, *, ticker: str, uow: Uow):
        """Retorna a última data persistida para o ticker ou None se não houver histórico."""
        session = uow.session
        model, _ = self.get_model_class()
        return (
            session.query(func.max(model.date))
            .filter(model.ticker == ticker)
            .scalar()
        )

    def get_history(
        self,
        *,
        ticker: str,
        limit: int | None,
        uow: Uow,
    ) -> list[StockQuoteDTO]:
        session = uow.session
        model, _ = self.get_model_class()

        query = (
            session
            .query(model)
            .filter(model.ticker == ticker)
            .order_by(model.date.asc())
        )
        if limit is not None:
            query = query.limit(limit)

        rows = query.all()
        return [row.to_dto() for row in rows]
