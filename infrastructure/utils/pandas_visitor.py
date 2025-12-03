# infrastructure/utils/pandas_visitor.py
import pandas as pd
import numpy as np
import re
from typing import Iterable
from .types import ensure_datetime_col, ensure_list_col

class PandasVisitor:
    """Converte Spec -> mask booleana, respeitando tipo da coluna."""
    def visit_and(self, node, df): 
        m = pd.Series(True, index=df.index)
        for it in node.items: m &= it.accept(self, df)
        return m

    def visit_or(self, node, df):
        m = pd.Series(False, index=df.index)
        for it in node.items: m |= it.accept(self, df)
        return m

    def visit_not(self, node, df): 
        return ~node.item.accept(self, df)

    def visit_null(self, node, df):
        s = df[node.field]
        m = s.isna()
        return ~m if node.negate else m

    def visit_cmp(self, node, df):
        s = df[node.field]
        # Datas convertidas quando necessário
        if str(s.dtype).startswith(("datetime", "date")):
            s = ensure_datetime_col(s)
        op, val = node.op, node.value

        if op == "in":
            vals = set(val if isinstance(val, (list, tuple, set)) else [val])
            return s.isin(vals)
        if op == "nin":
            vals = set(val if isinstance(val, (list, tuple, set)) else [val])
            return ~s.isin(vals)
        if op == "between":
            low, high = val
            return s.between(low, high, inclusive="both")
        if op == "==":  return s.eq(val)
        if op == "!=":  return s.ne(val)
        if op == ">":   return s.gt(val)
        if op == ">=":  return s.ge(val)
        if op == "<":   return s.lt(val)
        if op == "<=":  return s.le(val)
        raise ValueError(f"Operador desconhecido: {op}")

    def visit_str(self, node, df):
        s = df[node.field].astype("string")
        if node.mode == "regex":
            return s.str.contains(node.pattern, case=node.case, regex=True, na=node.na)
        if node.mode == "contains":
            return s.str.contains(re.escape(node.pattern), case=node.case, regex=True, na=node.na)
        if node.mode == "startswith":
            return s.str.startswith(node.pattern, na=node.na)
        if node.mode == "endswith":
            return s.str.endswith(node.pattern, na=node.na)
        raise ValueError(f"Modo string desconhecido: {node.mode}")

    def visit_list_any(self, node, df):
        """Suporta listas de strings em JSON. Converte None->[] e padroniza."""
        s = ensure_list_col(df[node.field])
        if node.op == "contains":
            x = str(node.value)
            return s.apply(lambda xs: any(x == str(i) for i in xs))
        if node.op == "in":
            vals = {str(v) for v in (node.value if isinstance(node.value, (list, tuple, set)) else [node.value])}
            return s.apply(lambda xs: any(str(i) in vals for i in xs))
        if node.op == "overlap":
            vals = {str(v) for v in node.value}
            return s.apply(lambda xs: bool(vals.intersection({str(i) for i in xs})))
        raise ValueError(f"Operador lista desconhecido: {node.op}")
