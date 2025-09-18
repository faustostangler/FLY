import csv
from pathlib import Path
from dataclasses import asdict, is_dataclass
from typing import Any, Sequence, Union


# def save_list_to_csv(data: Union[Sequence, str], filepath: str) -> None:
#     """Save list, tuple, or str (split by commas) to CSV file."""
#     if isinstance(data, str):
#         data = [d.strip() for d in data.split(",")]
#     elif not isinstance(data, (list, tuple)):
#         raise TypeError("Input must be list, tuple, or str")
#     with Path(filepath).open(mode="w", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)
#         writer.writerow([[d] for d in data])
#     print('save done')

def save_list_to_csv(data: Union[Sequence[Any], Any], filepath: str) -> None:
    """
    Salva lista de DTOs (dataclasses) ou lista comum em CSV.
    Cada DTO vira uma linha tabular (colunas = campos).
    Listas comuns viram uma linha por item.
    Sem cabeçalho.
    """
    if not isinstance(data, (list, tuple)):
        raise TypeError("Input deve ser lista ou tupla de DTOs ou valores simples")

    with Path(filepath).open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        for item in data:
            if is_dataclass(item):
                row = list(asdict(item).values())
            elif isinstance(item, (list, tuple)):
                row = list(item)
            else:
                row = [item]
            writer.writerow(row)

    print("save done")


def read_list_from_csv(filepath: str) -> list[list[str]]:
    """Lê todas as linhas do CSV como tabela (lista de listas de strings)."""
    with Path(filepath).open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        result = [row for row in reader if row]
        print("read done")
        return result


import csv
import importlib
from dataclasses import asdict, is_dataclass, fields
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, List, Sequence, Type, TypeVar, get_args, get_origin

T = TypeVar("T")

# ---------- util de serialização básica ----------
def _to_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)

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
    if origin is list or origin is Sequence:
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
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            try:
                return _from_cell(cell, non_none[0])
            except Exception:
                return cell
    return cell  # fallback

# ---------- salvar ----------
def save_rows_typed(data: Sequence[Any], filepath: str) -> None:
    """
    Salva uma lista de itens.
    - Se item for dataclass: 1ª coluna = caminho do tipo "pkg.mod.Classe"; demais = valores.
    - Se item for tupla/list: escreve os elementos como colunas.
    - Caso contrário: uma coluna com o valor.
    Sem cabeçalho. Uma linha por item.
    """
    with Path(filepath).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for item in data:
            if is_dataclass(item):
                cls = type(item)
                type_tag = f"{cls.__module__}.{cls.__name__}"
                row = [type_tag] + [_to_cell(v) for v in asdict(item).values()]
                w.writerow(row)
            elif isinstance(item, (list, tuple)):
                w.writerow([_to_cell(v) for v in item])
            else:
                w.writerow([_to_cell(item)])

# ---------- carregar: modo “sei o tipo” ----------
def load_as(filepath: str, cls: Type[T]) -> List[T]:
    """
    Reconstrói todos os itens como o dataclass informado.
    Ignora a 1ª coluna se ela contiver um type-tag.
    """
    flds = [f for f in fields(cls)]
    out: List[T] = []
    with Path(filepath).open("r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            # se vier com type-tag na primeira coluna, descarte-a
            start = 1 if row[0].count(".") >= 1 and len(row) == len(flds) + 1 else 0
            vals = [
                _from_cell(row[start + i] if start + i < len(row) else "", f.type)
                for i, f in enumerate(flds)
            ]
            out.append(cls(*vals))  # dataclasses imutáveis: posicional na ordem dos campos
    return out

# ---------- carregar: modo “auto” ----------
def load_auto(filepath: str) -> List[Any]:
    """
    Reconstrói itens quando a 1ª coluna é um type-tag fully-qualified.
    Linhas sem type-tag retornam como listas de strings.
    """
    out: List[Any] = []
    with Path(filepath).open("r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            type_tag = row[0]
            if "." in type_tag:
                module_name, class_name = type_tag.rsplit(".", 1)
                try:
                    mod = importlib.import_module(module_name)
                    cls = getattr(mod, class_name)
                    if is_dataclass(cls):
                        flds = [f for f in fields(cls)]
                        vals = [
                            _from_cell(row[1 + i] if 1 + i < len(row) else "", f.type)
                            for i, f in enumerate(flds)
                        ]
                        out.append(cls(*vals))
                        continue
                except Exception:
                    pass  # fallback para linha crua
            out.append(row)  # sem type-tag válido: devolve a linha como lista
    return out

# Salvar dataclasses e valores mistos, sem cabeçalho:
# save_rows_typed([dto1, dto2, "foo", (1, 2)], "data.csv")


# Carregar quando você sabe o tipo:
# itens: list[StatementRawDTO] = load_as("data.csv", StatementRawDTO)


# Carregar automaticamente quando salvou com type-tag:
# itens = load_auto("data.csv")
