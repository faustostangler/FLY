"""Utilities for writing DTOs to CSV files."""

import csv
from typing import List


def save_dtos_to_csv(dtos: List, filepath: str) -> None:
    """Save DTOs to ``filepath`` with columns from object attributes."""
    if not dtos:
        raise ValueError("No DTOs provided to save.")

    # Extract field names from the first DTO
    first = dtos[0]
    if hasattr(first, "__dict__"):
        headers = list(vars(first).keys())
    else:
        # Fallback: use dir() to find public attributes
        headers = [
            attr
            for attr in dir(first)
            if not attr.startswith("_") and not callable(getattr(first, attr))
        ]

    # Write CSV
    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for dto in dtos:
            row = {h: getattr(dto, h) for h in headers}
            writer.writerow(row)


# Example usage:
# save_dtos_to_csv(raws_dto, "raws_statements.csv")
