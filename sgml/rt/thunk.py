class Function:
    def __init__(self, parameters, body, static_env):
        self.parameters = parameters
        self.body = body
        self.static_env = static_env

    def __repr__(self):
        return "Function(parameters={}, body={}, static_env={})".format(
            "(params)",  # self.parameters,
            "(body)",  # self.body,
            self.static_env
        )


