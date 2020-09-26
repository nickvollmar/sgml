import re
from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import List

from sgml.reader.macros import Macros
from sgml.reader.streams import Stream

_ESCAPE_CHARS = {
    'n': '\n',
    'r': '\r',
    't': '\t',
    '\\': '\\',
    '"': '"',
}
_INT_PAT = re.compile("[0-9]+")

@dataclass
class ReaderState:
    rt: object
    macros: Macros
    stream: Stream
    dotted_lists: bool = True


def _is_whitespace(ch):
    return ch == ' ' or ch == '\n' or ch == '\t'


def _is_constituent(macros, ch):
    if _is_whitespace(ch) or macros.is_terminating(ch):
        return False
    # todo: probably more cases
    return True

def _read_token(state, ch):
    result = ch
    for ch in state.stream:
        if _is_whitespace(ch) or state.macros.is_terminating(ch):
            state.stream.ungetc(ch)
            break
        elif _is_constituent(state.macros, ch):
            result += ch
        else:
            raise state.stream.error("Nonconstituent character '{}'".format(ch))
    if result == "*t*":
        return state.rt.true()
    if result == "nil":
        return state.rt.null()
    if _INT_PAT.match(result):
        return state.rt.integer(int(result, 10))
    return state.rt.symbol(result)


def _read(state):
    for ch in state.stream:
        if _is_whitespace(ch):
            continue
        if ch in state.macros.initial:
            f = state.macros.initial[ch]
            return f(state, ch)
        return _read_token(state, ch)


def _read_list(state, ch):
    assert ch == '('
    forms = []
    dotted = False
    seen_improper_cdr = False
    for ch in state.stream:
        if _is_whitespace(ch):
            continue
        if ch == ')':
            if state.dotted_lists:
                return state.rt.forms_to_list(forms, dotted)
            return tuple(forms)

        if dotted and seen_improper_cdr:
            raise state.stream.error("Expected one cdr in dotted s-expression")
        state.stream.ungetc(ch)
        next_form = _read(state)
        if next_form is None:
            continue
        if next_form == state.rt.symbol('.'):
            if not state.dotted_lists:
                raise state.stream.error("Dotted s-expressions are disabled")
            if dotted:
                raise state.stream.error("Expected one '.' in dotted s-expression")
            dotted = True
        else:
            forms.append(next_form)
            if state.dotted_lists and dotted:
                seen_improper_cdr = True
    raise state.stream.error("EOF while reading list")


def _read_line_comment(state, ch):
    assert ch == ';'
    for ch in state.stream:
        if ch == '\n':
            break
    return None


def _read_quote(state, ch):
    assert ch == "'"
    form = _read(state)
    return state.rt.cons(state.rt.symbol("quote"), state.rt.cons(form, state.rt.null()))


def _read_backquote(state, ch):
    assert ch == "`"
    form = _read(state)
    return state.rt.cons(state.rt.symbol("quasiquote"), state.rt.cons(form, state.rt.null()))


def _read_unquote(state, ch):
    """
    This won't work until the relevant macros are implemented.
    https://stackoverflow.com/a/18515345
    """
    assert ch == ","
    peek = state.stream.getc()
    if peek == "@":
        form = _read(state)
        return state.rt.cons(state.rt.symbol("unquote-splicing"), state.rt.cons(form, state.rt.null()))
    state.stream.ungetc(peek)
    form = _read(state)
    return state.rt.cons(state.rt.symbol("unquote"), state.rt.cons(form, state.rt.null()))


def _read_dispatch(state, ch):
    assert ch == '#'
    for ch in state.stream:
        if ch not in state.macros.dispatch:
            raise state.stream.error("Illegal dispatch character {}".format(ch))
        f = state.macros.dispatch[ch]
        return f(state, ch)


def _ignore(state, ch):
    assert ch == "_"
    _read(state)
    return None


def _read_string(state, ch):
    assert ch == '"'
    text = ""
    escaped = False
    for ch in state.stream:
        if escaped:
            if ch in _ESCAPE_CHARS:
                text += _ESCAPE_CHARS[ch]
                escaped = False
            else:
                raise state.stream.error("Illegal escape character: '{}'".format(ch))
        elif ch == '\\':
            escaped = True
        elif ch == '"':
            return state.rt.string(text)
        else:
            text += ch
    raise state.stream.error("EOF while reading string literal")


def _unmatched_delimiter(state, ch):
    raise state.stream.error("Unmatched delimiter: '{}'".format(ch))


def read_one(rt, macros, stream):
    state = ReaderState(rt, macros, stream)
    result = _read(state)
    for ch in state.stream:
        if not _is_whitespace(ch):
            state.stream.ungetc(ch)
            raise state.stream.error(
                "Unconsumed input: \"{}\"".format(state.stream.remainder())
            )
    return result


def read_many(rt, macros, stream):
    state = ReaderState(rt, macros, stream)
    forms = []
    while not state.stream.at_eof():
        form = _read(state)
        if form is not None:
            forms.append(form)
    return state.rt.forms_to_list(forms)


INITIAL_MACROS = Macros(
    {
        '(': _read_list,
        ')': _unmatched_delimiter,
        '"': _read_string,
        ';': _read_line_comment,
        "'": _read_quote,
        '#': _read_dispatch,
        "`": _read_backquote,
        ",": _read_unquote,
    },
    {
        '_': _ignore,
    },
)
