import pytest

from . pylisp import (
    Symbol,
    builtins,
    eval_line,
    eval_expr,
    parse_line,
    tokenize,
)

S = Symbol  # shorthand


@pytest.mark.parametrize('given, expect', [
    ('123 - 1', ['123', '-', '1']),
    ('((1 + 2) + 3)', ['(', '(', '1', '+', '2', ')', '+', '3', ')']),
    ('(1 1 +) (1 2 +)', ['(', '1', '1', '+', ')', '(', '1', '2', '+', ')']),
])
def test_tokenize(given, expect):
    assert all(t == v for t, v in zip(tokenize(given), expect))


@pytest.mark.parametrize('given, expect', [
    # arithmetic
    ([1, 1, S('+')], 2),
    ([2, 1, S('-')], 1),
    ([4, 2, S('/')], 2),
    ([3, 3, S('*')], 9),
    ([[1, 1, S('+')], 10, S('+')], 12),

    # eq?, atom?
    ([3, 3, S('eq?')], True),
    ([3, 2, S('eq?')], False),
    ([1, S('atom?')], True),
    ([S('nil'), S('atom?')], True),

    # >
    ([3, 2, S('>')], True),
    ([3, 3, S('>')], False),
    ([3.2, 3.1, S('>')], True),

    # quote
    ([1, S('quote')], 1),
    ([[1, 2, 3], S('quote')], [1, 2, 3]),

    # cons, car, cdr
    ([0, [[1], S('quote')], S('cons')], [0, 1]),
    ([[0, [[1, 2], S('quote')], S('cons')], S('car')], 0),
    ([[0, [[1, 2], S('quote')], S('cons')], S('cdr')], [1, 2]),

    # if
    ([[1, 0, Symbol(val='eq?')], [10, 10, Symbol(val='+')], [20, 20, Symbol(val='+')], Symbol(val='if')], 40),
    ([[[[1], Symbol(val='quote')], Symbol(val='atom?')], 1, 0, Symbol(val='if')], 0),
])
def test_eval_expr(given, expect):
    assert eval_expr(builtins(), given) == expect


def test_define():
    binds = builtins()
    exprs = [S('pi'), 3.14, S('define')]
    eval_expr(binds, exprs)
    assert 'pi' in binds


def test_e2e():
    line = '(pi 3.14 define) (2 pi *)'
    expect = [[Symbol(val='pi'), 3.14, Symbol(val='define')], [2, Symbol(val='pi'), Symbol(val='*')]]
    assert parse_line(line) == expect


@pytest.mark.parametrize('line, expect', [
    ('(1 1 +)', [[1, 1, S('+')]]),
    ('(11 11 +)', [[11, 11, S('+')]]),
    ('(10 (5 6 +) -)', [[10, [5, 6, S('+')], S('-')]]),
    ('(pi 3.14 define)', [[S('pi'), 3.14, S('define')]]),
    ('(1 1 +) (1 2 +)', [[1, 1, S('+')], [1, 2, S('+')]]),
    ('((1 0 eq?) (10 f) (20 f) if)', [[[1, 0, Symbol(val='eq?')], [10, Symbol(val='f')], [20, Symbol(val='f')], Symbol(val='if')]]),
    ('((((1) quote) atom?) 1 0 if)', [[[[[1], Symbol(val='quote')], Symbol(val='atom?')], 1, 0, Symbol(val='if')]]),
])
def test_parse_line(line, expect):
    assert parse_line(line) == expect


@pytest.mark.parametrize('exprs, expect', [
    ([[1, 1, S('+')], [1, 2, S('+')]], [2, 3]),
    ([[Symbol('pi'), 3.14, S('define')], [Symbol('pi'), 2, S('*')]], [None, 6.28]),
    # lambda
    ([[Symbol(val='f'), [[Symbol(val='x')], [Symbol(val='x'), Symbol(val='x'), Symbol(val='+')], Symbol(val='lambda')], Symbol(val='define')], [1, Symbol(val='f')]], [None, 2]),
])
def test_eval_line(exprs, expect):
    assert list(eval_line(builtins(), exprs)) == expect


def test_scope():
    line = '(x 1 define) (f (() (x 2 define) lambda) define) (f) x'
    exprs = parse_line(line)
    binds = builtins()
    assert list(filter(None, eval_line(binds, exprs)))[0] == 1
