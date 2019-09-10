from sgml.rt.symbol import Symbol
from sgml.rt.error import bail


class Environment:
    def __init__(self, env: dict, parent):
        self.env = env
        self.parent = parent

    def __str__(self):
        return "Environment(" + str(self.env) + ")"

    def child_scope(self):
        return Environment(env={}, parent=self)

    def get(self, symbol):
        """
        a.k.a. `assoc` in the LISP 1.5 manual
        """
        if not isinstance(symbol, Symbol):
            bail("internal error: lookup called on non-symbol {} ({})", symbol, type(symbol))
        if symbol in self.env:
            return self.env[symbol]
        if self.parent is not None:
            return self.parent.get(symbol)
        bail("Unbound variable: {}", symbol)

    def add(self, symbol, form):
        if not isinstance(symbol, Symbol):
            bail("internal error: add called with non-symbol {} ({})", symbol, type(symbol))
        if symbol.text == "_":
            return
        self.env[symbol] = form
