import functools

from sgml.rt.symbol import Symbol
from sgml.rt.environment import Environment
from sgml.rt.error import bail
from sgml.rt.thunk import Applicative, Operative, SpecialFunction


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


def fourth(lst):
    return first(rest(rest(rest(lst))))


def length(lst):
    result = 0
    while not is_atom(lst):
        result += 1
        lst = rest(lst)
    return result + (0 if is_null(lst) else 1)


def as_string(form):
    if is_atom(form):
        if is_true(form):
            return 't'
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
    symbol(name): SpecialFunction(name, func)

    for (name, func) in [
        ("car", lambda arguments: first(first(arguments))),
        ("cdr", lambda arguments: rest(first(arguments))),
        ("cons", lambda arguments: cons(first(arguments), second(arguments))),
        ("atom", lambda arguments: is_atom(first(arguments))),
        ("eq", lambda arguments: eq(first(arguments), second(arguments))),
        ("null", lambda arguments: is_null(first(arguments))),
        ("+", lambda arguments: functools.reduce(lambda x, y: x + y, iter_elements(arguments), 0)),
        ("-", lambda arguments: functools.reduce(lambda x, y: x - y, iter_elements(arguments))),
        ("*", lambda arguments: functools.reduce(lambda x, y: x * y, iter_elements(arguments), 1)),
        ("/", lambda arguments: functools.reduce(lambda x, y: x / y, iter_elements(arguments))),
        ("print", _print),
    ]
}


def is_special_function(fn):
    return isinstance(fn, SpecialFunction)


def apply_special_function(form: SpecialFunction, arguments):
    return form.f(arguments)


def base_env():
    env = {
        symbol('t'): true(),
        symbol('nil'): null()
    }
    env.update(SPECIAL_FUNCTIONS)
    return Environment(env=env, parent=None)


def operative(parameters, dynamic_env, body, static_env):
    return Operative(parameters, dynamic_env, body, static_env)


def is_operative(form):
    return isinstance(form, Operative)


def operative_parameters(f):
    return f.parameters


def operative_body(f):
    return f.body


def operative_dynamic_env_parameter(f):
    return f.dynamic_env_parameter


def operative_static_env(f):
    return f.static_env


def is_applicative(code):
    return isinstance(code, (Applicative, SpecialFunction))


def applicative_underlying_combiner(applicative):
    if isinstance(applicative, Applicative):
        return applicative.combiner
    if isinstance(applicative, SpecialFunction):
        return applicative
    raise AssertionError("applicative_underlying_combiner called on non-applicative {}".format(applicative))
