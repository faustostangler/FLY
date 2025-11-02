"""Repository implementing the eligible companies read/write ports."""

from __future__ import annotations

from typing import Sequence, Tuple

from sqlalchemy import delete
from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.models.company_eligible_model import CompanyEligibleModel


class EligibleCompaniesProjectionRepository(
    RepositoryBase[CompanyEligibleDTO, str],
    CompaniesEligiblePort,
):
    """SQLite-backed repository for the eligible companies projection."""

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
        return CompanyEligibleModel, (CompanyEligibleModel.cvm_code,)

    # # Se o seu RepositoryBase também pede mapeamento DTO<->Model, exponha:
    # def to_model(self, dto: CompanyEligibleDTO) -> CompanyEligibleModel:  # opcional, se o base chamar
    #     return CompanyEligibleModel.from_dto(dto)

    # def to_dto(self, model: CompanyEligibleModel) -> CompanyEligibleDTO:  # opcional, se o base chamar
    #     return model.to_dto()

    def list(
        self,
        *,
        uow: Uow,
        cvm_code: str | None = None,
        company_name: str | None = None,
        segment: str | None = None,
    ) -> list[CompanyEligibleDTO]:
        session: Session = uow.session
        query = session.query(CompanyEligibleModel)

        if cvm_code:
            query = query.filter(CompanyEligibleModel.cvm_code == cvm_code)

        if company_name:
            like = f"%{company_name}%"
            query = query.filter(CompanyEligibleModel.company_name.ilike(like))

        if segment:
            like = f"%{segment}%"
            query = query.filter(
                (CompanyEligibleModel.company_segment.ilike(like))
                | (CompanyEligibleModel.industry_segment.ilike(like))
            )

        query = query.order_by(CompanyEligibleModel.company_name)
        rows = query.all()

        return [row.to_dto() for row in rows]

    def replace_all(
        self,
        items: Sequence[CompanyEligibleDTO],
        *,
        uow: Uow,
    ) -> None:
        session: Session = uow.session

        session.execute(delete(CompanyEligibleModel))

        if items:
            objects = [CompanyEligibleModel.from_dto(item) for item in items]
            session.bulk_save_objects(objects)

        self._logger.log(
            f"Projection proj_eligible_companies replaced with {len(items)} rows",
            level="debug",
        )
