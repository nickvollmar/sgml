from abc import ABC, abstractmethod


class Stream(ABC):
    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def at_eof(self) -> bool:
        raise NotImplementedError()

    def getc(self):
        try:
            return next(self)
        except StopIteration:
            raise self.error("Empty stream")

    @abstractmethod
    def ungetc(self, ch):
        raise NotImplementedError()

    @abstractmethod
    def remainder(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def error(self, message) -> Exception:
        raise NotImplementedError()


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


class LineNumberingStream(Stream):
    def __init__(self, delegate):
        self.stream = delegate
        self._line_number = None
        self._column_number = None
        self._init = True
        self._at_line_end = False
        self._prev_column_number = None

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


class FileStream(Stream):
    def __init__(self, f):
        self.f = f
        self._at_eof = False
        self._ungetc_buf = ''

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


class StringStream(Stream):
    def __init__(self, text):
        self.text = text
        self.position = 0

    def __repr__(self):
        return "StringStream(text={}, position={})".format(
            repr(self.text),
            repr(self.position)
        )

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
