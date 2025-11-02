"""Processors implement the statement pipelines."""

from legacy.application.processors.base_processor import BaseProcessor
from legacy.application.processors.fetch_statements_processor import (
    FetchStatementsProcessor,
)
from legacy.application.processors.parse_statements_processor import (
    ParseStatementsProcessor,
)
from legacy.application.processors.transform_statements_processor import (
    TransformStatementsProcessor,
)

__all__ = [
    "BaseProcessor",
    "FetchStatementsProcessor",
    "ParseStatementsProcessor",
    "TransformStatementsProcessor",
]
