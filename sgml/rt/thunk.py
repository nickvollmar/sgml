class Applicative:
    def __init__(self, combiner):
        self.combiner = combiner

    def __repr__(self):
        return "Applicative(combiner={})".format(self.combiner)


class Operative:
    def __init__(self, parameters, dynamic_env_parameter, body, static_env):
        self.parameters = parameters
        self.dynamic_env_parameter = dynamic_env_parameter
        self.body = body
        self.static_env = static_env

    def __repr__(self):
        return "Operative(parameters={}, dynamic_env_parameter={}, body={}, static_env={})".format(
            self.parameters,
            self.dynamic_env_parameter,
            "...",  # self.body,
            self.static_env,
        )

class SpecialFunction:
    def __init__(self, name, f):
        self.name = name
        self.f = f

    def __repr__(self):
        return "SpecialFunction(name={}, f={})".format(self.name, self.f)

