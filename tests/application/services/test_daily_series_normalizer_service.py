from datetime import datetime

from application.services.daily_series_normalizer_service import (
    DailySeriesNormalizerService,
)
from application.services.indicator_normalizer_service import (
    IndicatorNormalizerService,
)
from domain.dtos.stock_quote_dto import StockQuoteDTO


def test_normalize_quotes_creates_ticker_specific_metrics() -> None:
    normalizer = DailySeriesNormalizerService(
        indicator_normalizer=IndicatorNormalizerService(),
        indicator_factor_rules=(),
    )

    quotes = [
        StockQuoteDTO(
            company_name="COMPANY",
            ticker="ABCD3",
            date=datetime(2023, 1, 1),
            open=10.0,
            low=9.5,
            high=10.5,
            close=10.2,
            adj_close=10.1,
            volume=1000,
            currency="BRL",
        ),
        StockQuoteDTO(
            company_name="COMPANY",
            ticker="ABCD4",
            date=datetime(2023, 1, 2),
            open=20.0,
            low=19.5,
            high=20.5,
            close=20.2,
            adj_close=20.0,
            volume=2000,
            currency="BRL",
        ),
    ]

    bundle = normalizer.normalize(
        company_id="COMPANY",
        statements=[],
        quotes=quotes,
        indicators=[],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 3),
    )

    assert bundle.get("QUOTE.ABCD3.CLOSE") is not None
    assert bundle.get("QUOTE.ABCD4.CLOSE") is not None
