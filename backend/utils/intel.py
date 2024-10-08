import numpy as np

from utils import system

# statements standardization

# 00.01.01 - Ações ON Ordinárias
# 00.01.02 - Ações PN Preferenciais
# 00.02.01 - Em Tesouraria Ações ON Ordinárias
# 00.02.02 - Em Tesouraria Ações PN Preferenciais
section_0_criteria = [
    {
        'target': '00.01.01 - Ações ON Ordinárias',
        'filter': [
            ['account', 'equals', '00.01.01'],
            ['description', 'equals', 'Ações ON Ordinárias']
        ],
        'sub_criteria': []  # No sub-criteria for this example
    },
    {
        'target': '00.01.02 - Ações PN Preferenciais',
        'filter': [
            ['account', 'equals', '00.01.02'],
            ['description', 'equals', 'Ações PN Preferenciais']
        ],
        'sub_criteria': []  # No sub-criteria for this example
    },
    {
        'target': '00.02.01 - Em Tesouraria Ações ON Ordinárias',
        'filter': [
            ['account', 'equals', '00.02.01'],
            ['description', 'equals', 'Em Tesouraria Ações ON Ordinárias']
        ],
        'sub_criteria': []  # No sub-criteria for this example
    },
    {
        'target': '00.02.02 - Em Tesouraria Ações PN Preferenciais',
        'filter': [
            ['account', 'equals', '00.02.02'],
            ['description', 'equals', 'Em Tesouraria Ações PN Preferenciais']
        ],
        'sub_criteria': []  # No sub-criteria for this example
    }
]

# 01 - Ativo Total
# 01.01 - Ativo Circulante de Curto Prazo
# 01.01.01 - Caixa e Equivalentes de Caixa de Curto Prazo
# 01.01.01.01 - Caixa e Bancos de Curto Prazo
# 01.01.01.02 - Aplicações Líquidas de Curto Prazo
# 01.01.02 - Aplicações Financeiras de Curto Prazo
# 01.01.02.01 - Aplicações a Valor Justo de Curto Prazo
# 01.01.02.02 - Aplicações ao Custo Amortizado de Curto Prazo
# 01.01.03 - Contas a Receber de Curto Prazo
# 01.01.03.01 - Contas de Clientes de Curto Prazo
# 01.01.03.01.01 - Clientes
# 01.01.03.01.02 - Créditos de Liquidação Duvidosa
# 01.01.03.01.03 - Outros
# 01.01.03.02 - Outras Contas de Curto Prazo
# 01.01.04 - Estoques de Curto Prazo
# 01.01.04.01 - Estoques de Material de Consumo de Curto Prazo
# 01.01.04.02 - Estoques de Material para Revenda de Curto Prazo
# 01.01.04.03 - Estoques de Outros Itens de Curto Prazo
# 01.01.05 - Ativos Biológicos de Curto Prazo
# 01.01.06 - Tributos a Recuperar de Curto Prazo
# 01.01.07 - Despesas Antecipadas de Curto Prazo
# 01.01.09 - Outros Ativos Circulantes de Curto Prazo
# 01.02 - Ativo Não Circulante de Longo Prazo
# 01.02.01 - Ativo Realizável a Longo Prazo
# 01.02.01.02 - Aplicações a Valor Justo de Longo Prazo
# 01.02.01.03 - Contas a Receber de Longo Prazo
# 01.02.01.04 - Estoques de Longo Prazo
# 01.02.01.05 - Ativos Biológicos de Longo Prazo
# 01.02.01.06 - Tributos a Recuperar de Longo Prazo
# 01.02.01.07 - Despesas Antecipadas de Longo Prazo
# 01.02.01.08 - Créditos com Partes Relacionadas de Longo Prazo
# 01.02.01.09 - Outros Ativos Circulantes de Longo Prazo
# 01.02.02 - Investimentos
# 01.02.02.01 - Participações Societárias
# 01.02.02.01.01 - Participações em Coligadas
# 01.02.02.01.02 - Participações em Controladas
# 01.02.02.01.03 - Outras
# 01.02.02.02 - Propriedades para Investimento
# 01.02.03 - Imobilizado
# 01.02.03.01 - Imobilizado em Operação
# 01.02.03.02 - Direito de Uso em Arrendamento
# 01.02.04 - Intangível
# 01.02.04.01 - Intangíveis
# 01.02.04.01.01 - Carteira de Clientes
# 01.02.04.01.02 - Softwares
# 01.02.04.01.03 - Marcas e Patentes
# 01.02.04.02 - Goodwill
# 01.02.04.02.01 - Goodwill
# 01.02.04.02.02 - Mais Valia
section_1_criteria = [
    {
        'target': '01 - Ativo Total',
        'filter': [
            ['account', 'level', 1],
            ['account', 'startswith', '1']
        ],
        'sub_criteria': [
            {
                'target': '01.01 - Ativo Circulante de Curto Prazo',
                'filter': [
                    ['account', 'level', 2],
                    ['account', 'startswith', '1.01'],
                    ['description', 'contains_all', 'circul'],
                    ['description', 'not_contains', 'não']
                ],
                'sub_criteria': [
                    {
                        'target': '01.01.01 - Caixa e Equivalentes de Caixa de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'caixa']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.01.01.01 - Caixa e Bancos de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.01'],
                                    ['description', 'contains_all', 'caix']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.01.01.02 - Aplicações Líquidas de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.01'],
                                    ['description', 'contains_all', 'aplic']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '01.01.02 - Aplicações Financeiras de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'aplica']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.01.02.01 - Aplicações a Valor Justo de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.02'],
                                    ['description', 'contains_all', 'just']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.01.02.02 - Aplicações ao Custo Amortizado de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.02'],
                                    ['description', 'contains_all', 'cust']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '01.01.03 - Contas a Receber de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'receb']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.01.03.01 - Contas de Clientes de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.03'],
                                    ['description', 'contains_all', 'client']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '01.01.03.01.01 - Clientes',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.01.03.01'],
                                            ['description', 'contains_all', 'client']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '01.01.03.01.02 - Créditos de Liquidação Duvidosa',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.01.03.01'],
                                            ['description', 'contains_all', 'duvid']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '01.01.03.01.03 - Outros',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.01.03.01'],
                                            ['description', 'contains_none', ['client', 'duvid']]
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '01.01.03.02 - Outras Contas de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.03'],
                                    ['description', 'not_contains', 'client']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '01.01.04 - Estoques de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'estoq']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.01.04.01 - Estoques de Material de Consumo de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.04'],
                                    ['description', 'contains_all', 'mater']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.01.04.02 - Estoques de Material para Revenda de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.04'],
                                    ['description', 'contains_all', 'revend']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.01.04.03 - Estoques de Outros Itens de Curto Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.01.04'],
                                    ['description', 'contains_none', ['mater', 'revend']]
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '01.01.05 - Ativos Biológicos de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'biol']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '01.01.06 - Tributos a Recuperar de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'tribut']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '01.01.07 - Despesas Antecipadas de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'despes']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '01.01.09 - Outros Ativos Circulantes de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.01'],
                            ['description', 'contains_all', 'outros']
                        ],
                        'sub_criteria': []
                    }
                ]
            },
            {
                'target': '01.02 - Ativo Não Circulante de Longo Prazo',
                'filter': [
                    ['account', 'level', 2],
                    ['account', 'startswith', '1.02'],
                    ['description', 'contains_all', ['não', 'circul']]
                ],
                'sub_criteria': [
                    {
                        'target': '01.02.01 - Ativo Realizável a Longo Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.02'],
                            ['description', 'contains_all', 'longo prazo']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.02.01.02 - Aplicações a Valor Justo de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'aplic']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.01.03 - Contas a Receber de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'cont']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.01.04 - Estoques de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'estoq']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.01.05 - Ativos Biológicos de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'biol']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.01.06 - Tributos a Recuperar de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'tribut']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.01.07 - Despesas Antecipadas de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'despes']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.01.08 - Créditos com Partes Relacionadas de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'relacionad']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.01.09 - Outros Ativos Circulantes de Longo Prazo',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.01'],
                                    ['description', 'contains_all', 'outros'],
                                    ['description', 'not_contains', 'aplic']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '01.02.02 - Investimentos',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.02'],
                            ['description', 'contains_all', 'invest']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.02.02.01 - Participações Societárias',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.02'],
                                    ['description', 'contains_all', 'particip']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '01.02.02.01.01 - Participações em Coligadas',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.02.01'],
                                            ['description', 'contains_all', 'colig']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '01.02.02.01.02 - Participações em Controladas',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.02.01'],
                                            ['description', 'contains_all', 'control']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '01.02.02.01.03 - Outras',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.02.01'],
                                            ['description', 'contains_none', ['colig', 'control']]
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '01.02.02.02 - Propriedades para Investimento',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.02'],
                                    ['description', 'contains_all', 'propried']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '01.02.03 - Imobilizado',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.02'],
                            ['description', 'contains_all', 'imob']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.02.03.01 - Imobilizado em Operação',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.03'],
                                    ['description', 'contains_all', 'imobiliz']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '01.02.03.02 - Direito de Uso em Arrendamento',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.03'],
                                    ['description', 'contains_all', 'direito']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '01.02.04 - Intangível',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '1.02'],
                            ['description', 'contains_all', 'intang']
                        ],
                        'sub_criteria': [
                            {
                                'target': '01.02.04.01 - Intangíveis',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.04'],
                                    ['description', 'contains_all', 'intang']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '01.02.04.01.01 - Carteira de Clientes',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.04.01'],
                                            ['description', 'contains_all', 'client']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '01.02.04.01.02 - Softwares',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.04.01'],
                                            ['description', 'contains_any', ['softwar', 'aplicativ', 'sistem']]
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '01.02.04.01.03 - Marcas e Patentes',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.04.01'],
                                            ['description', 'contains_any', ['marc', 'patent']]
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '01.02.04.02 - Goodwill',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '1.02.04'],
                                    ['description', 'contains_all', 'goodwill']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '01.02.04.02.01 - Goodwill',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.04.02'],
                                            ['description', 'contains_any', ['ágio', 'agio', 'goodwill']]
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '01.02.04.02.02 - Mais Valia',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '1.02.04.02'],
                                            ['description', 'contains_all', 'mais valia']
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
]

