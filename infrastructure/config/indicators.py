from __future__ import annotations

from dataclasses import dataclass, field

# Template URL for fetching time series data from the Brazilian Central Bank (BCB)
DEFAULT_BCB_URL_TEMPLATE = (
    "http://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados"
    "?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
)


@dataclass(frozen=True)
class IndicatorsConfig:
    """Immutable configuration for financial indicators integrations.

    Attributes:
        bcb_url_template (str): URL template for querying the BCB time-series
            endpoint. The template expects ``codigo_serie`` (series identifier),
            ``data_inicial`` (start date in YYYY-MM-DD), and ``data_final``
            (end date in YYYY-MM-DD) placeholders that will be formatted by
            callers when building requests.
    """

    # URL template to request data from the BCB API
    bcb_url_template: str = field(default=DEFAULT_BCB_URL_TEMPLATE)

    def build_bcb_url(self, codigo_serie: str, data_inicial: str, data_final: str) -> str:
        """Compose the BCB endpoint using the configured template."""

        return self.bcb_url_template.format(
            codigo_serie=codigo_serie,
            data_inicial=data_inicial,
            data_final=data_final,
        )


def load_indicators_config() -> IndicatorsConfig:
    """Factory method returning the indicators configuration."""

    return IndicatorsConfig(bcb_url_template=DEFAULT_BCB_URL_TEMPLATE)
