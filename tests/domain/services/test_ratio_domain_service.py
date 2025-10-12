from datetime import datetime

import pytest

from domain.dtos.normalized_series_dto import (
    NormalizedMetricSeriesDTO,
    NormalizedSeriesBundleDTO,
)
from domain.services.ratio_domain_service import RatioDomainService


def _make_series(
    *,
    code: str,
    company_id: str,
    calendar: tuple[datetime, ...],
    values: tuple[float | None, ...],
    versions: tuple[str | None, ...],
    hashes: tuple[str | None, ...],
    source: str,
) -> NormalizedMetricSeriesDTO:
    return NormalizedMetricSeriesDTO(
        company_id=company_id,
        metric_code=code,
        calendar=calendar,
        values=values,
        versions=versions,
        hashes=hashes,
        source=source,
    )


def test_revenue_price_ratio_per_ticker() -> None:
    company_id = "COMPANY"
    calendar = (
        datetime(2023, 1, 1),
        datetime(2023, 1, 2),
    )

    series_map = {
        "03.01": _make_series(
            code="03.01",
            company_id=company_id,
            calendar=calendar,
            values=(100.0, 200.0),
            versions=("rev-1", "rev-2"),
            hashes=("hash-rev-1", "hash-rev-2"),
            source="statement",
        ),
        "QUOTE.ABC3.CLOSE": _make_series(
            code="QUOTE.ABC3.CLOSE",
            company_id=company_id,
            calendar=calendar,
            values=(10.0, 20.0),
            versions=("px3-1", "px3-2"),
            hashes=("hash-px3-1", "hash-px3-2"),
            source="stock_quote",
        ),
        "QUOTE.ABC4.CLOSE": _make_series(
            code="QUOTE.ABC4.CLOSE",
            company_id=company_id,
            calendar=calendar,
            values=(25.0, 40.0),
            versions=("px4-1", "px4-2"),
            hashes=("hash-px4-1", "hash-px4-2"),
            source="stock_quote",
        ),
        "IND.SELIC_FACTOR": _make_series(
            code="IND.SELIC_FACTOR",
            company_id=company_id,
            calendar=calendar,
            values=(1.0, 1.1),
            versions=("selic-1", "selic-2"),
            hashes=("hash-selic-1", "hash-selic-2"),
            source="indicator",
        ),
    }

    bundle = NormalizedSeriesBundleDTO(
        company_id=company_id,
        calendar=calendar,
        series_map=series_map,
    )

    service = RatioDomainService(logger=None)

    ratios = service.calculate(bundle)
    revenue_price_ratios = sorted(
        [r for r in ratios if r.ratio_code.startswith("R.REV_PRICE.")],
        key=lambda item: (item.ratio_code, item.date),
    )

    assert len(revenue_price_ratios) == 4

    expected = {
        ("R.REV_PRICE.ABC3", calendar[0]): pytest.approx(10.0),
        ("R.REV_PRICE.ABC3", calendar[1]): pytest.approx(200.0 / 20.0 / 1.1),
        ("R.REV_PRICE.ABC4", calendar[0]): pytest.approx(4.0),
        ("R.REV_PRICE.ABC4", calendar[1]): pytest.approx(200.0 / 40.0 / 1.1),
    }

    for ratio in revenue_price_ratios:
        key = (ratio.ratio_code, ratio.date)
        assert key in expected
        assert ratio.value == expected[key]
        inputs = dict(ratio.input_versions)
        assert inputs["03.01"]
        assert any(token.endswith(".CLOSE") for token in inputs)
        assert inputs["IND.SELIC_FACTOR"]
