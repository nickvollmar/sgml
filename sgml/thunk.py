class Applicative:
    def __init__(self, combiner):
        self.combiner = combiner


class Operative:
    def __init__(self, parameters, dynamic_env_parameter, body, static_env):
        self.parameters = parameters
        self.dynamic_env_parameter = dynamic_env_parameter
        self.body = body
        self.static_env = static_env


class PrimitiveFunction:
    def __init__(self, name, f):
        self.name = name
        self.f = f

    def __str__(self):
        return "<primitive function '{}'>".format(self.name)
