from __future__ import annotations

from typing import Any, Generic, Iterable, Iterator, TypeVar

T = TypeVar("T")


class ListFlattener(Generic[T]):
    """Recursively flatten a nested sequence of lists into a flat iterator.

    This utility can take arbitrarily nested lists and produce
    a single-level sequence of elements.

    Example:
        >>> ListFlattener.flatten([1, [2, [3, 4]], 5])
        [1, 2, 3, 4, 5]

    Attributes:
        _sequence (Iterable[Any]): The input sequence that may contain nested lists.
    """

    def __init__(self, sequence: Iterable[Any]) -> None:
        """Initialize the flattener with a sequence.

        Args:
            sequence (Iterable[Any]): A sequence that may contain nested lists.
        """
        self._sequence = sequence

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the flattened sequence.

        Yields:
            T: Elements from the sequence, fully flattened.
        """
        yield from self._flatten(self._sequence)

    def _flatten(self, seq: Iterable[Any]) -> Iterator[T]:
        """Recursively flatten a sequence.

        Args:
            seq (Iterable[Any]): A potentially nested list structure.

        Yields:
            T: Individual elements from nested lists in a flat order.
        """
        for elem in seq:
            if isinstance(elem, list):
                yield from self._flatten(elem)
            else:
                # Direct element, yield as is
                yield elem

    @classmethod
    def flatten(cls, sequence: Iterable[Any]) -> list[T]:
        """Flatten a nested sequence and return a list of elements.

        Args:
            sequence (Iterable[Any]): A sequence that may contain nested lists.

        Returns:
            list[T]: A fully flattened list of elements.
        """
        return list(cls(sequence))
