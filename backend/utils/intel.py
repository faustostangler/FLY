from utils import system

# statements standardization

default_example_data = [
    {
        'target': {'account': '01.01.01', 'description': 'Ações Preferenciais'},  # Example target values to update
        'filter': [
            {'column': 'account', 'condition': 'equals', 'value': '01.01.01'},  # Exact match
            {'column': 'account', 'condition': 'not_equals', 'value': '02.02.02'},  # Not equal to
            {'column': 'account', 'condition': 'startswith', 'value': '01.'},  # Starts with
            {'column': 'account', 'condition': 'not_startswith', 'value': '02.'},  # Does not start with
            {'column': 'account', 'condition': 'endswith', 'value': '.01'},  # Ends with
            {'column': 'account', 'condition': 'not_endswith', 'value': '.02'},  # Does not end with
            {'column': 'account', 'condition': 'contains_any', 'value': '01.01'},  # Contains
            {'column': 'account', 'condition': 'contains_none', 'value': '02.02'},  # Does not contain
            {'column': 'account', 'condition': 'contains_any', 'value': ['01', '03']},  # Contains any of these
            {'column': 'account', 'condition': 'contains_none', 'value': ['04', '05']},  # Contains none of these
            {'column': 'account', 'condition': 'contains_all', 'value': ['01', '01']},  # Contains all of these
            {'column': 'account', 'condition': 'not_contains_all', 'value': ['02', '02']},  # Does not contain all of these
            {'column': 'description', 'condition': 'equals', 'value': 'Ações Preferenciais'},  # Exact match
            {'column': 'description', 'condition': 'not_equals', 'value': 'Dividendos'},  # Not equal to
            {'column': 'description', 'condition': 'startswith', 'value': 'Ações'},  # Starts with
            {'column': 'description', 'condition': 'not_startswith', 'value': 'Dividendos'},  # Does not start with
            {'column': 'description', 'condition': 'endswith', 'value': 'Preferenciais'},  # Ends with
            {'column': 'description', 'condition': 'not_endswith', 'value': 'Dividendos'},  # Does not end with
            {'column': 'description', 'condition': 'contains_any', 'value': 'Preferenciais'},  # Contains
            {'column': 'description', 'condition': 'contains_none', 'value': 'Dividendos'},  # Does not contain
            {'column': 'description', 'condition': 'contains_any', 'value': ['Ações', 'Preferenciais']},  # Contains any of these
            {'column': 'description', 'condition': 'contains_none', 'value': ['Dividendos', 'Juros']},  # Contains none of these
            {'column': 'description', 'condition': 'contains_all', 'value': ['Ações', 'Preferenciais']},  # Contains all of these
            {'column': 'description', 'condition': 'not_contains_all', 'value': ['Dividendos', 'Juros']}  # Does not contain all of these
        ]
    }
]

section_0_criteria = [
    {
        'target': '00.01.01 - Ações ON Ordinárias',
        'filter': [
            ['account', 'equals', '00.01.01']
        ]
    },
    {
        'target': '00.01.02 - Ações PN Preferenciais',
        'filter': [
            ['account', 'equals', '00.01.02']
        ]
    },
    {
        'target': '00.02.01 - Em Tesouraria Ações ON Ordinárias',
        'filter': [
            ['account', 'equals', '00.02.01']
        ]
    },
    {
        'target': '00.02.02 - Em Tesouraria Ações PN Preferenciais',
        'filter': [
            ['account', 'equals', '00.02.02']
        ]
    }
]

