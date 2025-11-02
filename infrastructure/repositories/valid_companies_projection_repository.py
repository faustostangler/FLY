"""Repository implementing the valid companies read/write ports."""

from __future__ import annotations

from typing import Sequence, Tuple

from sqlalchemy import delete
from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.valid_company_read_model_dto import ValidCompanyReadModelDTO
from domain.ports.valid_companies_port import ValidCompaniesPort
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.models.valid_company_read_model import ValidCompanyReadModel


class ValidCompaniesProjectionRepository(
    RepositoryBase[ValidCompanyReadModelDTO, str],
    ValidCompaniesPort,
):
    """SQLite-backed repository for the valid companies projection."""

    def __init__(self, *, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config, logger)
        self._config = config
        self._logger = logger

    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the ORM model class and primary key tuple used by this repository.

        Returns:
            Tuple[type, tuple]: A tuple of (model class, primary key columns).
        """
        # Provide the bound model and its primary key columns
        return ValidCompanyReadModel, (ValidCompanyReadModel.id,)

    # # Se o seu RepositoryBase também pede mapeamento DTO<->Model, exponha:
    # def to_model(self, dto: ValidCompanyReadModelDTO) -> ValidCompanyReadModel:  # opcional, se o base chamar
    #     return ValidCompanyReadModel.from_dto(dto)

    # def to_dto(self, model: ValidCompanyReadModel) -> ValidCompanyReadModelDTO:  # opcional, se o base chamar
    #     return model.to_dto()

    def list(
        self,
        *,
        uow: Uow,
        cvm_code: str | None = None,
        company_name: str | None = None,
        segment: str | None = None,
    ) -> list[ValidCompanyReadModelDTO]:
        session: Session = uow.session
        query = session.query(ValidCompanyReadModel)

        if cvm_code:
            query = query.filter(ValidCompanyReadModel.cvm_code == cvm_code)

        if company_name:
            like = f"%{company_name}%"
            query = query.filter(ValidCompanyReadModel.company_name.ilike(like))

        if segment:
            like = f"%{segment}%"
            query = query.filter(
                (ValidCompanyReadModel.company_segment.ilike(like))
                | (ValidCompanyReadModel.industry_segment.ilike(like))
            )

        query = query.order_by(ValidCompanyReadModel.company_name)
        rows = query.all()

        return [row.to_dto() for row in rows]

    def replace_all(
        self,
        items: Sequence[ValidCompanyReadModelDTO],
        *,
        uow: Uow,
    ) -> None:
        session: Session = uow.session

        session.execute(delete(ValidCompanyReadModel))

        if items:
            objects = [ValidCompanyReadModel.from_dto(item) for item in items]
            session.bulk_save_objects(objects)

        self._logger.log(
            f"Projection read_valid_companies replaced with {len(items)} rows",
            level="debug",
        )
