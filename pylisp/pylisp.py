#!/usr/bin/env python
"""
We want you to make this a postfix Lisp instead of a traditional prefix Lisp.
Write a basic postfix Lisp interpreter that implements a subset of the Lisp
special forms. (here’s a good basic description of a basic Lisp)

http://pythonpracticeprojects.com/lisp.html


to do:
    [x] repl
    [x] lambda
    [x] if
    [ ] lambda functions that recurse themselves (e.g., fib)
    [ ] scope
    [ ] split file

"""
from dataclasses import dataclass
from itertools import chain
from numbers import Number
from operator import add, sub, mul, truediv
from typing import Dict, List, Any
import fileinput
import sys


def is_number(value):
    return isinstance(value, Number)


@dataclass(frozen=True)
class Symbol:
    val: str


@dataclass(frozen=True)
class Lambda:
    binds: Dict
    params: List
    body: Any

    def __call__(self, *args):
        binds = self.binds.copy()  # avoid copy
        binds.update({param.val: arg for param, arg in zip(self.params, args)})
        return evaluate(binds, self.body)


@dataclass(frozen=True)
class Binds:
    '''Lookups of value in nearest scope where symbol is bound'''


def is_symbol(value):
    return isinstance(value, Symbol)


def is_nil(value):
    return value is None

def builtins():
    return {
        '+': add,
        '-': sub,
        '*': mul,
        '/': truediv,
        'eq?': lambda a, b: a == b,
        'atom?': lambda a: is_symbol(a) or is_number(a) or is_nil(a),
        'cons': lambda a, b: [a] + b,
        'car': lambda a: a[0],
        'cdr': lambda a: a[1:],
        'nil': None,
    }.copy()


def evaluate(binds, expr):
    if is_number(expr):
        return expr
    if is_symbol(expr):
        return binds[expr.val]
    op, rest = expr[-1], expr[:-1]
    if op.val == 'define':  # ('pi' 3.14 define)
        symbol, subexpr = rest[0], rest[1]
        binds[symbol.val] = evaluate(binds, subexpr)
        return
    if op.val == 'quote':  # ((1 2) quote)
        return rest[0]
    # not done
    if op.val == 'if':  # (test then else if)
        test, then, else_ = rest
        subexpr = then if evaluate(binds, test) else else_
        return evaluate(binds, subexpr)
    # not tested
    if op.val == 'lambda':  # e.g., (name (params body lambda) define)
        params, body = rest
        return Lambda(binds, params, body)
    f = evaluate(binds, op)
    call = [evaluate(binds, subexpr) for subexpr in rest]
    return f(*call)


def tokenize(string):
    token = ''
    for c in string:
        if c == '(' or c == ')':
            if token:
                yield token
                token = ''
            yield c
        elif c == ' ':
            if token:
                yield token
                token = ''
        else:
            token += c
    if token:
        yield token


def symbolize(token):
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return Symbol(token)


class SignalEnd(Exception):
    '''Signal end of a expression'''


def parse_line(line: str) -> List:
    def _parse(tokens):
        for token in tokens:
            if token == '(':
                try:
                    frame = []
                    while True:
                        frame.append(_parse(tokens))
                except SignalEnd:
                    return frame
            elif token == ')':
                raise SignalEnd
            else:
                return symbolize(token)
        else:
            raise StopIteration
    tokens = iter(tokenize(line))
    exprs = []
    try:
        while True:
            exprs.append(_parse(tokens))
    except StopIteration:
        pass
    return exprs


def parse_all(input_):
    return (parse_line(line.strip()) for line in input_)


def eval_line(binds, iterable):
    result = []
    for expr in iterable:
        result.append(evaluate(binds, expr))
    return result


if __name__ == '__main__':
    binds = builtins()
    for exprs in parse_all(fileinput.input()):
        print(exprs)
        print(eval_line(binds, exprs))
    #sys.stdout.write(output)
