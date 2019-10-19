from __future__ import annotations


_missing = object()


class StackFrame:
    def __init__(self, env, parent):
        self.env = env
        self.parent = parent

    def frame_or_value(self, rt):
        pass

    def with_value(self, value):
        pass


class RuntimeErrorFrame(StackFrame):
    def __init__(self, message, env, parent):
        super(RuntimeErrorFrame, self).__init__(env, parent)
        self.message = message


# class LetStackFrame(StackFrame):
#     def frame_or_value(self, rt):
#         if not self.values:
#             return EvalStackFrame(evaluend=self.evaluend[0], env=self.env, parent=self)
#
#         if len(self.values) % 2 and rt.is_truthy(self.values[-1]):
#             return EvalStackFrame(evaluend=self.evaluend[len(self.values)], env=self.env, parent=self.parent)


class CondStackFrame(StackFrame):
    def __init__(self, pred_expr_list, env, parent):
        super(CondStackFrame, self).__init__(env, parent)
        self.pred_expr_list = pred_expr_list


class EvalStackFrame(StackFrame):
    def __init__(self, evaluend, env, parent):
        super(EvalStackFrame, self).__init__(env, parent)
        self.form = evaluend
        self.head = _missing

    def with_value(self, value):
        if self.head is _missing:
            result = EvalStackFrame(self.form, self.env, self.parent)
            result.head = value
            return result
        return RuntimeErrorFrame("with_value called twice", self.env, self.parent)

    def frame_or_value(self, rt):
        if rt.is_symbol(self.form):
            return self.env.get(rt, self.form)
        if rt.is_atom(self.form):
            return self.form

        # it's a compound form
        if self.head is _missing:
            return EvalStackFrame(rt.car(self.form), env=self.env, parent=self)

        if self.head is rt.IGNORE:
            return rt.IGNORE
        if self.head is rt.QUOTE:
            return rt.second(self.form)


def apply(rt, function, arguments, env):
    if rt.is_primitive_function(function):
        return rt.apply_primitive_function(function, arguments, env)

    if rt.is_operative(function):
        parameters = rt.operative_parameters(function)
        body = rt.operative_body(function)
        static_env = rt.operative_static_env(function).child_scope()
        env_param = rt.operative_dynamic_env_parameter(function)
        static_env.add_match(rt, tree=parameters, obj=arguments)
        static_env.add_match(rt, tree=env_param, obj=env)
        result = None
        for form in rt.iter_elements(body):
            result = evaluate(rt, form, static_env)
        return result

    if rt.is_symbol(function):
        # Is this possible?
        f = evaluate(rt, function, env)
        return apply(rt, f, arguments, env)

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
            branch_scope = env.child_scope()
            test = evaluate(rt, rt.first(branch), branch_scope)
            if rt.is_truthy(test):
                return evaluate(rt, rt.second(branch), branch_scope)
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
        body = rt.rest(rt.rest(rt.rest(code)))
        return rt.operative(parameters, env_formal, body, env.child_scope())
    if head is rt.LABEL:
        # (label ff (lambda (x) (cond ...)))
        name = rt.second(code)
        label_env = env.child_scope()
        body = evaluate(rt, rt.third(code), label_env)  # presumably captures label_env
        label_env.add(rt, name, body)  # mutate label_env
        return body
    if head is rt.DEFINE:
        symbol = rt.second(code)
        body = rt.third(code)
        env.add_match(rt, tree=symbol, obj=evaluate(rt, body, env))
        # LISP 1.5 behavior: return a list of defined objects
        return rt.cons(symbol, rt.null())
    if head is rt.LET:
        let_env = env.child_scope()
        parameters = rt.second(code)
        for binding in rt.iter_elements(parameters):
            sym = rt.first(binding)
            val = rt.second(binding)
            let_env.add_match(rt, tree=sym, obj=evaluate(rt, val, let_env))
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
