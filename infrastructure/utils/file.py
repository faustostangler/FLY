from __future__ import annotations

import csv
import importlib
from dataclasses import asdict, fields, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import (
    Any,
    List,
    Protocol,
    Sequence,
    Type,
    TypeGuard,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    runtime_checkable,
)

T = TypeVar("T", bound="DataclassProtocol")


@runtime_checkable
class DataclassProtocol(Protocol):
    """Structural protocol for the dataclass features we rely on."""

    __dataclass_fields__: dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...


def _is_dataclass_instance(value: Any) -> TypeGuard[DataclassProtocol]:
    """Return True when ``value`` is a dataclass instance."""

    return is_dataclass(value) and not isinstance(value, type)


def _is_dataclass_type(value: Any) -> TypeGuard[type[DataclassProtocol]]:
    """Return True when ``value`` is a dataclass class."""

    return isinstance(value, type) and is_dataclass(value)


def save_list_to_csv(data: Sequence[Any], filepath: str) -> None:
    """Persist a homogeneous sequence (dataclasses, tuples, scalars) to CSV."""

    if not isinstance(data, (list, tuple)):
        raise TypeError("Input deve ser lista ou tupla de DTOs ou valores simples")

    with Path(filepath).open(mode="w", newline="", encoding="utf-8") as file_obj:
        writer = csv.writer(file_obj)

        for item in data:
            if _is_dataclass_instance(item):
                row = list(asdict(cast(Any, item)).values())
            elif isinstance(item, (list, tuple)):
                row = list(item)
            else:
                row = [item]
            writer.writerow(row)

    print("save done")


def read_list_from_csv(filepath: str) -> list[list[str]]:
    """Lê todas as linhas do CSV como tabela (lista de listas de strings)."""

    with Path(filepath).open(mode="r", newline="", encoding="utf-8") as file_obj:
        reader = csv.reader(file_obj)
        result = [row for row in reader if row]
        print("read done")
        return result


# ---------- util de serialização básica ----------
def _to_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _from_cell(cell: str, typ: Any) -> Any:
    if cell == "":
        # tenta None para Optionals
        if get_origin(typ) is type(None) or typ is Any:
            return None
        origin = get_origin(typ)
        if origin is None and typ in (str,):
            return ""
        return None
    origin = get_origin(typ)
    if origin in {list, Sequence}:
        # primeira coluna só armazena escalares; listas exigem outro formato
        return cell  # fallback
    if typ in (str, Any) or origin is str:
        return cell
    if typ in (int,) or origin is int:
        return int(cell)
    if typ in (float,) or origin is float:
        return float(cell)
    if typ in (bool,) or origin is bool:
        return cell.lower() in {"1", "true", "t", "yes", "y"}
    if typ in (datetime,):
        return datetime.fromisoformat(cell)
    if typ in (date,):
        return date.fromisoformat(cell)
    # Optional[T]
    if origin is None and hasattr(typ, "__args__"):
        # typing.Optional é Union[T, NoneType]
        args = get_args(typ)
        non_none = [arg for arg in args if arg is not type(None)]
        if non_none:
            try:
                return _from_cell(cell, non_none[0])
            except Exception:
                return cell
    return cell  # fallback


# ---------- salvar ----------
def save_rows_typed(rows: Sequence[DataclassProtocol], path: str) -> None:
    if not rows:
        return

    first = rows[0]
    if not _is_dataclass_instance(first):
        raise TypeError("save_rows_typed expects dataclass instances")

    dto_type: type[DataclassProtocol] = type(first)
    columns = [field.name for field in fields(cast(Any, dto_type))]

    with open(path, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(columns)
        for row in rows:
            if not _is_dataclass_instance(row):
                raise TypeError("save_rows_typed expects dataclass instances")
            data = asdict(cast(Any, row))
            writer.writerow([data.get(column, "") for column in columns])


# ---------- carregar: modo “sei o tipo” ----------
def load_as(filepath: str, cls: type[T]) -> List[T]:
    """Reconstrói todos os itens como o dataclass informado."""

    if not _is_dataclass_type(cls):
        raise TypeError("load_as requires a dataclass type")

    dataclass_fields = list(fields(cast(Any, cls)))
    output: List[T] = []
    with Path(filepath).open("r", newline="", encoding="utf-8") as file_obj:
        reader = csv.reader(file_obj)
        for row in reader:
            if not row:
                continue
            # se vier com type-tag na primeira coluna, descarte-a
            start = 1 if row[0].count(".") >= 1 and len(row) == len(dataclass_fields) + 1 else 0
            values = [
                _from_cell(row[start + index] if start + index < len(row) else "", field.type)
                for index, field in enumerate(dataclass_fields)
            ]
            output.append(cls(*values))
    return output


# ---------- carregar: modo “auto” ----------
def load_auto(filepath: str) -> List[Any]:
    """Reconstrói itens quando a 1ª coluna é um type-tag fully-qualified."""

    output: List[Any] = []
    with Path(filepath).open("r", newline="", encoding="utf-8") as file_obj:
        reader = csv.reader(file_obj)
        for row in reader:
            if not row:
                continue
            type_tag = row[0]
            if "." in type_tag:
                module_name, class_name = type_tag.rsplit(".", 1)
                try:
                    module = importlib.import_module(module_name)
                    candidate = getattr(module, class_name)
                    if _is_dataclass_type(candidate):
                        dataclass_fields = list(fields(cast(Any, candidate)))
                        values = [
                            _from_cell(row[1 + index] if 1 + index < len(row) else "", field.type)
                            for index, field in enumerate(dataclass_fields)
                        ]
                        output.append(candidate(*values))
                        continue
                except Exception:
                    pass  # fallback para linha crua
            output.append(row)
    return output

