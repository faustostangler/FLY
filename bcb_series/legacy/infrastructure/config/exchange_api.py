from dataclasses import dataclass, field
from typing import Mapping

LANGUAGE = "pt-br"
COMPANY_ENDPOINT = {
    "initial": "https://sistemaswebb3-listados.b3.com.br/"
    "listedCompaniesProxy/CompanyCall/GetInitialCompanies/",
    "detail": "https://sistemaswebb3-listados.b3.com.br/"
    "listedCompaniesProxy/CompanyCall/GetDetail/",
    "financial": "https://sistemaswebb3-listados.b3.com.br/"
    "listedCompaniesProxy/CompanyCall/GetListedFinancial/",
}
NSD_ENDPOINT = (
    "https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?"
    "NumeroSequencialDocumento={nsd}&CodigoTipoInstituicao=1"
)


@dataclass(frozen=True)
class ExchangeApiConfig:
    """API configuration for accessing the stock exchange endpoints.

    Attributes:
        language: Language code for requests (fixed to ``"pt-br"``).
        company_data_endpoint: Mapping of logical names to exchange URLs.
    """

    language: str = field(default=LANGUAGE)
    company_data_endpoint: Mapping[str, str] = field(
        default_factory=lambda: COMPANY_ENDPOINT
    )
    nsd_endpoint: str = field(default=NSD_ENDPOINT)


def load_exchange_api_config() -> ExchangeApiConfig:
    """Create an :class:`ExchangeApiConfig` with the default values."""

    return ExchangeApiConfig(
        language=LANGUAGE,
        company_data_endpoint=COMPANY_ENDPOINT,
        nsd_endpoint=NSD_ENDPOINT,
    )
