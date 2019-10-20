class Environment:
    def __init__(self, env: dict, parent):
        self.env = env
        self.parent = parent

    def child_scope(self):
        return Environment(env={}, parent=self)

    def get(self, rt, symbol):
        """
        a.k.a. `assoc` in the LISP 1.5 manual
        """
        if not rt.is_symbol(symbol):
            raise TypeError("get called with non-symbol {} ({})".format(symbol, type(symbol)))
        if symbol in self.env:
            return self.env[symbol]
        if self.parent is not None:
            return self.parent.get(rt, symbol)
        raise KeyError(symbol)

    def add(self, rt, symbol, form):
        if not rt.is_symbol(symbol):
            raise TypeError("add called with non-symbol {} ({})".format(symbol, type(symbol)))
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
        if rt.is_null(tree) and rt.is_null(obj):
            return
        if rt.is_null(tree) or rt.is_null(obj):
            raise ValueError("arity error")
        # it's a pair
        self.add_match(rt, rt.first(tree), rt.first(obj))
        self.add_match(rt, rt.rest(tree), rt.rest(obj))
