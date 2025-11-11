from datetime import date

from application.dtos.account_series_dto import AccountSeriesDTO, AccountSeriesPointDTO
from application.dtos.company_accounts_series_dto import CompanyAccountsSeriesDTO
from presentation.backend.mappers.accounts_series_chart_mapper import (
    company_accounts_to_chart,
)


def test_company_accounts_to_chart_includes_cache_meta():
    dto = CompanyAccountsSeriesDTO(
        company_name="TEST",
        ticker="TST3",
        series=[
            AccountSeriesDTO(
                ticker="TST3",
                account_code="02.03",
                label="Patrimônio",
                points=[
                    AccountSeriesPointDTO(date=date(2024, 1, 1), value=1.0),
                    AccountSeriesPointDTO(date=date(2024, 2, 1), value=2.0),
                ],
            )
        ],
        meta={"filters": {"status": "ATIVO"}},
        cache_info={"hit": True, "cache_key": "abc"},
    )

    chart = company_accounts_to_chart(dto)

    assert chart.meta["company_name"] == "TEST"
    assert chart.meta["cache"]["hit"] is True
    assert chart.data[0].name == "02.03 - Patrimônio"
    assert chart.data[0].x[0] == date(2024, 1, 1)
