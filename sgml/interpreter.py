def match(rt, tree, obj, env):
    """
    Match the formal parameter tree to an object.
    See kernel.pdf p51.

    :param rt: Runtime instance
    :param tree: The formal parameter tree
    :param obj: The argument object
    :param env: The environment in which to match (will be mutated)
    """
    if rt.is_symbol(tree):
        env.add(rt, tree, obj)
        return
    if tree is rt.IGNORE:
        return
    if rt.is_null(tree):
        if not rt.is_null(obj):
            rt.bail("arity error")
        return
    # it's a pair
    match(rt, rt.first(tree), rt.first(obj), env)
    match(rt, rt.rest(tree), rt.rest(obj), env)


def apply(rt, function, arguments, env):
    if rt.is_primitive_function(function):
        return rt.apply_primitive_function(function, arguments, env)

    if rt.is_operative(function):
        parameters = rt.operative_parameters(function)
        body = rt.operative_body(function)
        static_env = rt.operative_static_env(function).child_scope()
        match(rt, parameters, arguments, static_env)
        env_param = rt.operative_dynamic_env_parameter(function)
        if env_param is not rt.IGNORE:
            static_env.add(rt, env_param, env)
        return evaluate(rt, body, static_env)

    if rt.is_symbol(function):
        return apply(rt, evaluate(rt, function, env), arguments, env)

    raise ValueError("apply() called on non-applicable object: {}".format(function))


def evaluate(rt, code, env):
    if rt.is_symbol(code):
        return env.get(rt, code)
    if rt.is_atom(code):
        return code

    # it's a compound form
    head = evaluate(rt, rt.first(code), env)

    # *** Special forms ***
    if head is rt.IGNORE:
        return rt.IGNORE
    if head is rt.QUOTE:
        return rt.second(code)
    if head is rt.COND:
        for branch in rt.iter_elements(rt.rest(code)):
            test = evaluate(rt, rt.first(branch), env)
            if rt.is_truthy(test):
                return evaluate(rt, rt.second(branch), env)
        raise ValueError("No matching branches in `cond`: {}".format(code))
    if head is rt.EVAL:
        eval_code = evaluate(rt, rt.second(code), env)
        if rt.length(code) >= 3:
            eval_env = evaluate(rt, rt.third(code), env)
        else:
            eval_env = rt.base_env()
        return evaluate(rt, eval_code, eval_env)
    if head is rt.MACRO:
        # (macro (x y z) (...))
        # from the Kernel concept "vau"
        parameters = rt.second(code)
        env_formal = rt.third(code)
        body = rt.fourth(code)
        return rt.operative(parameters, env_formal, body, env)
    if head is rt.LABEL:
        # (label ff (lambda (x) (cond ...)))
        name = rt.second(code)
        label_env = env.child_scope()
        body = evaluate(rt, rt.third(code), label_env)
        label_env.add(rt, name, body)
        return body
    if head is rt.DEFINE:
        symbol = rt.second(code)
        body = rt.third(code)
        env.add(rt, symbol, evaluate(rt, body, env))
        return rt.cons(symbol, rt.null())
    if head is rt.LET:
        let_env = env.child_scope()
        parameters = rt.second(code)
        for binding in rt.iter_elements(parameters):
            sym = rt.first(binding)
            val = evaluate(rt, rt.second(binding), let_env)
            match(rt, sym, val, let_env)
        body = rt.third(code)
        return evaluate(rt, body, let_env)

    # *** Combinators ***
    # Applicative: evaluate, then apply
    if rt.is_applicative(head):
        f = rt.unwrap(head)
        args = eval_list(rt, rt.rest(code), env)
        return apply(rt, f, args, env)

    # Operative: apply directly
    return apply(rt, head, rt.rest(code), env)


def eval_list(rt, lst, env):
    if rt.is_null(lst):
        return lst
    hd = evaluate(rt, rt.first(lst), env)
    tl = eval_list(rt, rt.rest(lst), env)
    return rt.cons(hd, tl)


# TODO: what was this for?
def eval_quote(rt, fn, x):
    return apply(rt, fn, x, {})
