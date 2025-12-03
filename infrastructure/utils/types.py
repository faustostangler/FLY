# infrastructure/utils/types.py
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

def ensure_datetime_col(s: pd.Series) -> pd.Series:
    return s if is_datetime64_any_dtype(s) else pd.to_datetime(s, errors="coerce")

def ensure_list_col(s: pd.Series) -> pd.Series:
    return s.apply(lambda v: v if isinstance(v, (list, tuple)) else ([] if v is None else [v]))
