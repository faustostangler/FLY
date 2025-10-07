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
("Interest rate – Australia", "17880"),
("Interest rate – Canada", "17881"),
("Interest rate – China", "17899"),
("Interest rate – India", "17901"),
("Interest rate – Japan", "17903"),
("Interest rate – Mexico", "17904"),
("Interest rate – Russia", "17905"),
("Interest rate – South Africa", "17906"),
("Interest rate – Turkey", "17907"),
("Interest rate – United Kingdom", "17908"),
("CET1 Ratio Brazil Quarterly", "29508"),
("Leverage Ratio Brazil Quarterly", "29515"),
("IMA - General", "12469"),
("Bovespa index", "7"),
("Swap reference rate - preset DI rate (BM&F) - 120-day term", "7804"),
("Swap reference rate - preset DI rate (BM&F) - 180-day term", "7805"),
("Swap reference rate - preset DI rate (BM&F) - 30-day term", "7801"),
("Swap reference rate - preset DI rate (BM&F) - 360-day term", "7806"),
("Swap reference rate - preset DI rate (BM&F) - 60-day term", "7802"),
("Swap reference rate - preset DI rate (BM&F) - 90-day term", "7803"),
("IGP-M montlhy - consistent with index number", "28655"),
("IGP-DI - Total", "10641"),
("IGP-DI - Total", "10686"),
("IGP-M - Total", "10648"),
("IGP-M - Total", "10694"),
("Households disposable income", "29023"),
("Households disposable income (accumulated in 12 months)", "29029"),
("Households disposable income (deflated by IPCA, seasonally adjusted)", "29027"),
("Fiscal net debt", "17421"),
("Fiscal net debt with exchange devaluation", "17419"),
("Fiscal net debt with exchange devaluation with Petrobras and Eletrobras", "16825"),
("Fiscal net debt with Petrobras and Eletrobras", "16827"),
("Direct Investment Liabilities accumulated in 12 months - monthly", "24422"),
("Direct Investment Liabilities accumulated in 12 months in relation to GDP - monthly", "23080"),
("Broad National Consumer Price Index (IPCA)", "433"),
("National Consumer Price Index (INPC)", "188"),
("National Consumer Price Index (Restricted) - IPC-r", "229"),
("Broad Producer Price Index (IPA-DI)", "225"),
("General Price Index-Domestic Supply (IGP-DI)", "190"),
("General Price Index-Market (IGP-M)", "189"),
("Selic target rate", "27885"),
("Credit operations to households – Total balance", "27878"),
("Credit operations to corporations – Total balance", "27879"),
("Default rate of credit operations – Households", "27904"),
("Default rate of credit operations – Corporations", "27905"),
("Average cost of credit – Households", "27907"),
("Average cost of credit – Corporations", "27908"),
("Exports volume index – Total", "11752"),
("Imports volume index – Total", "11754"),
("Exports price index – Total", "11756"),
("Imports price index – Total", "11758"),
("Terms of trade index", "11760"),
("Balance of trade (exports – imports)", "11762"),
("Motor vehicles production – Units", "13522"),
("Motor vehicles domestic sales – Units", "13521"),
("Supermarkets sales – Seasonally adjusted index", "14421"),
("Retail sales volume – General – Seasonally adjusted", "14426"),
("Households disposable income (deflated, SA)", "27868"),
("Households savings deposits – Balance", "27869"),
("Households financial investments – Balance", "27870"),
("Households cash sales index (proxy consumption)", "27873"),
("Net debt of federal government", "4504"),
("Primary result of federal government – Cumulative in year", "4520"),
("Nominal result of federal government – Cumulative in year", "4525"),
("IMA-B (public bonds index, inflation-linked)", "27890"),
("IMA-Geral (public bonds index, general)", "27891"),
("Mutual funds net inflows – Fixed income", "27892"),
("Mutual funds net inflows – Equity", "27893")
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