section_1_criteria = [
    {'target': '01 - Ativo Total',
     'filter': [['account', 'equals', '1']]},

    {'target': '01.01 - Ativo Circulante de Curto Prazo',
     'filter': [['account', 'equals', '1.01']]},

    {'target': '01.01.01 - Caixa e Aplicações com Disponibilidades de Caixa',
     'filter': [
         ['account', 'startswith', '1.01.'], 
         ['account', 'level_min', 3],
         ['account', 'level_max', 3],
         ['account', 'contains_any', ['1.01.01', '1.01.02']], 
         ]},

    {'target': '01.01.01.01 - Caixa e Disponibilidades de Caixa Detalhamento',
     'filter': [
         ['account', 'startswith', '1.01.'], 
         ['account', 'level_min', 4],
         ['account', 'level_max', 4],
         ['account', 'contains_any', ['1.01.01', '1.01.02']], 
         ]},

    {'target': '01.01.02 - Créditos Diversos e Depósitos Judiciais',
     'filter': [
         ['account', 'startswith', '1.01.'],
         ['account', 'contains_none', ['1.01.01', '1.01.02', '1.01.06']],
         ['description', 'contains_any', ['aplica', 'depósito', 'reserv', 'saldo', 'centra', 'interfinanceir', 'crédit']]
     ]},

    {'target': '01.01.03 - Contas a Receber',
     'filter': [
         ['account', 'startswith', '1.01.'],
         ['account', 'level_min', 3],
         ['account', 'level_max', 3],
         ['description', 'contains_any', ['conta', 'client']]
     ]},

    {'target': '01.01.04 - Estoques',
     'filter': [
         ['account', 'startswith', '1.01.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'estoque']
     ]},

    {'target': '01.01.05 - Ativos Biológicos',
     'filter': [
         ['account', 'startswith', '1.01.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'biológic']
     ]},

    {'target': '01.01.06 - Tributos',
     'filter': [
         ['account', 'startswith', '1.01.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'tribut']
     ]},

    {'target': '01.01.07 - Despesas',
     'filter': [
         ['account', 'startswith', '1.01.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'despes']
     ]},

    {'target': '01.01.09 - Outros Ativos Circulantes',
     'filter': [
         ['account', 'startswith', '1.01.'],
         ['account', 'level_min', 3],
         ['account', 'level_max', 3],
         ['description', 'contains_none', ['aplica', 'depósito', 'reserv', 'saldo', 'centra', 'interfinanceir', 'crédit', 'conta', 'client', 'estoque', 'biológic', 'tribut', 'despes']],
         ['account', 'contains_none', ['1.01.01', '1.01.02', '1.01.03', '1.01.04', '1.01.05', '1.01.06', '1.01.07']]
     ]},

    {'target': '01.02 - Ativo Não Circulante de Longo Prazo',
     'filter': [['account', 'equals', '1.02']]},

    {'target': '01.02.01 - Ativos Financeiros',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_none', ['investiment', 'imobilizad', 'intangív']]
     ]},

    {'target': '01.02.01.01 - Ativos Financeiros a Valor Justo',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'valor justo'],
         ['description', 'contains_none', 'custo amortizado']
     ]},

    {'target': '01.02.01.02 - Ativos Financeiros ao Custo Amortizado',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'custo amortizado'],
         ['description', 'contains_none', 'valor justo']
     ]},

    {'target': '01.02.01.03 - Contas a Receber',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', ['conta', 'client']]
     ]},

    {'target': '01.02.01.04 - Estoques',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'estoque']
     ]},

    {'target': '01.02.01.05 - Ativos Biológicos',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'biológic']
     ]},

    {'target': '01.02.01.06 - Tributos',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'tribut']
     ]},

    {'target': '01.02.01.07 - Despesas',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'despes']
     ]},

    {'target': '01.02.01.09 - Outros Ativos Não Circulantes',
     'filter': [
         ['account', 'startswith', '1.02.01'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_none', ['valor justo', 'custo amortizado', 'conta', 'client', 'estoque', 'biológic', 'tribut', 'despes']]
     ]},

    {'target': '01.02.02 - Investimentos Não Capex',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'investiment']
     ]},

    {'target': '01.02.02.01 - Participações Investimentos Não Capex',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'particip']
     ]},

    {'target': '01.02.02.02 - Propriedades Investimentos Não Capex',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'investiment']
     ]},

    {'target': '01.02.02.03 - Arrendamentos Investimentos Não Capex',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'arrendam'],
         ['description', 'contains_none', ['software', 'imobilizad', 'intangív', 'direit']]
     ]},

    {'target': '01.02.03 - Imobilizados',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'imobilizad']
     ]},

    {'target': '01.02.03.01 - Imobilizados em Operação',
     'filter': [
         ['account', 'startswith', '1.02.03.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'operaç']
     ]},

    {'target': '01.02.03.02 - Imobilizados em Arrendamento',
     'filter': [
         ['account', 'startswith', '1.02.03.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'arrend']
     ]},

    {'target': '01.02.03.03 - Imobilizados em Andamento',
     'filter': [
         ['account', 'startswith', '1.02.03.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'andament']
     ]},

    {'target': '01.02.04 - Intangível',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'intangív']
     ]},

    {'target': '01.03 - Empréstimos',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'empr']
     ]},

    {'target': '01.04 - Tributos Diferidos',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'tributo']
     ]},

    {'target': '01.05 - Investimentos',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'investimento']
     ]},

    {'target': '01.05.01 - Participações em Coligadas',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 5], 
         ['account', 'level_max', 5], 
         ['description', 'contains_any', 'coligad']
     ]},

    {'target': '01.05.02 - Participações em Controladas',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 5], 
         ['account', 'level_max', 5], 
         ['description', 'contains_any', 'controlad']
     ]},

    {'target': '01.06 - Imobilizados',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'imobilizado']
     ]},

    {'target': '01.06.01 - Propriedades Investimentos Não Capex',
     'filter': [
         ['account', 'startswith', '1.02'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', ['propriedad', 'imóve']],
     ]},

    {'target': '01.06.02 - Arrendamento Investimentos Não Capex',
     'filter': [
         ['account', 'startswith', '1.02'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'arrendam'],
     ]},

    {'target': '01.06.03 - Tangíveis Investimentos Não Capex',
     'filter': [
         ['account', 'startswith', '1.02'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', ['arrendam', 'equipamento']],
     ]},

    {'target': '01.07 - Intangíveis',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'intangíve']
     ]},

    {'target': '01.07.01 - Intangíveis',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'intangíve'],
     ]},

    {'target': '01.07.02 - Goodwill',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 4], 
         ['account', 'level_max', 4], 
         ['description', 'contains_any', 'goodwill'],
     ]},

    {'target': '01.08 - Permanente',
     'filter': [
         ['account', 'startswith', '1.02.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_any', 'permanente']
     ]},

    {'target': '01.09.09 - Outros Ativos',
     'filter': [
         ['account', 'startswith', '1.'],
         ['account', 'level_min', 3], 
         ['account', 'level_max', 3], 
         ['description', 'contains_none', ['depreciaç', 'amortizaç', 'empréstimo', 'tributo', 'investimento', 'imobilizado', 'intangíve', 'permanente', 'goodwill', 'arrendam', 'equipamento', 'propriedad', 'imóve', 'coligad', 'controlad']],
         ['account', 'not_startswith', ['1.01.', '1.02.']]
     ]}
]

