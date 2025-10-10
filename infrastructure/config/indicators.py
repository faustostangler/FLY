from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, List, Tuple

# 
ENDPOINT = {
    "bcb": 
    "http://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/"
    "dados?formato=json&dataInicial={dataInicial}&dataFinal={dataFinal}"

    }

SOURCE = {
    "bcb": [
        ("17880", "Interest rate - Australia", "Monthly"),
        ("17881", "Interest rate - Canada", "Monthly"),
        ("17899", "Interest rate - China", "Monthly"),
        ("17901", "Interest rate - India", "Monthly"),
        ("17903", "Interest rate - Japan", "Monthly"),
        ("17904", "Interest rate - Mexico", "Monthly"),
        ("17905", "Interest rate - Russia", "Monthly"),
        ("17906", "Interest rate - South Africa", "Monthly"),
        ("17907", "Interest rate - Turkey", "Monthly"),
        ("17908", "Interest rate - United Kingdom", "Monthly"),
        ("29508", "CET1 Ratio Brazil Quarterly", "Quarterly"),
        ("29515", "Leverage Ratio Brazil Quarterly", "Quarterly"),
        ("12469", "IMA - General", "Daily"),
        ("7", "Bovespa index", "Daily"),
        ("7804", "Swap reference rate - preset DI rate (BM&F) - 120-day term", "Daily"),
        ("7805", "Swap reference rate - preset DI rate (BM&F) - 180-day term", "Daily"),
        ("7801", "Swap reference rate - preset DI rate (BM&F) - 30-day term", "Daily"),
        ("7806", "Swap reference rate - preset DI rate (BM&F) - 360-day term", "Daily"),
        ("7802", "Swap reference rate - preset DI rate (BM&F) - 60-day term", "Daily"),
        ("7803", "Swap reference rate - preset DI rate (BM&F) - 90-day term", "Daily"),
        ("28655", "IGP-M montlhy - consistent with index number", "Monthly"),
        ("10641", "IGP-DI - Total", "Monthly"),
        ("10686", "IGP-DI - Total", "Monthly"),
        ("10648", "IGP-M - Total", "Monthly"),
        ("10694", "IGP-M - Total", "Monthly"),
        ("29023", "Households disposable income", "Monthly"),
        ("29029", "Households disposable income (accumulated in 12 months)", "Monthly"),
        ("29027", "Households disposable income (deflated by IPCA, seasonally adjusted)", "Monthly"),
        ("17421", "Fiscal net debt", "Monthly"),
        ("17419", "Fiscal net debt with exchange devaluation", "Monthly"),
        ("16825", "Fiscal net debt with exchange devaluation with Petrobras and Eletrobras", "Monthly"),
        ("16827", "Fiscal net debt with Petrobras and Eletrobras", "Monthly"),
        ("24422", "Direct Investment Liabilities accumulated in 12 months - monthly", "Monthly"),
        ("23080", "Direct Investment Liabilities accumulated in 12 months in relation to GDP - monthly", "Monthly"),
        ("433", "Broad National Consumer Price Index (IPCA)", "Monthly"),
        ("188", "National Consumer Price Index (INPC)", "Monthly"),
        ("229", "National Consumer Price Index (Restricted) - IPC-r", "Monthly"),
        ("225", "Broad Producer Price Index (IPA-DI)", "Monthly"),
        ("190", "General Price Index-Domestic Supply (IGP-DI)", "Monthly"),
        ("189", "General Price Index-Market (IGP-M)", "Monthly"),
        ("11752", "Exports volume index - Total", "Monthly"),
        ("11754", "Imports volume index - Total", "Monthly"),
        ("11756", "Exports price index - Total", "Monthly"),
        ("11758", "Imports price index - Total", "Monthly"),
        ("11760", "Terms of trade index", "Monthly"),
        ("11762", "Balance of trade (exports - imports)", "Monthly"),
        ("13522", "Motor vehicles production - Units", "Monthly"),
        ("13521", "Motor vehicles domestic sales - Units", "Annual"),
        ("4504", "Net debt of federal government", "Monthly"),
        ("4520", "Primary result of federal government - Cumulative in year", "Monthly"),
        ("4525", "Nominal result of federal government - Cumulative in year", "Monthly"),
        ],}


@dataclass(frozen=True)
class IndicatorsConfig:
    """
    """

    # 
    endpoint: Mapping[str, str] = field(default_factory=lambda:ENDPOINT)
    source: Mapping[str, List[Tuple[str, str]]] = field(default_factory=lambda: SOURCE)



def load_indicators_config() -> IndicatorsConfig:
    """Factory function to load repository configuration.

    Returns:
        RepositoryConfig: Initialized with default batch size and
        persistence threshold.
    """
    # Construct and return repository configuration with defaults
    return IndicatorsConfig(
        endpoint=ENDPOINT,
        source=SOURCE,
    )
