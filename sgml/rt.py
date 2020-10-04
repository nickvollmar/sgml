import functools
import operator as op
import os
import sys
from contextlib import contextmanager

import sgml.interpreter
import sgml.reader
from sgml.symbol import Symbol
from sgml.environment import Namespace
from sgml.thunk import Applicative, Continuation, Operative, PrimitiveFunction


def forms_to_list(forms, dotted=False):
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


def as_string(value):
    if is_atom(value):
        if is_true(value):
            return 't'
        if is_null(value):
            return 'nil'
        if is_operative(value):
            return "<operative body=" + as_string(operative_body(value)) + ">"
        return str(value)

    result = '('
    result += as_string(first(value))
    cur = rest(value)
    while not is_atom(cur):
        result += ' ' + as_string(first(cur))
        cur = rest(cur)
    if not is_null(cur):
        result += ' . ' + as_string(cur)
    result += ')'
    return result


def is_primitive_function(value):
    return isinstance(value, PrimitiveFunction)


def apply_primitive_function(value: PrimitiveFunction, arguments, env):
    return value.f(arguments, env)


def operative(parameters, dynamic_env, body, static_env):
    return Operative(parameters, dynamic_env, body, static_env)


def is_operative(value):
    return isinstance(value, Operative)


def operative_parameters(f: Operative):
    return f.parameters


def operative_body(f: Operative):
    return f.body


def operative_dynamic_env_parameter(f: Operative):
    return f.dynamic_env_parameter


def operative_static_env(f: Operative):
    return f.static_env


def is_applicative(value):
    return isinstance(value, (Applicative, PrimitiveFunction, Continuation))


def is_continuation(value):
    return isinstance(value, Continuation)


def continuation(frame):
    return Continuation(frame)


def continuation_frame(continuation):
    return continuation.frame


def wrap(f):
    if is_operative(f):
        return Applicative(f)
    if is_applicative(f):
        return f
    raise AssertionError("wrap called on non-operative and non-applicative {}".format(as_string(f)))


def unwrap(a):
    if isinstance(a, Applicative):
        return a.combiner
    if is_applicative(a):
        return a
    raise AssertionError("unwrap called on non-applicative {}".format(as_string(a)))


def _print(args, env):
    strs = [as_string(arg) for arg in iter_elements(args)]
    print(*strs)


def _negative(args):
    return all(i < 0 for i in iter_elements(args))


