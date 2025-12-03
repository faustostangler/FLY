from __future__ import annotations

from typing import Iterable, Iterator, Sequence, TypeVar

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from infrastructure.utils.list_flatenner import ListFlattener

T = TypeVar("T")


def iter_valid_dtos(items: Iterable[T]) -> Iterator[T]:
    """Yield non-``None`` DTOs from possibly nested iterables.

    The repository layer frequently receives nested lists produced by
    upstream batching helpers. This utility centralises the flattening
    and ``None`` filtering rules to keep repositories focused on the
    persistence logic itself.
    """

    for item in ListFlattener.flatten(items):
        if item is not None:
            yield item


def execute_sqlite_upsert(
    session: Session,
    model: type,
    dto: T,
    *,
    conflict_columns: Sequence[str],
    skip_update_columns: Iterable[str] = (),
) -> None:
    """Execute a deterministic SQLite upsert for the given DTO.

    Args:
        session: Active SQLAlchemy session provided by the UoW.
        model: ORM model that exposes ``from_dto`` and ``__table__`` metadata.
        dto: Domain transfer object to persist.
        conflict_columns: Natural key identifying the upsert target.
        skip_update_columns: Columns that must not be updated during conflicts
            (e.g. auto-increment identifiers or audit fields).
    """

    obj = model.from_dto(dto)
    data = {column.name: getattr(obj, column.name) for column in model.__table__.columns}

    stmt = insert(model).values(**data)

    excluded = stmt.excluded
    skip_set = set(skip_update_columns)
    update_dict = {
        column.name: getattr(excluded, column.name)
        for column in model.__table__.columns
        if column.name not in skip_set
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=list(conflict_columns),
        set_=update_dict,
    )

    session.execute(stmt)
