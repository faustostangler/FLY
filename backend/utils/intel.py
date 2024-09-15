import numpy as np

from utils import system

# statements standardization
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
            ['account', 'startswith', '3.04'],
            ['description', 'contains_all', ['despesas', 'receitas']]
        ],
        'sub_criteria': [
            {
                'target': '03.04.01 - Despesas Operacionais',
                'filter': [
                    ['account', 'level', 3],
                    ['account', 'startswith', '3.04.01']
                ],
                'sub_criteria': [
                    {
                        'target': '03.04.01.01 - Despesas Comerciais',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.01'],
                            ['description', 'contains_any', 'comerci']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.02 - Despesas Gerais e Administrativas',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.02'],
                            ['description', 'contains_all', 'administrativ']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.03 - Honorários da Diretoria',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.03'],
                            ['description', 'contains_all', 'diretor']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.04 - Despesas Tributárias e Judiciais',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.04'],
                            ['description', 'contains_any', ['tribut', 'judic', 'impost']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.05 - Despesas com Pessoal e Encargos',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.05'],
                            ['description', 'contains_all', 'pessoal']
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.06 - Dividendos',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.07'],
                            ['description', 'contains_any', ['dividend']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.07 - Provisões',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.08'],
                            ['description', 'contains_any', ['provis']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.08 - Diversos',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.06'],
                            ['description', 'contains_none', ['comerci', 'administrativ', 'diretor', 'tribut', 'judic', 'impost', 'pessoal', 'dividend', 'provis', 'outr']]
                        ],
                        'sub_criteria': []
                    },
                    {
                        'target': '03.04.01.09 - Outras Despesas',
                        'filter': [
                            ['account', 'level', 4],
                            ['account', 'startswith', '3.04.01.09'],
                            ['description', 'contains_any', ['outr']]
                        ],
                        'sub_criteria': []
                    }
                ]
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
    """
    Base class for all formula operations.
    """
    def __call__(self, df):
        raise NotImplementedError("Each formula must implement the __call__ method.")

class Addition(Formula):
    def __init__(self, *accounts, multiplier=1):
        """
        Initializes the Addition operation.

        Parameters:
        - *accounts: A list of account names or Formula instances to be summed.
        """
        if len(accounts) < 1:
            raise ValueError("Addition requires at least one account.")
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
            raise KeyError(f"Missing account: {e}")

class Subtraction(Formula):
    def __init__(self, minuend, *subtrahends, multiplier=1):
        """
        Initializes the Subtraction operation.

        Parameters:
        - minuend (str or Formula): The account name or Formula instance from which to subtract.
        - *subtrahends: A list of account names or Formula instances to subtract.
        """
        if len(subtrahends) < 1:
            raise ValueError("Subtraction requires at least one subtrahend.")
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
            raise KeyError(f"Missing account: {e}")

class Multiplication(Formula):
    def __init__(self, *multiplicands, multiplier=1):
        """
        Initializes the Multiplication operation.

        Parameters:
        - *multiplicands: A list of account names or Formula instances to be multiplied.
        """
        if len(multiplicands) < 1:
            raise ValueError("Multiplication requires at least one multiplicand.")
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
            raise KeyError(f"Missing account: {e}")

class Division(Formula):
    def __init__(self, numerator, denominator, multiplier=1):
        """
        Initializes the Division operation.

        Parameters:
        - numerator (str or Formula): The account name or Formula instance for the numerator.
        - denominator (str or Formula): The account name or Formula instance for the denominator.
        - multiplier (float): A constant to multiply the result by. Defaults to 1.
        """
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
            raise KeyError(f"Missing account: {e}")

##### New Indicators
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
            '03.04'  # Despesas Operacionais
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
            '08.01'  # Dividendos Mínimos Obrigatórios
        )
    }
]

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
