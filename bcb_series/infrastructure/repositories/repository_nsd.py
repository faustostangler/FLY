"""SQLite-backed repository implementation for NSD data."""

from __future__ import annotations

from typing import List, Set, Tuple, TypeVar

from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.nsd_dto import NsdDTO
from domain.ports.repository_nsd_port import RepositoryNsdPort
from infrastructure.models.nsd_model import NSDModel
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.utils.list_flatenner import ListFlattener

T = TypeVar("T")


class RepositoryNsd(RepositoryBase[NsdDTO, int], RepositoryNsdPort):
    """Concrete repository for NsdDTO using SQLite via SQLAlchemy."""

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
        return NSDModel, (NSDModel.id,)

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
                stmt = stmt.on_conflict_do_update(index_elements=["nsd"], set_=update_dict)
                session.execute(stmt)
        except Exception as e:
            self.logger.log(f"Error saving NSD data: {e}", level="error")
            raise

    def get_all_pending(
        self,
        company_names: Set[str],
        valid_types: Set[str],
        exclude_nsd: Set[str],
        *,
        uow: Uow,
    ) -> List[NsdDTO]:
        """Retorna todos os NSDs que ainda não foram processados, filtrando por
        empresa, tipo e NSD.

        Args:
            company_names (Set[str]): Conjunto de nomes de empresas válidas.
            valid_types (Set[str]): Tipos de NSDs aceitos (ex: DFP, ITR...).
            exclude_nsd (Set[str]): Lista de códigos NSD já processados (raw ou fetched).

        Returns:
            List[NsdDTO]: Lista de NSDs pendentes.
        """
        session = uow.session
        query = session.query(NSDModel).filter(
                NSDModel.company_name.in_(company_names),
                NSDModel.nsd_type.in_(valid_types),
                ~NSDModel.nsd.in_(exclude_nsd),
            )
        results = query.all()
        return sorted(
            [nsd.to_dto() for nsd in results],
            key=lambda dto: (dto.company_name, dto.quarter, dto.version),
        )
