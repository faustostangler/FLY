# infrastructure/cache/ratios_cache.py
from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort

from domain.dtos.cache_ratios_context_dto import CacheRatiosContextDTO
from domain.dtos.cache_ratios_entry_dto import CacheRatiosEntryDTO
from domain.ports.cache_ratios_port import CacheRatiosPort

from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.models.cache_ratios_model import CacheBase, CacheEntry


class CacheRatiosAdapter(CacheRatiosPort, EngineSetup):
    """
    Adaptador de cache para DataFrames de índices/ratios.

    Camada: Infraestrutura.
    Depende de: EngineSetup (injeção da base do cache), pandas, SQLAlchemy.
    Armazena payloads em Parquet; metadados no SQLite dedicado ao cache.
    """

    def __init__(self, *, config: ConfigPort, logger: LoggerPort | None) -> None:
        self._config = config
        self._logger = logger

        # Conexão isolada do cache. NUNCA a mesma do fly.
        # Usa a base declarativa exclusiva do cache para limitar o schema.
        EngineSetup.__init__(
            self,
            connection_string=self._config.database.connection_cache_string,
            logger=logger,
            orm_base=CacheBase,
            create_schema=True,  # materializa apenas o metadata do cache
        )

        # Log defensivo para auditoria
        # if self._logger:
        #     self._logger.log(
        #         f"CacheRatiosAdapter schema materialized | tables=['tbl_cache']",
        #         level="debug",
        #     )

    # ---------- API de porta (CacheRatiosPort) ----------

    def load(self, cache_key: str) -> Optional[Tuple[pd.DataFrame, CacheRatiosEntryDTO]]:
        """
        Busca o entry pelo cache_key. Se o arquivo não existir ou estiver ilegível,
        remove o metadado órfão e retorna None.
        """
        with self.Session() as session:
            entry = session.get(CacheEntry, cache_key)
            if entry is None:
                return None

            file_path = Path(entry.file_path)
            if not file_path.exists():
                self._delete_entry_and_file(session, entry, unlink_file=False)
                return None

            try:
                df = pd.read_parquet(file_path)
            except Exception:
                # Arquivo corrompido. Limpa ambos.
                self._delete_entry_and_file(session, entry, unlink_file=True)
                return None

            # Telemetria de acesso
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            session.add(entry)

            return df, entry.to_dto()

    def store(
        self,
        *,
        context: CacheRatiosContextDTO,
        df: pd.DataFrame,
        company_name: str,
    ) -> CacheRatiosEntryDTO:
        """
        Persiste o DataFrame em Parquet com flush/fsync atômico e grava metadados.
        Atualiza acessos e executa políticas de invalidação/evicção.
        """
        # Caminho final (.parquet) e temporário (.tmp)
        file_path = self._build_file_path(context=context, company_name=company_name)
        file_path = Path(file_path)  # defesa: garante Path
        temp_path = file_path.with_suffix(".tmp")

        # Garante que o diretório pai do TEMP existe
        parent_dir = temp_path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        # Log defensivo de caminho
        if self._logger:
            self._logger.log(
                f"[CacheRatiosAdapter.store] "
                f"company={company_name!r} cache_key={context.cache_key} "
                f"temp_path={temp_path} parent_exists={parent_dir.exists()}",
                level="info",
            )

        # Escrita atômica do payload
        df.to_parquet(
            temp_path,
            compression=str(self._config.cache.parquet_compression),  # type: ignore[arg-type]
        )
        with temp_path.open("rb+") as handle:
            handle.flush()
            os.fsync(handle.fileno())

        size_bytes = temp_path.stat().st_size
        now = datetime.now()

        try:
            with self.Session.begin() as session:
                entry = session.get(CacheEntry, context.cache_key)
                if entry is None:
                    entry = CacheEntry(
                        cache_key=context.cache_key,
                        file_path=str(file_path),
                        size_bytes=size_bytes,
                        created_at=now,
                        accessed_at=now,
                        access_count=1,
                        code_hash=context.code_hash,
                    )
                    session.add(entry)
                else:
                    entry.file_path = str(file_path)
                    entry.size_bytes = size_bytes
                    entry.created_at = now
                    entry.accessed_at = now
                    entry.access_count = 1
                    entry.code_hash = context.code_hash
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

        # Move atômico depois do metadado persistido
        try:
            temp_path.replace(file_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            # rollback lógico do metadado
            with self.Session.begin() as session:
                stale = session.get(CacheEntry, context.cache_key)
                if stale is not None:
                    session.delete(stale)
            raise

        entry_dto = CacheRatiosEntryDTO(
            cache_key=context.cache_key,
            file_path=str(file_path),
            size_bytes=size_bytes,
            created_at=now,
            accessed_at=now,
            access_count=1,
            code_hash=context.code_hash,
        )

        # Políticas de manutenção
        self.invalidate_outdated(code_hash=context.code_hash)
        self._evict_cache_if_needed()

        return entry_dto

    def invalidate_outdated(self, *, code_hash: str) -> None:
        """
        Remove entradas antigas por versão de código (code_hash) ou por idade máxima.
        """
        cutoff: datetime = datetime.now() - self._config.cache.max_age
        with self.Session.begin() as session:
            rows = session.scalars(
                select(CacheEntry).where(
                    (CacheEntry.code_hash != code_hash) | (CacheEntry.accessed_at < cutoff)
                )
            ).all()
            for row in rows:
                Path(row.file_path).unlink(missing_ok=True)
                session.delete(row)

    # ---------- Internals ----------

    def _evict_cache_if_needed(self) -> None:
        with self.Session.begin() as session:
            total_size = session.execute(select(func.coalesce(func.sum(CacheEntry.size_bytes), 0))).scalar_one()
            budget = int(self._config.cache.max_cache_size_bytes)
            if total_size <= budget:
                return

            # LFU + FIFO: menos acessado primeiro; em empate, mais antigo primeiro
            victims = session.scalars(
                select(CacheEntry).order_by(
                    CacheEntry.access_count.asc(),
                    CacheEntry.created_at.asc(),
                )
            )
            for v in victims:
                if total_size <= budget:
                    break
                Path(v.file_path).unlink(missing_ok=True)
                total_size -= v.size_bytes
                session.delete(v)

    def _delete_entry_and_file(self, session: Session, entry: CacheEntry, *, unlink_file: bool) -> None:
        if unlink_file:
            Path(entry.file_path).unlink(missing_ok=True)
        session.delete(entry)

    def _build_file_path(self, *, context: CacheRatiosContextDTO, company_name: str) -> Path:
        """
        Retorna um caminho simples para o Parquet dentro da hierarquia de cache.

        Estrutura:

            <cache_dir>/<empresa-normalizada>/<cache_key>.parquet

        Onde:
          - cache_dir vem de config.paths.cache_dir
          - empresa-normalizada é o nome sanitizado da companhia
          - cache_key garante unicidade por versão e snapshot de dados
        """
        base_dir = Path(self._config.paths.cache_dir)

        safe_company = self._sanitize_company_name(company_name)

        target_dir = base_dir / safe_company
        target_dir.mkdir(parents=True, exist_ok=True)

        return target_dir / f"{context.cache_key}.parquet"

    def _sanitize_company_name(self, company_name: str) -> str:
        normalized = unicodedata.normalize("NFKD", company_name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        cleaned = re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-")
        return cleaned[:120] if cleaned else "unknown"

