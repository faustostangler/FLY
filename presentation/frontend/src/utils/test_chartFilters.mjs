import { buildChartFilterTree } from './chartFilters.js';

const testCases = [
    {
        name: 'Simple Leaf',
        input: {
            clauses: [
                {
                    logical: 'AND',
                    condition: { field: 'status', operator: 'EQUALS', values: ['ATIVO'] }
                }
            ]
        },
        expected: { status: 'ATIVO' }
    },
    {
        name: 'Simple List (IN)',
        input: {
            clauses: [
                {
                    logical: 'AND',
                    condition: { field: 'market', operator: 'IN', values: ['NM', 'N2'] }
                }
            ]
        },
        expected: { market: { in: ['NM', 'N2'] } }
    },
    {
        name: 'Nested Group (OR)',
        input: {
            clauses: [
                {
                    logical: 'AND',
                    condition: { field: 'status', operator: 'EQUALS', values: ['ATIVO'] }
                },
                {
                    logical: 'AND',
                    group: {
                        clauses: [
                            {
                                logical: 'OR',
                                condition: { field: 'has_bdr', operator: 'EQUALS', values: ['true'] }
                            },
                            {
                                logical: 'OR',
                                condition: { field: 'market', operator: 'IN', values: ['NM'] }
                            }
                        ]
                    }
                }
            ]
        },
        expected: {
            and: [
                { status: 'ATIVO' },
                {
                    or: [
                        { has_bdr: 'true' },
                        { market: { in: ['NM'] } }
                    ]
                }
            ]
        }
    },
    {
        name: 'NOT Logic',
        input: {
            clauses: [
                {
                    logical: 'NOT',
                    condition: { field: 'sector', operator: 'EQUALS', values: ['Finance'] }
                }
            ]
        },
        expected: { not: { sector: 'Finance' } }
    },
    {
        name: 'Complex Deep Nesting',
        input: {
            clauses: [
                {
                    logical: 'AND',
                    group: {
                        clauses: [
                            {
                                logical: 'AND',
                                condition: { field: 'A', operator: 'EQ', values: ['1'] }
                            },
                            {
                                logical: 'NOT',
                                group: {
                                    clauses: [
                                        {
                                            logical: 'OR',
                                            condition: { field: 'B', operator: 'EQ', values: ['2'] }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        },
        expected: {
            and: [
                { A: '1' },
                { not: { B: '2' } }
            ]
        }
    }
];

function runTests() {
    let passed = 0;
    let failed = 0;

    testCases.forEach(test => {
        console.log(`Running test: ${test.name}`);
        const result = buildChartFilterTree(test.input);
        const jsonResult = JSON.stringify(result);
        const jsonExpected = JSON.stringify(test.expected);

        if (jsonResult === jsonExpected) {
            console.log('✅ PASSED');
            passed++;
        } else {
            console.log('❌ FAILED');
            console.log('Expected:', jsonExpected);
            console.log('Actual:  ', jsonResult);
            failed++;
        }
        console.log('---');
    });

    console.log(`Total: ${passed + failed}, Passed: ${passed}, Failed: ${failed}`);
    if (failed > 0) process.exit(1);
}

runTests();
