"""SQLAlchemy adapter for raw statement persistence."""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from infrastructure.models.statements_raw_model import StatementRawModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener


class StatementRawRepository(
    RepositoryBase[StatementRawDTO, int],
    RepositoryStatementsRawPort,
):
    """SQLite-backed repository for ``StatementRawDTO`` objects."""

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
        return StatementRawModel, (StatementRawModel.id,)

    def save_all(self, items: List[StatementRawDTO], *, uow: Uow) -> None:
        """Persist raw statements using SQLite upserts."""
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

    def get_by_company_name(self, company_name: str) -> list[StatementRawDTO]:
        """Return raw statement rows for the given company."""
        with self.Session() as session:
            results = (
                session.query(StatementRawModel)
                .filter(StatementRawModel.company_name == company_name)
                .all()
            )
            return [r.to_dto() for r in results]

    def get_company_year_view(
        self,
        *,
        company_name: str,
        year: int,
        uow: Uow,
    ) -> List[StatementRawDTO]:
        """
        Retorna todos os RAW da companhia no ano informado, sem deduplicar por versão.
        Usa a mesma sessão do UoW e ordena de forma estável para a deduplicação no serviço.
        """
        try:
            session = uow.session
            model, _ = self.get_model_class()

            # Filtro por ano a partir de quarter (ISO 'YYYY-MM-DD' compatível com strftime do SQLite).
            year_filter = func.strftime("%Y", getattr(model, "quarter")) == str(year)

            # company filter
            company_filter = getattr(model, "company_name") == company_name

            q = (
                session.query(model)
                .filter(company_filter)
                .filter(year_filter)
            )

            # Ordenação determinística: chave natural + maior versão primeiro + nsd para desempate.
            order_cols = []
            for name in ("account", "quadro", "grupo"):
                if hasattr(model, name):
                    order_cols.append(getattr(model, name))
            if hasattr(model, "version"):
                order_cols.append(getattr(model, "version").desc())
            if hasattr(model, "nsd"):
                order_cols.append(getattr(model, "nsd"))

            if order_cols:
                q = q.order_by(*order_cols)

            rows = q.all()
            return [m.to_dto() for m in rows]
        except Exception as e:
            self.logger.log(
                "get_company_year_view failed",
                extra={"company_name": company_name, "year": year},
            )
            raise
