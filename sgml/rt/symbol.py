class Symbol:
    def __init__(self, text: str):
        self.text = text

    def __hash__(self):
        return hash(self.text)

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.text == other.text

    def __str__(self):
        return self.text

    def __repr__(self):
        return 'Symbol({})'.format(repr(self.text))
