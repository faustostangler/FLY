# domain/dto/value_objects_statement.py

from dataclasses import dataclass
from typing import Optional

# Value Objects (VOs)

@dataclass(frozen=True)
class CompanyQuarterKey:
    """Identidade de uma empresa em um trimestre, sem se preocupar com quadro ou versão."""
    # representa o agregado mais alto, a existência de uma companhia em um trimestre. Identidade macro, útil para localizar rapidamente todos os quadros de um período.
    company_name: str
    quarter: str


@dataclass(frozen=True)
class QuarterFrameKey:
    """Identidade de um quadro específico de demonstração dentro de um trimestre de uma companhia."""
    # é a identidade de um frame de demonstração (um quadro contábil específico, dentro de um grupo, em um trimestre). Dá para nomear como FrameKey ou QuarterlyFrameKey, para destacar que não envolve versão/publicação. É a “chave natural” de um quadro.
    company_name: str
    quarter: str
    grupo: str
    quadro: str


@dataclass(frozen=True)
class FramePublicationKey:
    """Identidade de uma publicação de quadro (NSD + versão)."""
    # representa uma edição publicada de um frame, com versionamento explícito. O nome “Publication” está ótimo. É exatamente o que diferencia “o mesmo quadro em V1, V2, V3...”. Também poderia ser FrameVersionKey, se você preferir realçar a noção de versão.
    company_name: str
    quarter: str
    grupo: str
    quadro: str
    version: int
    nsd: int


@dataclass(frozen=True)
class StatementLineKey:
    """Identidade de uma linha publicada de demonstração financeira."""
    # identifica uma linha específica de demonstração, publicada em um NSD/version de um quadro. É a “chave da linha de negócio” na granularidade mínima.
    company_name: str
    quarter: str
    grupo: str
    quadro: str
    version: int
    nsd: int
    account: str
    description: str

