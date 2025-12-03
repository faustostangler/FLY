"""Tests for iter_existing_by_columns method."""

from dataclasses import dataclass
from typing import Tuple

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.orm import Session as SASession

from infrastructure.models.base_model import BaseModel
from infrastructure.repositories.sqlalchemy_repository_base import (
    SqlAlchemyRepositoryBase,
)
from tests.conftest import DummyConfig, DummyLogger


@dataclass(frozen=True)
class DummyDTO:
    id: int | None
    name: str | None


class DummyModel(BaseModel):
    __tablename__ = "dummy_model_iter_existing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    @staticmethod
    def from_dto(dto: DummyDTO) -> "DummyModel":
        return DummyModel(id=dto.id, name=dto.name)

    def to_dto(self) -> DummyDTO:
        return DummyDTO(id=self.id, name=self.name)


class DummyRepository(SqlAlchemyRepositoryBase[DummyDTO, int]):
    def get_model_class(self) -> Tuple[type, tuple]:
        return DummyModel, (DummyModel.id,)


@dataclass(frozen=True)
class CompositeDTO:
    part1: int
    part2: int
    value: str


class CompositeModel(BaseModel):
    __tablename__ = "composite_model_iter_existing"

    part1: Mapped[int] = mapped_column(Integer, primary_key=True)
    part2: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[str] = mapped_column(String)

    @staticmethod
    def from_dto(dto: CompositeDTO) -> "CompositeModel":
        return CompositeModel(part1=dto.part1, part2=dto.part2, value=dto.value)

    def to_dto(self) -> CompositeDTO:
        return CompositeDTO(part1=self.part1, part2=self.part2, value=self.value)


class CompositeRepository(SqlAlchemyRepositoryBase[CompositeDTO, tuple[int, int]]):
    def get_model_class(self) -> Tuple[type, tuple]:
        return CompositeModel, (CompositeModel.part1, CompositeModel.part2)


def _setup_repo(repo, engine, SessionLocal) -> None:
    repo.engine = engine
    repo.Session = SessionLocal
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)


def test_iter_existing_by_columns_simple(SessionLocal, engine) -> None:
    cfg = DummyConfig()
    repo = DummyRepository(cfg.database.connection_string, cfg, DummyLogger())
    _setup_repo(repo, engine, SessionLocal)
    items = [DummyDTO(id=i, name=str(i)) for i in range(1, 6)]
    repo.save_all(items)

    result = list(repo.iter_existing_by_columns("id", batch_size=2))
    assert result == [(1,), (2,), (3,), (4,), (5,)]


def test_iter_existing_by_columns_composite(SessionLocal, engine) -> None:
    cfg = DummyConfig()
    repo = CompositeRepository(cfg.database.connection_string, cfg, DummyLogger())
    _setup_repo(repo, engine, SessionLocal)
    items = [
        CompositeDTO(part1=1, part2=1, value="a"),
        CompositeDTO(part1=1, part2=2, value="b"),
        CompositeDTO(part1=2, part2=1, value="c"),
    ]
    repo.save_all(items)

    result = list(repo.iter_existing_by_columns(["part1", "part2"], batch_size=1))
    assert result == [(1, 1), (1, 2), (2, 1)]


def test_iter_existing_by_columns_closes_session_on_break(SessionLocal, engine) -> None:
    cfg = DummyConfig()
    repo = DummyRepository(cfg.database.connection_string, cfg, DummyLogger())
    _setup_repo(repo, engine, SessionLocal)
    repo.save_all([DummyDTO(id=1, name="a"), DummyDTO(id=2, name="b")])

    closed = {"value": False}

    class TrackingSession(SASession):
        def close(self) -> None:  # type: ignore[override]
            closed["value"] = True
            super().close()

    repo.Session = sessionmaker(bind=engine, class_=TrackingSession)

    for _ in repo.iter_existing_by_columns("id", batch_size=1):
        break
    assert closed["value"]


def test_iter_existing_by_columns_null_policy(SessionLocal, engine) -> None:
    cfg = DummyConfig()
    repo = DummyRepository(cfg.database.connection_string, cfg, DummyLogger())
    _setup_repo(repo, engine, SessionLocal)
    repo.save_all(
        [
            DummyDTO(id=1, name="a"),
            DummyDTO(id=2, name=None),
            DummyDTO(id=3, name="b"),
        ]
    )

    result = list(repo.iter_existing_by_columns("name"))
    assert result == [("a",), ("b",)]


def test_iter_existing_by_columns_include_nulls(SessionLocal, engine) -> None:
    cfg = DummyConfig()
    repo = DummyRepository(cfg.database.connection_string, cfg, DummyLogger())
    _setup_repo(repo, engine, SessionLocal)
    repo.save_all(
        [
            DummyDTO(id=1, name="a"),
            DummyDTO(id=2, name=None),
            DummyDTO(id=3, name="b"),
        ]
    )

    result = list(
        repo.iter_existing_by_columns("name", include_nulls=True, batch_size=2)
    )
    assert result == [(None,), ("a",), ("b",)]