PRIMITIVE_FUNCTIONS = {
    name: PrimitiveFunction(name, func)

    for (name, func) in [
        ("car", lambda arguments, env: first(first(arguments))),
        ("caar", lambda arguments, env: first(first(first(arguments)))),
        ("cdr", lambda arguments, env: rest(first(arguments))),
        ("cons", lambda arguments, env: cons(first(arguments), second(arguments))),
        ("atom", lambda arguments, env: is_atom(first(arguments))),
        ("eq", lambda arguments, env: eq(first(arguments), second(arguments))),
        ("null", lambda arguments, env: is_null(first(arguments))),
        ("list", lambda arguments, env: arguments),
        ("+", lambda arguments, env: functools.reduce(op.add, iter_elements(arguments), 0)),
        ("-", lambda arguments, env: functools.reduce(op.sub, iter_elements(arguments))),
        ("*", lambda arguments, env: functools.reduce(op.mul, iter_elements(arguments), 1)),
        ("/", lambda arguments, env: functools.reduce(op.truediv, iter_elements(arguments))),
        ("<", lambda arguments, env: first(arguments) < second(arguments)),
        (">", lambda arguments, env: first(arguments) > second(arguments)),
        ("print", _print),
        ("wrap", lambda arguments, env: wrap(first(arguments))),
        ("unwrap", lambda arguments, env: unwrap(first(arguments))),
        ("make-environment", lambda _, __: _cached_stdlib_ns().scope()),
        ("get-current-environment", lambda _, env: env),

        ("negative?", lambda arguments, env: _negative(arguments)),
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
FEXPR = SpecialForm("fexpr")
LABEL = SpecialForm("label")
DEFINE = SpecialForm("define")
LET = SpecialForm("let")  # TODO: define as fexpr when am more comfortable
IGNORE = SpecialForm("_")
CALL_CC = SpecialForm("call/cc")
SET = SpecialForm("set!")
QUASIQUOTE = SpecialForm("quasiquote")
NS = SpecialForm("ns")
REQUIRE = SpecialForm("require")
LOAD = SpecialForm("load")

SPECIAL_FORMS = {
    form.name: form
    for form in [
    QUOTE,
    COND,
    EVAL,
    FEXPR,
    LABEL,
    DEFINE,
    LET,
    IGNORE,
    CALL_CC,
    SET,
    QUASIQUOTE,
    NS,
    REQUIRE,
    LOAD,
]
}


_cached_primitives = None
def primitives():
    global _cached_primitives
    if _cached_primitives is None:
        primitives = {
            't': true(),
            'nil': null(),
        }
        primitives.update(SPECIAL_FORMS)
        primitives.update(PRIMITIVE_FUNCTIONS)
        _cached_primitives = primitives
    return _cached_primitives


_CURRENT_NS = None
_NS_BY_NAME = {}
_IMPORT_SEARCH_PATHS = [os.getcwd(), os.path.join(os.path.dirname(__file__), "lib")]


@contextmanager
def namespace_context(next_ns=None):
    global _CURRENT_NS
    _current_ns = _CURRENT_NS
    if next_ns is not None:
        _CURRENT_NS = next_ns
    try:
        yield
    finally:
        _CURRENT_NS = _current_ns


def _do_load_file(f):
    stream = sgml.reader.streams.LineNumberingStream(sgml.reader.streams.FileStream(f))
    # https://stackoverflow.com/questions/1676835/how-to-get-a-reference-to-a-module-inside-the-module-itself/1676860#1676860
    module = sys.modules[__name__]
    forms = sgml.reader.read_many(module, sgml.reader.INITIAL_MACROS, stream)
    for form in iter_elements(forms):
        sgml.interpreter.evaluate(module, form)


_cached_stdlib_env_dict = None
def stdlib_env():
    global _cached_stdlib_env_dict
    if _cached_stdlib_env_dict is None:
        with open(os.path.join(os.path.dirname(__file__), "lib", "core.sgml")) as f:
            _do_load_file(f)
        _cached_stdlib_env_dict = dict(current_ns().env)
    return _cached_stdlib_env_dict


def _create_ns(name: Symbol):
    new_ns = Namespace(name, stdlib_env())
    _NS_BY_NAME[name.text] = new_ns
    return new_ns


def current_ns():
    return _CURRENT_NS


def set_current_ns(name: Symbol):
    global _CURRENT_NS
    _CURRENT_NS = _NS_BY_NAME.get(name.text) or _create_ns(name)


def require_ns(name: Symbol):
    if name.text in _NS_BY_NAME:
        return _NS_BY_NAME[name.text]
    with namespace_context():
        new_ns = _create_ns(name)
        loaded = False
        for p in _IMPORT_SEARCH_PATHS:
            try:
                with open(os.path.join(p, name.text + ".sgml")) as f:
                    _do_load_file(f)
            except FileNotFoundError:
                continue
            loaded = True
            break
        assert loaded, "Unable to locate file for namespace {} (classpath {})".format(name.text, _IMPORT_SEARCH_PATHS)
    current_ns().add_import(new_ns)


def load_file(path: str):
    with open(path) as f:
        _do_load_file(f)


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


def init():
    global _CURRENT_NS
    bootstrap = Namespace(symbol("core"), primitives())
    _CURRENT_NS = bootstrap
    _NS_BY_NAME["core"] = bootstrap
    _CURRENT_NS = _create_ns(symbol("user"))
