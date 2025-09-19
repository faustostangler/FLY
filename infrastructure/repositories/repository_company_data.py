from __future__ import annotations

import json
import re
from typing import List, Optional, Sequence, Tuple

from sqlalchemy.dialects.sqlite import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.market_symbol_dto import MarketSymbolsDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from infrastructure.models.company_data_model import CompanyDataModel
from infrastructure.repositories.repository_base import RepositoryBase

# from infrastructure.uils.list_flattener import ListFlattener


class RepositoryCompanyData(
    RepositoryBase[CompanyDataDTO, int], RepositoryCompanyDataPort
):
    """SQLite/SQLAlchemy repository for company data.

    Implements the `RepositoryCompanyDataPort` using a local SQLite database
    with SQLAlchemy Core/ORM.

    Notes:
        - Uses `check_same_thread=False` in the engine (configured upstream) to enable
          multi-threaded access. Sessions must not be shared across threads.
        - Enables Write-Ahead Logging (WAL) at the engine level to improve concurrent
          read/write behavior.

    Args:
        config (ConfigPort): Configuration provider used by the base repository.
        logger (LoggerPort): Logger provider used for diagnostics.

    """

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        """Initialize the repository with configuration and logger.

        Args:
            config (ConfigPort): Application configuration port.
            logger (LoggerPort): Application logger port.
        """
        # Initialize base repository infrastructure (engine, Session, etc.)
        super().__init__(config, logger)

        # Keep references for convenience inside repository methods
        self.config = config
        self.logger = logger

    # Provide a canonical factory the rest of infra can depend on.
    def get_model_class(self) -> Tuple[type, tuple]:
        """Return the ORM model class and primary key tuple used by this repository.

        Returns:
            Tuple[type, tuple]: A tuple of (model class, primary key columns).
        """
        # Provide the bound model and its primary key columns
        return CompanyDataModel, (CompanyDataModel.id,)

    def save_all(self, items: List[CompanyDataDTO], *, uow: Uow) -> None:
        """Upsert all provided `CompanyDataDTO` items into SQLite.

        Performs batched upserts using `INSERT ... ON CONFLICT DO UPDATE` keyed on
        `company_name`. Commits once at the end for consistency.

        Args:
            items (List[CompanyDataDTO]): Collection of DTOs to persist.

        Raises:
            Exception: Propagates any database or data-mapping errors after logging.

        Notes:
            - This method expects a `ListFlattener.flatten` utility. If it is not
              available/imported, a `NameError` will occur. Ensure the import
              `from infrastructure.uils.list_flattener import ListFlattener`
              is enabled or provide an equivalent flattener.
        """
        # Create a short-lived session for this unit of work
        session = uow.session

        # Resolve ORM model and primary key columns
        model, pk_columns = self.get_model_class()

        # Normalize potentially nested inputs into a flat list
        flat_items = items  # ListFlattener.flatten(items)

        # Filter out `None` values to avoid mapping errors
        valid_items = [i for i in flat_items if i is not None]

        # Upsert each DTO using a deterministic conflict target
        for dto in valid_items:
            # Convert DTO into ORM instance
            obj = model.from_dto(dto)

            # Build a plain dict for SQLAlchemy Core insert
            data = {c.name: getattr(obj, c.name) for c in model.__table__.columns}

            # Prepare an INSERT statement with all fields
            stmt = insert(model).values(**data)

            # Define update payload excluding the PK
            update_dict = {
                c.name: getattr(stmt.excluded, c.name)
                for c in model.__table__.columns
                if c.name != "id"
            }

            # Apply ON CONFLICT DO UPDATE on a unique business key
            stmt = stmt.on_conflict_do_update(
                index_elements=["company_name"], set_=update_dict
            )

            # Execute the upsert operation
            session.execute(stmt)

        # Commit the transaction once after processing all items
        session.commit()

        # Intentionally disabled noisy lifecycle log; re-enable if needed.
        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def get_cvm_by_name(self, company_name: str, *, uow: Uow) -> Optional[str]:
        """Look up the CVM code for a company by its name.

        Args:
            company_name (str): Exact company name to search.

        Returns:
            str: The CVM code associated with the company.

        Raises:
            ValueError: If the company name is not found.
        """
        # Create a short-lived session for this query
        session = uow.session

        # Query only the needed column for efficiency
        row = (
            session.query(CompanyDataModel.cvm_code)
            .filter(CompanyDataModel.company_name == company_name)
            .one_or_none()
        )

        return row[0] if row else None

    @staticmethod
    def _normalize_symbol(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).upper().strip()
        if not cleaned:
            return None
        cleaned = re.sub(r"[^A-Z0-9]", "", cleaned)
        if cleaned.endswith("F") and any(ch.isdigit() for ch in cleaned[:-1]):
            cleaned = cleaned[:-1]
        return cleaned or None

    @classmethod
    def _split_codes(cls, raw: Optional[str]) -> List[str]:
        if raw is None:
            return []
        raw = str(raw).strip()
        if raw == "":
            return []

        items: List[str] = []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            tokens = re.split(r"[,;/\s]+", raw)
            items.extend(token for token in tokens if token)
        else:
            if isinstance(parsed, list):
                items.extend(str(item) for item in parsed if item)
            elif isinstance(parsed, str):
                items.append(parsed)
            elif parsed is not None:
                items.append(str(parsed))

        normalized: List[str] = []
        seen = set()
        for item in items:
            symbol = cls._normalize_symbol(item)
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            normalized.append(symbol)
        return normalized

    @staticmethod
    def _score_symbol(symbol: str, index: int) -> tuple[int, int, int, str]:
        digits = "".join(ch for ch in symbol if ch.isdigit())
        suffix_two = digits[-2:] if len(digits) >= 2 else ""
        suffix_one = digits[-1] if digits else ""

        rank = 5
        if suffix_one == "3":
            rank = 0
        elif suffix_one == "4":
            rank = 1
        elif suffix_two == "11":
            rank = 2
        elif suffix_one == "5":
            rank = 3
        elif suffix_one == "6":
            rank = 4

        penalty = 1 if suffix_one and symbol.endswith("F") else 0
        return rank, penalty, index, symbol

    @classmethod
    def _ordered_candidates(cls, candidates: Sequence[str]) -> List[str]:
        scored = [
            cls._score_symbol(symbol, idx) for idx, symbol in enumerate(candidates)
        ]
        scored.sort()
        return [item[-1] for item in scored]

    @classmethod
    def _extract_root(cls, value: Optional[str]) -> Optional[str]:
        normalized = cls._normalize_symbol(value)
        if not normalized:
            return None
        for idx, char in enumerate(normalized):
            if char.isdigit():
                return normalized[:idx] or None
        return normalized

    def get_market_symbol(
        self, nsd: str | int, company_name: str, *, uow: Uow
    ) -> Optional[MarketSymbolsDTO]:
        session = uow.session
        _ = nsd  # mantido para compatibilidade futura com códigos distintos
        row = (
            session.query(
                CompanyDataModel.code,
                CompanyDataModel.ticker_codes,
                CompanyDataModel.issuing_company,
            )
            .filter(CompanyDataModel.company_name == company_name)
            .one_or_none()
        )
        if not row:
            return None

        code, tickers, issuing = row

        primary_candidates = self._split_codes(tickers)

        fallback_codes: List[str] = []
        fallback_codes.extend(self._split_codes(code))
        fallback_codes.extend(self._split_codes(issuing))
        for candidate in fallback_codes:
            if candidate not in primary_candidates:
                primary_candidates.append(candidate)

        ordered = (
            self._ordered_candidates(primary_candidates) if primary_candidates else []
        )
        primary = ordered[0] if ordered else None

        root_candidates = list(self._split_codes(issuing)) + list(
            self._split_codes(code)
        )
        root = None
        for candidate in ordered + root_candidates:
            root = self._extract_root(candidate)
            if root:
                break

        return MarketSymbolsDTO(primary=primary, tickers=tuple(ordered), b3_root=root)
