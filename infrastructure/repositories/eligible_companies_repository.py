"""Repositories for the eligible companies projection."""

from __future__ import annotations

from typing import Sequence, Tuple

from sqlalchemy import update
from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.dtos.eligible_companies_command_dto import EligibleCompaniesCommandDTO
from domain.dtos.eligible_companies_result_dto import EligibleCompaniesResultDTO
from domain.ports.eligible_companies_read_port import EligibleCompaniesReadPort
from domain.ports.eligible_companies_write_port import EligibleCompaniesWritePort
from infrastructure.models.company_eligible_model import CompanyEligibleModel
from infrastructure.models.company_eligible_projection_model import (
    CompanyEligibleProjectionModel,
)
from infrastructure.repositories.repository_base import RepositoryBase


class EligibleCompaniesReadRepository(
    RepositoryBase[CompanyEligibleDTO, int],
    EligibleCompaniesReadPort,
):
    """Read repository for eligible companies leveraging the shared base class."""

    def __init__(self, *, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config, logger)
        self._logger = logger

    # RepositoryBase requirement -------------------------------------------------
    def get_model_class(self) -> Tuple[type, tuple]:
        return CompanyEligibleModel, (CompanyEligibleModel.id,)

    # Port implementation -------------------------------------------------------
    def get_current(self, *, uow: Uow) -> EligibleCompaniesResultDTO | None:
        session: Session = uow.session
        projection = (
            session.query(CompanyEligibleProjectionModel)
            .filter(CompanyEligibleProjectionModel.is_current.is_(True))
            .one_or_none()
        )
        if not projection:
            return None

        return EligibleCompaniesResultDTO(
            evaluated_count=projection.evaluated_count,
            eligible_count=projection.eligible_count,
            version=projection.version,
            started_at=projection.started_at,
            completed_at=projection.completed_at,
        )

    def list_current_companies(self, *, uow: Uow) -> list[CompanyEligibleDTO]:
        session: Session = uow.session
        rows = (
            session.query(CompanyEligibleModel)
            .filter(CompanyEligibleModel.is_current.is_(True))
            .order_by(CompanyEligibleModel.company_name)
            .all()
        )
        return [row.to_dto() for row in rows]

    def get_by_company_name(
        self,
        company_name: str,
        *,
        uow: Uow,
    ) -> CompanyEligibleDTO | None:
        session: Session = uow.session
        row = (
            session.query(CompanyEligibleModel)
            .filter(
                CompanyEligibleModel.is_current.is_(True),
                CompanyEligibleModel.company_name == company_name,
            )
            .one_or_none()
        )
        return row.to_dto() if row else None


class EligibleCompaniesWriteRepository(
    RepositoryBase[CompanyEligibleDTO, int],
    EligibleCompaniesWritePort,
):
    """Write repository focused on persisting projection versions."""

    def __init__(self, *, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config, logger)

    def get_model_class(self) -> Tuple[type, tuple]:
        return CompanyEligibleModel, (CompanyEligibleModel.id,)

    # Port implementation ------------------------------------------------------
    def save_projection(
        self,
        *,
        uow: Uow,
        command: EligibleCompaniesCommandDTO,
        companies: Sequence[CompanyEligibleDTO],
        result: EligibleCompaniesResultDTO,
    ) -> None:
        session: Session = uow.session

        session.execute(update(CompanyEligibleModel).values(is_current=False))
        session.execute(update(CompanyEligibleProjectionModel).values(is_current=False))

        existing = (
            session.query(CompanyEligibleProjectionModel)
            .filter(CompanyEligibleProjectionModel.version == command.version)
            .one_or_none()
        )

        if existing:
            existing.is_current = True
            session.execute(
                update(CompanyEligibleModel)
                .where(CompanyEligibleModel.projection_version == command.version)
                .values(is_current=True)
            )
            return

        persisted = [
            CompanyEligibleModel.from_dto(item, is_current=True)
            for item in companies
        ]
        if persisted:
            session.bulk_save_objects(persisted)

        projection = CompanyEligibleProjectionModel(
            version=result.version,
            evaluated_count=result.evaluated_count,
            eligible_count=result.eligible_count,
            started_at=result.started_at,
            completed_at=result.completed_at,
            is_current=True,
        )
        session.add(projection)
