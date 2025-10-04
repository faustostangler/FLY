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
        ("IPCA", "433"), 
        ("IPCA ALimentação e Bebidas", "1635"),
        ("Índice nacional de preços ao consumidor (INPC)", "188"),
        ("INPC - Alimentação e bebidas", "1644"),
        ("Reservas internacionais - Total - diária", "13621"),
        ("Taxa de câmbio - Livre - Dólar americano (venda) - diário", "1"),
        ("Taxa de câmbio - Livre - Dólar americano (compra) - Fim de período - mensal", "3695"), 
        ],
}


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
