class Symbol:
    def __init__(self, text: str, ns=None):
        if ns is not None:
            self.ns = ns
            self.text = text
        elif "::" in text:
            parts = text.split("::", 2)
            self.ns = parts[0]
            self.text = parts[1]
        else:
            self.ns = None
            self.text = text

    def with_ns(self, ns: str):
        assert self.ns is None
        return Symbol(self.text, ns)

    def __hash__(self):
        return hash((self.ns, self.text))

    def __eq__(self, other):
        return isinstance(other, Symbol) and (self.ns, self.text) == (other.ns, other.text)

    def __str__(self):
        if self.ns:
            return self.ns + "/" + self.text
        return self.text

    def __repr__(self):
        if self.ns:
            return 'Symbol(ns={}, text={})'.format(repr(self.ns), repr(self.text))
        return 'Symbol({})'.format(repr(self.text))
