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

    def set(self, rt, symbol, form):
        if not rt.is_symbol(symbol):
            raise TypeError("set called with non-symbol {} ({})".format(symbol, type(symbol)))
        if symbol.text == "_":
            return

        if symbol in self.env:
            self.env[symbol] = form
        elif self.parent is not None:
            self.parent.set(rt, symbol, form)
        else:
            raise AttributeError("set called with undefined symbol {}".format(symbol))

    def add_match(self, rt, tree, obj):
        traverse_symbol_tree(rt, tree, obj, self.add)

    def set_match(self, rt, tree, obj):
        traverse_symbol_tree(rt, tree, obj, self.set)

def traverse_symbol_tree(rt, tree, obj, f):
    """
    Match the formal parameter tree to an object.
    At every leaf of the tree (i.e. atomic symbol)
    invoke f.
    See kernel.pdf p51.

    :param rt: Runtime instance
    :param tree: The formal parameter tree
    :param obj: The argument object
    :param f: func(rt, symbol, value) void
    """
    if rt.is_symbol(tree):
        f(rt, tree, obj)
        return
    if tree is rt.IGNORE:
        return
    if rt.is_null(tree) and rt.is_null(obj):
        return
    if rt.is_null(tree) or rt.is_null(obj):
        raise ValueError("tree: {}, obj: {}".format(rt.as_string(tree), rt.as_string(obj)))
    # it's a pair
    traverse_symbol_tree(rt, rt.first(tree), rt.first(obj), f)
    traverse_symbol_tree(rt, rt.rest(tree), rt.rest(obj), f)
