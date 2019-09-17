from sgml.rt.symbol import Symbol


class Environment:
    def __init__(self, env: dict, parent):
        self.env = env
        self.parent = parent

    def __str__(self):
        return "Environment(" + str(self.env) + ")"

    def child_scope(self):
        return Environment(env={}, parent=self)

    def get(self, rt, symbol):
        """
        a.k.a. `assoc` in the LISP 1.5 manual
        """
        if not isinstance(symbol, Symbol):
            rt.bail("internal error: lookup called on non-symbol {} ({})", symbol, type(symbol))
        if symbol in self.env:
            return self.env[symbol]
        if self.parent is not None:
            return self.parent.get(rt, symbol)
        rt.bail("Unbound variable: {}", symbol)

    def add(self, rt, symbol, form):
        if not isinstance(symbol, Symbol):
            rt.bail("internal error: add called with non-symbol {} ({})", symbol, type(symbol))
        if symbol.text == "_":
            return
        self.env[symbol] = form

    def add_match(self, rt, tree, obj):
        """
        Match the formal parameter tree to an object.
        See kernel.pdf p51.

        :param rt: Runtime instance
        :param tree: The formal parameter tree
        :param obj: The argument object
        """
        if rt.is_symbol(tree):
            self.add(rt, tree, obj)
            return
        if tree is rt.IGNORE:
            return
        if rt.is_null(tree):
            if not rt.is_null(obj):
                rt.bail("arity error")
            return
        # it's a pair
        self.add_match(rt, rt.first(tree), rt.first(obj))
        self.add_match(rt, rt.rest(tree), rt.rest(obj))