section_2_criteria = [
    {'target': {'account': '02', 'description': 'Passivo Total'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '2'}]},

    {'target': {'account': '02.01', 'description': 'Passivo Circulante de Curto Prazo'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 2},
         {'column': 'account', 'condition': 'level_max', 'value': 2},
         {'column': 'description', 'condition': 'contains', 'value': ['circulante', 'o resultado', 'amortizado', 'negociaç']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['não', 'patrimônio', 'fisca']}
     ]},

    {'target': {'account': '02.01.01', 'description': 'Obrigações Sociais e Trabalhistas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['obrigações sociais']}
     ]},

    {'target': {'account': '02.01.01.01', 'description': 'Obrigações Sociais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['socia']}
     ]},

    {'target': {'account': '02.01.01.02', 'description': 'Obrigações Trabalhistas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['trabalhista']}
     ]},

    {'target': {'account': '02.01.01.09', 'description': 'Outras Obrigações'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'not_contains', 'value': ['socia', 'trabalhista']}
     ]},

    {'target': {'account': '02.01.02', 'description': 'Fornecedores'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['fornecedor']}
     ]},

    {'target': {'account': '02.01.02.01', 'description': 'Fornecedores Nacionais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': ['2.01.01.', '2.01.02']},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['fornecedores nacionais']}
     ]},

    {'target': {'account': '02.01.02.02', 'description': 'Fornecedores Estrangeiros'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': ['2.01.01.', '2.01.02']},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['fornecedores estrangeiros']}
     ]},

    {'target': {'account': '02.01.03', 'description': 'Obrigações Fiscais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['obrigaç', 'fisca']},
         {'column': 'description', 'condition': 'not_contains', 'value': 'socia'}
     ]},

    {'target': {'account': '02.01.03.01', 'description': 'Obrigações Fiscais Federais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['federa']}
     ]},

    {'target': {'account': '02.01.03.02', 'description': 'Obrigações Fiscais Estaduais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['estadua']}
     ]},

    {'target': {'account': '02.01.03.03', 'description': 'Obrigações Fiscais Municipais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': 'municipa'}
     ]},

    {'target': {'account': '02.01.03.09', 'description': 'Outras Obrigações Fiscais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'not_contains', 'value': ['federa', 'estadua', 'municipa']}
     ]},

    {'target': {'account': '02.01.04', 'description': 'Empréstimos, Financiamentos e Debêntures'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['empréstimo', 'financiamento']}
     ]},

    {'target': {'account': '02.01.04.01', 'description': 'Empréstimos e Financiamentos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.04'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['empréstimo', 'financiamento']}
     ]},

    {'target': {'account': '02.01.04.01.01', 'description': 'Empréstimos e Financiamentos em Moeda Nacional'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.04.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'naciona'}
     ]},

    {'target': {'account': '02.01.04.01.02', 'description': 'Empréstimos e Financiamentos em Moeda Estrangeira'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.04.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'estrangeir'}
     ]},

    {'target': {'account': '02.01.04.02', 'description': 'Debêntures'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.04'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': 'debentur'}
     ]},

    {'target': {'account': '02.01.04.03', 'description': 'Arrendamentos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.04'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': 'arrendament'}
     ]},

    {'target': {'account': '02.01.04.09', 'description': 'Outros Empréstimos, Financiamentos e Debêntures'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.04'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'not_contains', 'value': ['empréstimo', 'financiamento', 'debentur', 'arrendament']}
     ]},

    {'target': {'account': '02.01.05', 'description': 'Outras Obrigações'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.05'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['outr', 'relaç']}
     ]},

    {'target': {'account': '02.01.05.01', 'description': 'Passivos com Partes Relacionadas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.05'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['partes relacionadas']}
     ]},

    {'target': {'account': '02.01.05.09', 'description': 'Outros'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.05'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'not_contains', 'value': ['partes relacionadas']}
     ]},

    {'target': {'account': '02.01.06', 'description': 'Provisões'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['provis']}
     ]},

    {'target': {'account': '02.01.06.01', 'description': 'Provisões Específicas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['provis']}
     ]},

    {'target': {'account': '02.01.06.01.01', 'description': 'Provisões Fiscais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.01.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['fisca']}
     ]},

    {'target': {'account': '02.01.06.01.02', 'description': 'Provisões Trabalhistas e Previdenciárias'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.01.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['trabalhist']}
     ]},

    {'target': {'account': '02.01.06.01.03', 'description': 'Provisões para Benefícios a Empregados'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.01.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['benefício']}
     ]},

    {'target': {'account': '02.01.06.01.04', 'description': 'Provisões Judiciais Cíveis'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.01.04'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['cív']}
     ]},

    {'target': {'account': '02.01.06.01.05', 'description': 'Outras Provisões Específicas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.01.05'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['outr']}
     ]},

    {'target': {'account': '02.01.06.02', 'description': 'Provisões Outras'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['provis']}
     ]},

    {'target': {'account': '02.01.06.02.01', 'description': 'Provisões para Garantias'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['garantia']}
     ]},

    {'target': {'account': '02.01.06.02.02', 'description': 'Provisões para Reestruturação'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['reestrutura']}
     ]},

    {'target': {'account': '02.01.06.02.03', 'description': 'Provisões para Passivos Ambientais e de Desativação'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.06.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['ambient']}
     ]},

    {'target': {'account': '02.01.07', 'description': 'Passivos sobre Ativos Não-Correntes a Venda e Descontinuados'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['Passivos sobre ativos']}
     ]},

    {'target': {'account': '02.01.07.01', 'description': 'Passivos sobre Ativos Não-Correntes a Venda'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.07.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['venda']}
     ]},

    {'target': {'account': '02.01.07.02', 'description': 'Passivos sobre Ativos de Operações Descontinuadas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.07.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['descontinuad']}
     ]},

    {'target': {'account': '02.01.09', 'description': 'Outros Passivos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'not_contains', 'value': ['obrigações sociais', 'fornecedor', 'obrigaç', 'fisca', 'empréstimo', 'financiamento', 'provis', 'Passivos sobre ativos']}
     ]},

    {'target': {'account': '02.02', 'description': 'Passivo Não Circulante de Longo Prazo'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 2},
         {'column': 'account', 'condition': 'level_max', 'value': 2},
         {'column': 'description', 'condition': 'contains', 'value': ['longo prazo', 'não circulante', 'negociação', 'fisca', 'provis', 'exercício', 'outr', 'venda']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['patrimônio']}
     ]},

    {'target': {'account': '02.02.01', 'description': 'Empréstimos e Financiamentos de Longo Prazo'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['empréstim', 'financiament']}
     ]},

    {'target': {'account': '02.02.01.01', 'description': 'Empréstimos e Financiamentos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['empréstim', 'financiament']}
     ]},

    {'target': {'account': '02.02.01.01.01', 'description': 'Empréstimos e Financiamentos em Moeda Nacional'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.01.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['naciona']}
     ]},

    {'target': {'account': '02.02.01.01.02', 'description': 'Empréstimos e Financiamentos em Moeda Estrangeira'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.01.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['estrangeir']}
     ]},

    {'target': {'account': '02.02.01.02', 'description': 'Debêntures'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['debentur']}
     ]},

    {'target': {'account': '02.02.01.03', 'description': 'Arrendamentos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['arrendament']}
     ]},

    {'target': {'account': '02.02.02.09', 'description': 'Outros Empréstimos, Financiamentos e Debêntures'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'not_contains', 'value': ['empréstimo', 'financiamento', 'debentur', 'arrendament']}
     ]},

    {'target': {'account': '02.02.02', 'description': 'Outras Obrigações'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['obriga']}
     ]},

    {'target': {'account': '02.02.02.01', 'description': 'Com Partes Relacionadas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.02.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['relacionad']}
     ]},

    {'target': {'account': '02.02.02.02', 'description': 'Outras Obrigações'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.02.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['outr']}
     ]},

    {'target': {'account': '02.02.03', 'description': 'Tributos Diferidos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': 'tributo'}
     ]},

    {'target': {'account': '02.02.03.01', 'description': 'Imposto de Renda e Contribuição Social'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['imposto de renda', 'contribuição social']}
     ]},

    {'target': {'account': '02.02.03.02', 'description': 'Outros tributos diferidos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'not_contains', 'value': ['imposto de renda', 'contribuição social']}
     ]},

    {'target': {'account': '02.02.04', 'description': 'Provisões'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': 'provis'}
     ]},

    {'target': {'account': '02.02.04.01', 'description': 'Provisões Específicas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': 'provis'}
     ]},

    {'target': {'account': '02.02.04.01.01', 'description': 'Provisões Fiscais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.01.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'fisca'}
     ]},

    {'target': {'account': '02.02.04.01.02', 'description': 'Provisões Trabalhistas e Previdenciárias'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.01.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'trabalhist'}
     ]},

    {'target': {'account': '02.02.04.01.03', 'description': 'Provisões para Benefícios a Empregados'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.01.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'benefício'}
     ]},

    {'target': {'account': '02.02.04.01.04', 'description': 'Provisões Judiciais Cíveis'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.01.04'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'cív'}
     ]},

    {'target': {'account': '02.02.04.02', 'description': 'Outras Provisões'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': 'provis'}
     ]},

    {'target': {'account': '02.02.04.02.01', 'description': 'Provisões para Garantias'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'garantia'}
     ]},

    {'target': {'account': '02.02.04.02.02', 'description': 'Provisões para Reestruturação'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': 'reestrutura'}
     ]},

    {'target': {'account': '02.02.04.02.03', 'description': 'Provisões para Passivos Ambientais e de Desativação'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.04.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 5},
         {'column': 'account', 'condition': 'level_max', 'value': 5},
         {'column': 'description', 'condition': 'contains', 'value': ['ambient']}
     ]},

    {'target': {'account': '02.02.05', 'description': 'Passivos sobre Ativos Não-Correntes a Venda e Descontinuados'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['Passivos sobre ativos']}
     ]},

    {'target': {'account': '02.02.05.01', 'description': 'Passivos sobre Ativos Não-Correntes a Venda'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.05.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['venda']}
     ]},

    {'target': {'account': '02.02.05.02', 'description': 'Passivos sobre Ativos de Operações Descontinuadas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.05.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['descontinuad']}
     ]},

    {'target': {'account': '02.02.06', 'description': 'Lucros e Receitas a Apropriar'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['lucros e receitas']}
     ]},

    {'target': {'account': '02.02.06.01', 'description': 'Lucros a Apropriar'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.06.01'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['lucr']}
     ]},

    {'target': {'account': '02.02.06.02', 'description': 'Receitas a Apropriar'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.06.02'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['receit']}
     ]},

    {'target': {'account': '02.02.06.03', 'description': 'Subvenções de Investimento a Apropriar'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.02.06.03'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['subvenç']}
     ]},

    {'target': {'account': '02.02.09', 'description': 'Outros Passivos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': ['2.02.07', '2.02.08', '2.02.09']},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3}
     ]},

    {'target': {'account': '02.03', 'description': 'Patrimônio Líquido'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 2},
         {'column': 'account', 'condition': 'level_max', 'value': 2},
         {'column': 'description', 'condition': 'contains', 'value': 'patrimônio'}
     ]},

    {'target': {'account': '02.03.01', 'description': 'Capital Social'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['capital social']}
     ]},

    {'target': {'account': '02.03.02', 'description': 'Reservas de Capital'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['reservas de capital']}
     ]},

    {'target': {'account': '02.03.03', 'description': 'Reservas de Reavaliação'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['reservas de reavaliaç']}
     ]},

    {'target': {'account': '02.03.04', 'description': 'Reservas de Lucros'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['reservas de lucro']}
     ]}, 
        {'target': {'account': '02.03.05', 'description': 'Lucros ou Prejuízos Acumulados'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['lucro', 'prejuízo', 'acumulad']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['reserva']}
     ]},

    {'target': {'account': '02.03.06', 'description': 'Ajustes de Avaliação Patrimonial'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['avaliação patrimonial']}
     ]},

    {'target': {'account': '02.03.07', 'description': 'Ajustes Acumulados de Conversão'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['ajustes acumulados']}
     ]},

    {'target': {'account': '02.03.08', 'description': 'Outros Resultados Abrangentes'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '2.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['2.01', '2.02']},
         {'column': 'description', 'condition': 'contains', 'value': ['resultados abrangentes']}
     ]},

    {'target': {'account': '02.04', 'description': 'Outros Passivos ou Provissões'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': ['2.04', '2.05', '2.06', '2.07', '2.08', '2.09']},
         {'column': 'account', 'condition': 'level_min', 'value': 2},
         {'column': 'account', 'condition': 'level_max', 'value': 2},
         {'column': 'description', 'condition': 'not_contains', 'value': ['patrimonio']}
     ]},
]