# 02 - Passivo Total
# 02.01 - Passivo Circulante de Curto Prazo
# 02.01.01 - Obrigações Sociais e Trabalhistas de Curto Prazo
# 02.01.01.01 - Obrigações Sociais
# 02.01.01.02 - Obrigações Trabalhistas
# 02.01.02 - Fornecedores de Curto Prazo
# 02.01.02.01 - Fornecedores Nacionais
# 02.01.02.02 - Fornecedores Estrangeiros
# 02.01.03 - Obrigações Fiscais de Curto Prazo
# 02.01.03.01 - Obrigações Fiscais Federais
# 02.01.03.01.01 - Imposto de Renda e Contribuição Social a Pagar
# 02.01.03.01.02 - Outras Obrigações Fiscais Federais
# 02.01.03.01.03 - Tributos Parcelados
# 02.01.03.02 - Obrigações Fiscais Estaduais
# 02.01.03.03 - Obrigações Fiscais Municipais
# 02.01.04 - Empréstimos e Financiamentos de Curto Prazo
# 02.01.04.01 - Empréstimos e Financiamentos
# 02.01.04.01.01 - Em Moeda Nacional
# 02.01.04.01.02 - Em Moeda Estrangeira
# 02.01.04.02 - Debêntures
# 02.01.04.03 - Financiamento por Arrendamento Financeiro
# 02.01.05 - Outras Obrigações de Curto Prazo
# 02.01.05.01 - Passivos com Partes Relacionadas
# 02.01.05.01.01 - Débitos com Coligadas
# 02.01.05.01.03 - Débitos com Controladores
# 02.01.05.01.04 - Débitos com Outras Partes Relacionadas
# 02.01.05.02 - Outros
# 02.01.05.02.01 - Dividendos e Ações
# 02.01.05.02.02 - Obrigações Tributárias e Autorizações
# 02.01.05.02.03 - Telecomunicações e Consignações
# 02.01.05.02.04 - Derivativos e Participações
# 02.01.05.02.09 - Outros
# 02.01.06 - Provisões de Curto Prazo
# 02.01.06.01 - Provisões Judiciais
# 02.01.06.01.01 - Provisões Fiscais
# 02.01.06.01.02 - Provisões Previdenciárias e Trabalhistas
# 02.01.06.01.03 - Provisões para Benefícios a Empregados
# 02.01.06.01.04 - Provisões Cíveis
# 02.01.06.02 - Outras Provisões
# 02.01.06.02.01 - Provisões para Garantias
# 02.01.06.02.02 - Provisões para Reestruturação
# 02.01.06.02.03 - Provisões para Passivos Ambientais e de Desativação
# 02.02 - Passivo Não Circulante de Longo Prazo
# 02.02.01 - Empréstimos e Financiamentos de Longo Prazo
# 02.02.01.01 - Empréstimos e Financiamentos
# 02.02.01.01.01 - Em Moeda Nacional
# 02.02.01.01.02 - Em Moeda Estrangeira
# 02.02.01.02 - Debêntures
# 02.02.01.03 - Financiamento por Arrendamento Financeiro
# 02.02.02 - Passivos com Partes Relacionadas de Longo Prazo
# 02.02.02.01 - Débitos com Partes Relacionadas
# 02.02.02.01.01 - Débitos com Coligadas
# 02.02.02.01.03 - Débitos com Controladores
# 02.02.02.01.04 - Débitos com Outras Partes Relacionadas
# 02.02.02.02 - Obrigações por Pagamentos Baseados em Ações
# 02.02.02.03 - Adiantamento para Futuro Aumento de Capital
# 02.02.02.04 - Tributos Parcelados
# 02.02.03 - Imposto de Renda e Contribuição Social Diferidos
# 02.02.04 - Provisões de Longo Prazo
# 02.02.04.01 - Provisões Fiscais Previdenciárias Trabalhistas e Cíveis
# 02.02.04.02 - Outras Provisões
# 02.02.04.02.01 - Provisões para Garantias
# 02.02.04.02.02 - Provisões para Reestruturação
# 02.02.04.02.03 - Provisões para Passivos Ambientais e de Desativação
# 02.02.04.02.04 - Fornecedores de Equipamentos
# 02.02.04.02.09 - Outras Obrigações
# 02.03 - Patrimônio Líquido
# 02.03.01 - Capital Social Realizado
# 02.03.01.01 - Capital Social
# 02.03.01.02 - Gastos na emissão de ações
# 02.03.02 - Reservas de Capital
# 02.03.02.01 - Ágio e Reserva Especial
# 02.03.02.02 - Ações, Remuneração e Opções
# 02.03.02.09 - Outros
# 02.03.03 - Reservas de Reavaliação
# 02.03.04 - Reservas de Lucros
# 02.03.04.01 - Reservas Legais e Estatutárias
# 02.03.04.02 - Retenção de Lucros e Incentivos Fiscais
# 02.03.04.03 - Dividendos e Ações em Tesouraria
# 02.03.04.09 - Outros
# 02.03.05 - Lucros/Prejuízos Acumulados
# 02.03.06 - Ajustes de Avaliação Patrimonial
# 02.03.06.01 - Ajustes Patrimoniais
# 02.03.06.02 - Perdas e Aquisições com Não Controladores
# 02.03.06.09 - Outros
# 02.03.07 - Ajustes Acumulados de Conversão
# 02.03.08 - Outros Resultados Abrangentes
# 02.03.09 - Participação dos Acionistas Não Controladores
section_2_criteria = [
    {
        'target': '02 - Passivo Total',
        'filter': [
            ['account', 'level', 1],
            ['account', 'startswith', '2']
        ],
        'sub_criteria': [
            {
                'target': '02.01 - Passivo Circulante de Curto Prazo',
                'filter': [
                    ['account', 'level', 2],
                    ['account', 'startswith', '2.01'],
                    ['description', 'contains_all', 'circul'],
                    ['description', 'not_contains', 'não']
                ],
                'sub_criteria': [
                    {
                        'target': '02.01.01 - Obrigações Sociais e Trabalhistas de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.01'],
                            ['description', 'contains_all', ['soc', 'trab']]
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.01.01.01 - Obrigações Sociais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.01'],
                                    ['description', 'contains_all', 'soc']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.01.01.02 - Obrigações Trabalhistas',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.01'],
                                    ['description', 'contains_all', 'trabalh']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.01.02 - Fornecedores de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.01'],
                            ['description', 'contains_all', 'forneced']
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.01.02.01 - Fornecedores Nacionais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.02'],
                                    ['description', 'contains_all', 'nacion']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.01.02.02 - Fornecedores Estrangeiros',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.02'],
                                    ['description', 'contains_all', 'estrang']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.01.03 - Obrigações Fiscais de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.01'],
                            ['description', 'contains_all', 'fisc']
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.01.03.01 - Obrigações Fiscais Federais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.03'],
                                    ['description', 'contains_all', 'feder']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.01.03.01.01 - Imposto de Renda e Contribuição Social a Pagar',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.03.01'],
                                            ['description', 'contains_all', 'renda']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.03.01.02 - Outras Obrigações Fiscais Federais',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.03.01'],
                                            ['description', 'contains_all', 'outras']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.03.01.03 - Tributos Parcelados',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.03.01'],
                                            ['description', 'contains_all', 'parcelados']
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '02.01.03.02 - Obrigações Fiscais Estaduais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.03'],
                                    ['description', 'contains_all', 'estad']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.01.03.03 - Obrigações Fiscais Municipais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.03'],
                                    ['description', 'contains_all', 'municip']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.01.04 - Empréstimos e Financiamentos de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.01'],
                            ['description', 'contains_any', ['emprést', 'emprest', 'financ']]
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.01.04.01 - Empréstimos e Financiamentos',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.04'],
                                    ['description', 'contains_any', ['emprést', 'emprest', 'financ']]
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.01.04.01.01 - Em Moeda Nacional',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.04.01'],
                                            ['description', 'contains_all', 'nacion']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.04.01.02 - Em Moeda Estrangeira',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.04.01'],
                                            ['description', 'contains_all', 'estrang']
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '02.01.04.02 - Debêntures',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.04'],
                                    ['description', 'contains_any', ['debênt', 'debent']]
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.01.04.03 - Financiamento por Arrendamento Financeiro',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.04'],
                                    ['description', 'contains_all', 'arrend']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.01.05 - Outras Obrigações de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.01'],
                            ['description', 'contains_all', 'obrig'],
                            ['description', 'not_contains', 'fisc']
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.01.05.01 - Passivos com Partes Relacionadas',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.05'],
                                    ['description', 'contains_all', 'passiv']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.01.05.01.01 - Débitos com Coligadas',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.01'],
                                            ['description', 'contains_all', 'colig']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.05.01.03 - Débitos com Controladores',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.01'],
                                            ['description', 'contains_all', 'control']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.05.01.04 - Débitos com Outras Partes Relacionadas',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.01'],
                                            ['description', 'contains_none', ['colig', 'control']]
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '02.01.05.02 - Outros',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.05'],
                                    ['description', 'not_contains', 'passiv']
                                ],
                                'sub_criteria': [
                                    # Group 1: Dividendos e Ações
                                    {
                                        'target': '02.01.05.02.01 - Dividendos e Ações',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.02'],
                                            ['description', 'contains_any', ['divid', ' ações']],
                                        ],
                                        'sub_criteria': []
                                    },
                                    # Group 2: Obrigações Tributárias e Autorizações
                                    {
                                        'target': '02.01.05.02.02 - Obrigações Tributárias e Autorizações',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.02'],
                                            ['description', 'contains_any', ['tribut', 'autoriz', 'concessão']],
                                        ],
                                        'sub_criteria': []
                                    },
                                    # Group 3: Telecomunicações e Consignações
                                    {
                                        'target': '02.01.05.02.03 - Telecomunicações e Consignações',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.02'],
                                            ['description', 'contains_any', ['telecomunicação', 'interconex', 'consign']],
                                        ],
                                        'sub_criteria': []
                                    },
                                    # Group 4: Derivativos e Participações
                                    {
                                        'target': '02.01.05.02.04 - Derivativos e Participações',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.02'],
                                            ['description', 'contains_any', ['derivativ', 'participações']],
                                        ],
                                        'sub_criteria': []
                                    },
                                    # 02.01.05.02.09 - Outros
                                    {
                                        'target': '02.01.05.02.09 - Outros',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.05.02'],
                                            ['description', 'contains_none', ['divid', ' ações', 'tribut', 'autoriz', 'telecomunicação', 'interconex', 'consign', 'derivativ', 'participações']],
                                        ],
                                        'sub_criteria': []
                                    },
                                ]
                            }
                        ]
                    },
                    {
                        'target': '02.01.06 - Provisões de Curto Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.01'],
                            ['description', 'contains_all', 'provis']
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.01.06.01 - Provisões Judiciais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.06'],
                                    ['description', 'not_contains', 'outr']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.01.06.01.01 - Provisões Fiscais',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.06.01'],
                                            ['description', 'contains_all', 'fisc']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.06.01.02 - Provisões Previdenciárias e Trabalhistas',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.06.01'],
                                            ['description', 'contains_any', ['previd', 'trabalh']]
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.06.01.03 - Provisões para Benefícios a Empregados',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.06.01'],
                                            ['description', 'contains_all', 'benef']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.06.01.04 - Provisões Cíveis',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.06.01'],
                                            ['description', 'contains_all', 'cív']
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '02.01.06.02 - Outras Provisões',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.01.06'],
                                    ['description', 'contains_all', 'outr']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.01.06.02.01 - Provisões para Garantias',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.06.02'],
                                            ['description', 'contains_all', 'garant']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.06.02.02 - Provisões para Reestruturação',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.06.02'],
                                            ['description', 'contains_all', 'reestrut']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.01.06.02.03 - Provisões para Passivos Ambientais e de Desativação',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.01.06.02'],
                                            ['description', 'contains_all', 'ambient']
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                'target': '02.02 - Passivo Não Circulante de Longo Prazo',
                'filter': [
                    ['account', 'level', 2],
                    ['account', 'startswith', '2.02'],
                    ['description', 'contains_all', ['circul', 'não']]
                ],
                'sub_criteria': [
                    {
                        'target': '02.02.01 - Empréstimos e Financiamentos de Longo Prazo',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.02'],
                            ['description', 'contains_any', ['emprést', 'emprest', 'financ']]
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.02.01.01 - Empréstimos e Financiamentos',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.02.01'],
                                    ['description', 'contains_any', ['emprést', 'emprest', 'financ']]
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.02.01.01.01 - Em Moeda Nacional',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.01.01'],
                                            ['description', 'contains_all', 'nacion']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.02.01.01.02 - Em Moeda Estrangeira',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.01.01'],
                                            ['description', 'contains_all', 'estrang']
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '02.02.01.02 - Debêntures',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.02.01'],
                                    ['description', 'contains_any', ['debênt', 'debent']]
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.02.01.03 - Financiamento por Arrendamento Financeiro',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.02.01'],
                                    ['description', 'contains_all', 'arrend']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.02.02 - Passivos com Partes Relacionadas de Longo Prazo',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '2.02.02'],
                            ['description', 'contains_all', 'passiv']
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.02.02.01 - Débitos com Partes Relacionadas',
                                'filter': [
                                    ['account', 'level', 5],
                                    ['account', 'startswith', '2.02.02'],
                                    ['description', 'contains_all', 'relacion']
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.02.02.01.01 - Débitos com Coligadas',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.02'],
                                            ['description', 'contains_all', 'colig']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.02.02.01.03 - Débitos com Controladores',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.02'],
                                            ['description', 'contains_all', 'control']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.02.02.01.04 - Débitos com Outras Partes Relacionadas',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.02'],
                                            ['description', 'contains_all', 'relacion']
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            },
                            {
                                'target': '02.02.02.02 - Obrigações por Pagamentos Baseados em Ações',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.02.02'],
                                    ['description', 'contains_all', 'ações']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.02.02.03 - Adiantamento para Futuro Aumento de Capital',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.02.02'],
                                    ['description', 'contains_all', 'capit']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.02.02.04 - Tributos Parcelados',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.02.02'],
                                    ['description', 'contains_all', 'tribut']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.02.03 - Imposto de Renda e Contribuição Social Diferidos',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '2.02.03'],
                            ['description', 'contains_all', 'renda']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '02.02.04 - Provisões de Longo Prazo',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '2.02.04'],
                            ['description', 'contains_any', ['provis']], 
                            ['description', 'contains_none', ['emprest', 'emprést', 'debent', 'debênt', 'outr', 'renda']]
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.02.04.01 - Provisões Fiscais Previdenciárias Trabalhistas e Cíveis',
                                'filter': [
                                    ['account', 'level', 5],
                                    ['account', 'startswith', '2.02.04.01'],
                                    ['description', 'contains_any', ['fisc', 'previd', 'trabalh', 'benef', 'cív']]
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.02.04.02 - Outras Provisões',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.02.04'],
                                    ['description', 'contains_none', ['fisc', 'previd', 'trabalh', 'benef', 'cív']]
                                ],
                                'sub_criteria': [
                                    {
                                        'target': '02.02.04.02.01 - Provisões para Garantias',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.04'],
                                            ['description', 'contains_any', 'garant']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.02.04.02.02 - Provisões para Reestruturação',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.04'],
                                            ['description', 'contains_any', 'reestrutur']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.02.04.02.03 - Provisões para Passivos Ambientais e de Desativação',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.04'],
                                            ['description', 'contains_any', 'ambient']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.02.04.02.04 - Fornecedores de Equipamentos',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.04'],
                                            ['description', 'contains_any', 'forneced']
                                        ],
                                        'sub_criteria': []
                                    },
                                    {
                                        'target': '02.02.04.02.09 - Outras Obrigações',
                                        'filter': [
                                            ['account', 'level', 5],
                                            ['account', 'startswith', '2.02.06'],
                                            ['description', 'contains_none', ['garant', 'reestrutur', 'ambient', 'forneced']]
                                        ],
                                        'sub_criteria': []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                'target': '02.03 - Patrimônio Líquido',
                'filter': [
                    ['account', 'level', 2],
                    ['account', 'startswith', '2.03'],
                    ['description', 'contains_all', ['patrim', 'líquid']]
                ],
                'sub_criteria': [
                    {
                        'target': '02.03.01 - Capital Social Realizado',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', 'soc']
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.03.01.01 - Capital Social',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.01'],
                                    ['description', 'contains_all', 'social']
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.03.01.02 - Gastos na emissão de ações',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.01'],
                                    ['description', 'contains_all', 'ações']
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.03.02 - Reservas de Capital',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03.02'],
                            ['description', 'contains_all', 'capit']
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.03.02.01 - Ágio e Reserva Especial',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.02'],
                                    ['description', 'contains_any', ['ágio', 'prêm', 'prem', 'reserv']]
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.03.02.02 - Ações, Remuneração e Opções',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.02'],
                                    ['description', 'contains_any', [' ações', ' opções', 'remunera', 'tesour']], 
                                    ['description', 'contains_none', ['ágio', 'prêm', 'prem', 'reserv']]
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.03.02.09 - Outros',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.02'],
                                    ['description', 'contains_none', ['ágio', 'prêm', 'prem', 'reserv', ' ações', ' opções', 'remunera', 'tesour']]
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.03.03 - Reservas de Reavaliação',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', 'reaval']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '02.03.04 - Reservas de Lucros',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', 'lucr']
                        ],
                        'sub_criteria': [
                            # Group 1: Legal and Statutory Reserves
                            {
                                'target': '02.03.04.01 - Reservas Legais e Estatutárias',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.04'],
                                    ['description', 'contains_any', ['legal', 'estatutár']]
                                ],
                                'sub_criteria': []
                            },
                            # Group 2: Retenção e Incentivos Fiscais
                            {
                                'target': '02.03.04.02 - Retenção de Lucros e Incentivos Fiscais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.04'],
                                    ['description', 'contains_any', ['retenção', 'incentivo', 'expansão', 'modernização']]
                                ],
                                'sub_criteria': []
                            },
                            # Group 3: Dividendos e Ações em Tesouraria
                            {
                                'target': '02.03.04.03 - Dividendos e Ações em Tesouraria',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.04'],
                                    ['description', 'contains_any', ['dividendo', 'ações em tesouraria']]
                                ],
                                'sub_criteria': []
                            },
                            # Group 4: Outros
                            {
                                'target': '02.03.04.09 - Outros',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.04'],
                                    ['description', 'contains_none', ['lucr', 'legal', 'estatutár', 'retenção', 'incentivo', 'expansão', 'modernização', 'dividendo', 'ações em tesouraria']]
                                ],
                                'sub_criteria': []
                            }
                        ]
                    }, 
                    {
                        'target': '02.03.05 - Lucros/Prejuízos Acumulados',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', 'acumul'],
                            ['description', 'not_contains', 'reserv']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '02.03.06 - Ajustes de Avaliação Patrimonial',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', ['ajust', 'patrim']]
                        ],
                        'sub_criteria': [
                            {
                                'target': '02.03.06.01 - Ajustes Patrimoniais',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.06'],
                                    ['description', 'contains_any', ['ajuste', 'custo atribuído']]
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.03.06.02 - Perdas e Aquisições com Não Controladores',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.06'],
                                    ['description', 'contains_any', ['perda', 'aquisição', 'não controladores']]
                                ],
                                'sub_criteria': []
                            },
                            {
                                'target': '02.03.06.09 - Outros',
                                'filter': [
                                    ['account', 'level', 4],
                                    ['account', 'startswith', '2.03.06'],
                                    ['description', 'contains_none', ['ajuste', 'custo atribuído', 'perda', 'aquisição', 'não controladores']]
                                ],
                                'sub_criteria': []
                            }
                        ]
                    },
                    {
                        'target': '02.03.07 - Ajustes Acumulados de Conversão',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', ['ajust', 'convers']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '02.03.08 - Outros Resultados Abrangentes',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', 'outr']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '02.03.09 - Participação dos Acionistas Não Controladores',
                        'filter': [
                            ['account', 'level', 3],
                            ['account', 'startswith', '2.03'],
                            ['description', 'contains_all', 'controlad']
                        ],
                        'sub_criteria': []
                    }
                ]
            }
        ]
    }
]

