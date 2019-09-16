import re

from sgml.reader.macros import Macros
from sgml.reader.streams import Stream

_DOTTED_LISTS_ = True
_ESCAPE_CHARS = {
    'n': '\n',
    'r': '\r',
    't': '\t',
    '\\': '\\',
    '"': '"',
}
_INT_PAT = re.compile("[0-9]+")


def _is_whitespace(ch):
    return ch == ' ' or ch == '\n' or ch == '\t'


def _is_constituent(macros, ch):
    if _is_whitespace(ch) or ch in macros.initial:
        return False
    # todo: probably more cases
    return True


def _read_token(rt, macros, stream, ch):
    result = ch
    for ch in stream:
        if _is_whitespace(ch) or macros.is_terminating(ch):
            stream.ungetc(ch)
            break
        elif _is_constituent(macros, ch):
            result += ch
        else:
            raise stream.error("Nonconstituent character '{}'".format(ch))
    if result == "*t*":
        return rt.true()
    if result == "nil":
        return rt.null()
    if _INT_PAT.match(result):
        return rt.integer(int(result, 10))
    return rt.symbol(result)


def _read(rt, macros, stream):
    for ch in stream:
        if _is_whitespace(ch):
            continue
        if ch in macros.initial:
            f = macros.initial[ch]
            return f(rt, macros, stream, ch)
        return _read_token(rt, macros, stream, ch)


def _read_list(rt, macros, stream, ch):
    assert ch == '('
    forms = []
    dotted = False
    seen_improper_cdr = False
    for ch in stream:
        if _is_whitespace(ch):
            continue
        if ch == ')':
            if _DOTTED_LISTS_:
                return rt._forms_to_list(forms, dotted)
            return tuple(forms)

        if dotted and seen_improper_cdr:
            raise stream.error("Expected one cdr in dotted s-expression")
        stream.ungetc(ch)
        next_form = _read(rt, macros, stream)
        if next_form is None:
            continue
        if next_form == rt.symbol('.'):
            if not _DOTTED_LISTS_:
                raise stream.error("Dotted s-expressions are disabled")
            if dotted:
                raise stream.error("Expected one '.' in dotted s-expression")
            dotted = True
        else:
            forms.append(next_form)
            if _DOTTED_LISTS_ and dotted:
                seen_improper_cdr = True
    raise stream.error("EOF while reading list")


def _read_line_comment(rt, macros, stream, ch):
    assert ch == ';'
    for ch in stream:
        if ch == '\n':
            break
    return None


def _read_dispatch(rt, macros, stream, ch):
    assert ch == '#'
    for ch in stream:
        if ch not in macros.dispatch:
            raise stream.error("Illegal dispatch character {}".format(ch))
        f = macros.dispatch[ch]
        return f(rt, macros, stream, ch)


def _ignore(rt, macros, stream, ch):
    assert ch == "_"
    _read(rt, macros, stream)
    return None


def _read_string(rt, macros, stream, ch):
    assert ch == '"'
    text = ""
    escaped = False
    for ch in stream:
        if escaped:
            if ch in _ESCAPE_CHARS:
                text += _ESCAPE_CHARS[ch]
                escaped = False
            else:
                raise stream.error("Illegal escape character: '{}'".format(ch))
        elif ch == '\\':
            escaped = True
        elif ch == '"':
            return rt.string(text)
        else:
            text += ch
    raise stream.error("EOF while reading string literal")


def _unmatched_delimiter(rt, macros, stream, ch):
    raise stream.error("Unmatched delimiter: '{}'".format(ch))


def read_one(rt, macros, stream):
    result = _read(rt, macros, stream)
    for ch in stream:
        if not _is_whitespace(ch):
            stream.ungetc(ch)
            raise stream.error(
                "Unconsumed input: \"{}\"".format(stream.remainder())
            )
    return result


def read_many(rt, macros: Macros, stream: Stream):
    forms = []
    while not stream.at_eof():
        form = _read(rt, macros, stream)
        if form is not None:
            forms.append(form)
    return rt._forms_to_list(forms)


INITIAL_MACROS = Macros(
    {
        '(': _read_list,
        ')': _unmatched_delimiter,
        '"': _read_string,
        '#': _read_dispatch,
        ';': _read_line_comment,
    },
    {
        '_': _ignore,
    },
)
