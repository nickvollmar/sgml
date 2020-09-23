class Macros:
    def __init__(self, initial, dispatch):
        self.initial = initial
        self.dispatch = dispatch

    def is_terminating(self, ch):
        return ch in self.initial and ch != "'"
