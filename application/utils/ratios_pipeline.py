from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Iterable, List, Mapping

import numpy as np
import pandas as pd

import domain.utils.intel as intel


def load_indicators(repository_indicators, *, uow) -> dict[str, pd.DataFrame]:
    indicators: dict[str, pd.DataFrame] = {}

    rows = repository_indicators.get_all(uow=uow)
    if not rows:
        return indicators

    indicators_df = pd.DataFrame(rows)
    indicators_df["date"] = pd.to_datetime(indicators_df["date"], errors="coerce")
    indicators_df["value"] = pd.to_numeric(indicators_df["value"], errors="coerce")
    indicators_df.sort_values(["code", "name", "date"], inplace=True)
    indicators_df = indicators_df.dropna(subset=["date"]).reset_index(drop=True)

    for (source, code), group in indicators_df.groupby(["source", "code"]):
        pivot = (
            group.pivot_table(
                index="date",
                columns="name",
                values="value",
                aggfunc="last",
            )
            .sort_index()
            .reset_index()
        )
        indicators[str(code)] = pivot

    return indicators


def load_statements(repository_statements_fetched, company_name: str, *, uow) -> dict[str, pd.DataFrame]:
    statements_df: dict[str, pd.DataFrame] = {}
    rows = repository_statements_fetched.get_by_column_values(
        values=[("company_name", company_name)],
        uow=uow,
    )
    if not rows:
        return statements_df

    def _build_set(df: pd.DataFrame, use_other: bool, df_other: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        parts = [df]
        if use_other and df_other is not None and not df_other.empty:
            parts.append(df_other)
        out = pd.concat(parts, ignore_index=True)
        return out.sort_values(["quarter", "account"], kind="mergesort").reset_index(drop=True)

    statements = pd.DataFrame(rows)
    statements["quarter"] = pd.to_datetime(statements["quarter"], errors="coerce")
    statements["value"] = pd.to_numeric(statements["value"], errors="coerce")
    statements["version_numeric"] = pd.to_numeric(statements["version"], errors="coerce").fillna(-1)
    statements.sort_values(["company_name", "quarter", "version_numeric"], inplace=True)
    df = statements.dropna(subset=["quarter"]).reset_index(drop=True)

    mask = df["version_numeric"] == df.groupby("quarter")["version_numeric"].transform("max")
    df = df[mask].reset_index(drop=True)

    if "grupo" not in df.columns:
        raise ValueError("coluna 'grupo' ausente")

    df_ind0 = df[df["grupo"] == "DFs Individuais"]
    df_con0 = df[df["grupo"] == "DFs Consolidadas"]
    df_other = df[~df["grupo"].isin(["DFs Individuais", "DFs Consolidadas"])].drop(columns=[], errors="ignore")

    has_ind = not df_ind0.empty
    has_con = not df_con0.empty
    has_other = not df_other.empty

    if has_con:
        statements_df["statements"] = _build_set(df_con0, has_other and has_con, df_other)
    else:
        statements_df["statements"] = _build_set(df_ind0, has_other and has_ind, df_other)

    if has_con:
        statements_df["df_consolidadas"] = _build_set(df_con0, has_other and has_con, df_other)
    if has_ind:
        statements_df["df_individuais"] = _build_set(df_ind0, has_other and has_ind, df_other)

    return statements_df


def load_quotes(repository_stock_quote, ticker_codes: Iterable[str], *, uow) -> dict[str, pd.DataFrame]:
    quotes_df: dict[str, pd.DataFrame] = {}
    for ticker in ticker_codes:
        rows = repository_stock_quote.get_by_column_values(values=[("ticker", ticker)], uow=uow)
        if not rows:
            continue

        quotes = pd.DataFrame(rows)
        quotes["date"] = pd.to_datetime(quotes["date"], errors="coerce")
        numeric_cols = ["open", "low", "high", "close", "adj_close", "volume"]
        for col in numeric_cols:
            quotes[col] = pd.to_numeric(quotes[col], errors="coerce")
        quotes.sort_values(["ticker", "date"], inplace=True)

        m = re.search(r"\d+$", ticker)
        digit = m.group() if m else ""
        key = f"stock_{digit}" if digit else f"stock_{len(quotes_df)+1}"
        quotes_df[key] = quotes.dropna(subset=["date"]).reset_index(drop=True)

    return quotes_df


def treat_quotes(q: pd.DataFrame, calendar: pd.DataFrame | None = None) -> pd.DataFrame:
    if "date" in q.columns:
        q["date"] = pd.to_datetime(q["date"])
        q = q.sort_values("date").drop_duplicates(subset=["date"]).set_index("date")
    else:
        q.index = pd.to_datetime(q.index)
        q = q.sort_index().drop_duplicates()

    if calendar is not None and not calendar.empty:
        q = q.sort_index().reindex(calendar.index, method="ffill")
        if q.iloc[0].isna().any():
            q = q.bfill()

    return q


def treat_statements(s: pd.DataFrame, calendar: pd.DataFrame | None = None) -> pd.DataFrame:
    s["quarter"] = pd.to_datetime(s["quarter"])

    key_columns = ["company_name", "quarter", "account"]
    s["account_description"] = (
        s["account"] + " - " + s["description"] + " - " + s["grupo"] + " - " + s["quadro"]
    )

    context_columns = ["nsd", "company_name", "version"]
    meta = (
        s[["quarter"] + context_columns]
        .drop_duplicates(subset=["quarter"], keep="last")
        .set_index("quarter")
    )

    s = s.sort_values(key_columns)
    s = s.drop_duplicates(subset=key_columns, keep="last")
    s = (
        s.pivot_table(
            index=["quarter"],
            columns="account_description",
            values="value",
            aggfunc="last",
        )
        .sort_index()
    )
    s.columns.name = None

    s = meta.join(s, how="right")

    if calendar is not None:
        s = s.copy()
        s = s.reset_index()

        s["quarter"] = pd.to_datetime(s["quarter"])
        s = (
            s.rename(columns={"quarter": "date"})
            .set_index("date")
            .sort_index()
        )

        s = s.reindex(calendar.index, method="ffill")
        if s.iloc[0].isna().any():
            s = s.bfill()

        s = s.set_index(context_columns, append=True).sort_index()

    return s


def treat_indicators(i: pd.DataFrame, calendar: pd.DataFrame | None = None) -> pd.DataFrame:
    if calendar is None:
        i["date"] = pd.to_datetime(i["date"])
        i = i.sort_values("date").drop_duplicates(subset=["date"]).set_index("date")
    else:
        i = i.sort_index().reindex(calendar.index, method="ffill")
        if i.iloc[0].isna().any():
            i = i.bfill()

    return i


def _get_stock_calendar(data: dict[str, dict[str, pd.DataFrame]], cutoff: datetime) -> pd.DatetimeIndex:
    stock_calendar = pd.DatetimeIndex([])
    data_quotes = data.get("quotes", {})
    if data_quotes:
        for dfq in data_quotes.values():
            if isinstance(dfq, pd.DataFrame) and "date" in dfq.columns and not dfq.empty:
                stock_calendar = pd.to_datetime(dfq["date"], errors="coerce")
                stock_calendar = pd.DatetimeIndex(stock_calendar).tz_localize(None)
                stock_calendar = stock_calendar[~stock_calendar.isna()]
                stock_calendar = stock_calendar[stock_calendar > cutoff]
                break

    return stock_calendar


def _create_daily_calendar(data: dict[str, dict[str, pd.DataFrame]], cutoff: datetime) -> pd.DatetimeIndex:
    date_min = cutoff
    date_max = pd.Timestamp.now()
    data_quotes = data.get("quotes", {})
    data_statements = data.get("statements", {})
    data_indicators = data.get("indicators", {})

    if data_quotes:
        mins: List[pd.Timestamp] = []
        maxs: List[pd.Timestamp] = []
        for dfq in data_quotes.values():
            if isinstance(dfq, pd.DataFrame) and "date" in dfq.columns and not dfq.empty:
                dts = pd.to_datetime(dfq["date"], errors="coerce")
                dts = pd.DatetimeIndex(dts).tz_localize(None)
                dts = dts[~dts.isna()]
                if len(dts):
                    mins.append(dts.min())
                    maxs.append(dts.max())
        if mins:
            date_min = min(mins)
        if maxs:
            date_max = max(maxs)

    if date_min == cutoff and data_statements:
        statements = data_statements.get("statements")
        if statements is not None and not statements.empty and "quarter" in statements.columns:
            dates = pd.to_datetime(statements["quarter"].unique())
            date_min = dates.min().tz_localize(None)
            date_max = dates.max().tz_localize(None)

    if date_min == cutoff and data_indicators:
        mins = []
        maxs = []
        for dfi in data_indicators.values():
            if isinstance(dfi, pd.DataFrame) and not dfi.empty:
                dts = pd.to_datetime(dfi.index, errors="coerce").tz_localize(None)
                dts = dts[~dts.isna()]
                if len(dts):
                    mins.append(dts.min())
                    maxs.append(dts.max())
        if mins:
            date_min = min(mins)
        if maxs:
            date_max = max(maxs)

    start = max(date_min, pd.Timestamp(cutoff)) + pd.Timedelta(days=1)
    end = max(date_max, pd.Timestamp.now()) - pd.Timedelta(days=1)

    if start > end:
        start = end - pd.Timedelta(days=365)

    return pd.date_range(start=start, end=end, freq="B")


def _create_calendar(
    data: dict[str, dict[str, pd.DataFrame]],
    cutoff: datetime,
    *,
    granularity: str = "day",
) -> pd.DataFrame:
    calendar_index = _create_daily_calendar(data, cutoff)
    if granularity == "day":
        df_calendar = pd.DataFrame(index=calendar_index)
    else:
        stock_calendar = _get_stock_calendar(data, cutoff)
        if stock_calendar.empty:
            df_calendar = pd.DataFrame(index=calendar_index)
        else:
            df_calendar = pd.DataFrame(index=stock_calendar)

    df_calendar.index.name = "date"
    return df_calendar


def _infer_granularity(idx: pd.Index) -> str:
    if not isinstance(idx, pd.DatetimeIndex):
        try:
            idx = pd.to_datetime(idx, errors="coerce")
            idx = idx[~idx.isna()]
            if len(idx) < 2:
                return "unknown"
        except Exception:
            return "unknown"

    inferred_freq = pd.infer_freq(idx)
    freq_map = {
        "D": "day",
        "B": "B",
        "ME": "ME",
        "MS": "MS",
        "QE": "QE",
        "QS": "QS",
        "YE": "YE",
        "YS": "YS",
    }
    if inferred_freq in freq_map:
        return freq_map[inferred_freq]

    deltas = np.diff(idx.view("i8"))
    if len(deltas) == 0:
        return "unknown"

    med = np.median(deltas)
    d1 = pd.Timedelta(days=1).value

    if med <= 7 * d1:
        return "B"
    if med <= 45 * d1:
        return "ME"
    if med <= 120 * d1:
        return "QE"
    return "YE"


def _resample_series(
    df_data: pd.DataFrame,
    df_anchor_calendar: pd.DataFrame,
    aggregate_method: str,
) -> pd.DataFrame:
    if df_data.empty:
        return df_data

    if not isinstance(df_data.index, pd.DatetimeIndex):
        df_data.index = pd.to_datetime(df_data.index, errors="coerce")
        df_data = df_data.dropna(subset=[df_data.index.name])

    granularity_order = {"B": 1, "D": 2, "MS": 3, "ME": 4, "QS": 5, "QE": 6, "YS": 7, "YE": 8}
    granularity_anchor = pd.infer_freq(df_anchor_calendar.index) or "B"
    granularity_data = _infer_granularity(df_data.index)
    sampling_anchor = granularity_order.get(granularity_anchor, 1)
    sampling_data = granularity_order.get(granularity_data, 1)
    if sampling_data > sampling_anchor:
        sampling_action = "upsampling"
    elif sampling_data < sampling_anchor:
        sampling_action = "downsampling"
    else:
        sampling_action = "same"

    if sampling_action == "upsampling":
        df_data = df_data.sort_index()
        df_data = df_data.reindex(df_data.index.union(df_anchor_calendar.index))
        df_data = df_data.ffill().bfill()
        df_data = df_data.reindex(df_anchor_calendar.index).sort_index()
    elif sampling_action == "downsampling":
        df_data = df_data.sort_index()

        daily_index = pd.date_range(df_data.index.min(), df_data.index.max(), freq="B")
        df_data = df_data.reindex(daily_index).ffill().bfill()
        grouper_freq = granularity_anchor
        agg_dict: Dict[str, str] = {}
        for col in df_data.columns:
            if col in ["open"]:
                agg_dict[col] = "first"
            elif col in ["high"]:
                agg_dict[col] = "max"
            elif col in ["low"]:
                agg_dict[col] = "min"
            elif col in ["close", "adj_close"]:
                agg_dict[col] = "last"
            elif col in ["volume"]:
                agg_dict[col] = "sum"
            else:
                agg_dict[col] = aggregate_method

        df_data = df_data.groupby(pd.Grouper(freq=grouper_freq)).agg(agg_dict)
        df_data = df_data.reindex(df_anchor_calendar.index)

    return df_data


def treat_data(
    data: dict[str, dict[str, pd.DataFrame]],
    *,
    aggregate_method: str = "last",
) -> dict[str, dict[str, pd.DataFrame]]:
    cutoff: datetime = datetime(year=2010, month=12, day=31)
    g_map: dict[str, str] = {"day": "D", "month": "ME", "quarter": "QE", "year": "Y"}
    granularity = g_map["day"]
    calendar = _create_calendar(data, cutoff, granularity="day")

    data_treated: dict[str, dict[str, pd.DataFrame]] = {}
    for key, dataset in data.items():
        if key == "quotes":
            data_treated[key] = {}
            for stock_quote, df_stock_quote in dataset.items():
                df_stock_quote = df_stock_quote.set_index("date")
                _resample_series(df_stock_quote, calendar, aggregate_method=aggregate_method)
                data_treated[key][stock_quote] = treat_quotes(df_stock_quote, calendar)
        elif key == "statements":
            data_treated[key] = {}
            if dataset:
                for statement, df_statement in dataset.items():
                    data_treated[key][statement] = treat_statements(df_statement, calendar)
            else:
                data_treated[key] = {}
        elif key == "indicators":
            data_treated[key] = {}
            if dataset:
                for indicator, df_indicator in dataset.items():
                    data_treated[key][indicator] = treat_indicators(df_indicator, calendar)
            else:
                data_treated[key] = {}
        else:
            data_treated[key] = dataset

    return data_treated


def create_ratios(company_data: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    source_df = company_data["statements"]["statements"].copy()
    ratios_df = source_df.copy()

    quotes: Mapping[str, pd.DataFrame] = company_data.get("quotes", {}) or {}

    stock_keys = [k for k in quotes.keys() if str(k).startswith("stock_")]
    stock_keys.sort(key=lambda x: int(str(x).split("_", 1)[1]) if "_" in str(x) else float("inf"))

    ignore_stock_keys_cols = ["id", "date", "company_name", "ticker"]
    frames: List[pd.DataFrame] = []

    for i, qkey in enumerate(stock_keys):
        try:
            suffix = qkey.split("_", 1)[1]
            code = f"99.{suffix}"
        except Exception:
            code = f"99.{i+3}"

        dfq = quotes.get(qkey)
        if dfq is None or dfq.empty:
            continue

        dfq = dfq.loc[:, [c for c in dfq.columns if c not in ignore_stock_keys_cols]].copy()
        if dfq.empty:
            continue

        dfq.columns = [f"{code}.{c} - {qkey}" for c in dfq.columns]
        frames.append(dfq)

    if frames:
        price_df = pd.concat(frames, axis=1)
        source_df = source_df.join(price_df, how="left")
        ratios_df = ratios_df.join(price_df, how="left")

    account_long_map = {c: c.split(" - ")[0] for c in source_df.columns if " - " in c}
    calculate_df = source_df.rename(columns=account_long_map).copy()

    indicator_names = [
        name
        for name in dir(intel)
        if name.startswith("indicators_") and isinstance(getattr(intel, name), list)
    ]
    indicator_names.sort()

    for name in indicator_names:
        ratios_df = ratios_df.copy()
        calculate_df = calculate_df.copy()
        indicators_list = getattr(intel, name)
        for indicator in indicators_list:
            account_name = indicator["account"]
            description = indicator["description"]
            formula_obj = indicator["formula"]
            col_out = f"{account_name} - {description}"
            try:
                series_value = formula_obj(calculate_df)
                ratios_df[col_out] = series_value
                calculate_df[account_name] = series_value
            except KeyError:
                ratios_df[col_out] = np.nan
                calculate_df[account_name] = np.nan

    if isinstance(ratios_df.index, pd.MultiIndex):
        ratios_df = ratios_df.reset_index(drop=False)
        ratios_df = ratios_df.set_index("date").sort_index()

    return ratios_df.fillna(0)
