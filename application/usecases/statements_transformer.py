from __future__ import annotations

from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.ports.datacleaner_port import DataCleanerPort


class StatementTransformer:
    """Transforms raw financial statements into fetched statements.

    This class uses a data cleaner to sanitize raw statements
    and generates a fetched DTO ready for persistence.

    Attributes:
        cleaner (DataCleanerPort): Component responsible for cleaning
            and normalizing raw statement data.
    """

    def __init__(self, cleaner: DataCleanerPort) -> None:
        # Data cleaner used for preprocessing statements
        self.cleaner = cleaner

    def transform(self, raw: StatementRawDTO) -> StatementFetchedDTO:
        """Convert a raw statement into a fetched statement.

        Args:
            raw (StatementRawDTO): Raw financial statement input.

        Returns:
            StatementFetchedDTO: Structured and cleaned statement.
        """
        # normaliza textos
        company = self.cleaner.clean_text(raw.company_name or "") if hasattr(self.cleaner, "clean_text") else (raw.company_name or "")
        grupo = self.cleaner.clean_text(raw.grupo) if hasattr(self.cleaner, "clean_text") else raw.grupo
        quadro = self.cleaner.clean_text(raw.quadro) if hasattr(self.cleaner, "clean_text") else raw.quadro
        account = self.cleaner.clean_text(raw.account) if hasattr(self.cleaner, "clean_text") else raw.account
        description = self.cleaner.clean_text(raw.description) if hasattr(self.cleaner, "clean_text") else raw.description

        # quarter permanece string; o normalizer já converte para YYYY-MM quando aplicável
        quarter = raw.quarter
        version = str(raw.version) if raw.version is not None else None

        fetched = StatementFetchedDTO(
            id=None,
            nsd=str(raw.nsd),
            company_name=company or None,
            quarter=quarter,
            version=version,
            grupo=grupo or "",
            quadro=quadro or "",
            account=account or "",
            description=description or "",
            value=float(raw.value),
        )

        return fetched
