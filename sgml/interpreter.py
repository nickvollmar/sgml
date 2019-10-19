from __future__ import annotations


class StackFrame:
    def __init__(self, env, parent):
        self.env = env
        self.parent = parent

    def frame_or_value(self, rt):
        raise NotImplementedError("subclass responsibility")

    def with_value(self, rt, value):
        raise NotImplementedError("subclass responsibility")


class RuntimeErrorFrame(StackFrame):
    def __init__(self, env, parent, message, form=None):
        super(RuntimeErrorFrame, self).__init__(env, parent)
        self.message = message
        self.details = form


class CondStackFrame(StackFrame):
    def __init__(self, env, parent, branches):
        super(CondStackFrame, self).__init__(env, parent)
        self.branches = branches


class EvalStackFrame(StackFrame):
    __missing = object()

    def __init__(self, env, parent, formlist):
        super(EvalStackFrame, self).__init__(env, parent)
        self.formlist = formlist
        self.eval_value = self.__missing
        self.env_value = self.__missing

    def with_value(self, rt, value):
        if self.eval_value is self.__missing:
            result = EvalStackFrame(self.env, self.parent, formlist=rt.rest(self.formlist))
            result.eval_value = value
            return result
        if self.env_value is self.__missing:
            result = EvalStackFrame(self.env, self.parent, formlist=rt.rest(self.formlist))
            result.eval_value = self.eval_value
            result.env_value = value
            return result
        return RuntimeErrorFrame(self.env, self.parent, "with_value called too many times")

    def frame_or_value(self, rt):
        if rt.is_null(self.formlist):
            env = rt.base_env() if self.env_value is self.__missing else self.env_value
            return DispatchStackFrame(self.eval_value, env, self.parent)
        return DispatchStackFrame(rt.first(self.formlist), self.env, self)


class DefineStackFrame(StackFrame):
    __missing = object()

    def __init__(self, env, parent, tree, form):
        super(DefineStackFrame, self).__init__(env, parent)
        self.tree = tree
        self.form = form
        self.form_value = self.__missing

    def with_value(self, rt, value):
        if self.form_value is self.__missing:
            result = DefineStackFrame(self.env, self.parent, self.tree, self.form)
            result.form_value = value
            return result
        return RuntimeErrorFrame(self.env, self.parent, "with_value called too many times")

    def frame_or_value(self, rt):
        if self.form_value is self.__missing:
            return DispatchStackFrame(self.env, self, self.form)
        if self.parent:
            self.parent.env.add_match(rt, tree=self.tree, obj=self.form_value)
            return self.parent


class ApplicativeStackFrame(StackFrame):
    def __init__(self, env, parent, func_value, num_args, args):
        super(ApplicativeStackFrame, self).__init__(env, parent)
        self.func_value = func_value
        self.total_num_args = num_args
        self.remaining_args = args
        self.arg_values = []

    def with_value(self, rt, value):
        if len(self.arg_values) >= self.total_num_args:
            return RuntimeErrorFrame(self.env, self.parent, "with_value called too many times")
        result = ApplicativeStackFrame(self.env, self.parent, self.func_value, self.total_num_args, self.remaining_args)
        result.arg_values = self.arg_values + [value]
        return result

    def frame_or_value(self, rt):
        if len(self.arg_values) < self.total_num_args:
            eval_rest = ApplicativeStackFrame(self.env, self.parent, self.func_value, self.total_num_args, rt.rest(self.remaining_args))
            return DispatchStackFrame(self.env, eval_rest, rt.first(self.remaining_args))

        if len(self.arg_values) == self.total_num_args:
            args_value = rt.forms_to_list(self.arg_values)

            if rt.is_primitive_function(self.func_value):
                return rt.apply_primitive_function(self.func_value, args_value, self.env)

            return make_operative_stack_frame(rt, self.env, self.parent, self.func_value, args_value)

        return RuntimeErrorFrame(self.env, self.parent, "too many arg_values somehow")


def make_operative_stack_frame(rt, env, parent, func, args):
    operative_env = rt.operative_static_env(func).child_scope()
    operative_env.add_match(rt, tree=rt.operative_parameters(func), obj=args)
    operative_env.add_match(rt, tree=rt.operative_dynamic_env_parameter(func), obj=env)
    return OperativeStackFrame(env, parent, rt.operative_body(func), operative_env)


class OperativeStackFrame(StackFrame):
    __missing = object()

    def __init__(self, env, parent, operative_body, operative_env):
        super(OperativeStackFrame, self).__init__(env, parent)
        self.operative_body = operative_body
        self.operative_env = operative_env
        self.result_value = self.__missing

    def with_value(self, rt, value):
        result = OperativeStackFrame(self.env, self.parent, self.operative_body, self.operative_env)
        result.result_value = value
        return result

    def frame_or_value(self, rt):
        if rt.is_null(self.operative_body):
            if self.result_value is self.__missing:
                return RuntimeErrorFrame(self.env, self.parent, "empty operative somehow")
            return self.result_value
        eval_rest = OperativeStackFrame(self.env, self.parent, rt.rest(self.operative_body), self.operative_env)
        return DispatchStackFrame(self.operative_env, eval_rest, rt.first(self.operative_body))


class DispatchStackFrame(StackFrame):
    __missing = object()

    def __init__(self, env, parent, form):
        super(DispatchStackFrame, self).__init__(env, parent)
        self.form = form
        self.head = self.__missing

    def with_value(self, rt, value):
        if self.head is self.__missing:
            result = DispatchStackFrame(
                self.env, self.parent,
                form=self.form,
            )
            result.head = value
            return result
        return RuntimeErrorFrame(self.env, self.parent, "with_value called too many times")

    def frame_or_value(self, rt):
        if rt.is_symbol(self.form):
            return self.env.get(rt, self.form)
        if rt.is_atom(self.form):
            return self.form

        # it's a compound form
        if self.head is self.__missing:
            # recur to get the first value
            return DispatchStackFrame(self.env, self, form=rt.first(self.form))

        if self.head is rt.IGNORE:
            return rt.IGNORE
        if self.head is rt.QUOTE:
            return rt.second(self.form)
        if self.head is rt.MACRO:
            # (macro (x y z) (...))
            # from the Kernel concept "vau"
            parameters = rt.second(self.form)
            env_formal = rt.third(self.form)
            body = rt.rest(rt.rest(rt.rest(self.form)))
            return rt.operative(parameters, env_formal, body, self.env.child_scope())

        if self.head is rt.COND:
            return CondStackFrame(self.env, self.parent, branches=rt.rest(self.form))
        if self.head is rt.EVAL:
            if rt.length(self.form) not in (2, 3):
                return RuntimeErrorFrame(self.env, self.parent, "wrong arguments to eval", self.form)
            return EvalStackFrame(self.env, self.parent, formlist=rt.rest(self.form))
        if self.head is rt.DEFINE:
            if rt.length(self.form) != 3:
                return RuntimeErrorFrame(self.env, self.parent, "wrong arguments to define", self.form)
            return DefineStackFrame(self.env, self.parent, tree=rt.second(self.form), form=rt.third(self.form))
        if rt.is_applicative(self.head):
            args = rt.rest(self.form)
            return ApplicativeStackFrame(self.env, self.parent, func_value=self.head, num_args=rt.length(args), args=args)
        return make_operative_stack_frame(rt, self.env, self.parent, func=self.head, args=rt.rest(self.form))


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
