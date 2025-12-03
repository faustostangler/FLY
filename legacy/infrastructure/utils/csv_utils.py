import csv
from typing import Any, Sequence


def save_dtos_to_csv(dtos: Sequence[Any], filepath: str) -> None:
    """
    Save any list of DTOs to a CSV file. Each attribute of the DTO becomes a column.

    Args:
        dtos (List): A list of objects with __dict__ attribute (e.g., dataclass instances).
        filepath (str): Destination CSV file path.
    """
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
