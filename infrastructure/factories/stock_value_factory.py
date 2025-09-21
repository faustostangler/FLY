from __future__ import annotations

from datetime import date, datetime
from typing import Tuple

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.services.stock_value import StockValueService
from domain.polices.quarter_median_policy import QuarterMedianPolicy
from domain.services.price_series_service import PriceSeriesService
from infrastructure.gateways.yfinance_gateway import YFinanceGateway
from infrastructure.repositories.stock_companies_repository import (
    SqlAlchemyCompaniesRepository,
)
from infrastructure.repositories.stock_quotes_repository import (
    SqlAlchemyQuotesRepository,
)

DEFAULT_STOCK_START = date(2000, 1, 1)


def build_stock_value_service(
    config: ConfigPort, logger: LoggerPort
) -> Tuple[StockValueService, date]:
    """Compose the stock-value service and resolve its start date."""

    companies_repo = SqlAlchemyCompaniesRepository(config=config, logger=logger)
    quotes_repo = SqlAlchemyQuotesRepository(config=config, logger=logger)
    price_feed = YFinanceGateway()
    price_series_service = PriceSeriesService(
        quarter_policy=QuarterMedianPolicy()
    )

    service = StockValueService(
        companies_repo=companies_repo,
        quotes_repo=quotes_repo,
        price_feed=price_feed,
        price_series_service=price_series_service,
    )

    start_config = getattr(config.domain, "stock_data_start_date", DEFAULT_STOCK_START)
    start_date = _normalize_start_date(start_config)

    return service, start_date


def _normalize_start_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return DEFAULT_STOCK_START
    return DEFAULT_STOCK_START