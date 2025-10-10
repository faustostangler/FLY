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
        ("Interest rate - Australia", "17880", "Monthly"),
        ("Interest rate - Canada", "17881", "Monthly"),
        ("Interest rate - China", "17899", "Monthly"),
        ("Interest rate - India", "17901", "Monthly"),
        ("Interest rate - Japan", "17903", "Monthly"),
        ("Interest rate - Mexico", "17904", "Monthly"),
        ("Interest rate - Russia", "17905", "Monthly"),
        ("Interest rate - South Africa", "17906", "Monthly"),
        ("Interest rate - Turkey", "17907", "Monthly"),
        ("Interest rate - United Kingdom", "17908", "Monthly"),
        ("CET1 Ratio Brazil Quarterly", "29508", "Quarterly"),
        ("Leverage Ratio Brazil Quarterly", "29515", "Quarterly"),
        ("IMA - General", "12469", "Daily"),
        ("Bovespa index", "7", "Daily"),
        ("Swap reference rate - preset DI rate (BM&F) - 120-day term", "7804", "Daily"),
        ("Swap reference rate - preset DI rate (BM&F) - 180-day term", "7805", "Daily"),
        ("Swap reference rate - preset DI rate (BM&F) - 30-day term", "7801", "Daily"),
        ("Swap reference rate - preset DI rate (BM&F) - 360-day term", "7806", "Daily"),
        ("Swap reference rate - preset DI rate (BM&F) - 60-day term", "7802", "Daily"),
        ("Swap reference rate - preset DI rate (BM&F) - 90-day term", "7803", "Daily"),
        ("IGP-M montlhy - consistent with index number", "28655", "Monthly"),
        ("IGP-DI - Total", "10641", "Monthly"),
        ("IGP-DI - Total", "10686", "Monthly"),
        ("IGP-M - Total", "10648", "Monthly"),
        ("IGP-M - Total", "10694", "Monthly"),
        ("Households disposable income", "29023", "Monthly"),
        ("Households disposable income (accumulated in 12 months)", "29029", "Monthly"),
        ("Households disposable income (deflated by IPCA, seasonally adjusted)", "29027", "Monthly"),
        ("Fiscal net debt", "17421", "Monthly"),
        ("Fiscal net debt with exchange devaluation", "17419", "Monthly"),
        ("Fiscal net debt with exchange devaluation with Petrobras and Eletrobras", "16825", "Monthly"),
        ("Fiscal net debt with Petrobras and Eletrobras", "16827", "Monthly"),
        ("Direct Investment Liabilities accumulated in 12 months - monthly", "24422", "Monthly"),
        ("Direct Investment Liabilities accumulated in 12 months in relation to GDP - monthly", "23080", "Monthly"),
        ("Broad National Consumer Price Index (IPCA)", "433", "Monthly"),
        ("National Consumer Price Index (INPC)", "188", "Monthly"),
        ("National Consumer Price Index (Restricted) - IPC-r", "229", "Monthly"),
        ("Broad Producer Price Index (IPA-DI)", "225", "Monthly"),
        ("General Price Index-Domestic Supply (IGP-DI)", "190", "Monthly"),
        ("General Price Index-Market (IGP-M)", "189", "Monthly"),
        # ("Selic target rate", "27885", "N/A"),
        # ("Credit operations to households - Total balance", "27878", "N/A"),
        # ("Credit operations to corporations - Total balance", "27879", "N/A"),
        # ("Default rate of credit operations - Households", "27904", "N/A"),
        # ("Default rate of credit operations - Corporations", "27905", "N/A"),
        # ("Average cost of credit - Households", "27907", "N/A"),
        # ("Average cost of credit - Corporations", "27908", "N/A"),
        ("Exports volume index - Total", "11752", "Monthly"),
        ("Imports volume index - Total", "11754", "Monthly"),
        ("Exports price index - Total", "11756", "Monthly"),
        ("Imports price index - Total", "11758", "Monthly"),
        ("Terms of trade index", "11760", "Monthly"),
        ("Balance of trade (exports - imports)", "11762", "Monthly"),
        ("Motor vehicles production - Units", "13522", "Monthly"),
        ("Motor vehicles domestic sales - Units", "13521", "Annual"),
        # ("Supermarkets sales - Seasonally adjusted index", "14421", "N/A"),
        # ("Retail sales volume - General - Seasonally adjusted", "14426", "N/A"),
        # ("Households disposable income (deflated, SA)", "27868", "N/A"),
        # ("Households savings deposits - Balance", "27869", "N/A"),
        # ("Households financial investments - Balance", "27870", "N/A"),
        # ("Households cash sales index (proxy consumption)", "27873", "N/A"),
        ("Net debt of federal government", "4504", "Monthly"),
        ("Primary result of federal government - Cumulative in year", "4520", "Monthly"),
        ("Nominal result of federal government - Cumulative in year", "4525", "Monthly"),
        # ("IMA-B (public bonds index, inflation-linked)", "27890", "N/A"),
        # ("IMA-Geral (public bonds index, general)", "27891", "N/A"),
        # ("Mutual funds net inflows - Fixed income", "27892", "N/A"),
        # ("Mutual funds net inflows - Equity", "27893", "N/A"),
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
