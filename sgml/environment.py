class Namespace:
    def __init__(self, name, symbols=None):
        self.name = name
        self.env = {} if symbols is None else symbols
        self.imports = {}

    def add_import(self, other, alias=None):
        self.imports[alias or other.name] = other

    def define(self, symbol, value):
        assert symbol.ns is None, "Can't define namespaced symbol {}".format(symbol)
        self.env[symbol.text] = value

    def get(self, symbol):
        if symbol.ns:
            assert symbol.ns in self.imports, "Undefined namespace {}".format(symbol.ns)
            return self.imports[symbol.ns].get(symbol)
        if symbol.text not in self.env:
            print(self.env)
        assert symbol.text in self.env, "Undefined symbol {}".format(symbol)
        return self.env[symbol.text]

    def set(self, symbol, value):
        assert symbol.ns is None, "Can't define namespaced symbol {}".format(symbol)
        # assert symbol.text in self.env, "Undefined symbol {}".format(symbol)
        self.env[symbol.text] = value

    def scope(self):
        return Scope(env={}, parent=None, ns=self)

class Scope:
    def __init__(self, env: dict, parent, ns):
        self.env = env
        self.parent = parent
        self.ns = ns

    def child_scope(self):
        return Scope(env={}, parent=self, ns=self.ns)

    def get(self, rt, symbol):
        """
        a.k.a. `assoc` in the LISP 1.5 manual
        """
        if not rt.is_symbol(symbol):
            raise TypeError("get called with non-symbol {} ({})".format(symbol, type(symbol)))
        if symbol.text in self.env:
            return self.env[symbol.text]
        if self.parent is not None:
            return self.parent.get(rt, symbol)
        return self.ns.get(symbol)

    def ns_define(self, rt, symbol, form):
        if not rt.is_symbol(symbol):
            raise TypeError("define called with non-symbol {} ({})".format(symbol, type(symbol)))
        self.ns.define(symbol, form)

    def ns_set(self, rt, symbol, form):
        if not rt.is_symbol(symbol):
            raise TypeError("set called with non-symbol {} ({})".format(symbol, type(symbol)))
        self.ns.set(symbol, form)

    def add(self, rt, symbol, form):
        if not rt.is_symbol(symbol):
            raise TypeError("add called with non-symbol {} ({})".format(symbol, type(symbol)))
        if symbol.text == "_":
            return
        self.env[symbol.text] = form

    def set(self, rt, symbol, form):
        if not rt.is_symbol(symbol):
            raise TypeError("set called with non-symbol {} ({})".format(symbol, type(symbol)))
        if symbol.text == "_":
            return

        if symbol in self.env:
            self.env[symbol.text] = form
        elif self.parent is not None:
            self.parent.set(rt, symbol, form)
        else:
            raise AttributeError("set called with undefined symbol {}".format(symbol))

    def add_match(self, rt, tree, obj):
        traverse_symbol_tree(rt, tree, obj, self.add)

    def set_match(self, rt, tree, obj):
        traverse_symbol_tree(rt, tree, obj, self.set)

    def ns_define_match(self, rt, tree, obj):
        traverse_symbol_tree(rt, tree, obj, self.ns_define)

    def ns_set_match(self, rt, tree, obj):
        traverse_symbol_tree(rt, tree, obj, self.ns_set)

def traverse_symbol_tree(rt, tree, obj, f):
    """
    Match the formal parameter tree to an object.
    At every leaf of the tree (i.e. symbol) invoke f.
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
