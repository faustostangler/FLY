"""SQLite-backed repository implementation for NSD data."""

from __future__ import annotations

from typing import List, Set, Tuple

from sqlalchemy.dialects.sqlite import insert

from domain.ports import ConfigPort
from domain.dto.nsd_dto import NsdDTO
from domain.ports import LoggerPort, NSDRepositoryPort
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.models.nsd_model import NSDModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyNsdRepository(SqlAlchemyRepositoryBase[NsdDTO, int], NSDRepositoryPort):
    """Concrete repository for NsdDTO using SQLite via SQLAlchemy."""

    def __init__(
        self, database_url: str, config: ConfigPort, logger: LoggerPort
    ) -> None:
        super().__init__(database_url, config, logger)

        self.config = config
        self.logger = logger

    def save_all(self, items: List[NsdDTO]) -> None:
        """Persist ``NsdDTO`` objects using SQLite upserts."""
        session = self.Session()
        try:
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
                    index_elements=["nsd"], set_=update_dict
                )
                session.execute(stmt)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.log(f"Error saving NSD data: {e}", level="error")
            raise
        finally:
            session.close()

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the SQLAlchemy ORM model class managed by this repository.

        Returns:
            type: The model class associated with this repository.
        """
        return NSDModel, (NSDModel.id,)

    def get_all_pending(
        self,
        company_names: Set[str],
        valid_types: Set[str],
        exclude_nsd: Set[str],
    ) -> List[NsdDTO]:
        """Retorna todos os NSDs que ainda não foram processados, filtrando por
        empresa, tipo e NSD.

        Args:
            company_names (Set[str]): Conjunto de nomes de empresas válidas.
            valid_types (Set[str]): Tipos de NSDs aceitos (ex: DFP, ITR...).
            exclude_nsd (Set[str]): Lista de códigos NSD já processados (raw ou parsed).

        Returns:
            List[NsdDTO]: Lista de NSDs pendentes.
        """
        with self.Session() as session:  # <=== aqui está a correção
            query = session.query(NSDModel).filter(
                NSDModel.company_name.in_(company_names),
                NSDModel.nsd_type.in_(valid_types),
                ~NSDModel.nsd.in_(exclude_nsd),
            )
            results = query.all()
        return sorted([nsd.to_dto() for nsd in results], key=lambda dto: int(dto.nsd))
