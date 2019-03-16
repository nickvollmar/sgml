import sgml.rt as rt


def apply(function, arguments, env):
    if rt.is_special_function(function):
        return rt.apply_special_function(function, arguments)

    if rt.is_function(function):
        parameters = rt.function_parameters(function)
        body = rt.function_body(function)
        static_env = rt.function_static_env(function).child_scope()
        for param, arg in zip(rt.iter_elements(parameters), rt.iter_elements(arguments)):
            static_env.add(param, arg)
        return evaluate(body, static_env)

    if rt.is_atom(function) and not rt.is_symbol(function):
        raise ValueError("apply() called on non-applicable object: {}".format(function))

    return apply(evaluate(function, env), arguments, env)


def evaluate(code, env):
    if rt.is_symbol(code):
        return env.get(code)
    if rt.is_atom(code):
        return code

    if rt.first(code) == rt.symbol("quote"):
        return rt.second(code)
    if rt.first(code) == rt.symbol("cond"):
        for branch in rt.iter_elements(rt.rest(code)):
            test = evaluate(rt.first(branch), env)
            if rt.is_truthy(test):
                return evaluate(rt.second(branch), env)
        raise ValueError("No matching branches in `cond`: {}".format(code))
    if rt.first(code) == rt.symbol("lambda"):
        # (lambda (x y z) (...))
        parameters = rt.second(code)
        body = rt.third(code)
        return rt.function(parameters, body, env)
    if rt.first(code) == rt.symbol("label"):
        # (label ff (lambda (x) (cond ...)))
        name = rt.second(code)
        label_env = env.child_scope()
        body = evaluate(rt.third(code), label_env)
        label_env.add(name, body)
        return body
    if rt.first(code) == rt.symbol("define"):
        result = []
        defs = list(rt.iter_elements(rt.rest(code)))
        if len(defs) % 2:
            raise ValueError("Expected even number of pairs in `def`: {}".format(code))
        for i in range(0, len(defs), 2):
            env.add(defs[i], evaluate(defs[i+1], env))
            result.append(defs[i])
        return rt._forms_to_list(result)
    
    return apply(rt.first(code), eval_list(rt.rest(code), env), env)


def eval_list(lst, env):
    if rt.is_null(lst):
        return lst
    hd = evaluate(rt.first(lst), env)
    tl = eval_list(rt.rest(lst), env)
    return rt.cons(hd, tl)


def eval_quote(fn, x):
    return apply(fn, x, {})
