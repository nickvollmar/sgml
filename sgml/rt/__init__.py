import functools

from sgml.rt.symbol import Symbol
from sgml.rt.environment import Environment
from sgml.rt.error import bail
from sgml.rt.thunk import Function


def _forms_to_list(forms, dotted=False):
    result = forms.pop() if dotted else null()
    for head in reversed(forms):
        result = cons(head, result)
    return result


def symbol(text):
    return Symbol(text)


def is_symbol(text):
    return isinstance(text, Symbol)


def integer(i):
    return i


def string(text):
    return text


def true():
    return True


def is_truthy(x):
    return x is not False


def is_true(x):
    return x is True


def first(lst):
    return lst[0]


def rest(lst):
    return lst[1]


def cons(head, tail):
    return (head, tail)


def is_atom(x):
    return not isinstance(x, tuple)


def eq(x, y):
    return x == y


def null():
    return False


def is_null(x):
    return x is False


def iter_elements(lst):
    cur = lst
    while not is_atom(cur):
        yield first(cur)
        cur = rest(cur)
    if not is_null(cur):
        yield cur


def second(lst):
    return first(rest(lst))


def third(lst):
    return first(rest(rest(lst)))



def as_string(form):
    if is_atom(form):
        if is_true(form):
            return '*t*'
        if is_null(form):
            return 'nil'
        return str(form)

    result = '('
    result += as_string(first(form))
    cur = rest(form)
    while not is_atom(cur):
        result += ' ' + as_string(first(cur))
        cur = rest(cur)
    if not is_null(cur):
        result += ' . ' + as_string(cur)
    result += ')'
    return result


def _print(args):
    strs = [as_string(arg) for arg in iter_elements(args)]
    print(*strs)


SPECIAL_FUNCTIONS = {
    symbol("car"): lambda arguments: first(first(arguments)),
    symbol("cdr"): lambda arguments: rest(first(arguments)),
    symbol("cons"): lambda arguments: cons(first(arguments), second(arguments)),
    symbol("atom"): lambda arguments: is_atom(first(arguments)),
    symbol("eq"): lambda arguments: eq(first(arguments), second(arguments)),
    symbol("null"): lambda arguments: is_null(first(arguments)),

    symbol("+"): lambda arguments: functools.reduce(lambda x, y: x + y, iter_elements(arguments), 0),
    symbol("-"): lambda arguments: functools.reduce(lambda x, y: x - y, iter_elements(arguments)),
    symbol("*"): lambda arguments: functools.reduce(lambda x, y: x * y, iter_elements(arguments), 1),
    symbol("/"): lambda arguments: functools.reduce(lambda x, y: x / y, iter_elements(arguments)),

    symbol("print"): _print
}


def is_special_function(fn):
    return fn in SPECIAL_FUNCTIONS


def apply_special_function(form, arguments):
    if not is_special_function(form):
        bail("not a special function: {}", form)
    return SPECIAL_FUNCTIONS[form](arguments)


def base_env():
    return Environment(env={symbol('t'): true()}, parent=None)


def function(parameters, body, static_env):
    return Function(parameters, body, static_env)


def is_function(form):
    return isinstance(form, Function)


def function_parameters(f):
    return f.parameters


def function_body(f):
    return f.body


def function_static_env(f):
    return f.static_env