section_3_criteria = [
    {'target': {'account': '03.01', 'description': 'Receita Bruta'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.01'}
     ]},

    {'target': {'account': '03.02', 'description': 'Custo de Produção'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.02'}
     ]},

    {'target': {'account': '03.03', 'description': 'Resultado Bruto (Receita Líquida)'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.03'}
     ]},

    {'target': {'account': '03.04', 'description': 'Despesas Operacionais'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.04'}
     ]},

    {'target': {'account': '03.04.01', 'description': 'Despesas com Vendas'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.04.01'}
     ]},

    {'target': {'account': '03.04.02', 'description': 'Despesas Gerais e Administrativas'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.04.02'}
     ]},

    {'target': {'account': '03.04.09', 'description': 'Outras despesas, receitas ou equivalências'},
     'filter': [
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'account', 'condition': 'startswith', 'value': ['3.04.']},
         {'column': 'account', 'condition': 'not_startswith', 'value': ['3.04.01', '3.04.02']}
     ]},

    {'target': {'account': '03.05', 'description': 'LAJIR EBIT Resultado Antes do Resultado Financeiro e dos Tributos'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.05'}
     ]},

    {'target': {'account': '03.06', 'description': 'Resultado Financeiro (Não Operacional)'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.06'}
     ]},

    {'target': {'account': '03.07', 'description': 'Resultado Antes dos Tributos sobre o Lucro'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.07'}
     ]},

    {'target': {'account': '03.08', 'description': 'Impostos IRPJ e CSLL'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.08'}
     ]},

    {'target': {'account': '03.09', 'description': 'Resultado Líquido das Operações Continuadas'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.09'}
     ]},

    {'target': {'account': '03.10', 'description': 'Resultado Líquido das Operações Descontinuadas'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.10'}
     ]},

    {'target': {'account': '03.11', 'description': 'Lucro Líquido'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '3.11'}
     ]}
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

