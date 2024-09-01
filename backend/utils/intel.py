# statements standardization

section_0_lines = {
    ('00.01.01', 'Ações ON Ordinárias'): {'filter': 'account', 'condition': 'exact', 'value': '00.01.01'},
    ('00.01.02', 'Ações PN Preferenciais'): {'filter': 'account', 'condition': 'exact', 'value': '00.01.02'},
    ('00.02.01', 'Em Tesouraria Ações ON Ordinárias'): {'filter': 'account', 'condition': 'exact', 'value': '00.02.01'},
    ('00.02.02', 'Em Tesouraria Ações PN Preferenciais'): {'filter': 'account', 'condition': 'exact', 'value': '00.02.02'},
}

section_1_lines = {
    ('01', 'Ativo Total'): {'filter': 'account', 'condition': 'exact', 'value': '1'},
    ('01.01', 'Ativo Circulante de Curto Prazo'): {'filter': 'account', 'condition': 'exact', 'value': '1.01'},
    ('01.01.01', 'Caixa e Disponibilidades de Caixa'): {'filter': 'account', 'condition': 'exact', 'value': '1.01.01'},
    ('01.01.02', 'Aplicações Financeiras'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.01.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'description', 'condition': 'contains', 'value': ['aplica', 'depósito', 'reserv', 'saldo', 'centra', 'interfinanceir', 'crédit']},
            {'filter': 'account', 'condition': 'not_contains', 'value': ['1.01.01', '1.01.02', '1.01.06']}
        ]
    },
    ('01.01.03', 'Contas a Receber'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.01.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['conta']}]
    },
    ('01.01.04', 'Estoques'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.01.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['estoque']}]
    },
    ('01.01.05', 'Ativos Biológicos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.01.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['biológic']}]
    },
    ('01.01.06', 'Tributos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.01.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['tribut']}]
    },
    ('01.01.07', 'Despesas'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.01.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['despes']}]
    },
    ('01.01.09', 'Outros Ativos Circulantes'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.01.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'description', 'condition': 'contains', 'value': 'outr'},
            {'filter': 'description', 'condition': 'not_contains', 'value': ['aplica', 'depósito', 'reserv', 'saldo', 'centra', 'interfinanceir', 'crédit', 'conta', 'estoque', 'biológic', 'tribut', 'despes']},
            {'filter': 'account', 'condition': 'not_contains', 'value': ['1.01.01', '1.01.02', '1.01.03', '1.01.04', '1.01.05', '1.01.06', '1.01.07']}
        ]
    },
    ('01.02', 'Ativo Não Circulante de Longo Prazo'): {'filter': 'account', 'condition': 'exact', 'value': '1.02'},
    ('01.02.01', 'Ativos Financeiros'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.',
        'additional_filters': [{'filter': 'description', 'condition': 'not_contains', 'value': ['investiment', 'imobilizad', 'intangív']}]
    },
    ('01.02.01.01', 'Ativos Financeiros a Valor Justo'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [
            {'filter': 'description', 'condition': 'contains', 'value': 'valor justo'},
            {'filter': 'description', 'condition': 'not_contains', 'value': 'custo amortizado'}
        ]
    },
    ('01.02.01.02', 'Ativos Financeiros ao Custo Amortizado'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [
            {'filter': 'description', 'condition': 'contains', 'value': 'custo amortizado'},
            {'filter': 'description', 'condition': 'not_contains', 'value': 'valor justo'}
        ]
    },
    ('01.02.01.03', 'Contas a Receber'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'conta'}]
    },
    ('01.02.01.04', 'Estoques'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'estoque'}]
    },
    ('01.02.01.05', 'Ativos Biológicos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'biológic'}]
    },
    ('01.02.01.06', 'Tributos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'tribut'}]
    },
    ('01.02.01.07', 'Despesas'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'despes'}]
    },
    ('01.02.01.09', 'Outros Ativos Não Circulantes'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.01',
        'levelmin': 4, 'levelmax': 4,
        'additional_filters': [{'filter': 'description', 'condition': 'not_contains', 'value': ['valor justo', 'custo amortizado', 'conta', 'estoque', 'biológic', 'tribut', 'despes']}]
    },
    ('01.02.02', 'Investimentos Não Capex'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.',
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['investiment']}]
    },
    ('01.02.02.01', 'Propriedades - Investimentos Não Capex'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.',
        'levelmin': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['propriedad']}]
    },
    ('01.02.02.02', 'Arrendamentos - Investimentos Não Capex'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.',
        'levelmin': 3,
        'additional_filters': [
            {'filter': 'description', 'condition': 'contains', 'value': ['arrendam']},
            {'filter': 'description', 'condition': 'not_contains', 'value': ['sotware', 'imobilizad', 'intangív', 'direit']}
        ]
    },
    ('01.02.03', 'Imobilizados'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.',
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['imobilizad']}]
    },
    ('01.02.03.01', 'Imobilizados em Operação'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.03.',
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['operaç']}]
    },
    ('01.02.03.02', 'Imobilizados em Arrendamento'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.03.',
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['arrend']}]
    },
    ('01.02.03.03', 'Imobilizados em Andamento'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.03.',
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['andament']}]
    },
    ('01.02.04', 'Intangível'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.02.',
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': ['intangív']}]
    },
    ('01.03', 'Empréstimos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmax': 2,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'empréstimo'}]
    },
    ('01.04', 'Tributos Diferidos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmax': 2,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'tributo'}]
    },
    ('01.05', 'Investimentos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmax': 2,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'investimento'}]
    },
    ('01.05.01', 'Participações em Coligadas'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'coligad'}]
    },
    ('01.05.02', 'Participações em Controladas'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'controlad'}]
    },
    ('01.06', 'Imobilizados'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmax': 2,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'imobilizado'}]
    },
    ('01.06.01', 'Propriedades - Investimentos Não Capex'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'account', 'condition': 'not_startswith', 'value': ['1.02.']},
            {'filter': 'description', 'condition': 'contains', 'value': ['propriedad', 'imóve']}
        ]
    },
    ('01.06.02', 'Arrendamento - Investimentos Não Capex'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'account', 'condition': 'not_startswith', 'value': ['1.02.']},
            {'filter': 'description', 'condition': 'contains', 'value': 'arrendam'}
        ]
    },
    ('01.06.03', 'Tangíveis - Investimentos Não Capex'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'account', 'condition': 'not_startswith', 'value': ['1.02.']},
            {'filter': 'description', 'condition': 'contains', 'value': ['arrendam', 'equipamento']}
        ]
    },
    ('01.07', 'Intangíveis'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmax': 2,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'intangíve'}]
    },
    ('01.07.01', 'Intangíveis'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'account', 'condition': 'not_startswith', 'value': ['1.02.']},
            {'filter': 'description', 'condition': 'contains', 'value': 'intangíve'}
        ]
    },
    ('01.07.02', 'Goodwill'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'account', 'condition': 'not_startswith', 'value': ['1.02.']},
            {'filter': 'description', 'condition': 'contains', 'value': 'goodwill'}
        ]
    },
    ('01.08', 'Permanente'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.0',
        'levelmax': 2,
        'additional_filters': [{'filter': 'description', 'condition': 'contains', 'value': 'permanente'}]
    },
    ('01.09.09', 'Outros Ativos'): {
        'filter': 'account', 'condition': 'startswith', 'value': '1.',
        'levelmin': 3, 'levelmax': 3,
        'additional_filters': [
            {'filter': 'account', 'condition': 'not_startswith', 'value': ['1.01.', '1.02']},
            {'filter': 'description', 'condition': 'not_contains', 'value': ['depreciaç', 'amortizaç', 'empréstimo', 'tributo', 'investimento', 'imobilizado', 'intangíve', 'permanente', 'goodwill', 'arrendam', 'equipamento', 'propriedad', 'imóve', 'coligad', 'controlad']}
        ]
    }
}
