from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

# Default language code used in API requests
LANGUAGE = "pt-br"

# Endpoints for retrieving company data from B3 (Brazilian Stock Exchange)
COMPANY_ENDPOINT = {
    "initial": "https://sistemaswebb3-listados.b3.com.br/"
    "listedCompaniesProxy/CompanyCall/GetInitialCompanies/",
    "detail": "https://sistemaswebb3-listados.b3.com.br/"
    "listedCompaniesProxy/CompanyCall/GetDetail/",
    "financial": "https://sistemaswebb3-listados.b3.com.br/"
    "listedCompaniesProxy/CompanyCall/GetListedFinancial/",
}

# Endpoint for retrieving financial reports by NSD identifier (CVM system)
NSD_ENDPOINT = (
    "https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?"
    "NumeroSequencialDocumento={nsd}&CodigoTipoInstituicao=1"
)


@dataclass(frozen=True)
class ExchangeApiConfig:
    """Immutable configuration for stock exchange API access.

    Attributes:
        language (str): Language code for requests (default: "pt-br").
        company_data_endpoint (Mapping[str, str]): Mapping of logical names
            to B3 company-related endpoints (initial, detail, financial).
        nsd_endpoint (str): Endpoint template for accessing NSD documents
            from CVM (Brazilian Securities Commission).
    """

    # Request language (fixed to pt-br)
    language: str = field(default=LANGUAGE)

    # Endpoints for company-related data
    company_data_endpoint: Mapping[str, str] = field(
        default_factory=lambda: COMPANY_ENDPOINT
    )

    # Template URL for NSD document retrieval
    nsd_endpoint: str = field(default=NSD_ENDPOINT)


def load_exchange_api_config() -> ExchangeApiConfig:
    """Factory function to load the exchange API configuration.

    Returns:
        ExchangeApiConfig: Initialized with default language, company endpoints,
        and NSD endpoint.
    """
    # Construct and return configuration object with defaults
    return ExchangeApiConfig(
        language=LANGUAGE,
        company_data_endpoint=COMPANY_ENDPOINT,
        nsd_endpoint=NSD_ENDPOINT,
    )