# 03.01 - Receita de Venda de Bens e/ou Serviços
# 03.02 - Custo dos Bens e/ou Serviços Vendidos
# 03.03 - Resultado Bruto
# 03.04 - Despesas/Receitas Operacionais
# 03.04.01 - Despesas com Vendas
# 03.04.02 - Despesas Gerais e Administrativas
# 03.04.03 - Outras
# 03.05 - Resultado Antes do Resultado Financeiro e dos Tributos
# 03.06 - Resultado Financeiro
# 03.07 - Resultado Antes dos Tributos sobre o Lucro
# 03.08 - Imposto de Renda e Contribuição Social sobre o Lucro
# 03.09 - Resultado Líquido das Operações Continuadas
# 03.10 - Resultado Líquido das Operações Descontinuadas
# 03.11 - Lucro do Período
# 03.11.01 - Atribuído a Sócios da Empresa Controladora
# 03.11.02 - Atribuído a Sócios Não Controladores
section_3_criteria = [
    {
        'target': '03.01 - Receita de Venda de Bens e/ou Serviços',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.01'],
            ['description', 'contains_all', ['venda', 'bens']]
        ],
        'sub_criteria': []
    },
    {
        'target': '03.02 - Custo dos Bens e/ou Serviços Vendidos',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.02'],
            ['description', 'contains_all', ['custo']]
        ],
        'sub_criteria': []
    },
    {
        'target': '03.03 - Resultado Bruto',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.03'],
            ['description', 'contains_all', ['bruto']]
        ],
        'sub_criteria': []
    },
    {
        'target': '03.04 - Despesas/Receitas Operacionais',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.04']
        ],
        'sub_criteria': [
            {
                'target': '03.04.01 - Despesas com Vendas',
                'filter': [
                    ['account', 'level', 3],
                    ['account', 'startswith', '3.04.01'],
                    ['description', 'contains_all', 'vend']
                ],
                'sub_criteria': []
            },
            {
                'target': '03.04.02 - Despesas Gerais e Administrativas',
                'filter': [
                    ['account', 'level', 3],
                    ['account', 'startswith', '3.04.02'],
                    ['description', 'contains_all', 'administrativ']
                ],
                'sub_criteria': []
            },
            {
                'target': '03.04.03 - Outras Despesas',
                'filter': [
                    ['account', 'level', 3],
                    ['account', 'startswith', '3.04'],
                    ['description', 'contains_none', ['vend', 'administrativ']]
                ],
                'sub_criteria': []
            }
        ]
    },
    {
        'target': '03.05 - Resultado Antes do Resultado Financeiro e dos Tributos',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.05'],
            ['description', 'contains_all', ['resultado', 'antes', 'financeiro']]
        ],
        'sub_criteria': []
    },
    {
        'target': '03.06 - Resultado Financeiro',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.06'],
            ['description', 'contains_all', 'financeiro'], 
            ['description', 'contains_none', 'antes']
        ],
        'sub_criteria': []
    },
    {
        'target': '03.07 - Resultado Antes dos Tributos sobre o Lucro',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.07'],
            ['description', 'contains_all', 'tributos'],
            ['description', 'contains_none', 'financeiro']
        ],
        'sub_criteria': []
    },
    {
        'target': '03.08 - Imposto de Renda e Contribuição Social sobre o Lucro',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.08'],
            ['description', 'contains_all', 'imposto de renda']
        ],
        'sub_criteria': []
    },
    {
        'target': '03.09 - Resultado Líquido das Operações Continuadas',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.09'],
            ['description', 'contains_all', ['resultado líquido', 'Continuadas']],
            ['description', 'contains_none', 'Descontinuadas']
        ],
        'sub_criteria': []
    }, 
    {
        'target': '03.10 - Resultado Líquido das Operações Descontinuadas',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.10'],
            ['description', 'contains_all', ['resultado líquido', 'Descontinuadas']],
            ['description', 'contains_none', 'Continuadas']
        ],
        'sub_criteria': []
    }, 
    {
        'target': '03.11 - Lucro do Período',
        'filter': [
            ['account', 'level', 2],
            ['account', 'startswith', '3.11'],
            ['description', 'contains_all', ['lucro', 'período']]
        ],
        'sub_criteria': [
            {
                'target': '03.11.01 - Atribuído a Sócios da Empresa Controladora',
                'filter': [
                    ['account', 'level', 3],
                    ['account', 'startswith', '3.11.01'],
                    ['description', 'contains_all', 'controladora'], 
                    ['description', 'contains_none', 'não']
                ],
                'sub_criteria': []
            },
            {
                'target': '03.11.02 - Atribuído a Sócios Não Controladores',
                'filter': [
                    ['account', 'level', 3],
                    ['account', 'startswith', '3.11.02'],
                    ['description', 'contains_all', ['não', 'controladores']], 
                ],
                'sub_criteria': []
            }
        ]
    }
]

# 06.01 - Caixa de Operações (Operacional)
# 06.02 - Caixa de Investimento
# 06.03 - Caixa de Financiamento
section_6_criteria = [
    {
        'target': '06.01 - Caixa de Operações (Operacional)',
        'filter': [
            ['account', 'equals', '6.01'],
       ],
    },
    {
        'target': '06.02 - Caixa de Investimento',
        'filter': [
            ['account', 'equals', '6.02'],
       ],
    },
    {
        'target': '06.03 - Caixa de Financiamento',
        'filter': [
            ['account', 'equals', '6.03'],
       ],
    },
]

