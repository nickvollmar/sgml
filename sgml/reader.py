import re

import sgml.rt as rt

_DOTTED_LISTS_ = True
_ESCAPE_CHARS = {
    'n': '\n',
    'r': '\r',
    't': '\t',
    '\\': '\\',
    '"': '"',
}
_INT_PAT = re.compile("[0-9]+")


class StreamError(Exception):
    def __init__(self, message, line=None, column=None):
        self.line = line
        self.column = column
        self.message = message

    def __str__(self):
        return "line {}, column {}: {}".format(
            self.line,
            self.column,
            self.message
        )


class LineNumberingStream:
    def __init__(self, delegate):
        self.stream = delegate
        self._line_number = None
        self._column_number = None
        self._init = True
        self._at_line_end = False
        self._prev_column_number = None

    def __iter__(self):
        return self

    def __next__(self):
        ch = None
        stop_iteration = False
        try:
            ch = self.stream.__next__()
        except StopIteration:
            stop_iteration = True

        if self._init:
            self._init = False
            self._line_number = 1
            self._column_number = 1
        elif self._at_line_end:
            self._line_number += 1
            self._column_number = 1
        else:
            self._column_number += 1

        self._prev_column_number = self._column_number
        self._at_line_end = ch == '\n'

        if stop_iteration:
            raise StopIteration
        return ch

    def at_eof(self):
        return self.stream.at_eof()

    def ungetc(self, ch):
        self.stream.ungetc(ch)
        if self._column_number == 1:
            self._column_number = self._prev_column_number
            self._line_number -= 1
            self._at_line_end = True
        else:
            self._column_number -= 1
            self._at_line_end = False

    def remainder(self):
        return self.stream.remainder()

    def error(self, message):
        error = self.stream.error(message)
        error.line = self._line_number
        error.column = self._column_number
        return error


class FileStream:
    def __init__(self, f):
        self.f = f
        self._at_eof = False
        self._ungetc_buf = ''

    def __iter__(self):
        return self

    def __next__(self):
        if len(self._ungetc_buf) > 0:
            result = self._ungetc_buf
            self._ungetc_buf = ''
            return result

        result = self.f.read(1)
        if result == '':
            self._at_eof = True
            raise StopIteration
        return result

    def at_eof(self):
        return len(self._ungetc_buf) == 0 and self._at_eof

    def ungetc(self, ch):
        self._ungetc_buf = ch + self._ungetc_buf

    def remainder(self):
        return self._ungetc_buf + self.f.read()

    def error(self, message):
        return StreamError(message)


class StringStream:
    def __init__(self, text):
        self.text = text
        self.position = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.position >= len(self.text):
            raise StopIteration
        result = self.text[self.position]
        self.position += 1
        return result

    def at_eof(self):
        return self.position >= len(self.text)

    def ungetc(self, ch):
        self.position -= 1

    def remainder(self):
        return self.text[self.position:len(self.text)]

    def error(self, message):
        return StreamError(message)


def _is_whitespace(ch):
    return ch == ' ' or ch == '\n' or ch == '\t'


def _is_constituent(macros, ch):
    if _is_whitespace(ch) or ch in macros.initial:
        return False
    # todo: probably more cases
    return True


def _read_token(macros, stream, ch):
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


def read(macros, stream):
    for ch in stream:
        if _is_whitespace(ch):
            continue
        if ch in macros.initial:
            f = macros.initial[ch]
            return f(macros, stream, ch)
        return _read_token(macros, stream, ch)


def _read_list(macros, stream, ch):
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
        next_form = read(macros, stream)
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


def _read_line_comment(macros, stream, ch):
    assert ch == ';'
    for ch in stream:
        if ch != '\n':
            continue
    return None


def _read_dispatch(macros, stream, ch):
    assert ch == '#'
    for ch in stream:
        if ch not in macros.dispatch:
            raise stream.error("Illegal dispatch character {}".format(ch))
        f = macros.dispatch[ch]
        return f(macros, stream, ch)


def _ignore(macros, stream, ch):
    assert ch == "_"
    read(macros, stream)
    return None


def _read_string(macros, stream, ch):
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


def _unmatched_delimiter(macros, stream, ch):
    raise stream.error("Unmatched delimiter: '{}'".format(ch))


def read_one(macros, stream):
    result = read(macros, stream)
    for ch in stream:
        if not _is_whitespace(ch):
            stream.ungetc(ch)
            raise stream.error(
                "Unconsumed input: \"{}\"".format(stream.remainder())
            )
    return result


def read_many(macros, stream):
    forms = []
    while not stream.at_eof():
        form = read(macros, stream)
        if form is not None:
            forms.append(form)
    return rt._forms_to_list(forms)


class Macros:
    def __init__(self, initial, dispatch):
        self.initial = initial
        self.dispatch = dispatch

    def is_terminating(self, ch):
        return ch in self.initial and ch != '"'


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
