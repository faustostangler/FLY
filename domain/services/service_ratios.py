from typing import Any, List, Dict, Optional
import pandas as pd
from datetime import date, datetime
import re


from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.services.eligible_companies_batch_updater_service import (
    EligibleCompaniesBatchUpdaterService,
)
from application.usecases.normalize_ratios import NormalizeUseCase
from application.usecases.companies_eligible import (
    CompaniesEligibleUseCase,
)
from domain.dtos.company_eligible_dto import CompanyEligibleDTO

from domain.dtos import CacheRatiosResultDTO, SyncResultsDTO
from domain.ports.cache_ratios_port import CacheRatiosPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.companies_eligible_port import CompaniesEligiblePort


class RatiosService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        repository_stock_quote: RepositoryStockQuotePort,
        repository_indicators: RepositoryIndicatorsPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        cache_ratios: CacheRatiosPort,

        uow_factory: UowFactoryPort,
        worker_pool: WorkerPoolPort,
        companies_eligible_port: CompaniesEligiblePort,
    ):
        """Initialize the service with required dependencies.

        Args:
            config (ConfigPort): Provides application configuration settings.
            logger (LoggerPort): Logging interface for tracking operations.
            repository (RepositoryCompanyDataPort): Repository for persisting company data.
            scraper (ScraperCompanyDataPort): Scraper for fetching company data.
        """
        # Keep references to injected dependencies
        self.logger = logger
        self.config = config

        self.repository_company = repository_company
        self.repository_stock_quote = repository_stock_quote
        self.repository_indicators = repository_indicators
        self.repository_statements_fetched = repository_statements_fetched
        self.cache_ratios = cache_ratios
        self.companies_eligible_port = companies_eligible_port

        self.uow_factory = uow_factory
        self.worker_pool = worker_pool
        # self.http_client = http_client

        self._companies_eligible_batch_service = EligibleCompaniesBatchUpdaterService(
            logger=self.logger,
            port=companies_eligible_port,
        )

        self.companies_eligible_usecase = CompaniesEligibleUseCase(
            logger=self.logger,
            repository_company=self.repository_company,
            repository_statements_fetched=self.repository_statements_fetched,
            repository_stock_quote=self.repository_stock_quote,
            batch_service=self._companies_eligible_batch_service,
            uow_factory=self.uow_factory,
        )

        # Initialize the use case responsible for company synchronization
        self.normalize_usecase = NormalizeUseCase(
            config=self.config,
            logger=self.logger,

            repository_stock_quote=self.repository_stock_quote,
            repository_indicators=self.repository_indicators,
            repository_statements_fetched=self.repository_statements_fetched,
            cache_ratios=self.cache_ratios,
            companies_eligible_port=companies_eligible_port,

            uow_factory=self.uow_factory,
            worker_pool=self.worker_pool,
            # http_client=self.http_client,

            # max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO[CacheRatiosResultDTO]:
        return self.run()

    def run(self, filters: Optional[Dict[str, Any]] = None) -> SyncResultsDTO[CacheRatiosResultDTO]:
        """
        Executa a normalização com filtros complexos.

        Args:
            filters: Dicionário de filtros (ex: {'company_name': {'contains': 'GERDAU'}}).
                     Se None, processa todas as empresas elegíveis.
        """
        filters = {
            "and": [
                # 1. CONTAINS (case insensitive + regex)
                {
                    "company_name": {
                        "contains": "GERDAU",
                        "case": False,
                        "regex": True,
                        "na": False
                    }
                },
                
                # 2. OPERADORES COMPARATIVOS (>, >=, <, <=, !=, in)
                {
                    "id": {">=": 1000}
                },
                {
                    "id": {"<": 5000}
                },
                {
                    "cvm_code": {"in": ["22179", "12345"]}
                },
                {
                    "has_bdr": {"ne": False}  # != False
                },
                
                # 3. OR ANINHADO (com múltiplas condições)
                {
                    "or": [
                        {"market": "NM"},
                        {
                            "and": [
                                {"status": "ATIVO"},
                                {"has_quotation": True}
                            ]
                        }
                    ]
                },
                
                # 4. BOOLEANO direto
                {"has_emissions": True},
                
                # 5. DATA (com operador >=)
                {
                    "listing_date": {">=": "2020-01-01"}
                }
            ]
        }
        with self.uow_factory() as uow:
            companies_eligible: List[CompanyEligibleDTO] = self.companies_eligible_port.list(uow=uow)

        if not companies_eligible:
            return SyncResultsDTO(items=[], metrics=0)

        df = pd.DataFrame([c.to_dict() for c in companies_eligible])

        # === Pré-processamento: JSON → string para .str.contains ===
        json_cols = ['ticker_codes', 'isin_codes', 'other_codes']
        for col in json_cols:
            if col in df.columns:
                try:
                    df[col] = df[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
                except Exception as e:
                    df = df.drop(columns=[col])

        # === Monta e aplica query ===
        if filters:
            query = self._build_query(filters)
            self.logger.log(f"Query aplicada: {query}", level="info")
            try:
                df_filtered = df.query(query)
            except Exception as e:
                self.logger.log(f"Erro na query: {e}", level="error")
                raise ValueError(f"Query inválida: {query}")
        else:
            df_filtered = df
            self.logger.log(f"Sem filtro. Processando {len(df)} empresas.", level="info")

        companies_to_process = [
            CompanyEligibleDTO(**row) for _, row in df_filtered.iterrows()
        ]

        return self.normalize_usecase(companies=companies_to_process)

    def _build_query(self, filters: Dict[str, Any]) -> str:
        """
        Monta uma string de filtro para uso com pandas.DataFrame.query().

        Suporta:
        - contains (com case, regex, na)
        - operadores: >, >=, <, <=, ==, !=, in
        - lógica: and, or, aninhamento com dicionários e listas
        - tipos: str, date, datetime, bool, list, None

        Exemplo de entrada:
            {
                "and": [
                    {"name": {"contains": "Ana", "case": False}},
                    {"age": {"gt": 25}},
                    {"active": True}
                ]
            }

        Saída: "(name.str.contains('Ana', case=False, regex=False, na=True) and age > 25 and active == True)"
        """

        # =============================================================
        # 1. FUNÇÃO AUXILIAR: FORMATA VALORES PARA STRING PANDAS-SEGURA
        # =============================================================
        def _format_value(value: Any) -> str:
            """
            Converte qualquer valor Python em uma representação válida dentro de uma string .query().

            Exemplos:
                "texto" → "'texto'"
                datetime(2023,1,1) → "'2023-01-01T00:00:00'"
                True → "True"
                [1, 2, 3] → "[1, 2, 3]"
                None → "None"
            """
            if value is None:
                return "None"  # pandas entende None como NaN

            elif isinstance(value, (date, datetime)):
                # Datas precisam estar entre aspas simples no .query()
                return f"'{value.isoformat()}'"

            elif isinstance(value, str):
                # Strings sempre entre aspas simples
                return f"'{value}'"

            elif isinstance(value, bool):
                # Booleano: True/False (sem aspas)
                return "True" if value else "False"

            elif isinstance(value, (list, tuple)):
                # Listas: [val1, val2, ...] → usado com 'in'
                formatted_items = [_format_value(v) for v in value]
                return f"[{', '.join(formatted_items)}]"

            else:
                # Números, int, float → direto como string
                return str(value)

        # =============================================================
        # 2. FUNÇÃO AUXILIAR: CONSTRÓI UMA CONDIÇÃO SIMPLES (campo + op)
        # =============================================================
        def _build_condition(field: str, condition: Any) -> str:
            """
            Recebe um campo (ex: 'age') e uma condição (dict ou valor direto)
            e retorna uma string de condição válida para pandas.

            Exemplos:
                _build_condition("name", {"contains": "Ana"}) 
                    → "name.str.contains('Ana', case=True, regex=False, na=True)"

                _build_condition("age", {"gt": 30}) 
                    → "age > 30"
            """
            # Caso 1: Condição é um dicionário com operadores especiais
            if isinstance(condition, dict):

                # --- OPERADOR 'contains' ---
                if 'contains' in condition:
                    val = condition['contains']
                    case = condition.get('case', True)    # padrão: sensível a maiúscula
                    regex = condition.get('regex', False) # padrão: não é regex
                    na = condition.get('na', True)        # padrão: NaN não passa
                    return f"{field}.str.contains({_format_value(val)}, case={case}, regex={regex}, na={na})"

                # --- OPERADORES COMPARATIVOS (gt, gte, lt, lte, eq, ne, in) ---
                op_map = {
                    'gt': '>', 'gte': '>=',
                    'lt': '<', 'lte': '<=',
                    'eq': '==', 'ne': '!=',
                    'in': 'in'
                }
                for op_key, op_sym in op_map.items():
                    if op_key in condition:
                        # Ex: {"gt": 30} → "age > 30"
                        # Ex: {"in": [1,2,3]} → "age in [1, 2, 3]"
                        return f"{field} {op_sym} {_format_value(condition[op_key])}"

            # Caso 2: Valor direto ou dicionário sem operador conhecido
            # → assume igualdade: {"age": 30} ou "age": 30 → "age == 30"
            return f"{field} == {_format_value(condition)}"

        # =============================================================
        # 3. FUNÇÃO RECURSIVA PRINCIPAL: PROCESSA O NÓ DO FILTRO
        # =============================================================
        def _process_node(node: Any) -> str:
            """
            Recebe um nó do dicionário de filtros (dict, list ou valor)
            e retorna uma string de condição pandas válida.

            Suporta:
            - {"and": [...]} ou {"or": [...]}
            - {"campo": condicao}
            - [cond1, cond2] → OR implícito
            - aninhamento profundo
            """

            # --- CASO 1: Dicionário com operador lógico 'and' ou 'or' ---
            if isinstance(node, dict):
                keys = node.keys()
                if len(node) == 1 and {"and", "or"} & keys:
                    op = next(iter(keys))  # pega 'and' ou 'or'
                    subconditions = node[op]  # lista de sub-nós

                    # Processa cada subcondição recursivamente
                    processed_subs = [_process_node(sub) for sub in subconditions]

                    # Junta com ' and ' ou ' or '
                    joiner = " and " if op == "and" else " or "

                    # Se houver mais de uma, envolve em parênteses
                    if len(processed_subs) > 1:
                        return f"({joiner.join(processed_subs)})"
                    else:
                        return processed_subs[0]  # evita parênteses desnecessários

                # --- CASO 2: Dicionário com um único campo → condição simples ---
                elif len(node) == 1:
                    field, cond = next(iter(node.items()))
                    return _build_condition(field, cond)

                # --- CASO 3: Dicionário com múltiplos campos → AND implícito ---
                else:
                    # Ex: {"age": 30, "active": True} → "age == 30 and active == True"
                    conditions = [_build_condition(field, val) for field, val in node.items()]
                    return f"({' and '.join(conditions)})"

            # --- CASO 4: Lista → OR entre todos os itens ---
            elif isinstance(node, list):
                processed = [_process_node(item) for item in node]
                return f"({' or '.join(processed)})"

            # --- ERRO: Tipo não suportado ---
            else:
                raise ValueError(f"Nó inválido: {node}. Tipo: {type(node)}")

        # =============================================================
        # 4. RETORNO FINAL: Inicia o processamento do filtro raiz
        # =============================================================
        return _process_node(filters)