# 07.01 - Receitas
# 07.01.01 - Vendas de Mercadorias, Produtos e Serviços
# 07.01.02 - Outras Receitas
# 07.01.03 - Receitas refs. à Construção de Ativos Próprios
# 07.01.04 - Provisão/Reversão de Créds. Liquidação Duvidosa
# 07.02 - Insumos Adquiridos de Terceiros
# 07.02.01 - Custos Prods., Mercs. e Servs. Vendidos
# 07.02.02 - Materiais, Energia, Servs. de Terceiros e Outros
# 07.02.03 - Perda/Recuperação de Valores Ativos
# 07.02.04 - Outros
# 07.03 - Valor Adicionado Bruto
# 07.04 - Retenções
# 07.04.01 - Depreciação, Amortização e Exaustão
# 07.04.02 - Outras
# 07.05 - Valor Adicionado Líquido Produzido
# 07.06 - Vlr Adicionado Recebido em Transferência
# 07.06.01 - Resultado de Equivalência Patrimonial
# 07.06.02 - Receitas Financeiras
# 07.06.03 - Outros
# 07.06.03.01 - Dividendos
# 07.06.03.02 - Aluguéis
# 07.07 - Valor Adicionado Total a Distribuir
# 07.08 - Distribuição do Valor Adicionado
# 07.08.01 - Pessoal
# 07.08.01.01 - Remuneração Direta
# 07.08.01.02 - Benefícios
# 07.08.01.03 - F.G.T.S.
# 07.08.01.04 - Outros
# 07.08.02 - Impostos, Taxas e Contribuições
# 07.08.02.01 - Federais
# 07.08.02.02 - Estaduais
# 07.08.02.03 - Municipais
# 07.08.03 - Remuneração de Capitais de Terceiros
# 07.08.03.01 - Juros
# 07.08.03.02 - Aluguéis
# 07.08.03.03 - Outras
# 07.08.04 - Remuneração de Capitais Próprios
# 07.08.04.01 - Juros sobre o Capital Próprio
# 07.08.04.02 - Dividendos
# 07.08.04.03 - Lucros Retidos / Prejuízo do Período
# 07.08.04.04 - Part. Não Controladores nos Lucros Retidos
# 07.08.05 - Outros
# 07.08.05.01 - Provisões trabalhistas e cíveis, líquidas
# 07.08.05.02 - Investimento Social
# 07.08.05.03 - Lucros Retidos
# 07.08.05.04 - Participação Minoritária
# 07.08.05.09 - Outros
section_7_criteria = [
    {
        'target': '07.01 - Receitas',
        'filter': [['account', 'equals', '7.01']],
        'sub_criteria': [
            {
                'target': '07.01.01 - Vendas de Mercadorias, Produtos e Serviços',
                'filter': [['account', 'equals', '7.01.01']],
                'sub_criteria': []
            },
            {
                'target': '07.01.02 - Outras Receitas',
                'filter': [['account', 'equals', '7.01.02']],
                'sub_criteria': []
            },
            {
                'target': '07.01.03 - Receitas refs. à Construção de Ativos Próprios',
                'filter': [['account', 'equals', '7.01.03']],
                'sub_criteria': []
            },
            {
                'target': '07.01.04 - Provisão/Reversão de Créds. Liquidação Duvidosa',
                'filter': [['account', 'equals', '7.01.04']],
                'sub_criteria': []
            }
        ]
    },
    {
        'target': '07.02 - Insumos Adquiridos de Terceiros',
        'filter': [['account', 'equals', '7.02']],
        'sub_criteria': [
            {
                'target': '07.02.01 - Custos Prods., Mercs. e Servs. Vendidos',
                'filter': [['account', 'equals', '7.02.01']],
                'sub_criteria': []
            },
            {
                'target': '07.02.02 - Materiais, Energia, Servs. de Terceiros e Outros',
                'filter': [['account', 'equals', '7.02.02']],
                'sub_criteria': []
            },
            {
                'target': '07.02.03 - Perda/Recuperação de Valores Ativos',
                'filter': [['account', 'equals', '7.02.03']],
                'sub_criteria': []
            },
            {
                'target': '07.02.04 - Outros',
                'filter': [['account', 'equals', '7.02.04']],
                'sub_criteria': []
            }
        ]
    },
    {
        'target': '07.03 - Valor Adicionado Bruto',
        'filter': [['account', 'equals', '7.03']],
        'sub_criteria': []
    },
    {
        'target': '07.04 - Retenções',
        'filter': [['account', 'equals', '7.04']],
        'sub_criteria': [
            {
                'target': '07.04.01 - Depreciação, Amortização e Exaustão',
                'filter': [['account', 'equals', '7.04.01']],
                'sub_criteria': []
            },
            {
                'target': '07.04.02 - Outras',
                'filter': [['account', 'equals', '7.04.02']],
                'sub_criteria': []
            }
        ]
    },
    {
        'target': '07.05 - Valor Adicionado Líquido Produzido',
        'filter': [['account', 'equals', '7.05']],
        'sub_criteria': []
    },
    {
        'target': '07.06 - Vlr Adicionado Recebido em Transferência',
        'filter': [['account', 'equals', '7.06']],
        'sub_criteria': [
            {
                'target': '07.06.01 - Resultado de Equivalência Patrimonial',
                'filter': [['account', 'equals', '7.06.01']],
                'sub_criteria': []
            },
            {
                'target': '07.06.02 - Receitas Financeiras',
                'filter': [['account', 'equals', '7.06.02']],
                'sub_criteria': []
            },
            {
                'target': '07.06.03 - Outros',
                'filter': [['account', 'equals', '7.06.03']],
                'sub_criteria': [
                    {
                        'target': '07.06.03.01 - Dividendos',
                        'filter': [
                            ['account', 'startswith', '7.06.03'],
                            ['description', 'contains_all', ['dividend']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.06.03.02 - Aluguéis',
                        'filter': [
                            ['account', 'startswith', '7.06.03'],
                            ['description', 'contains_all', ['alugue']]
                        ],
                        'sub_criteria': []
                    }
                ]
            }
        ]
    },
    {
        'target': '07.07 - Valor Adicionado Total a Distribuir',
        'filter': [['account', 'equals', '7.07']],
        'sub_criteria': []
    },
    {
        'target': '07.08 - Distribuição do Valor Adicionado',
        'filter': [['account', 'equals', '7.08']],
        'sub_criteria': [
            {
                'target': '07.08.01 - Pessoal',
                'filter': [['account', 'equals', '7.08.01']],
                'sub_criteria': [
                    {
                        'target': '07.08.01.01 - Remuneração Direta',
                        'filter': [['account', 'equals', '7.08.01.01']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.01.02 - Benefícios',
                        'filter': [['account', 'equals', '7.08.01.02']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.01.03 - F.G.T.S.',
                        'filter': [['account', 'equals', '7.08.01.03']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.01.04 - Outros',
                        'filter': [['account', 'equals', '7.08.01.04']],
                        'sub_criteria': []
                    }
                ]
            },
            {
                'target': '07.08.02 - Impostos, Taxas e Contribuições',
                'filter': [['account', 'equals', '7.08.02']],
                'sub_criteria': [
                    {
                        'target': '07.08.02.01 - Federais',
                        'filter': [['account', 'equals', '7.08.02.01']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.02.02 - Estaduais',
                        'filter': [['account', 'equals', '7.08.02.02']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.02.03 - Municipais',
                        'filter': [['account', 'equals', '7.08.02.03']],
                        'sub_criteria': []
                    }
                ]
            },
            {
                'target': '07.08.03 - Remuneração de Capitais de Terceiros',
                'filter': [['account', 'equals', '7.08.03']],
                'sub_criteria': [
                    {
                        'target': '07.08.03.01 - Juros',
                        'filter': [['account', 'equals', '7.08.03.01']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.03.02 - Aluguéis',
                        'filter': [['account', 'equals', '7.08.03.02']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.03.03 - Outras',
                        'filter': [['account', 'equals', '7.08.03.03']],
                        'sub_criteria': []
                    }
                ]
            },
            {
                'target': '07.08.04 - Remuneração de Capitais Próprios',
                'filter': [['account', 'equals', '7.08.04']],
                'sub_criteria': [
                    {
                        'target': '07.08.04.01 - Juros sobre o Capital Próprio',
                        'filter': [['account', 'equals', '7.08.04.01']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.04.02 - Dividendos',
                        'filter': [['account', 'equals', '7.08.04.02']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.04.03 - Lucros Retidos / Prejuízo do Período',
                        'filter': [['account', 'equals', '7.08.04.03']],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.04.04 - Part. Não Controladores nos Lucros Retidos',
                        'filter': [['account', 'equals', '7.08.04.04']],
                        'sub_criteria': []
                    }
                ]
            },
            {
                'target': '07.08.05 - Outros',
                'filter': [['account', 'equals', '7.08.05']],
                'sub_criteria': [
                    {
                        'target': '07.08.05.01 - Provisões trabalhistas e cíveis, líquidas',
                        'filter': [
                            ['account', 'startswith', '7.08.05'],
                            ['description', 'contains_all', ['trabalhist']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.05.02 - Investimento Social',
                        'filter': [
                            ['account', 'startswith', '7.08.05'],
                            ['description', 'contains_all', ['social']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.05.03 - Lucros Retidos',
                        'filter': [
                            ['account', 'startswith', '7.08.05'],
                            ['description', 'contains_all', ['lucr']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.05.04 - Participação Minoritária',
                        'filter': [
                            ['account', 'startswith', '7.08.05'],
                            ['description', 'contains_all', ['minorit']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '07.08.05.09 - Outros',
                        'filter': [
                            ['account', 'startswith', '7.08.05'],
                            ['description', 'contains_none', ['trabalhist', 'social', 'lucr', 'minorit']]
                        ],
                        'sub_criteria': []
                    }
                ]
            }
        ]
    }
]

# imobilizado e intangível
investment_keywords = ['investiment', 'mobiliár', 'derivativ', 'propriedad']
tangible_intangible_keywords = ['imob', 'intangív']
financial_keywords = ['financeir']
affiliated_controlled_keywords = ['coligad', 'controlad', 'ligad']
interest_dividends_keywords = ['juro', 'jcp', 'jscp', 'dividend']
all_investment_related_keywords = list(set(investment_keywords + tangible_intangible_keywords + financial_keywords + affiliated_controlled_keywords + interest_dividends_keywords))

# dividend juros jcp, jscp bonifica, 
capital_keywords = ['capital']
shares_keywords = ['ação', 'ações', 'acionist']
debentures_loans_keywords = ['debentur', 'empréstim', 'financiam']
creditor_keywords = ['credor']
amortization_funding_keywords = ['amortizaç', 'captaç']
dividends_interest_keywords = ['dividend', 'juros', 'jcp', 'bonifica']
all_financing_related_keywords = list(set(capital_keywords + shares_keywords + debentures_loans_keywords + creditor_keywords + amortization_funding_keywords + dividends_interest_keywords))

class Formula:
    '''
    Base class for all formula operations.
    '''
    def __call__(self, df):
        raise NotImplementedError('Each formula must implement the __call__ method.')

class Addition(Formula):
    def __init__(self, *accounts, multiplier=1):
        '''
        Initializes the Addition operation.

        Parameters:
        - *accounts: A list of account names or Formula instances to be summed.
        '''
        if len(accounts) < 1:
            raise ValueError('Addition requires at least one account.')
        self.accounts = accounts
        self.multiplier = multiplier

    def __call__(self, df):
        try:
            # Sum all accounts or formulas
            result = sum(
                acc(df) if isinstance(acc, Formula) else df[acc]
                for acc in self.accounts
            )
            return result * self.multiplier
        except KeyError as e:
            raise KeyError(f'Missing account: {e}')

class Subtraction(Formula):
    def __init__(self, minuend, *subtrahends, multiplier=1):
        '''
        Initializes the Subtraction operation.

        Parameters:
        - minuend (str or Formula): The account name or Formula instance from which to subtract.
        - *subtrahends: A list of account names or Formula instances to subtract.
        '''
        if len(subtrahends) < 1:
            raise ValueError('Subtraction requires at least one subtrahend.')
        self.minuend = minuend
        self.subtrahends = subtrahends
        self.multiplier = multiplier

    def __call__(self, df):
        try:
            # Compute minuend value
            result = self.minuend(df) if isinstance(self.minuend, Formula) else df[self.minuend]
            # Subtract each subtrahend
            for acc in self.subtrahends:
                sub_val = acc(df) if isinstance(acc, Formula) else df[acc]
                result -= sub_val
            return result * self.multiplier
        except KeyError as e:
            raise KeyError(f'Missing account: {e}')

class Multiplication(Formula):
    def __init__(self, *multiplicands, multiplier=1):
        '''
        Initializes the Multiplication operation.

        Parameters:
        - *multiplicands: A list of account names or Formula instances to be multiplied.
        '''
        if len(multiplicands) < 1:
            raise ValueError('Multiplication requires at least one multiplicand.')
        self.multiplicands = multiplicands
        self.multiplier = multiplier

    def __call__(self, df):
        try:
            # Start with an initial value of 1 for multiplication
            result = np.ones(len(df))
            # Multiply each multiplicand
            for acc in self.multiplicands:
                val = acc(df) if isinstance(acc, Formula) else df[acc]
                result *= val
            return result * self.multiplier
        except KeyError as e:
            raise KeyError(f'Missing account: {e}')

class Division(Formula):
    def __init__(self, numerator, denominator, multiplier=1):
        '''
        Initializes the Division operation.

        Parameters:
        - numerator (str or Formula): The account name or Formula instance for the numerator.
        - denominator (str or Formula): The account name or Formula instance for the denominator.
        - multiplier (float): A constant to multiply the result by. Defaults to 1.
        '''
        self.numerator = numerator
        self.denominator = denominator
        self.multiplier = multiplier

    def __call__(self, df):
        try:
            # Compute numerator and denominator values
            numerator_val = self.numerator(df) if isinstance(self.numerator, Formula) else df[self.numerator]
            denominator_val = self.denominator(df) if isinstance(self.denominator, Formula) else df[self.denominator]
            # Handle division by zero
            result = np.where(
                denominator_val != 0,
                (numerator_val / denominator_val) * self.multiplier,
                np.nan
            )
            return result
        except KeyError as e:
            raise KeyError(f'Missing account: {e}')

class Average(Formula):
    def __init__(self, *accounts, multiplier=1):
        '''
        Initializes the Average operation.

        Parameters:
        - *accounts: A list of account names or Formula instances for which the average will be calculated.
        - multiplier (float): A constant to multiply the result by. Defaults to 1.
        '''
        if len(accounts) < 1:
            raise ValueError('Average requires at least one account.')
        self.accounts = accounts
        self.multiplier = multiplier

    def __call__(self, df):
        try:
            # Calculate the sum of all accounts or formulas
            total = sum(
                acc(df) if isinstance(acc, Formula) else df[acc]
                for acc in self.accounts
            )
            # Calculate the average
            result = total / len(self.accounts)
            return result * self.multiplier
        except KeyError as e:
            raise KeyError(f'Missing account: {e}')

##### New Indicators

# 11.01.01 - Capital de Giro (Ativos Circulantes - Passivos Circulantes) # 01.01 - 02.01
# 11.01.02 - Liquidez (Ativos Circulantes por Passivos Circulantes) # 01.01 / 02.01
# 11.01.03 - Ativos Circulantes de Curto Prazo por Ativos # 01.01 / 01
# 11.01.04 - Ativos Não Circulantes de Longo Prazo por Ativos # 01.02 / 01
# 11.02 - Passivos por Ativos # (02 - 02.03) / 01
# 11.02.01 - Passivos Circulantes de Curto Prazo por Ativos # 02.01 / 01
# 11.02.02 - Passivos Não Circulantes de Longo Prazo por Ativos # 02.02 / 01
# 11.02.03 - Passivos Circulantes de Curto Prazo por Passivos # 02.01 / 02
# 11.02.04 - Passivos Não Circulantes de Longo Prazo por Passivos # 02.02 / 02
# 11.03 - Patrimônio Líquido por Ativos # 02.03 / 01
# 11.03.01 - Equity Multiplier (Ativos por Patrimônio Líquido) # 01 / 02.03
# 11.03.02 - Passivos por Patrimônio Líquido # (02.01 + 02.02) / 02.03
# 11.03.02.01 - Passivos Circulantes de Curto Prazo por Patrimônio Líquido # 02.01 / 02.03
# 11.03.02.02 - Passivos Não Circulantes de Longo Prazo por Patrimônio Líquido # 02.02 / 02.03
indicators_11 = [
    {
        'account': '11.01.01', 
        'description': 'Capital de Giro (Ativos Circulantes - Passivos Circulantes)',
        'formula': Subtraction('01.01', '02.01') 
    },
    {
        'account': '11.01.02', 
        'description': 'Liquidez (Ativos Circulantes por Passivos Circulantes)',
        'formula': Division('01.01', '02.01') 
    },
    {
        'account': '11.01.03', 
        'description': 'Ativos Circulantes de Curto Prazo por Ativos',
        'formula': Division('01.01', '01') 
    },
    {
        'account': '11.01.04', 
        'description': 'Ativos Não Circulantes de Longo Prazo por Ativos',
        'formula': Division('01.02', '01') 
    },
    {
        'account': '11.02', 
        'description': 'Passivos por Ativos',
        'formula': Division(Subtraction('02', '02.03'), '01') 
    }, 
    {
        'account': '11.02.01', 
        'description': 'Passivos Circulantes de Curto Prazo por Ativos',
        'formula': Division('02.01', '01') 
    },
    {
        'account': '11.02.02', 
        'description': 'Passivos Não Circulantes de Longo Prazo por Ativos',
        'formula': Division('02.02', '01') 
    },
    {
        'account': '11.02.03', 
        'description': 'Passivos Circulantes de Curto Prazo por Passivos',
        'formula': Division('02.01', '02') 
    },
    {
        'account': '11.02.04', 
        'description': 'Passivos Não Circulantes de Longo Prazo por Passivos',
        'formula': Division('02.02', '02') 
    },
    {
        'account': '11.03', 
        'description': 'Patrimônio Líquido por Ativos',
        'formula': Division('02.03', '01') 
    },
    {
        'account': '11.03.01', 
        'description': 'Equity Multiplier (Ativos por Patrimônio Líquido)',
        'formula': Division('01', '02.03') 
    },
    {
        'account': '11.03.02', 
        'description': 'Passivos por Patrimônio Líquido',
        'formula': Division(Addition('02.01', '02.02'), '02.03') 
    },
    {
        'account': '11.03.02.01', 
        'description': 'Passivos Circulantes de Curto Prazo por Patrimônio Líquido',
        'formula': Division('02.01', '02.03') 
    },
    {
        'account': '11.03.02.02', 
        'description': 'Passivos Não Circulantes de Longo Prazo por Patrimônio Líquido',
        'formula': Division('02.02', '02.03') 
    },
]

# 11.04 - Capital Social por Patrimônio Líquido # 02.03.01 / 02.03
# 11.05 - Reservas por Patrimônio Líquido # (02.03.02 + 02.03.03 + 02.03.04) / 02.03
indicators_11b = [
    {
        'account': '11.04', 
        'description': 'Capital Social por Patrimônio Líquido',
        'formula': Division('02.03.01', '02.03')  # Capital Social divided by Patrimônio Líquido
    },
    {
        'account': '11.05', 
        'description': 'Reservas por Patrimônio Líquido',
        'formula': Division(
            Addition(
                '02.03.02',  # Reservas de Capital
                '02.03.03',  # Reservas de Reavaliação
                '02.03.04'   # Reservas de Lucros
            ),
            '02.03'  # Patrimônio Líquido
        )
    },
]

# 12.01 - Dívida Bruta # 02.01.04.01 + 02.01.04.02 + 02.01.04.03 + 02.02.01.01 + 02.02.01.02 + 02.02.01.03
# 12.01.01 - Dívida Bruta Circulante de Curto Prazo # 02.01.04.01 + 02.01.04.02 + 02.01.04.03
# 12.01.02 - Dívida Bruta Não Circulante de Longo Prazo # 02.02.01.01 + 02.02.01.02 + 02.02.01.03
# 12.01.03 - Dívida Bruta Circulante de Curto Prazo por Dívida Bruta # (02.01.04.01 + 02.01.04.02 + 02.01.04.03) / (02.01.04.01 + 02.01.04.02 + 02.01.04.03 + 02.02.01.01 + 02.02.01.02 + 02.02.01.03)
# 12.01.04 - Dívida Bruta Não Circulante de Longo Prazo por Dívida Bruta # (02.02.01.01 + 02.02.01.02 + 02.02.01.03) / (02.01.04.01 + 02.01.04.02 + 02.01.04.03 + 02.02.01.01 + 02.02.01.02 + 02.02.01.03)
# 12.01.05 - Dívida Bruta em Moeda Nacional # 02.01.04.01.01 + 02.02.01.01.01
# 12.01.06 - Dívida Bruta em Moeda Estrangeira # 02.01.04.01.02 + 02.02.01.01.02
# 12.01.07 - Dívida Bruta em Moeda Nacional por Dívida Bruta # (02.01.04.01.01 + 02.02.01.01.01) / (02.01.04.01.01 + 02.01.04.01.02 + 02.02.01.01.01 + 02.02.01.01.02)
# 12.01.08 - Dívida Bruta em Moeda Estrangeira por Dívida Bruta # (02.01.04.01.02 + 02.02.01.01.02) / (02.01.04.01.01 + 02.01.04.01.02 + 02.02.01.01.01 + 02.02.01.01.02)
# 12.02.02 - Endividamento Financeiro # (02.01.04.01 + 02.01.04.02 + 02.01.04.03 + 02.02.01.01 + 02.02.01.02 + 02.02.01.03) / (02.03 + 02.01.04.01 + 02.01.04.02 + 02.01.04.03 + 02.02.01.01 + 02.02.01.02 + 02.02.01.03)
# 12.03 - Patrimônio Imobilizado em Capex, Investimentos Não Capex e Intangível Não Capex # 01.02.02 + 01.02.03 + 01.02.04
# 12.03.01 - Patrimônio Imobilizado por Patrimônio Líquido # (01.02.02 + 01.02.03 + 01.02.04) / 02.03
# 12.04 - Dívida Líquida # (02.01.04.01.01 + 02.01.04.01.02 + 02.01.04.02 + 02.01.04.03) - (02.02.01.01.01 + 02.02.01.01.02 + 02.02.01.02 + 02.02.01.03)
# 12.04.01 - Dívida Líquida por EBITDA # [(02.01.04.01.01 + 02.01.04.01.02 + 02.01.04.02 + 02.01.04.03) - (02.02.01.01.01 + 02.02.01.01.02 + 02.02.01.02 + 02.02.01.03)] / 03.05
# 12.04.02 - Serviço da Dívida (Dívida Líquida por Resultado) # [(02.01.04.01.01 + 02.01.04.01.02 + 02.01.04.02 + 02.01.04.03) - (02.02.01.01.01 + 02.02.01.01.02 + 02.02.01.02 + 02.02.01.03)] / 03.11
indicators_12 = [
    {
        'account': '12.01', 
        'description': 'Dívida Bruta',
        'formula': Addition(
            '02.01.04.01',  # Empréstimos e Financiamentos em Moeda Nacional
            '02.01.04.02',  # Debêntures
            '02.01.04.03',  # Financiamento por Arrendamento Financeiro
            # '02.01.04.09',  # Outros Empréstimos e Financiamentos
            '02.02.01.01',  # Empréstimos e Financiamentos de Longo Prazo
            '02.02.01.02',  # Debêntures (longo prazo)
            '02.02.01.03',  # Financiamento por Arrendamento Financeiro (longo prazo)
            # '02.02.01.09'   # Outros Empréstimos e Financiamentos (longo prazo)
        )
    },
    {
        'account': '12.01.01', 
        'description': 'Dívida Bruta Circulante de Curto Prazo',
        'formula': Addition(
            '02.01.04.01',  # Empréstimos e Financiamentos em Moeda Nacional
            '02.01.04.02',  # Debêntures
            '02.01.04.03',  # Financiamento por Arrendamento Financeiro
            # '02.01.04.09'   # Outros Empréstimos e Financiamentos
        )
    },
    {
        'account': '12.01.02', 
        'description': 'Dívida Bruta Não Circulante de Longo Prazo',
        'formula': Addition(
            '02.02.01.01',  # Empréstimos e Financiamentos de Longo Prazo
            '02.02.01.02',  # Debêntures (longo prazo)
            '02.02.01.03',  # Financiamento por Arrendamento Financeiro
            # '02.02.01.09'   # Outros Empréstimos e Financiamentos (longo prazo)
        )
    },
    {
        'account': '12.01.03', 
        'description': 'Dívida Bruta Circulante de Curto Prazo por Dívida Bruta',
        'formula': Division(
            Addition(
                '02.01.04.01',  # Empréstimos e Financiamentos em Moeda Nacional
                '02.01.04.02',  # Debêntures
                '02.01.04.03',  # Financiamento por Arrendamento Financeiro
                # '02.01.04.09'   # Outros Empréstimos e Financiamentos
            ),
            Addition(
                '02.01.04.01', 
                '02.01.04.02', 
                '02.01.04.03', 
                # '02.01.04.09',   # Outros Empréstimos e Financiamentos
                '02.02.01.01', 
                '02.02.01.02', 
                '02.02.01.03', 
                # '02.02.01.09'   # Outros Empréstimos e Financiamentos (longo prazo)
            )  # Dívida Bruta Total
        )
    },
    {
        'account': '12.01.04', 
        'description': 'Dívida Bruta Não Circulante de Longo Prazo por Dívida Bruta',
        'formula': Division(
            Addition(
                '02.02.01.01',  # Empréstimos e Financiamentos de Longo Prazo
                '02.02.01.02',  # Debêntures (longo prazo)
                '02.02.01.03',  # Financiamento por Arrendamento Financeiro (longo prazo)
                # '02.02.01.09'   # Outros Empréstimos e Financiamentos (longo prazo)
            ),
            Addition(
                '02.01.04.01', 
                '02.01.04.02', 
                '02.01.04.03', 
                # '02.01.04.09',   # Outros Empréstimos e Financiamentos
                '02.02.01.01', 
                '02.02.01.02', 
                '02.02.01.03', 
                # '02.02.01.09'   # Outros Empréstimos e Financiamentos (longo prazo)
            )  # Dívida Bruta Total
        )
    },
    {
        'account': '12.01.05', 
        'description': 'Dívida Bruta em Moeda Nacional',
        'formula': Addition(
            '02.01.04.01.01',  # Empréstimos e Financiamentos em Moeda Nacional (Curto Prazo)
            '02.02.01.01.01'   # Empréstimos e Financiamentos em Moeda Nacional (Longo Prazo)
        )
    },
    {
        'account': '12.01.06', 
        'description': 'Dívida Bruta em Moeda Estrangeira',
        'formula': Addition(
            '02.01.04.01.02',  # Empréstimos e Financiamentos em Moeda Estrangeira (Curto Prazo)
            '02.02.01.01.02'   # Empréstimos e Financiamentos em Moeda Estrangeira (Longo Prazo)
        )
    },
    {
        'account': '12.01.07', 
        'description': 'Dívida Bruta em Moeda Nacional por Dívida Bruta',
        'formula': Division(
            Addition(
                '02.01.04.01.01',  # Dívida em Moeda Nacional (Curto Prazo)
                '02.02.01.01.01'   # Dívida em Moeda Nacional (Longo Prazo)
            ),
            Addition(
                '02.01.04.01.01', '02.01.04.01.02',  # Dívida Nacional e Estrangeira (Curto Prazo)
                '02.02.01.01.01', '02.02.01.01.02'   # Dívida Nacional e Estrangeira (Longo Prazo)
            )
        )
    },
    {
        'account': '12.01.08', 
        'description': 'Dívida Bruta em Moeda Estrangeira por Dívida Bruta',
        'formula': Division(
            Addition(
                '02.01.04.01.02',  # Dívida em Moeda Estrangeira (Curto Prazo)
                '02.02.01.01.02'   # Dívida em Moeda Estrangeira (Longo Prazo)
            ),
            Addition(
                '02.01.04.01.01', '02.01.04.01.02',  # Dívida Nacional e Estrangeira (Curto Prazo)
                '02.02.01.01.01', '02.02.01.01.02'   # Dívida Nacional e Estrangeira (Longo Prazo)
            )
        )
    }, 
    {
        'account': '12.02.02', 
        'description': 'Endividamento Financeiro',
        'formula': Division(
            Addition(
                '02.01.04.01', '02.01.04.02', '02.01.04.03', 
                # '02.01.04.09',
                '02.02.01.01', '02.02.01.02', '02.02.01.03', 
                # '02.02.01.09'
            ),
            Addition(
                '02.03',  # Patrimônio Líquido
                Addition(
                    '02.01.04.01', '02.01.04.02', '02.01.04.03', 
                    # '02.01.04.09',
                    '02.02.01.01', '02.02.01.02', '02.02.01.03', 
                    # '02.02.01.09'
                )  # Dívida Bruta
            )
        )
    },
    {
        'account': '12.03', 
        'description': 'Patrimônio Imobilizado em Capex, Investimentos Não Capex e Intangível Não Capex',
        'formula': Addition('01.02.02', '01.02.03', '01.02.04')  # Valor diretamente fornecido (Investimentos, Imobilizado, Intangível)
    },
    {
        'account': '12.03.01', 
        'description': 'Patrimônio Imobilizado por Patrimônio Líquido',
            'formula': Division(Addition('01.02.02', '01.02.03', '01.02.04'), '02.03')  # Razão de Patrimônio Imobilizado por Patrimônio Líquido
    },
    {
        'account': '12.04', 
        'description': 'Dívida Líquida',
        'formula': Subtraction(
            Addition(
                '02.01.04.01.01', 
                '02.01.04.01.02', 
                '02.01.04.02', 
                '02.01.04.03', 
                # '02.01.04.09', 
            ), 
            Addition(
                '02.02.01.01.01', 
                '02.02.01.01.02', 
                '02.02.01.02', 
                '02.02.01.03', 
                # '02.02.02.09', 
            ), 
            multiplier=-1
        )  # Valor diretamente fornecido (dl = -1 * (dbcp + dblp - dme))
    },
    {
        'account': '12.04.01', 
        'description': 'Dívida Líquida por EBITDA',
        'formula': Division(
            Subtraction(
                Addition(
                    '02.01.04.01.01', 
                    '02.01.04.01.02', 
                    '02.01.04.02', 
                    '02.01.04.03', 
                    # '02.01.04.09', 
                    ), 
                    Addition(
                        '02.02.01.01.01', 
                        '02.02.01.01.02', 
                        '02.02.01.02', 
                        '02.02.01.03', 
                        # '02.02.02.09',
                    ), 
                    multiplier=-1
            ), 
            '03.05'
        )  # Dívida Líquida por EBITDA
    },
    {
        'account': '12.04.02', 
        'description': 'Serviço da Dívida (Dívida Líquida por Resultado)',
        'formula': Division(
            Subtraction(
                Addition(
                    '02.01.04.01.01', 
                    '02.01.04.01.02', 
                    '02.01.04.02', 
                    '02.01.04.03', 
                    # '02.01.04.09',
                ), 
                Addition(
                    '02.02.01.01.01', 
                    '02.02.01.01.02', 
                    '02.02.01.02', 
                    '02.02.01.03', 
                    # '02.02.02.09', 
                ), 
                multiplier=-1
                ), 
            '03.11'
        )  # Dívida Líquida por Resultado (Lucro Líquido)
    },
]

# 13.03 - Contas a Receber por Faturamento # (01.01.03 + 01.02.01.03) / 03.01
# 13.03.01 - Contas a Receber Não Circulantes de Curto Prazo por Faturamento # 01.01.03 / 03.01
# 13.03.02 - Contas a Receber Circulantes de Longo Prazo por Faturamento # 01.02.01.03 / 03.01
# 13.04 - Estoques por Faturamento # (01.01.04 + 01.02.01.04) / 03.01
# 13.04.01 - Estoques Não Circulantes de Curto Prazo por Faturamento # 01.01.04 / 03.01
# 13.04.02 - Estoques Circulantes de Longo Prazo por Faturamento # 01.02.01.04 / 03.01
# 13.05 - Ativos Biológicos por Faturamento # (01.01.05 + 01.02.01.05) / 03.01
# 13.05.01 - Ativos Biológicos Não Circulantes de Curto Prazo por Faturamento # 01.01.05 / 03.01
# 13.05.02 - Ativos Biológicos Circulantes de Longo Prazo por Faturamento # 01.02.01.05 / 03.01
# 13.06 - Tributos por Faturamento # (01.01.06 + 01.02.01.06) / 03.01
# 13.06.01 - Tributos Não Circulantes de Curto Prazo por Faturamento # 01.01.06 / 03.01
# 13.06.02 - Tributos Circulantes de Longo Prazo por Faturamento # 01.02.01.06 / 03.01
# 13.07 - Despesas por Faturamento # (01.01.07 + 01.02.01.07) / 03.01
# 13.07.01 - Despesas Não Circulantes de Curto Prazo por Faturamento # 01.01.07 / 03.01
# 13.07.02 - Despesas Circulantes de Longo Prazo por Faturamento # 01.02.01.07 / 03.01
# 13.09 - Outros Ativos por Faturamento # (01.01.09 + 01.02.01.09) / 03.01
# 13.09.01 - Outros Ativos Não Circulantes de Curto Prazo por Faturamento # 01.01.09 / 03.01
# 13.09.02 - Outros Ativos Não Circulantes de Longo Prazo por Faturamento # 01.02.01.09 / 03.01
indicators_13 = [
    {
        'account': '13.03', 
        'description': 'Contas a Receber por Faturamento',
        'formula': Division(
            Addition(
                '01.01.03',  # Contas a Receber de Curto Prazo
                '01.02.01.03'  # Contas a Receber de Longo Prazo
            ), 
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.03.01', 
        'description': 'Contas a Receber Não Circulantes de Curto Prazo por Faturamento',
        'formula': Division(
            '01.01.03',  # Contas a Receber de Curto Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.03.02', 
        'description': 'Contas a Receber Circulantes de Longo Prazo por Faturamento',
        'formula': Division(
            '01.02.01.03',  # Contas a Receber de Longo Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.04', 
        'description': 'Estoques por Faturamento',
        'formula': Division(
            Addition(
                '01.01.04',  # Estoques de Curto Prazo
                '01.02.01.04'  # Estoques de Longo Prazo
            ), 
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.04.01', 
        'description': 'Estoques Não Circulantes de Curto Prazo por Faturamento',
        'formula': Division(
            '01.01.04',  # Estoques de Curto Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.04.02', 
        'description': 'Estoques Circulantes de Longo Prazo por Faturamento',
        'formula': Division(
            '01.02.01.04',  # Estoques de Longo Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.05', 
        'description': 'Ativos Biológicos por Faturamento',
        'formula': Division(
            Addition(
                '01.01.05',  # Ativos Biológicos de Curto Prazo
                '01.02.01.05'  # Ativos Biológicos de Longo Prazo
            ), 
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.05.01', 
        'description': 'Ativos Biológicos Não Circulantes de Curto Prazo por Faturamento',
        'formula': Division(
            '01.01.05',  # Ativos Biológicos de Curto Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.05.02', 
        'description': 'Ativos Biológicos Circulantes de Longo Prazo por Faturamento',
        'formula': Division(
            '01.02.01.05',  # Ativos Biológicos de Longo Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.06', 
        'description': 'Tributos por Faturamento',
        'formula': Division(
            Addition(
                '01.01.06',  # Tributos a Recuperar de Curto Prazo
                '01.02.01.06'  # Tributos a Recuperar de Longo Prazo
            ), 
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.06.01', 
        'description': 'Tributos Não Circulantes de Curto Prazo por Faturamento',
        'formula': Division(
            '01.01.06',  # Tributos a Recuperar de Curto Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.06.02', 
        'description': 'Tributos Circulantes de Longo Prazo por Faturamento',
        'formula': Division(
            '01.02.01.06',  # Tributos a Recuperar de Longo Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.07', 
        'description': 'Despesas por Faturamento',
        'formula': Division(
            Addition(
                '01.01.07',  # Despesas Antecipadas de Curto Prazo
                '01.02.01.07'  # Despesas Antecipadas de Longo Prazo
            ), 
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.07.01', 
        'description': 'Despesas Não Circulantes de Curto Prazo por Faturamento',
        'formula': Division(
            '01.01.07',  # Despesas Antecipadas de Curto Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.07.02', 
        'description': 'Despesas Circulantes de Longo Prazo por Faturamento',
        'formula': Division(
            '01.02.01.07',  # Despesas Antecipadas de Longo Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.09', 
        'description': 'Outros Ativos por Faturamento',
        'formula': Division(
            Addition(
                '01.01.09',  # Outros Ativos Circulantes de Curto Prazo
                '01.02.01.09'  # Outros Ativos de Longo Prazo
            ), 
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.09.01', 
        'description': 'Outros Ativos Não Circulantes de Curto Prazo por Faturamento',
        'formula': Division(
            '01.01.09',  # Outros Ativos Circulantes de Curto Prazo
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '13.09.02', 
        'description': 'Outros Ativos Não Circulantes de Longo Prazo por Faturamento',
        'formula': Division(
            '01.02.01.09',  # Outros Ativos de Longo Prazo
            '03.01'  # Receita Bruta
        )
    }
]

# 14.01.01 - Receita por Ativos # 03.01 / 01
# 14.01.02 - Receita por Patrimônio # 03.01 / 02.03
# 14.02.01 - Coeficiente de Retorno (Resultado por Ativos) # 03.11 / 01
# 14.02.02 - ROE (Resultado por Patrimônio) # 03.11 / 02.03
# 14.03 - Capital Investido # 06.01 + 06.02
# 14.03.01 - ROIC (Retorno por Capital Investido) # 03.11 / (06.01 + 06.02)
# 14.04.01 - ROAS (EBIT por Ativos) # 03.05 / 01
indicators_14 = [
    {
        'account': '14.01.01', 
        'description': 'Receita por Ativos',
        'formula': Division(
            '03.01',  # Receita Bruta
            '01'  # Ativo Total
        )
    },
    {
        'account': '14.01.02', 
        'description': 'Receita por Patrimônio',
        'formula': Division(
            '03.01',  # Receita Bruta
            '02.03'  # Patrimônio Líquido
        )
    },
    {
        'account': '14.02.01', 
        'description': 'Coeficiente de Retorno (Resultado por Ativos)',
        'formula': Division(
            '03.11',  # Lucro Líquido
            '01'  # Ativo Total
        )
    },
    {
        'account': '14.02.02', 
        'description': 'ROE (Resultado por Patrimônio)',
        'formula': Division(
            '03.11',  # Lucro Líquido
            '02.03'  # Patrimônio Líquido
        )
    },
    {
        'account': '14.03', 
        'description': 'Capital Investido',
        'formula': Addition(
            '06.01',  # Caixa das Operações
            '06.02'  # Caixa de Investimentos (CAPEX)
        )
    },
    {
        'account': '14.03.01', 
        'description': 'ROIC (Retorno por Capital Investido)',
        'formula': Division(
            '03.11',  # Lucro Líquido
            Addition(
                '06.01',  # Caixa das Operações
                '06.02'  # Caixa de Investimentos (CAPEX)
            )
        )
    },
    {
        'account': '14.04.01', 
        'description': 'ROAS (EBIT por Ativos)',
        'formula': Division(
            '03.05',  # EBIT
            '01'  # Ativo Total
        )
    }
]

# 15.01 - Remuneração de Capital # 07.08.03 + 07.08.04
# 15.01.01 - Remuneração de Capital de Terceiros por Remuneração de Capital # 07.08.03 / (07.08.03 + 07.08.04)
# 15.01.01.01 - Juros Pagos por Remuneração de Capital de Terceiros # 07.08.03.01 / 07.08.03
# 15.01.01.02 - Aluguéis por Remuneração de Capital de Terceiros # 07.08.03.02 / 07.08.03
# 15.01.02 - Remuneração de Capital Próprio por Remuneração de Capital # 07.08.04 / (07.08.03 + 07.08.04)
# 15.01.02.01 - Juros Sobre o Capital Próprio por Remuneração de Capital Próprio # 07.08.04.01 / 07.08.04
# 15.01.02.02 - Dividendos por Remuneração de Capital Próprio # 07.08.04.02 / 07.08.04
# 15.01.02.03 - Lucros Retidos por Remuneração de Capital Próprio # 07.08.04.03 / 07.08.04
# 15.02 - Remuneração de Capital por EBIT # (07.08.03 + 07.08.04) / 03.05
# 15.02.01 - Impostos por EBIT # 03.08 / 03.05
indicators_15 = [
    {
        'account': '15.01', 
        'description': 'Remuneração de Capital',
        'formula': Addition(
            '07.08.03',  # Remuneração de Capital de Terceiros
            '07.08.04'  # Remuneração de Capital Próprio
        )
    },
    {
        'account': '15.01.01', 
        'description': 'Remuneração de Capital de Terceiros por Remuneração de Capital',
        'formula': Division(
            '07.08.03',  # Remuneração de Capital de Terceiros
            Addition(
                '07.08.03',  # Remuneração de Capital de Terceiros
                '07.08.04'  # Remuneração de Capital Próprio
            )
        )
    },
    {
        'account': '15.01.01.01', 
        'description': 'Juros Pagos por Remuneração de Capital de Terceiros',
        'formula': Division(
            '07.08.03.01',  # Juros Pagos
            '07.08.03'  # Remuneração de Capital de Terceiros
        )
    },
    {
        'account': '15.01.01.02', 
        'description': 'Aluguéis por Remuneração de Capital de Terceiros',
        'formula': Division(
            '07.08.03.02',  # Aluguéis
            '07.08.03'  # Remuneração de Capital de Terceiros
        )
    },
    {
        'account': '15.01.02', 
        'description': 'Remuneração de Capital Próprio por Remuneração de Capital',
        'formula': Division(
            '07.08.04',  # Remuneração de Capital Próprio
            Addition(
                '07.08.03',  # Remuneração de Capital de Terceiros
                '07.08.04'  # Remuneração de Capital Próprio
            )
        )
    },
    {
        'account': '15.01.02.01', 
        'description': 'Juros Sobre o Capital Próprio por Remuneração de Capital Próprio',
        'formula': Division(
            '07.08.04.01',  # Juros Sobre o Capital Próprio
            '07.08.04'  # Remuneração de Capital Próprio
        )
    },
    {
        'account': '15.01.02.02', 
        'description': 'Dividendos por Remuneração de Capital Próprio',
        'formula': Division(
            '07.08.04.02',  # Dividendos
            '07.08.04'  # Remuneração de Capital Próprio
        )
    },
    {
        'account': '15.01.02.03', 
        'description': 'Lucros Retidos por Remuneração de Capital Próprio',
        'formula': Division(
            '07.08.04.03',  # Lucros Retidos
            '07.08.04'  # Remuneração de Capital Próprio
        )
    },
    {
        'account': '15.02', 
        'description': 'Remuneração de Capital por EBIT',
        'formula': Division(
            Addition(
                '07.08.03',  # Remuneração de Capital de Terceiros
                '07.08.04'  # Remuneração de Capital Próprio
            ),
            '03.05'  # EBIT
        )
    },
    {
        'account': '15.02.01', 
        'description': 'Impostos por EBIT',
        'formula': Division(
            '03.08',  # Impostos IRPJ e CSLL
            '03.05'  # EBIT
        )
    }
]

    # 16.01 - Margem Bruta (Resultado Bruto (Receita Líquida) por Receita Bruta) # 03.03 / 03.01
    # 16.02 - Margem Operacional (Despesas Operacionais por Receita Bruta) # 03.04 / 03.01
    # 16.02.01 - Força de Vendas (Despesas com Vendas por Despesas Operacionais) # 03.04.01 / 03.04
    # 16.02.02 - Peso Administrativo (Despesas com Administração por Despesas Operacionais) # 03.04.02 / 03.04
    # 16.03 - Margem EBITDA (EBITDA por Resultado Bruto (Receita Líquida)) # (03.05 + 07.04.01) / 03.03
    # 16.03.01 - Margem EBIT (EBIT por Resultado Bruto (Receita Líquida)) # 03.05 / 03.03
    # 16.03.02 - Margem de Depreciação por Resultado Bruto (Receita Líquida) # 07.04.01 / 03.03
    # 16.04 - Margem Não Operacional (Resultado Não Operacional por Resultado Bruto (Receita Líquida)) # 03.06 / 03.03
    # 16.05 - Margem Líquida (Lucro Líquido por Receita Bruta) # 03.11 / 03.01
indicators_16 = [
    {
        'account': '16.01', 
        'description': 'Margem Bruta (Resultado Bruto (Receita Líquida) por Receita Bruta)',
        'formula': Division(
            '03.03',  # Resultado Bruto (Receita Líquida)
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '16.02', 
        'description': 'Margem Operacional (Despesas Operacionais por Receita Bruta)',
        'formula': Division(
            '03.04',  # Despesas Operacionais
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '16.02.01', 
        'description': 'Força de Vendas (Despesas com Vendas por Despesas Operacionais)',
        'formula': Division(
            '03.04.01',  # Despesas com Vendas
            '03.04'  # Despesas Operacionais
        )
    },
    {
        'account': '16.02.02', 
        'description': 'Peso Administrativo (Despesas com Administração por Despesas Operacionais)',
        'formula': Division(
            '03.04.02',  # Despesas Gerais e Administrativas
            '03.04'      # Despesas/Receitas Operacionais
        )
    },
    {
        'account': '16.03', 
        'description': 'Margem EBITDA (EBITDA por Resultado Bruto (Receita Líquida))',
        'formula': Division(
            Addition(
                '03.05',  # EBIT (Resultado Antes do Resultado Financeiro e dos Tributos)
                '07.04.01'  # Depreciação e Amortização
            ),
            '03.03'  # Resultado Bruto (Receita Líquida)
        )
    },
    {
        'account': '16.03.01', 
        'description': 'Margem EBIT (EBIT por Resultado Bruto (Receita Líquida))',
        'formula': Division(
            '03.05',  # EBIT (Resultado Antes do Resultado Financeiro e dos Tributos)
            '03.03'  # Resultado Bruto (Receita Líquida)
        )
    },
    {
        'account': '16.03.02', 
        'description': 'Margem de Depreciação por Resultado Bruto (Receita Líquida)',
        'formula': Division(
            '07.04.01',  # Depreciação e Amortização
            '03.03'  # Resultado Bruto (Receita Líquida)
        )
    },
    {
        'account': '16.04', 
        'description': 'Margem Não Operacional (Resultado Não Operacional por Resultado Bruto (Receita Líquida))',
        'formula': Division(
            '03.06',  # Resultado Financeiro Não Operacional
            '03.03'  # Resultado Bruto (Receita Líquida)
        )
    },
    {
        'account': '16.05', 
        'description': 'Margem Líquida (Lucro Líquido por Receita Bruta)',
        'formula': Division(
            '03.11',  # Lucro Líquido
            '03.01'  # Receita Bruta
        )
    }
]

# 17.01 - Caixa Total # 06.01 + 06.02
# 17.02 - Caixa Livre # 06.01 + 06.02 + 06.03
# 17.03.01 - Caixa de Investimentos por Caixa das Operações # 06.02 / 06.01
# 17.03.02 - Caixa de Investimentos por EBIT # 06.02 / 03.05
# 17.04 - Caixa Imobilizado # 01.02.02 + 01.02.03 + 01.02.04
# 17.05 - FCFF simplificado (Caixa Livre para a Firma) # 06.01 - (01.02.02 + 01.02.03 + 01.02.04)
# 17.06 - FCFE simplificado (Caixa Livre para os Acionistas) # (06.01 - (01.02.02 + 01.02.03 + 01.02.04)) - 08.01
indicators_17 = [
    {
        'account': '17.01', 
        'description': 'Caixa Total',
        'formula': Addition(
            '06.01',  # Caixa das Operações
            '06.02'  # Caixa de Investimentos (CAPEX)
        )
    },
    {
        'account': '17.02', 
        'description': 'Caixa Livre',
        'formula': Addition(
            '06.01',  # Caixa das Operações
            '06.02',  # Caixa de Investimentos (CAPEX)
            '06.03',  # Caixa de Financiamentos
        )
    },
    {
        'account': '17.03.01', 
        'description': 'Caixa de Investimentos por Caixa das Operações',
        'formula': Division(
            '06.02',  # Caixa de Investimentos (CAPEX)
            '06.01'  # Caixa das Operações
        )
    },
    {
        'account': '17.03.02', 
        'description': 'Caixa de Investimentos por EBIT',
        'formula': Division(
            '06.02',  # Caixa de Investimentos (CAPEX)
            '03.05'  # EBIT (Resultado Antes do Resultado Financeiro e dos Tributos)
        )
    },
    {
        'account': '17.04', 
        'description': 'Caixa Imobilizado',
        'formula': Addition(
            '01.02.02',  # Investimentos
            '01.02.03',  # Imobilizado
            '01.02.04'  # Intangível
        )
    },
    {
        'account': '17.05', 
        'description': 'FCFF simplificado (Caixa Livre para a Firma)',
        'formula': Subtraction(
            '06.01',  # Caixa das Operações
            Addition(
                '01.02.02',  # Investimentos
                '01.02.03',  # Imobilizado
                '01.02.04'  # Intangível
            )
        )
    },
    {
        'account': '17.06', 
        'description': 'FCFE simplificado (Caixa Livre para os Acionistas)',
        'formula': Subtraction(
            Subtraction(
                '06.01',  # Caixa das Operações
                Addition(
                    '01.02.02',  # Investimentos
                    '01.02.03',  # Imobilizado
                    '01.02.04'  # Intangível
                )
            ),
            '07.08.04.02'  # Dividendos
        )
    }
]

# 18.01 - Margem de Vendas por Valor Agregado # 07.01 / 07.07
# 18.02 - Custo dos Insumos por Valor Agregado # 07.02 / 07.07
# 18.03 - Valor Adicionado Bruto por Valor Agregado # 07.03 / 07.07
# 18.04 - Retenções por Valor Agregado # 07.04 / 07.07
# 18.05 - Valor Adicionado Líquido por Valor Agregado # 07.05 / 07.07
# 18.06 - Valor Adicionado em Transferência por Valor Agregado # 07.06 / 07.07
# 18.07 - Recursos Humanos por Valor Agregado # 07.08.01 / 07.07
# 18.07.01 - Remuneração Direta (Recursos Humanos) por Valor Agregado # 07.08.01.01 / 07.07
# 18.07.02 - Benefícios (Recursos Humanos) por Valor Agregado # 07.08.01.02 / 07.07
# 18.07.03 - FGTS (Recursos Humanos) por Valor Agregado # 07.08.01.03 / 07.07
# 18.08 - Impostos por Valor Agregado # 07.08.02 / 07.07
# 18.09 - Remuneração de Capital de Terceiros por Valor Agregado # 07.08.03 / 07.07
# 18.09.01 - Juros Pagos a Terceiros por Valor Agregado # 07.08.03.01 / 07.07
# 18.09.02 - Aluguéis Pagos a Terceiros por Valor Agregado # 07.08.03.02 / 07.07
# 18.10 - Remuneração de Capital Próprio por Valor Agregado # 07.08.04 / 07.07
# 18.10.01 - Juros Sobre Capital Próprio por Valor Agregado # 07.08.04.01 / 07.07
# 18.10.02 - Dividendos por Valor Agregado # 07.08.04.02 / 07.07
# 18.10.03 - Lucros Retidos por Valor Agregado # 07.08.04.03 / 07.07
# 18.11.01 - Alíquota de Impostos (Impostos, Taxas e Contribuições por Receita Bruta) # 07.08.02 / 03.01
# 18.11.02 - Taxa de Juros Pagos (Remuneração de Capital de Terceiros por Receita Bruta) # 07.08.03 / 03.01
# 18.11.03 - Taxa de Proventos Gerados (Remuneração de Capital Próprio por Receita Bruta) # 07.08.04 / 03.01
indicators_18 = [
    {
        'account': '18.01', 
        'description': 'Margem de Vendas por Valor Agregado',
        'formula': Division(
            '07.01',  # Vendas
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.02', 
        'description': 'Custo dos Insumos por Valor Agregado',
        'formula': Division(
            '07.02',  # Custos dos Insumos
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.03', 
        'description': 'Valor Adicionado Bruto por Valor Agregado',
        'formula': Division(
            '07.03',  # Valor Adicionado Bruto
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.04', 
        'description': 'Retenções por Valor Agregado',
        'formula': Division(
            '07.04',  # Retenções
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.05', 
        'description': 'Valor Adicionado Líquido por Valor Agregado',
        'formula': Division(
            '07.05',  # Valor Adicionado Líquido
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.06', 
        'description': 'Valor Adicionado em Transferência por Valor Agregado',
        'formula': Division(
            '07.06',  # Valor Adicionado em Transferência
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.07', 
        'description': 'Recursos Humanos por Valor Agregado',
        'formula': Division(
            '07.08.01',  # Pessoal
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.07.01', 
        'description': 'Remuneração Direta (Recursos Humanos) por Valor Agregado',
        'formula': Division(
            '07.08.01.01',  # Remuneração Direta
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.07.02', 
        'description': 'Benefícios (Recursos Humanos) por Valor Agregado',
        'formula': Division(
            '07.08.01.02',  # Benefícios
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.07.03', 
        'description': 'FGTS (Recursos Humanos) por Valor Agregado',
        'formula': Division(
            '07.08.01.03',  # FGTS
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.08', 
        'description': 'Impostos por Valor Agregado',
        'formula': Division(
            '07.08.02',  # Impostos, Taxas e Contribuições
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.09', 
        'description': 'Remuneração de Capital de Terceiros por Valor Agregado',
        'formula': Division(
            '07.08.03',  # Remuneração de Capital de Terceiros
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.09.01', 
        'description': 'Juros Pagos a Terceiros por Valor Agregado',
        'formula': Division(
            '07.08.03.01',  # Juros Pagos
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.09.02', 
        'description': 'Aluguéis Pagos a Terceiros por Valor Agregado',
        'formula': Division(
            '07.08.03.02',  # Aluguéis
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.10', 
        'description': 'Remuneração de Capital Próprio por Valor Agregado',
        'formula': Division(
            '07.08.04',  # Remuneração de Capital Próprio
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.10.01', 
        'description': 'Juros Sobre Capital Próprio por Valor Agregado',
        'formula': Division(
            '07.08.04.01',  # Juros Sobre Capital Próprio
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.10.02', 
        'description': 'Dividendos por Valor Agregado',
        'formula': Division(
            '07.08.04.02',  # Dividendos
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.10.03', 
        'description': 'Lucros Retidos por Valor Agregado',
        'formula': Division(
            '07.08.04.03',  # Lucros Retidos
            '07.07'  # Valor Adicionado Total a Distribuir
        )
    },
    {
        'account': '18.11.01', 
        'description': 'Alíquota de Impostos (Impostos, Taxas e Contribuições por Receita Bruta)',
        'formula': Division(
            '07.08.02',  # Impostos, Taxas e Contribuições
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '18.11.02', 
        'description': 'Taxa de Juros Pagos (Remuneração de Capital de Terceiros por Receita Bruta)',
        'formula': Division(
            '07.08.03',  # Remuneração de Capital de Terceiros
            '03.01'  # Receita Bruta
        )
    },
    {
        'account': '18.11.03', 
        'description': 'Taxa de Proventos Gerados (Remuneração de Capital Próprio por Receita Bruta)',
        'formula': Division(
            '07.08.04',  # Remuneração de Capital Próprio
            '03.01'  # Receita Bruta
        )
    }
]

# 21.00.01 - Número de Ações ON em Circulação # 00.01.01 - 00.02.01
# 21.00.02 - Número de Ações PN em Circulação # 00.01.02 - 00.02.02
# 21.00.03 - Número Total de Ações em Circulação # 21.00.01 + 21.00.02
# 21.00.04 - Proporção das Ações ON # 21.00.01 / 21.00.03
# 21.00.05 - Proporção das Ações PN # 21.00.02 / 21.00.03
# 21.00.06 - Lucro Atribuído às Ações ON # 03.11 * 21.00.04
# 21.00.07 - Lucro Atribuído às Ações PN # 03.11 * 21.00.05
# 21.01 - Lucro por Ação (LPA) Total # 03.11 / 21.00.03
# 21.02 - Lucro por Ação (LPA) ON # 21.00.06 / 21.00.01
# 21.03 - Lucro por Ação (LPA) PN # 21.00.07 / 21.00.02
# 21.04 - Preço/Lucro (P/L) Total # Média(99.3, 99.4) / 21.01
# 21.05 - Preço/Lucro (P/L) ON # 99.3 / 21.02
# 21.06 - Preço/Lucro (P/L) PN # 99.4 / 21.03
# 21.07 - Valor Patrimonial por Ação (VPA) Total # 02.03 / 21.00.03
# 21.08 - Valor Patrimonial por Ação (VPA) ON # 02.03 / 21.00.01
# 21.09 - Valor Patrimonial por Ação (VPA) PN # 02.03 / 21.00.02
# 21.10 - Preço/Valor Patrimonial (P/VP) Total # Média(99.3, 99.4) / 21.07
# 21.11 - Preço/Valor Patrimonial (P/VP) ON # 99.3 / 21.08
# 21.12 - Preço/Valor Patrimonial (P/VP) PN # 99.4 / 21.09
# 21.13 - Dividendos por Ação (DPA) Total # 08.01 / 21.00.03
# 21.14 - Dividendos por Ação (DPA) ON # 08.01 / 21.00.01
# 21.15 - Dividendos por Ação (DPA) PN # 08.01 / 21.00.02
# 21.16 - Dividend Yield Total # 21.13 / Média(99.3, 99.4)
# 21.17 - Dividend Yield ON # 21.14 / 99.3
# 21.18 - Dividend Yield PN # 21.15 / 99.4
# 21.19 - Capitalização de Mercado Total # (99.3 * 21.00.01) + (99.4 * 21.00.02)
# 21.20 - Capitalização de Mercado ON # 99.3 * 21.00.01
# 21.21 - Capitalização de Mercado PN # 99.4 * 21.00.02
# 21.22 - Enterprise Value (EV) Total # 21.19 + ((12.01 + 12.02.02) - 01.01.01)
# 21.23 - EV/EBITDA Total # 21.22 / 21.24
# 21.24 - EBITDA Total # 03.05 + 07.04.01
# 21.25 - Earnings Yield Total # 21.01 / Média(99.3, 99.4)
# 21.26 - Earnings Yield ON # 21.02 / 99.3
# 21.27 - Earnings Yield PN # 21.03 / 99.4
# 21.28 - Preço/Receita (P/S) Total # Média(99.3, 99.4) / (03.01 / 21.00.03)
# 21.29 - Preço/Receita (P/S) ON # 99.3 / (03.01 / 21.00.01)
# 21.30 - Preço/Receita (P/S) PN # 99.4 / (03.01 / 21.00.02)
# 21.31 - Preço/Fluxo de Caixa Livre (P/FCF) Total # Média(99.3, 99.4) / (17.05 / 21.00.03)
# 21.32 - Preço/Fluxo de Caixa Livre (P/FCF) ON # 99.3 / (17.05 / 21.00.01)
# 21.33 - Preço/Fluxo de Caixa Livre (P/FCF) PN # 99.4 / (17.05 / 21.00.02)
indicators_21 = [
    # Cálculo das Quantidades de Ações em Circulação
    {
        'account': '21.00.01',
        'description': 'Número de Ações ON em Circulação',
        'formula': Subtraction('00.01.01', '00.02.01')
    },
    {
        'account': '21.00.02',
        'description': 'Número de Ações PN em Circulação',
        'formula': Subtraction('00.01.02', '00.02.02')
    },
    {
        'account': '21.00.03',
        'description': 'Número Total de Ações em Circulação',
        'formula': Addition('21.00.01', '21.00.02')
    },
    # Cálculo das Proporções
    {
        'account': '21.00.04',
        'description': 'Proporção das Ações ON',
        'formula': Division('21.00.01', '21.00.03')
    },
    {
        'account': '21.00.05',
        'description': 'Proporção das Ações PN',
        'formula': Division('21.00.02', '21.00.03')
    },
    # Lucro Atribuído a cada Classe de Ação
    {
        'account': '21.00.06',
        'description': 'Lucro Atribuído às Ações ON',
        'formula': Multiplication('03.11', '21.00.04')
    },
    {
        'account': '21.00.07',
        'description': 'Lucro Atribuído às Ações PN',
        'formula': Multiplication('03.11', '21.00.05')
    },
    # Lucro por Ação (LPA) Total
    {
        'account': '21.01',
        'description': 'Lucro por Ação (LPA) Total',
        'formula': Division('03.11', '21.00.03')
    },
    # Lucro por Ação (LPA) ON
    {
        'account': '21.02',
        'description': 'Lucro por Ação (LPA) ON',
        'formula': Division('21.00.06', '21.00.01')
    },
    # Lucro por Ação (LPA) PN
    {
        'account': '21.03',
        'description': 'Lucro por Ação (LPA) PN',
        'formula': Division('21.00.07', '21.00.02')
    },
    # Preço/Lucro (P/L) Total
    {
        'account': '21.04',
        'description': 'Preço/Lucro (P/L) Total',
        'formula': Division(
            Average('99.3', '99.4'),  # Média dos Preços das Ações ON e PN
            '21.01'  # LPA Total
        )
    },
    # Preço/Lucro (P/L) ON
    {
        'account': '21.05',
        'description': 'Preço/Lucro (P/L) ON',
        'formula': Division(
            '99.3',  # Preço da Ação ON
            '21.02'  # LPA ON
        )
    },
    # Preço/Lucro (P/L) PN
    {
        'account': '21.06',
        'description': 'Preço/Lucro (P/L) PN',
        'formula': Division(
            '99.4',  # Preço da Ação PN
            '21.03'  # LPA PN
        )
    },
    # Valor Patrimonial por Ação (VPA) Total
    {
        'account': '21.07',
        'description': 'Valor Patrimonial por Ação (VPA) Total',
        'formula': Division('02.03', '21.00.03')
    },
    # Valor Patrimonial por Ação (VPA) ON
    {
        'account': '21.08',
        'description': 'Valor Patrimonial por Ação (VPA) ON',
        'formula': Division('02.03', '21.00.01')
    },
    # Valor Patrimonial por Ação (VPA) PN
    {
        'account': '21.09',
        'description': 'Valor Patrimonial por Ação (VPA) PN',
        'formula': Division('02.03', '21.00.02')
    },
    # Preço/Valor Patrimonial (P/VP) Total
    {
        'account': '21.10',
        'description': 'Preço/Valor Patrimonial (P/VP) Total',
        'formula': Division(
            Average('99.3', '99.4'),  # Média dos Preços das Ações
            '21.07'  # VPA Total
        )
    },
    # Preço/Valor Patrimonial (P/VP) ON
    {
        'account': '21.11',
        'description': 'Preço/Valor Patrimonial (P/VP) ON',
        'formula': Division(
            '99.3',  # Preço da Ação ON
            '21.08'  # VPA ON
        )
    },
    # Preço/Valor Patrimonial (P/VP) PN
    {
        'account': '21.12',
        'description': 'Preço/Valor Patrimonial (P/VP) PN',
        'formula': Division(
            '99.4',  # Preço da Ação PN
            '21.09'  # VPA PN
        )
    },
    # Dividendos por Ação (DPA) Total
    {
        'account': '21.13',
        'description': 'Dividendos por Ação (DPA) Total',
        'formula': Division('07.08.04.02', '21.00.03')
    },
    # Dividendos por Ação (DPA) ON
    {
        'account': '21.14',
        'description': 'Dividendos por Ação (DPA) ON',
        'formula': Division('07.08.04.02', '21.00.01')  # Assumindo distribuição igualitária
    },
    # Dividendos por Ação (DPA) PN
    {
        'account': '21.15',
        'description': 'Dividendos por Ação (DPA) PN',
        'formula': Division('07.08.04.02', '21.00.02')  # Assumindo distribuição igualitária
    },
    # Dividend Yield Total
    {
        'account': '21.16',
        'description': 'Dividend Yield Total',
        'formula': Division(
            '21.13',  # DPA Total
            Average('99.3', '99.4')  # Média dos Preços das Ações
        )
    },
    # Dividend Yield ON
    {
        'account': '21.17',
        'description': 'Dividend Yield ON',
        'formula': Division(
            '21.14',  # DPA ON
            '99.3'    # Preço da Ação ON
        )
    },
    # Dividend Yield PN
    {
        'account': '21.18',
        'description': 'Dividend Yield PN',
        'formula': Division(
            '21.15',  # DPA PN
            '99.4'    # Preço da Ação PN
        )
    },
    # Capitalização de Mercado Total
    {
        'account': '21.19',
        'description': 'Capitalização de Mercado Total',
        'formula': Addition(
            Multiplication('99.3', '21.00.01'),  # Capitalização ON
            Multiplication('99.4', '21.00.02')   # Capitalização PN
        )
    },
    # Capitalização de Mercado ON
    {
        'account': '21.20',
        'description': 'Capitalização de Mercado ON',
        'formula': Multiplication('99.3', '21.00.01')
    },
    # Capitalização de Mercado PN
    {
        'account': '21.21',
        'description': 'Capitalização de Mercado PN',
        'formula': Multiplication('99.4', '21.00.02')
    },
    # Enterprise Value (EV) Total
    {
        'account': '21.22',
        'description': 'Enterprise Value (EV) Total',
        'formula': Addition(
            '21.19',  # Capitalização de Mercado Total
            Subtraction(
                Addition('12.01', '12.02.02'),  # Dívida Bruta Total (12.01 é Dívida Bruta)
                '01.01.01'  # Caixa e Equivalentes de Caixa
            )
        )
    },
    # EBITDA Total
    {
        'account': '21.24',
        'description': 'EBITDA Total',
        'formula': Addition('03.05', '07.04.01')
    },
    # EV/EBITDA Total
    {
        'account': '21.23',
        'description': 'EV/EBITDA Total',
        'formula': Division(
            '21.22',  # Enterprise Value Total
            '21.24'   # EBITDA Total
        )
    },
    # Earnings Yield Total
    {
        'account': '21.25',
        'description': 'Earnings Yield Total',
        'formula': Division(
            '21.01',  # LPA Total
            Average('99.3', '99.4')  # Média dos Preços das Ações
        )
    },
    # Earnings Yield ON
    {
        'account': '21.26',
        'description': 'Earnings Yield ON',
        'formula': Division(
            '21.02',  # LPA ON
            '99.3'    # Preço da Ação ON
        )
    },
    # Earnings Yield PN
    {
        'account': '21.27',
        'description': 'Earnings Yield PN',
        'formula': Division(
            '21.03',  # LPA PN
            '99.4'    # Preço da Ação PN
        )
    },
    # Preço/Receita (P/S) Total
    {
        'account': '21.28',
        'description': 'Preço/Receita (P/S) Total',
        'formula': Division(
            Average('99.3', '99.4'),  # Média dos Preços das Ações
            Division('03.01', '21.00.03')  # Receita por Ação Total
        )
    },
    # Preço/Receita (P/S) ON
    {
        'account': '21.29',
        'description': 'Preço/Receita (P/S) ON',
        'formula': Division(
            '99.3',  # Preço da Ação ON
            Division('03.01', '21.00.01')  # Receita por Ação ON
        )
    },
    # Preço/Receita (P/S) PN
    {
        'account': '21.30',
        'description': 'Preço/Receita (P/S) PN',
        'formula': Division(
            '99.4',  # Preço da Ação PN
            Division('03.01', '21.00.02')  # Receita por Ação PN
        )
    },
    # Preço/Fluxo de Caixa Livre (P/FCF) Total
    {
        'account': '21.31',
        'description': 'Preço/Fluxo de Caixa Livre (P/FCF) Total',
        'formula': Division(
            Average('99.3', '99.4'),  # Média dos Preços das Ações
            Division('17.05', '21.00.03')  # Fluxo de Caixa Livre por Ação Total
        )
    },
    # Preço/Fluxo de Caixa Livre (P/FCF) ON
    {
        'account': '21.32',
        'description': 'Preço/Fluxo de Caixa Livre (P/FCF) ON',
        'formula': Division(
            '99.3',  # Preço da Ação ON
            Division('17.05', '21.00.01')  # Fluxo de Caixa Livre por Ação ON
        )
    },
    # Preço/Fluxo de Caixa Livre (P/FCF) PN
    {
        'account': '21.33',
        'description': 'Preço/Fluxo de Caixa Livre (P/FCF) PN',
        'formula': Division(
            '99.4',  # Preço da Ação PN
            Division('17.05', '21.00.02')  # Fluxo de Caixa Livre por Ação PN
        )
    },
]

# 22.01 - Taxa de Crescimento do LPA Total # (21.01 - 21.01(-1)) / 21.01(-1)
# 22.02 - Taxa de Crescimento do LPA ON # (21.02 - 21.02(-1)) / 21.02(-1)
# 22.03 - Taxa de Crescimento do LPA PN # (21.03 - 21.03(-1)) / 21.03(-1)
# 22.04 - Índice PEG Total # 21.04 / 22.01
# 22.05 - Índice PEG ON # 21.05 / 22.02
# 22.06 - Índice PEG PN # 21.06 / 22.03
# 22.07 - Preço/EBITDA Total # Média(99.3, 99.4) / (21.24 / 21.00.03)
# 22.08 - Preço/EBITDA ON # 99.3 / (21.24 / 21.00.01)
# 22.09 - Preço/EBITDA PN # 99.4 / (21.24 / 21.00.02)
# 22.10 - Preço/EBIT Total # Média(99.3, 99.4) / (03.05 / 21.00.03)
# 22.11 - Preço/EBIT ON # 99.3 / (03.05 / 21.00.01)
# 22.12 - Preço/EBIT PN # 99.4 / (03.05 / 21.00.02)
# 22.13 - Preço/Fluxo de Caixa Operacional (P/OCF) Total # Média(99.3, 99.4) / (06.01 / 21.00.03)
# 22.14 - Preço/Fluxo de Caixa Operacional (P/OCF) ON # 99.3 / (06.01 / 21.00.01)
# 22.15 - Preço/Fluxo de Caixa Operacional (P/OCF) PN # 99.4 / (06.01 / 21.00.02)
indicators_22 = [
    # Taxa de Crescimento do Lucro por Ação (LPA) Total
    {
        'account': '22.01',
        'description': 'Taxa de Crescimento do LPA Total',
        'formula': Division(
            Subtraction('21.01', '21.01(-1)'),  # LPA Total atual menos LPA Total do período anterior
            '21.01(-1)'  # LPA Total do período anterior
        )
    },
    # Taxa de Crescimento do LPA ON
    {
        'account': '22.02',
        'description': 'Taxa de Crescimento do LPA ON',
        'formula': Division(
            Subtraction('21.02', '21.02(-1)'),  # LPA ON atual menos LPA ON do período anterior
            '21.02(-1)'  # LPA ON do período anterior
        )
    },
    # Taxa de Crescimento do LPA PN
    {
        'account': '22.03',
        'description': 'Taxa de Crescimento do LPA PN',
        'formula': Division(
            Subtraction('21.03', '21.03(-1)'),  # LPA PN atual menos LPA PN do período anterior
            '21.03(-1)'  # LPA PN do período anterior
        )
    },
    # Índice PEG Total (Preço/Lucro ajustado pelo crescimento)
    {
        'account': '22.04',
        'description': 'Índice PEG Total',
        'formula': Division(
            '21.04',  # P/L Total
            '22.01'   # Taxa de Crescimento do LPA Total
        )
    },
    # Índice PEG ON
    {
        'account': '22.05',
        'description': 'Índice PEG ON',
        'formula': Division(
            '21.05',  # P/L ON
            '22.02'   # Taxa de Crescimento do LPA ON
        )
    },
    # Índice PEG PN
    {
        'account': '22.06',
        'description': 'Índice PEG PN',
        'formula': Division(
            '21.06',  # P/L PN
            '22.03'   # Taxa de Crescimento do LPA PN
        )
    },
    # Preço/EBITDA Total
    {
        'account': '22.07',
        'description': 'Preço/EBITDA Total',
        'formula': Division(
            Average('99.3', '99.4'),  # Média dos preços das ações
            Division('21.24', '21.00.03')  # EBITDA Total por ação
        )
    },
    # Preço/EBITDA ON
    {
        'account': '22.08',
        'description': 'Preço/EBITDA ON',
        'formula': Division(
            '99.3',
            Division('21.24', '21.00.01')  # EBITDA por ação ON
        )
    },
    # Preço/EBITDA PN
    {
        'account': '22.09',
        'description': 'Preço/EBITDA PN',
        'formula': Division(
            '99.4',
            Division('21.24', '21.00.02')  # EBITDA por ação PN
        )
    },
    # Preço/EBIT Total
    {
        'account': '22.10',
        'description': 'Preço/EBIT Total',
        'formula': Division(
            Average('99.3', '99.4'),
            Division('03.05', '21.00.03')  # EBIT por ação Total
        )
    },
    # Preço/EBIT ON
    {
        'account': '22.11',
        'description': 'Preço/EBIT ON',
        'formula': Division(
            '99.3',
            Division('03.05', '21.00.01')  # EBIT por ação ON
        )
    },
    # Preço/EBIT PN
    {
        'account': '22.12',
        'description': 'Preço/EBIT PN',
        'formula': Division(
            '99.4',
            Division('03.05', '21.00.02')  # EBIT por ação PN
        )
    },
    # Preço/Fluxo de Caixa Operacional (P/OCF) Total
    {
        'account': '22.13',
        'description': 'Preço/Fluxo de Caixa Operacional (P/OCF) Total',
        'formula': Division(
            Average('99.3', '99.4'),
            Division('06.01', '21.00.03')  # Caixa de Operações por ação Total
        )
    },
    # Preço/Fluxo de Caixa Operacional (P/OCF) ON
    {
        'account': '22.14',
        'description': 'Preço/Fluxo de Caixa Operacional (P/OCF) ON',
        'formula': Division(
            '99.3',
            Division('06.01', '21.00.01')  # Caixa de Operações por ação ON
        )
    },
    # Preço/Fluxo de Caixa Operacional (P/OCF) PN
    {
        'account': '22.15',
        'description': 'Preço/Fluxo de Caixa Operacional (P/OCF) PN',
        'formula': Division(
            '99.4',
            Division('06.01', '21.00.02')  # Caixa de Operações por ação PN
        )
    },
]

# 23.01 - Índice de Payout de Dividendos Total # 21.13 / 21.01
# 23.02 - Índice de Payout de Dividendos ON # 21.14 / 21.02
# 23.03 - Índice de Payout de Dividendos PN # 21.15 / 21.03
# 23.04 - Cobertura de Dividendos Total # 21.01 / 21.13
# 23.05 - Cobertura de Dividendos ON # 21.02 / 21.14
# 23.06 - Cobertura de Dividendos PN # 21.03 / 21.15
# 23.07 - Retorno Total para o Acionista (TSR) ON # ((99.3 - 99.3(-1)) / 99.3(-1)) + 21.17
# 23.08 - Retorno Total para o Acionista (TSR) PN # ((99.4 - 99.4(-1)) / 99.4(-1)) + 21.18
indicators_23 = [
    # Índice de Payout de Dividendos Total
    {
        'account': '23.01',
        'description': 'Índice de Payout de Dividendos Total',
        'formula': Division(
            '21.13',  # Dividendos por Ação Total
            '21.01'   # Lucro por Ação Total
        )
    },
    # Índice de Payout de Dividendos ON
    {
        'account': '23.02',
        'description': 'Índice de Payout de Dividendos ON',
        'formula': Division(
            '21.14',  # Dividendos por Ação ON
            '21.02'   # Lucro por Ação ON
        )
    },
    # Índice de Payout de Dividendos PN
    {
        'account': '23.03',
        'description': 'Índice de Payout de Dividendos PN',
        'formula': Division(
            '21.15',  # Dividendos por Ação PN
            '21.03'   # Lucro por Ação PN
        )
    },
    # Cobertura de Dividendos Total
    {
        'account': '23.04',
        'description': 'Cobertura de Dividendos Total',
        'formula': Division(
            '21.01',  # Lucro por Ação Total
            '21.13'   # Dividendos por Ação Total
        )
    },
    # Cobertura de Dividendos ON
    {
        'account': '23.05',
        'description': 'Cobertura de Dividendos ON',
        'formula': Division(
            '21.02',  # Lucro por Ação ON
            '21.14'   # Dividendos por Ação ON
        )
    },
    # Cobertura de Dividendos PN
    {
        'account': '23.06',
        'description': 'Cobertura de Dividendos PN',
        'formula': Division(
            '21.03',  # Lucro por Ação PN
            '21.15'   # Dividendos por Ação PN
        )
    },
    # Retorno Total para o Acionista (TSR) ON
    {
        'account': '23.07',
        'description': 'Retorno Total para o Acionista (TSR) ON',
        'formula': Addition(
            Division(
                Subtraction('99.3', '99.3(-1)'),  # Variação do Preço da Ação ON
                '99.3(-1)'
            ),
            '21.17'  # Dividend Yield ON
        )
    },
    # Retorno Total para o Acionista (TSR) PN
    {
        'account': '23.08',
        'description': 'Retorno Total para o Acionista (TSR) PN',
        'formula': Addition(
            Division(
                Subtraction('99.4', '99.4(-1)'),  # Variação do Preço da Ação PN
                '99.4(-1)'
            ),
            '21.18'  # Dividend Yield PN
        )
    },
]

# 24.01 - Múltiplo EV/EBIT Total # 21.22 / 03.05
# 24.02 - Múltiplo EV/Receita (EV/Sales) Total # 21.22 / 03.01
# 24.03 - Preço/Valor Patrimonial Líquido Tangível (P/TBV) Total # (Average(99.3, 99.4)) / ((02.03 - 01.02.04) / 21.00.03)
# 24.04 - Preço/Valor Patrimonial Líquido Tangível (P/TBV) ON # 99.3 / ((02.03 - 01.02.04) / 21.00.01)
# 24.05 - Preço/Valor Patrimonial Líquido Tangível (P/TBV) PN # 99.4 / ((02.03 - 01.02.04) / 21.00.02)
indicators_24 = [
    # Múltiplo EV/EBIT Total
    {
        'account': '24.01',
        'description': 'Múltiplo EV/EBIT Total',
        'formula': Division(
            '21.22',  # Enterprise Value Total
            '03.05'   # EBIT
        )
    },
    # Múltiplo EV/Receita (EV/Sales) Total
    {
        'account': '24.02',
        'description': 'Múltiplo EV/Receita Total',
        'formula': Division(
            '21.22',  # Enterprise Value Total
            '03.01'   # Receita de Venda de Bens e/ou Serviços
        )
    },
    # Preço/Valor Patrimonial Líquido Tangível (P/TBV) Total
    {
        'account': '24.03',
        'description': 'Preço/Valor Patrimonial Líquido Tangível (P/TBV) Total',
        'formula': Division(
            Average('99.3', '99.4'),
            Division(
                Subtraction('02.03', '01.02.04'),  # Patrimônio Líquido - Intangível
                '21.00.03'  # Número Total de Ações em Circulação
            )
        )
    },
    # Preço/Valor Patrimonial Líquido Tangível (P/TBV) ON
    {
        'account': '24.04',
        'description': 'Preço/Valor Patrimonial Líquido Tangível (P/TBV) ON',
        'formula': Division(
            '99.3',
            Division(
                Subtraction('02.03', '01.02.04'),
                '21.00.01'
            )
        )
    },
    # Preço/Valor Patrimonial Líquido Tangível (P/TBV) PN
    {
        'account': '24.05',
        'description': 'Preço/Valor Patrimonial Líquido Tangível (P/TBV) PN',
        'formula': Division(
            '99.4',
            Division(
                Subtraction('02.03', '01.02.04'),
                '21.00.02'
            )
        )
    },
]

# 25.01 - Fluxo de Caixa Livre por Ação Total # 17.05 / 21.00.03
# 25.02 - Fluxo de Caixa Livre por Ação ON # (17.05 × 21.00.04) / 21.00.01
# 25.03 - Fluxo de Caixa Livre por Ação PN # (17.05 × 21.00.05) / 21.00.02
# 25.04 - Preço/Fluxo de Caixa por Ação (P/FC) Total # (Average(99.3, 99.4)) / 25.01
# 25.05 - Preço/Fluxo de Caixa por Ação (P/FC) ON # 99.3 / 25.02
# 25.06 - Preço/Fluxo de Caixa por Ação (P/FC) PN # 99.4 / 25.03
indicators_25 = [
    # Fluxo de Caixa Livre por Ação Total
    {
        'account': '25.01',
        'description': 'Fluxo de Caixa Livre por Ação Total',
        'formula': Division(
            '17.05',  # FCFF simplificado (Caixa Livre para a Firma)
            '21.00.03'  # Número Total de Ações em Circulação
        )
    },
    # Fluxo de Caixa Livre por Ação ON
    {
        'account': '25.02',
        'description': 'Fluxo de Caixa Livre por Ação ON',
        'formula': Division(
            Multiplication('17.05', '21.00.04'),  # FCFF × Proporção ON
            '21.00.01'
        )
    },
    # Fluxo de Caixa Livre por Ação PN
    {
        'account': '25.03',
        'description': 'Fluxo de Caixa Livre por Ação PN',
        'formula': Division(
            Multiplication('17.05', '21.00.05'),  # FCFF × Proporção PN
            '21.00.02'
        )
    },
    # Preço/Fluxo de Caixa por Ação (P/FC) Total
    {
        'account': '25.04',
        'description': 'Preço/Fluxo de Caixa por Ação (P/FC) Total',
        'formula': Division(
            Average('99.3', '99.4'),
            '25.01'  # Fluxo de Caixa Livre por Ação Total
        )
    },
    # Preço/Fluxo de Caixa por Ação (P/FC) ON
    {
        'account': '25.05',
        'description': 'Preço/Fluxo de Caixa por Ação (P/FC) ON',
        'formula': Division(
            '99.3',
            '25.02'  # Fluxo de Caixa Livre por Ação ON
        )
    },
    # Preço/Fluxo de Caixa por Ação (P/FC) PN
    {
        'account': '25.06',
        'description': 'Preço/Fluxo de Caixa por Ação (P/FC) PN',
        'formula': Division(
            '99.4',
            '25.03'  # Fluxo de Caixa Livre por Ação PN
        )
    },
]

# 27.05 - Taxa de Retenção de Lucros por Ação Total # 1 - 23.01
indicators_27 = [
    # Taxa de Retenção de Lucros por Ação Total
    {
        'account': '27.05',
        'description': 'Taxa de Retenção de Lucros por Ação Total',
        'formula': Subtraction(
            1,
            '23.01'  # Índice de Payout de Dividendos Total
        )
    }
]

# 28.05 - Capitalização de Mercado por Patrimônio Líquido # 21.19 / 02.03
indicators_28 = [
    # Capitalização de Mercado por Patrimônio Líquido (Market to Book Ratio)
    {
        'account': '28.05',
        'description': 'Capitalização de Mercado por Patrimônio Líquido',
        'formula': Division(
            '21.19',  # Capitalização de Mercado Total
            '02.03'   # Patrimônio Líquido
        )
    }
]

# 29.01 - Fluxo de Caixa Operacional por Ação Total # 06.01 / 21.00.03
# 29.02 - Fluxo de Caixa Operacional por Ação ON # (06.01 × 21.00.04) / 21.00.01
# 29.03 - Fluxo de Caixa Operacional por Ação PN # (06.01 × 21.00.05) / 21.00.02
indicators_29 = [
    # Fluxo de Caixa Operacional por Ação Total
    {
        'account': '29.01',
        'description': 'Fluxo de Caixa Operacional por Ação Total',
        'formula': Division(
            '06.01',    # Caixa das Operações
            '21.00.03'  # Número Total de Ações em Circulação
        )
    },
    # Fluxo de Caixa Operacional por Ação ON
    {
        'account': '29.02',
        'description': 'Fluxo de Caixa Operacional por Ação ON',
        'formula': Division(
            Multiplication('06.01', '21.00.04'),  # Caixa das Operações × Proporção ON
            '21.00.01'
        )
    },
    # Fluxo de Caixa Operacional por Ação PN
    {
        'account': '29.03',
        'description': 'Fluxo de Caixa Operacional por Ação PN',
        'formula': Division(
            Multiplication('06.01', '21.00.05'),  # Caixa das Operações × Proporção PN
            '21.00.02'
        )
    }
]

# 30.01 - Valor Econômico Adicionado (EVA) # [03.05 - (03.05 × 21.05)] - [(02.03 + (02.01.04 + 02.02.01)) × 20.01]
# 30.02 - Valor de Mercado Adicionado (MVA) # 21.19 - 02.03
indicators_30 = [
    # Valor Econômico Adicionado (EVA)
    {
        'account': '30.01',
        'description': 'Valor Econômico Adicionado (EVA)',
        'formula': Subtraction(
            Multiplication(
                Subtraction('03.05', Multiplication('03.05', '21.05')),  # NOPAT = EBIT × (1 - Taxa de Imposto)
                0
            ),
            Multiplication(
                Addition('02.03', Addition('02.01.04', '02.02.01')),  # Capital Investido
                '20.01'  # WACC
            )
        )
    },
    # Valor de Mercado Adicionado (MVA)
    {
        'account': '30.02',
        'description': 'Valor de Mercado Adicionado (MVA)',
        'formula': Subtraction(
            '21.19',  # Capitalização de Mercado Total
            '02.03'   # Patrimônio Líquido
        )
    }
]
