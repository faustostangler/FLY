# infrastructure/config/statements.py
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

URL_DF = "https://www.rad.cvm.gov.br/ENET/frmDemonstracaoFinanceiraITR.aspx"
URL_CAPITAL = "https://www.rad.cvm.gov.br/ENET/frmDadosComposicaoCapitalITR.aspx"

CAPITAL_ITEMS: List[Dict[str, str]] = [
    {"elem_id": "QtdAordCapiItgz_1", "account": "00.01.01", "description": "Ações ON Circulação"},
    {"elem_id": "QtdAprfCapiItgz_1", "account": "00.01.02", "description": "Ações PN Circulação"},
    {"elem_id": "QtdAordTeso_1", "account": "00.02.01", "description": "Ações ON Tesouraria"},
    {"elem_id": "QtdAprfTeso_1", "account": "00.02.02", "description": "Ações PN Tesouraria"},
]

NSD_TYPE_MAP: Mapping[str, Tuple[str, int]] = {
    "INFORMACOES TRIMESTRAIS": ("ITR", 3),
    "DEMONSTRACOES FINANCEIRAS PADRONIZADAS": ("DFP", 4),
}

STATEMENT_ITEMS: Tuple[Dict[str, Optional[int | str]], ...] = (
    {"grupo": "DFs Individuais", "quadro": "Balanço Patrimonial Ativo", "informacao": 1, "demonstracao": 2, "periodo": 0},
    {"grupo": "DFs Individuais", "quadro": "Balanço Patrimonial Passivo", "informacao": 1, "demonstracao": 3, "periodo": 0},
    {"grupo": "DFs Individuais", "quadro": "Demonstração do Resultado", "informacao": 1, "demonstracao": 4, "periodo": 0},
    {"grupo": "DFs Individuais", "quadro": "Demonstração do Resultado Abrangente", "informacao": 1, "demonstracao": 5, "periodo": 0},
    {"grupo": "DFs Individuais", "quadro": "Demonstração do Fluxo de Caixa", "informacao": 1, "demonstracao": 99, "periodo": 0},
    {"grupo": "DFs Individuais", "quadro": "Demonstração de Valor Adicionado", "informacao": 1, "demonstracao": 9, "periodo": 0},
    {"grupo": "DFs Consolidadas", "quadro": "Balanço Patrimonial Ativo", "informacao": 2, "demonstracao": 2, "periodo": 0},
    {"grupo": "DFs Consolidadas", "quadro": "Balanço Patrimonial Passivo", "informacao": 2, "demonstracao": 3, "periodo": 0},
    {"grupo": "DFs Consolidadas", "quadro": "Demonstração do Resultado", "informacao": 2, "demonstracao": 4, "periodo": 0},
    {"grupo": "DFs Consolidadas", "quadro": "Demonstração do Resultado Abrangente", "informacao": 2, "demonstracao": 5, "periodo": 0},
    {"grupo": "DFs Consolidadas", "quadro": "Demonstração do Fluxo de Caixa", "informacao": 2, "demonstracao": 99, "periodo": 0},
    {"grupo": "DFs Consolidadas", "quadro": "Demonstração de Valor Adicionado", "informacao": 2, "demonstracao": 9, "periodo": 0},
    {"grupo": "Dados da Empresa", "quadro": "Composição do Capital", "informacao": None, "demonstracao": None, "periodo": 0},
)

@dataclass(frozen=True)
class StatementsConfig:
    statement_items: Tuple[Dict[str, Optional[int | str]], ...] = field(
        default_factory=lambda: tuple(dict(i) for i in STATEMENT_ITEMS)
    )
    nsd_type_map: Mapping[str, Tuple[str, int]] = field(
        default_factory=lambda: dict(NSD_TYPE_MAP)
    )
    capital_items: List[Dict[str, str]] = field(
        default_factory=lambda: [dict(i) for i in CAPITAL_ITEMS]
    )
    url_df: str = URL_DF
    url_capital: str = URL_CAPITAL

def load_statements_config() -> StatementsConfig:
    items = list(STATEMENT_ITEMS)
    items.sort(
        key=lambda item: (
            0 if item.get("grupo") == "Dados da Empresa" else 1,
            item.get("informacao") or 0,
            item.get("demonstracao") or 0,
        )
    )
    return StatementsConfig(statement_items=tuple(items))
