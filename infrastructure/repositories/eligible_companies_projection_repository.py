"""Repository implementing the eligible companies read/write ports."""

from __future__ import annotations

from typing import Sequence, Tuple

from sqlalchemy import delete
from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.eligible_company_read_model_dto import EligibleCompanyReadModelDTO
from domain.ports.eligible_companies_port import EligibleCompaniesPort
from infrastructure.repositories.repository_base import RepositoryBase
from infrastructure.models.eligible_company_read_model import EligibleCompanyReadModel


class EligibleCompaniesProjectionRepository(
    RepositoryBase[EligibleCompanyReadModelDTO, str],
    EligibleCompaniesPort,
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
        return EligibleCompanyReadModel, (EligibleCompanyReadModel.cvm_code,)

    # # Se o seu RepositoryBase também pede mapeamento DTO<->Model, exponha:
    # def to_model(self, dto: EligibleCompanyReadModelDTO) -> EligibleCompanyReadModel:  # opcional, se o base chamar
    #     return EligibleCompanyReadModel.from_dto(dto)

    # def to_dto(self, model: EligibleCompanyReadModel) -> EligibleCompanyReadModelDTO:  # opcional, se o base chamar
    #     return model.to_dto()

    def list(
        self,
        *,
        uow: Uow,
        cvm_code: str | None = None,
        company_name: str | None = None,
        segment: str | None = None,
    ) -> list[EligibleCompanyReadModelDTO]:
        session: Session = uow.session
        query = session.query(EligibleCompanyReadModel)

        if cvm_code:
            query = query.filter(EligibleCompanyReadModel.cvm_code == cvm_code)

        if company_name:
            like = f"%{company_name}%"
            query = query.filter(EligibleCompanyReadModel.company_name.ilike(like))

        if segment:
            like = f"%{segment}%"
            query = query.filter(
                (EligibleCompanyReadModel.company_segment.ilike(like))
                | (EligibleCompanyReadModel.industry_segment.ilike(like))
            )

        query = query.order_by(EligibleCompanyReadModel.company_name)
        rows = query.all()

        return [row.to_dto() for row in rows]

    def replace_all(
        self,
        items: Sequence[EligibleCompanyReadModelDTO],
        *,
        uow: Uow,
    ) -> None:
        session: Session = uow.session

        session.execute(delete(EligibleCompanyReadModel))

        if items:
            objects = [EligibleCompanyReadModel.from_dto(item) for item in items]
            session.bulk_save_objects(objects)

        self._logger.log(
            f"Projection proj_eligible_companies replaced with {len(items)} rows",
            level="debug",
        )
