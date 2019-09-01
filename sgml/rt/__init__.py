import functools

from sgml.rt.symbol import Symbol
from sgml.rt.environment import Environment
from sgml.rt.error import bail
from sgml.rt.thunk import Applicative, Operative, PrimitiveFunction


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

def is_primitive_function(fn):
    return isinstance(fn, PrimitiveFunction)


def apply_primitive_function(form: PrimitiveFunction, arguments):
    return form.f(arguments)


def operative(parameters, dynamic_env, body, static_env):
    return Operative(parameters, dynamic_env, body, static_env)


def is_operative(form):
    return isinstance(form, Operative)


def operative_parameters(f: Operative):
    return f.parameters


def operative_body(f: Operative):
    return f.body


def operative_dynamic_env_parameter(f: Operative):
    return f.dynamic_env_parameter


def operative_static_env(f: Operative):
    return f.static_env

def is_applicative(code):
    return isinstance(code, (Applicative, PrimitiveFunction))

def wrap(operative):
    return Applicative(operative)

def unwrap(applicative):
    if isinstance(applicative, Applicative):
        return applicative.combiner
    if isinstance(applicative, PrimitiveFunction):
        return applicative
    raise AssertionError("unwrap called on non-applicative {}".format(applicative))

PRIMITIVE_FUNCTIONS = {
    symbol(name): PrimitiveFunction(name, func)

    for (name, func) in [
        ("car", lambda arguments: first(first(arguments))),
        ("cdr", lambda arguments: rest(first(arguments))),
        ("cons", lambda arguments: cons(first(arguments), second(arguments))),
        ("atom", lambda arguments: is_atom(first(arguments))),
        ("eq", lambda arguments: eq(first(arguments), second(arguments))),
        ("null", lambda arguments: is_null(first(arguments))),
        ("list", lambda arguments: arguments),
        ("+", lambda arguments: functools.reduce(lambda x, y: x + y, iter_elements(arguments), 0)),
        ("-", lambda arguments: functools.reduce(lambda x, y: x - y, iter_elements(arguments))),
        ("*", lambda arguments: functools.reduce(lambda x, y: x * y, iter_elements(arguments), 1)),
        ("/", lambda arguments: functools.reduce(lambda x, y: x / y, iter_elements(arguments))),
        ("print", _print),
        ("wrap", lambda arguments: wrap(first(arguments))),
        ("unwrap", lambda arguments: unwrap(first(arguments))),
    ]
}

class SpecialForm:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "SpecialForm({})".format(self.name)

QUOTE = SpecialForm("quote")
COND = SpecialForm("cond")
EVAL = SpecialForm("eval")
MACRO = SpecialForm("macro")
LABEL = SpecialForm("label")
DEFINE = SpecialForm("define")
LET = SpecialForm("let")  # TODO: define as macro when am more comfortable
IGNORE = SpecialForm("_")

SPECIAL_FORMS = {
    symbol(form.name): form
    for form in [
        QUOTE,
        COND,
        EVAL,
        MACRO,
        LABEL,
        DEFINE,
        LET,
        IGNORE,
    ]
}

def base_env():
    env = {
        symbol('t'): true(),
        symbol('nil'): null()
    }
    env.update(SPECIAL_FORMS)
    env.update(PRIMITIVE_FUNCTIONS)
    return Environment(env=env, parent=None)