section_6_criteria = [
    {'target': {'account': '06.01', 'description': 'Caixa das Operações'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '6.01'}
     ]},

    {'target': {'account': '06.01.01', 'description': 'Caixa das Operações'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['operac']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['ativ', 'print(e)iv', 'despes', 'ingress', 'pagament', 'receb', 'arrendament', 'aquisic']}
     ]},

    {'target': {'account': '06.01.02', 'description': 'Variações de Ativos e Passivos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['ativ']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['operac', 'imob', 'intangív', 'adiantament', 'provis', 'permanent', 'despes', 'pagament', 'recebiment', 'caixa', 'derivativ', 'judicia']}
     ]},

    {'target': {'account': '06.01.09', 'description': 'Outros Caixas Operacionais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.01.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'not_contains', 'value': ['ativ', 'operac']}
     ]},

    {'target': {'account': '06.02', 'description': 'Caixa de Investimentos CAPEX'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '6.02'}
     ]},

    {'target': {'account': '06.02.01', 'description': 'Investimentos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': investment_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_investment_related_keywords, investment_keywords)}
     ]},

    {'target': {'account': '06.02.02', 'description': 'Imobilizado e Intangível'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': tangible_intangible_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_investment_related_keywords, tangible_intangible_keywords)}
     ]},

    {'target': {'account': '06.02.03', 'description': 'Aplicações Financeiras'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.02.'},
         {'column': 'account', 'condition': 'Impostos IRPJ e CSLL', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': financial_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_investment_related_keywords, financial_keywords)}
     ]},

    {'target': {'account': '06.02.04', 'description': 'Coligadas e Controladas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': affiliated_controlled_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_investment_related_keywords, affiliated_controlled_keywords)}
     ]},

    {'target': {'account': '06.02.05', 'description': 'Juros sobre Capital Próprio e Dividendos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': interest_dividends_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_investment_related_keywords, interest_dividends_keywords)}
     ]},

    {'target': {'account': '06.02.09', 'description': 'Outros Caixas de Investimento'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.02.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'not_contains', 'value': all_investment_related_keywords}
     ]},

    {'target': {'account': '06.03', 'description': 'Caixa de Financiamento'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '6.03'}
     ]},

    {'target': {'account': '06.03.01', 'description': 'Capital'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.03.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': capital_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_financing_related_keywords, capital_keywords)}
     ]},

    {'target': {'account': '06.03.02', 'description': 'Ações e Acionistas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.03.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': shares_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_financing_related_keywords, shares_keywords)}
     ]},

    {'target': {'account': '06.03.03', 'description': 'Debêntures, empréstimos e financiamentos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.03.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': debentures_loans_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_financing_related_keywords, debentures_loans_keywords)}
     ]},

    {'target': {'account': '06.03.04', 'description': 'Credores'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.03.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': creditor_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_financing_related_keywords, creditor_keywords)}
     ]},

    {'target': {'account': '06.03.05', 'description': 'Captações e Amortizações'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.03.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': amortization_funding_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_financing_related_keywords, amortization_funding_keywords)}
     ]},

    {'target': {'account': '06.03.06', 'description': 'Juros JCP e Dividendos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.03.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': dividends_interest_keywords},
         {'column': 'description', 'condition': 'not_contains', 'value': system.subtract_lists(all_financing_related_keywords, dividends_interest_keywords)}
     ]},

    {'target': {'account': '06.03.09', 'description': 'Outros Caixas de Financiamento'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '6.03.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'not_contains', 'value': all_financing_related_keywords}
     ]},

    {'target': {'account': '06.04', 'description': 'Caixa da Variação Cambial'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '6.04'}
     ]},

    {'target': {'account': '06.05', 'description': 'Variação do Caixa'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '6.05'}
     ]},

    {'target': {'account': '06.05.01', 'description': 'Saldo Inicial do Caixa'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '6.05.01'}
     ]},

    {'target': {'account': '06.05.02', 'description': 'Saldo Final do Caixa'},
     'filter': [
         {'column': 'account', 'condition': 'equals', 'value': '6.05.02'}
     ]}
]

