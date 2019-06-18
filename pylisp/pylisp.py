#!/usr/bin/env python
'''
We want you to make this a postfix Lisp instead of a traditional prefix Lisp.
Write a basic postfix Lisp interpreter that implements a subset of the Lisp
special forms. (here’s a good basic description of a basic Lisp)

http://pythonpracticeprojects.com/lisp.html


to do:
    [x] repl
    [x] lambda
    [x] if
    [x] lambda recurse (e.g., fib)
    [x] scope
    [x] improve repl
    [x] handling multi file inputs
    [ ] add signatures
    [ ] support for multi line inputs in repl

'''
import click
from dataclasses import dataclass
from numbers import Number
import operator as op
from typing import Any, Callable, Dict, List
import fileinput
import sys


PROMPT = 'pyl> '


@dataclass(frozen=True)
class Symbol:
    val: str


@dataclass(frozen=True)
class Lambda:
    binds: Dict[str, Callable]
    params: List
    body: Any

    def __call__(self, *args):
        binds = self.binds.copy()  # avoid copy
        binds.update({param.val: arg for param, arg in zip(self.params, args)})
        return eval_expr(binds, self.body)


class SignalEnd(Exception):
    '''Signal end of a expression'''


def is_number(value):
    return isinstance(value, Number)


def is_symbol(value):
    return isinstance(value, Symbol)


def is_nil(value: Any):
    return value is None


def builtins():
    return {
        '+': op.add,
        '-': op.sub,
        '*': op.mul,
        '/': op.truediv,
        '//': op.floordiv,
        '>': op.gt,
        '<': op.lt,
        '>=': op.ge,
        '<=': op.le,
        'eq?': lambda a, b: a == b,
        'atom?': lambda a: is_symbol(a) or is_number(a) or is_nil(a),
        'cons': lambda a, b: [a] + b,
        'car': lambda a: a[0],
        'cdr': lambda a: a[1:],
        'nil': None,
    }.copy()


def eval_expr(binds, expr):
    if is_number(expr):
        return expr
    if is_symbol(expr):
        return binds[expr.val]
    op, rest = expr[-1], expr[:-1]
    if op.val == 'define':  # ('pi' 3.14 define)
        symbol, subexpr = rest[0], rest[1]
        binds[symbol.val] = eval_expr(binds, subexpr)
        return
    if op.val == 'quote':  # ((1 2) quote)
        return rest[0]
    if op.val == 'if':  # (test then else if)
        test, then, else_ = rest
        subexpr = then if eval_expr(binds, test) else else_
        return eval_expr(binds, subexpr)
    if op.val == 'lambda':  # e.g., (name (params body lambda) define)
        try:
            params, body = rest
        except ValueError:
            body = rest
            params = []
        return Lambda(binds, params, body)
    f = eval_expr(binds, op)
    call = [eval_expr(binds, subexpr) for subexpr in rest]
    return f(*call)


def tokenize(string):
    token = ''
    for c in string:
        if c == '(' or c == ')':
            if token:
                yield token
                token = ''
            yield c
        elif c.isspace():
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


def eval_line(binds, iterable):
    result = []
    for expr in iterable:
        result.append(eval_expr(binds, expr))
    return result


def run_from_input(files):
    binds = builtins()
    if files:
        for file in files:
            with open(file) as fh:
                click.secho(file, fg='yellow')
                exprs = parse_line(''.join(fh.readlines()))
                click.echo(eval_line(binds, exprs))
        return
    lines = ''.join(fileinput.input())
    exprs = parse_line(lines)
    click.echo(eval_line(binds, exprs))


def run_interactive():
    binds = builtins()
    while True:
        line = input(PROMPT)
        try:
            print(eval_line(binds, parse_line(line)))
        except KeyError as e:
            print(f'Unbound: {e}')
        except SignalEnd as e:
            print('Unmatched )')
        except AttributeError as e:
            print('Non symbol in final position')
        except Exception as e:
            print(e)


@click.command()
@click.argument('files', nargs=-1)
@click.option('--interactive/--no-interactive', '-i', default=False)
def run(files: List, interactive):
    if interactive:
        run_interactive()
    else:
        run_from_input(files)


if __name__ == '__main__':
    run()
