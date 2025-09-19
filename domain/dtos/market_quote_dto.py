from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MarketQuoteDTO:
    provider: str
    symbol: str          # símbolo canônico interno da companhia
    day: date            # armazenado como 'YYYY-MM-DD'
    close: float
    adjusted_close: float
    currency: str        # 'BRL' por padrão