section_7_criteria = [
    {'target': {'account': '07.01', 'description': 'Receitas'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['receita']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['líquid']}
     ]},
    {'target': {'account': '07.01.01', 'description': 'Vendas'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.01.01'}]},
    {'target': {'account': '07.01.02', 'description': 'Outras Receitas'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.01.02'}]},
    {'target': {'account': '07.01.03', 'description': 'Ativos Próprios'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.01.03'}]},
    {'target': {'account': '07.01.04', 'description': 'Reversão de Créditos Podres'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.01.04'}]},
    {'target': {'account': '07.02', 'description': 'Custos dos Insumos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['insumos adquiridos', 'intermediação financeira', 'provis']}
     ]},
    {'target': {'account': '07.02.01', 'description': 'Custo de Mercadorias'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.02.01'}]},
    {'target': {'account': '07.02.02', 'description': 'Custo de Materiais, Energia e Terceiros'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.02.02'}]},
    {'target': {'account': '07.02.03', 'description': 'Valores Ativos'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.02.03'}]},
    {'target': {'account': '07.02.04', 'description': 'Outros'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.02.04'}]},
    {'target': {'account': '07.03', 'description': 'Valor Adicionado Bruto'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['valor adicionado bruto']}
     ]},
    {'target': {'account': '07.04', 'description': 'Retenções'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['retenç', 'Benefíci', 'sinistr']}
     ]},
    {'target': {'account': '07.04.01', 'description': 'Depreciação e Amortização'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['deprecia', 'amortiza', 'exaust']}
     ]},
    {'target': {'account': '07.04.02', 'description': 'Outras retenções'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.04.02'}]},
    {'target': {'account': '07.05', 'description': 'Valor Adicionado Líquido'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['valor adicionado líquid', 'receita operacional']},
         {'column': 'account', 'condition': 'not_startswith', 'value': '7.01'},
         {'column': 'description', 'condition': 'not_contains', 'value': ['transferência']}
     ]},
    {'target': {'account': '07.06', 'description': 'Valor Adicionado em Transferência'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['transferência']}
     ]},
    {'target': {'account': '07.06.01', 'description': 'Resultado de Equivalência Patrimonial'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['equivalencia patrimonial']}
     ]},
    {'target': {'account': '07.06.02', 'description': 'Receitas Financeiras'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.06.02'}]},
    {'target': {'account': '07.06.03', 'description': 'Outros'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.06.03'}]},
    {'target': {'account': '07.07', 'description': 'Valor Adicionado Total a Distribuir'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['total a distribuir']}
     ]},
    {'target': {'account': '07.08', 'description': 'Distribuição do Valor Adicionado'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'description', 'condition': 'contains', 'value': ['Distribuição do Valor Adicionado']}
     ]},
    {'target': {'account': '07.08.01', 'description': 'Pessoal'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['pessoal']}
     ]},
    {'target': {'account': '07.08.01.01', 'description': 'Remuneração Direta'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['remuneração direta']}
     ]},
    {'target': {'account': '07.08.01.02', 'description': 'Benefícios'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['benefícios']}
     ]},
    {'target': {'account': '07.08.01.03', 'description': 'FGTS'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['F.G.T.S.', 'fgts']}
     ]},
    {'target': {'account': '07.08.01.04', 'description': 'Outros'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.08.01.04'}]},
    {'target': {'account': '07.08.02', 'description': 'Impostos, Taxas e Contribuições'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['imposto', 'taxa', 'contribuiç']}
     ]},
    {'target': {'account': '07.08.02.01', 'description': 'Federais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['federa']}
     ]},
    {'target': {'account': '07.08.02.02', 'description': 'Estaduais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['estadua']}
     ]},
    {'target': {'account': '07.08.02.03', 'description': 'Municipais'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['municipa']}
     ]},
    {'target': {'account': '07.08.03', 'description': 'Remuneração de Capital de Terceiros'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['remuneraç', 'capital', 'terceir']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['própri']}
     ]},
    {'target': {'account': '07.08.03.01', 'description': 'Juros Pagos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['juro']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['propri']}
     ]},
    {'target': {'account': '07.08.03.02', 'description': 'Aluguéis'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['alugue']}
     ]},
    {'target': {'account': '07.08.04', 'description': 'Remuneração de Capital Próprio'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 3},
         {'column': 'account', 'condition': 'level_max', 'value': 3},
         {'column': 'description', 'condition': 'contains', 'value': ['remuneraç', 'capital', 'própri']},
         {'column': 'description', 'condition': 'not_contains', 'value': ['terceir']}
     ]},
    {'target': {'account': '07.08.04.01', 'description': 'Juros sobre o Capital Próprio'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['juros sobre', 'jcp']}
     ]},
    {'target': {'account': '07.08.04.02', 'description': 'Dividendos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['dividend']}
     ]},
    {'target': {'account': '07.08.04.03', 'description': 'Lucros Retidos'},
     'filter': [
         {'column': 'account', 'condition': 'startswith', 'value': '7.'},
         {'column': 'account', 'condition': 'level_min', 'value': 4},
         {'column': 'account', 'condition': 'level_max', 'value': 4},
         {'column': 'description', 'condition': 'contains', 'value': ['lucros retidos']}
     ]},
    {'target': {'account': '07.08.05', 'description': 'Outros'},
     'filter': [{'column': 'account', 'condition': 'equals', 'value': '7.08.05'}]},
]
