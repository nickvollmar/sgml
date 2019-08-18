import sgml.rt as rt


def apply(function, arguments, env):
    if rt.is_special_function(function):
        return rt.apply_special_function(function, arguments)

    if rt.is_operative(function):
        parameters = rt.operative_parameters(function)
        body = rt.operative_body(function)
        static_env = rt.operative_static_env(function).child_scope()
        static_env.add(rt.operative_dynamic_env_parameter(function), env)


    # if rt.is_function(function):
    #     parameters = rt.function_parameters(function)
    #     body = rt.function_body(function)
    #     static_env = rt.function_static_env(function).child_scope()
    #     for param, arg in zip(rt.iter_elements(parameters), rt.iter_elements(arguments)):
    #         static_env.add(param, arg)
    #     static_env.add(rt.function_dynamic_env_parameter(function), env)
    #     return evaluate(body, static_env)

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
    if rt.first(code) == rt.symbol("eval"):
        eval_code = evaluate(rt.second(code), env)
        if rt.length(code) >= 3:
            eval_env = evaluate(rt.third(code), env)
        else:
            eval_env = rt.base_env()
        return evaluate(eval_code, eval_env)
    if rt.first(code) == rt.symbol("vau"):
        # (vau (x y z) (...))
        parameters = rt.second(code)
        env_formal = rt.third(code)
        body = rt.fourth(code)
        return rt.operative(parameters, env_formal, body, env)
    if rt.first(code) == rt.symbol("label"):
        # (label ff (lambda (x) (cond ...)))
        name = rt.second(code)
        label_env = env.child_scope()
        body = evaluate(rt.third(code), label_env)
        label_env.add(name, body)
        return body
    if rt.first(code) == rt.symbol("define"):
        symbol = rt.second(code)
        body = rt.third(code)
        env.add(symbol, evaluate(body, env))
        return rt.cons(symbol, rt.null())

    head = evaluate(rt.first(code), env)
    if rt.is_applicative(head):
        f = rt.applicative_underlying_combiner(head)
        args = eval_list(rt.rest(code), env)
        return apply(f, args, env)
    return apply(head, rt.rest(code), env)


def eval_list(lst, env):
    if rt.is_null(lst):
        return lst
    hd = evaluate(rt.first(lst), env)
    tl = eval_list(rt.rest(lst), env)
    return rt.cons(hd, tl)


def eval_quote(fn, x):
    return apply(fn, x, {})
