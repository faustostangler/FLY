from typing import Any, Generic, Iterable, Iterator, TypeVar

T = TypeVar("T")


class ListFlattener(Generic[T]):
    """
    Desembrulha recursivamente uma sequência aninhada de listas em um iterador "plano".
    """

    def __init__(self, sequence: Iterable[Any]) -> None:
        self._sequence = sequence

    def __iter__(self) -> Iterator[T]:
        yield from self._flatten(self._sequence)

    def _flatten(self, seq: Iterable[Any]) -> Iterator[T]:
        for elem in seq:
            if isinstance(elem, list):
                yield from self._flatten(elem)
            else:
                yield elem  # assume que elem: T

    @classmethod
    def flatten(cls, sequence: Iterable[Any]) -> list[T]:
        """
        Retorna uma lista com todos os elementos “planos” de sequence.
        """
        return list(cls(sequence))
