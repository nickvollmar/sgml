import functools
import os
import sys

import sgml.interpreter
import sgml.reader
import sgml.rt.error
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


def is_symbol(form):
    return isinstance(form, Symbol)


def integer(i):
    return i


def string(text):
    return text


def true():
    return True


def is_truthy(form):
    return form is not False


def is_true(form):
    return form is True


def first(form):
    return form[0]


def rest(form):
    return form[1]


def cons(head, tail):
    return (head, tail)


def is_atom(form):
    return not isinstance(form, tuple)


def eq(x, y):
    return x == y


def null():
    return False


def is_null(form):
    return form is False


def iter_elements(form):
    cur = form
    while not is_atom(cur):
        yield first(cur)
        cur = rest(cur)
    if not is_null(cur):
        yield cur


def second(form):
    return first(rest(form))


def third(form):
    return first(rest(rest(form)))


def fourth(form):
    return first(rest(rest(rest(form))))


def length(form):
    result = 0
    while not is_atom(form):
        result += 1
        form = rest(form)
    return result if is_null(form) else result + 1


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


def _print(args, env):
    strs = [as_string(arg) for arg in iter_elements(args)]
    print(*strs)


def is_primitive_function(fn):
    return isinstance(fn, PrimitiveFunction)


def apply_primitive_function(form: PrimitiveFunction, arguments, env):
    try:
        return form.f(arguments, env)
    except Exception as e:
        raise sgml.rt.error.RuntimeException(e)


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


def wrap(f: Operative):
    return Applicative(f)


def unwrap(a):
    if isinstance(a, Applicative):
        return a.combiner
    if isinstance(a, PrimitiveFunction):
        return a
    raise AssertionError("unwrap called on non-applicative {}".format(a))


PRIMITIVE_FUNCTIONS = {
    symbol(name): PrimitiveFunction(name, func)

    for (name, func) in [
        ("car", lambda arguments, env: first(first(arguments))),
        ("caar", lambda arguments, env: first(first(first(arguments)))),
        ("cdr", lambda arguments, env: rest(first(arguments))),
        ("cons", lambda arguments, env: cons(first(arguments), second(arguments))),
        ("atom", lambda arguments, env: is_atom(first(arguments))),
        ("eq", lambda arguments, env: eq(first(arguments), second(arguments))),
        ("null", lambda arguments, env: is_null(first(arguments))),
        ("list", lambda arguments, env: arguments),
        ("+", lambda arguments, env: functools.reduce(lambda x, y: x + y, iter_elements(arguments), 0)),
        ("-", lambda arguments, env: functools.reduce(lambda x, y: x - y, iter_elements(arguments))),
        ("*", lambda arguments, env: functools.reduce(lambda x, y: x * y, iter_elements(arguments), 1)),
        ("/", lambda arguments, env: functools.reduce(lambda x, y: x / y, iter_elements(arguments))),
        ("<", lambda arguments, env: first(arguments) < second(arguments)),
        ("print", _print),
        # TODO: is this how to do this?
        ("wrap", lambda arguments, env: wrap(first(arguments))),
        ("unwrap", lambda arguments, env: unwrap(first(arguments))),
        ("make-environment", lambda _, __: base_env()),
        ("get-current-environment", lambda _, env: env),
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


_cached_base_env = None


def base_env():
    global _cached_base_env
    if _cached_base_env is None:
        primitive = {
            symbol('t'): true(),
            symbol('nil'): null(),
        }
        primitive.update(SPECIAL_FORMS)
        primitive.update(PRIMITIVE_FUNCTIONS)
        env = Environment(env=primitive, parent=None)
        with open(os.path.join(os.path.dirname(__file__), "stdlib.sgml")) as f:
            stream = sgml.reader.streams.LineNumberingStream(sgml.reader.streams.FileStream(f))
            # https://stackoverflow.com/questions/1676835/how-to-get-a-reference-to-a-module-inside-the-module-itself/1676860#1676860
            module = sys.modules[__name__]
            forms = sgml.reader.read_many(module, sgml.reader.INITIAL_MACROS, stream)
            for form in iter_elements(forms):
                sgml.interpreter.evaluate(module, form, env)
        _cached_base_env = env
    return _cached_base_env.child_scope()


def debug(form) -> str:
    if is_true(form):
        return 't'
    if is_null(form):
        return 'nil'
    if is_symbol(form):
        return form.text
    if is_atom(form):
        return repr(form)
    return (
        '('
        + ' '.join(debug(f) for f in iter_elements(form))
        + ')'
    )


def debug_environment(e: Environment):
    for sym, val in e.env.items():
        print('{}: {}'.format(sym, debug(val)))
    if e.parent:
        debug_environment(e.parent)
