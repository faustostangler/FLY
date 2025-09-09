import csv
from pathlib import Path
from typing import Sequence, Union

def save_list_to_csv(data: Union[Sequence, str], filepath: str) -> None:
    """Save list, tuple, or str (split by commas) to CSV file."""
    if isinstance(data, str):
        data = [d.strip() for d in data.split(",")]
    elif not isinstance(data, (list, tuple)):
        raise TypeError("Input must be list, tuple, or str")
    with Path(filepath).open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data)
    print('save done')

def read_list_from_csv(filepath: str) -> list[str]:
    """Read first row of CSV file into list of strings."""
    with Path(filepath).open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:   # read only first line
            print("read done")
            return row
    return []
