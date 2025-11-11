import pandas as pd

from application.dtos.company_accounts_series_dto import CompanyAccountsSeriesDTO
from application.dtos.company_ratios_frame_dto import CompanyRatiosFrameDTO
from application.usecases.get_company_accounts_chart import (
    GetCompanyAccountsChartUseCase,
)
from domain.dtos.cache_ratios_result_dto import CacheRatiosResultDTO
from domain.value_objects import SearchFilterTree


class DummyRatiosUseCase:
    def __call__(self, request):
        assert request.company_name == "TEST"
        df = pd.DataFrame(
            {
                "02.03": [10, 20],
                "03.01": [5, 15],
            },
            index=pd.to_datetime(["2024-01-01", "2024-02-01"]),
        )
        cache_info = CacheRatiosResultDTO(
            company_name="TEST",
            cache_key="abc",
            hit=True,
            entry=None,
        )
        filters = request.filters.to_dict() if request.filters else None
        meta = {"filters": filters}
        return CompanyRatiosFrameDTO(
            company_name="TEST",
            ticker="TST",
            frame=df,
            cache_info=cache_info,
            meta=meta,
        )


def test_chart_usecase_generates_series():
    usecase = GetCompanyAccountsChartUseCase(ratios_frame_usecase=DummyRatiosUseCase())
    filter_tree = SearchFilterTree.from_raw({"and": [{"status": "ATIVO"}]})

    result: CompanyAccountsSeriesDTO = usecase(
        company_name="TEST",
        accounts=["02.03", "03.01"],
        filters=filter_tree,
    )

    assert result.company_name == "TEST"
    assert len(result.series) == 2
    assert result.series[0].points[0].value == 10.0
    assert result.cache_info["hit"] is True
    assert result.meta["filters"] == filter_tree.to_dict()
