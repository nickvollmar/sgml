import sys

_print_stack_trace = True


class StackFrame:
    def __init__(self, scope, parent):
        self.scope = scope
        self.parent = parent

    def with_value(self, rt, value):
        raise NotImplementedError("subclass responsibility")

    def frame_or_value(self, rt):
        raise NotImplementedError("subclass responsibility")


class RuntimeErrorFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, message, detail=__missing):
        super(RuntimeErrorFrame, self).__init__(scope, parent)
        self.message = message
        self.detail = detail

    def has_detail(self):
        return self.detail is not self.__missing

    def __str__(self):
        if self.has_detail():
            return "RuntimeErrorFrame: {}: {}".format(self.message, self.detail)
        return "RuntimeErrorFrame: {}".format(self.message)

    def with_value(self, rt, value):
        return self

    def frame_or_value(self, rt):
        return self


class CondStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, branches):
        super(CondStackFrame, self).__init__(scope, parent)
        self.branches = branches
        self.last_predicate_value = self.__missing

    def with_value(self, rt, value):
        result = CondStackFrame(self.scope, self.parent, self.branches)
        result.last_predicate_value = value
        return result

    def frame_or_value(self, rt):
        if rt.is_null(self.branches):
            return RuntimeErrorFrame(self.scope, self.parent, "no matches in cond")
        if rt.length(rt.first(self.branches)) != 2:
            return RuntimeErrorFrame(self.scope, self, "should be two elements in a cond-pair", rt.first(self.branches))

        if self.last_predicate_value is self.__missing:
            return DispatchStackFrame(self.scope, self, rt.first(rt.first(self.branches)))
        if rt.is_truthy(self.last_predicate_value):
            return DispatchStackFrame(self.scope, self.parent, rt.second(rt.first(self.branches)))
        return CondStackFrame(self.scope, self.parent, rt.rest(self.branches))

    def __str__(self):
        return "{} branches={}".format(self.__class__.__name__, self.branches)

class EvalStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, formlist):
        super(EvalStackFrame, self).__init__(scope, parent)
        self.formlist = formlist
        self.eval_value = self.__missing
        self.env_value = self.__missing

    def with_value(self, rt, value):
        if self.eval_value is self.__missing:
            result = EvalStackFrame(self.scope, self.parent, formlist=rt.rest(self.formlist))
            result.eval_value = value
            return result
        if self.env_value is self.__missing:
            result = EvalStackFrame(self.scope, self.parent, formlist=rt.rest(self.formlist))
            result.eval_value = self.eval_value
            result.env_value = value
            return result
        return RuntimeErrorFrame(self.scope, self.parent, "with_value called too many times")

    def frame_or_value(self, rt):
        if rt.is_null(self.formlist):
            scope = rt._cached_stdlib_ns().scope() if self.env_value is self.__missing else self.env_value
            return DispatchStackFrame(scope, self.parent, form=self.eval_value)
        return DispatchStackFrame(self.scope, self, form=rt.first(self.formlist))

    def __str__(self):
        return "{} formlist={}".format(self.__class__.__name__, self.formlist)

class DefineStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, head, tree, form):
        super(DefineStackFrame, self).__init__(scope, parent)
        self.head = head
        self.tree = tree
        self.form = form
        self.form_value = self.__missing

    def with_value(self, rt, value):
        if self.form_value is self.__missing:
            result = DefineStackFrame(self.scope, self.parent, self.head, self.tree, self.form)
            result.form_value = value
            return result
        return RuntimeErrorFrame(self.scope, self, "with_value called too many times")

    def frame_or_value(self, rt):
        if self.form_value is self.__missing:
            return DispatchStackFrame(self.scope, self, self.form)
        if self.head is rt.DEFINE:
            self.scope.ns_define_match(rt, tree=self.tree, obj=self.form_value)
        elif self.head is rt.SET:
            self.scope.ns_set_match(rt, tree=self.tree, obj=self.form_value)
        # void
        return self.parent

    def __str__(self):
        return "{} tree={} form={}".format(self.__class__.__name__, self.tree, self.form)

class LabelStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, label, form):
        super(LabelStackFrame, self).__init__(scope, parent)
        self.label = label
        self.form = form
        self.form_value = self.__missing

    def with_value(self, rt, value):
        if self.form_value is self.__missing:
            result = LabelStackFrame(self.scope, self.parent, self.label, self.form)
            result.form_value = value
            return result
        return RuntimeErrorFrame(self.scope, self, "with_value called too many times")

    def frame_or_value(self, rt):
        if self.form_value is self.__missing:
            return DispatchStackFrame(self.scope, self, self.form)
        self.scope.add_match(rt, tree=self.label, obj=self.form_value)
        return self.form_value

    def __str__(self):
        return "{} label={} form={}".format(self.__class__.__name__, self.label, self.form)


class LetStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, bindings, body):
        super(LetStackFrame, self).__init__(scope.child_scope(), parent)
        self.bindings = bindings
        self.body = body
        self.next_binding_value = self.__missing

    def with_value(self, rt, value):
        result = LetStackFrame(self.scope, self.parent, self.bindings, self.body)
        result.next_binding_value = value
        return result

    def frame_or_value(self, rt):
        if rt.is_null(self.bindings):
            return OperativeStackFrame(self.scope, self.parent, self.body, self.scope)
        if self.next_binding_value is self.__missing:
            if rt.length(rt.first(self.bindings)) != 2:
                return RuntimeErrorFrame(self.scope, self, "should be two elements in a let-binding", rt.first(self.bindings))
            return DispatchStackFrame(self.scope, self, form=rt.second(rt.first(self.bindings)))
        self.scope.add_match(rt, tree=rt.first(rt.first(self.bindings)), obj=self.next_binding_value)
        return LetStackFrame(self.scope, self.parent, rt.rest(self.bindings), self.body)

    def __str__(self):
        return "{} bindings={} body={}".format(self.__class__.__name__, self.bindings, self.body)


class TopLevelReturnValue:
    def __init__(self, value):
        self.value = value

class ApplicativeStackFrame(StackFrame):
    def __init__(self, scope, parent, func_value, args):
        super(ApplicativeStackFrame, self).__init__(scope, parent)
        self.func_value = func_value
        self.remaining_args = args
        self.arg_values = []

    def with_value(self, rt, value):
        result = ApplicativeStackFrame(self.scope, self.parent, self.func_value, self.remaining_args)
        result.arg_values = self.arg_values + [value]
        return result

    def frame_or_value(self, rt):
        if rt.is_null(self.remaining_args):
            args = rt.forms_to_list(self.arg_values)
            func = rt.unwrap(self.func_value)
            if rt.is_continuation(func):
                # is this correct? and/or the best way to do this?
                result = rt.continuation_frame(func)
                if result is None:
                    if len(self.arg_values) != 1:
                        return RuntimeErrorFrame(self.scope, self, "top-level continuation should return one item", self.arg_values)
                    return TopLevelReturnValue(self.arg_values[0])
                for v in self.arg_values:
                    result = result.with_value(rt, v)
                return result
            if rt.is_primitive_function(func):
                return rt.apply_primitive_function(func, args, self.scope)
            return make_operative_stack_frame(rt, self.scope, self.parent, func, args)

        eval_rest = ApplicativeStackFrame(self.scope, self.parent, self.func_value, rt.rest(self.remaining_args))
        eval_rest.arg_values = self.arg_values
        return DispatchStackFrame(self.scope, eval_rest, rt.first(self.remaining_args))

    def __str__(self):
        return "{} func_value={}".format(self.__class__.__name__, self.func_value)

def make_operative_stack_frame(rt, scope, parent, func, args):
    operative_env = rt.operative_static_env(func).child_scope()
    operative_env.add_match(rt, tree=rt.operative_parameters(func), obj=args)
    operative_env.add_match(rt, tree=rt.operative_dynamic_env_parameter(func), obj=scope)
    return OperativeStackFrame(scope, parent, rt.operative_body(func), operative_env)


class OperativeStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, operative_body, operative_env):
        super(OperativeStackFrame, self).__init__(scope, parent)
        self.operative_body = operative_body
        self.operative_env = operative_env
        self.result_value = self.__missing

    def with_value(self, rt, value):
        result = OperativeStackFrame(self.scope, self.parent, self.operative_body, self.operative_env)
        result.result_value = value
        return result

    def frame_or_value(self, rt):
        if rt.is_null(self.operative_body):
            if self.result_value is self.__missing:
                return rt.IGNORE
            return self.result_value
        eval_rest = OperativeStackFrame(self.scope, self.parent, rt.rest(self.operative_body), self.operative_env)
        eval_rest.result_value = self.result_value
        return DispatchStackFrame(self.operative_env, eval_rest, rt.first(self.operative_body))

    def __str__(self):
        return "{} operative_body={}".format(self.__class__.__name__, self.operative_body)


class CallCCStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, form):
        super(CallCCStackFrame, self).__init__(scope, parent)
        self.form = form
        self.form_value = self.__missing

    def with_value(self, rt, value):
        if self.form_value is self.__missing:
            result = CallCCStackFrame(self.scope, self.parent, self.form)
            result.form_value = value
            return result
        return RuntimeErrorFrame(self.scope, self, "with_value called too many times")

    def frame_or_value(self, rt):
        if self.form_value is self.__missing:
            return DispatchStackFrame(self.scope, self, self.form)
        # invoke self.form_value with one argument, the continuation
        args = rt.cons(rt.continuation(self.parent), rt.null())
        result = DispatchStackFrame(self.scope, self.parent, rt.cons(self.form_value, args))
        result.head = self.form_value  # skip the "recur to get the first value" part
        return result

    def __str__(self):
        return "{} form={}".format(self.__class__.__name__, self.form)


class DispatchStackFrame(StackFrame):
    __missing = object()

    def __init__(self, scope, parent, form):
        super(DispatchStackFrame, self).__init__(scope, parent)
        self.form = form
        self.head = self.__missing

    def with_value(self, rt, value):
        if self.head is self.__missing:
            result = DispatchStackFrame(self.scope, self.parent, form=self.form)
            result.head = value
            return result
        return RuntimeErrorFrame(self.scope, self.parent, "with_value called too many times")

    def frame_or_value(self, rt):
        if rt.is_symbol(self.form):
            try:
                return self.scope.get(rt, self.form)
            except KeyError:
                return RuntimeErrorFrame(self.scope, self.parent, "Unbound variable", self.form)

        if rt.is_atom(self.form):
            return self.form

        # it's a compound form
        if self.head is self.__missing:
            # recur to get the first value
            return DispatchStackFrame(self.scope, self, form=rt.first(self.form))

        if self.head is rt.IGNORE:
            return rt.IGNORE
        if self.head is rt.NS:
            rt.set_current_ns(rt.second(self.form))
            self.scope.set_ns(rt.current_ns())
            return rt.IGNORE
        if self.head is rt.REQUIRE:
            rt.require_ns(rt.second(self.form))
            return rt.IGNORE
        if self.head is rt.LOAD:
            rt.load_file(rt.second(self.form))
            return rt.IGNORE
        if self.head is rt.QUOTE:
            return rt.second(self.form)
        if self.head is rt.FEXPR:
            # (fexpr (x y z) (...))
            # from the Kernel concept "vau"
            parameters = rt.second(self.form)
            env_formal = rt.third(self.form)
            body = rt.rest(rt.rest(rt.rest(self.form)))
            return rt.operative(parameters, env_formal, body, self.scope.child_scope())

        if self.head is rt.LABEL:
            if rt.length(self.form) != 3:
                return RuntimeErrorFrame(self.scope, self.parent, "wrong arguments to label", self.form)
            return LabelStackFrame(self.scope, self.parent, label=rt.second(self.form), form=rt.third(self.form))

        if self.head is rt.CALL_CC:
            if rt.length(self.form) != 2:
                return RuntimeErrorFrame(self.scope, self.parent, "wrong arguments to call/cc", self.form)
            return CallCCStackFrame(self.scope, self.parent, form=rt.second(self.form))

        if self.head is rt.COND:
            return CondStackFrame(self.scope, self.parent, branches=rt.rest(self.form))
        if self.head is rt.LET:
            return LetStackFrame(self.scope, self.parent, bindings=rt.second(self.form), body=rt.rest(rt.rest(self.form)))
        if self.head is rt.EVAL:
            if rt.length(self.form) not in (2, 3):
                return RuntimeErrorFrame(self.scope, self.parent, "wrong arguments to eval", self.form)
            return EvalStackFrame(self.scope, self.parent, formlist=rt.rest(self.form))
        if self.head is rt.DEFINE or self.head is rt.SET:
            if rt.length(self.form) != 3:
                return RuntimeErrorFrame(self.scope, self.parent, "wrong arguments to {}".format(self.head.name))
            return DefineStackFrame(self.scope, self.parent, head=self.head, tree=rt.second(self.form), form=rt.third(self.form))
        if rt.is_applicative(self.head):
            args = rt.rest(self.form)
            return ApplicativeStackFrame(self.scope, self.parent, func_value=self.head, args=args)
        if rt.is_operative(self.head):
            return make_operative_stack_frame(rt, self.scope, self.parent, func=self.head, args=rt.rest(self.form))

        return RuntimeErrorFrame(self.scope, self.parent, "non-applicable object", self.form)

    def __str__(self):
        return "{} form={}".format(self.__class__.__name__, self.form)


def stacktrace(stack_frame):
    trace = []
    while stack_frame is not None:
        trace.append(stack_frame)
        stack_frame = stack_frame.parent
    return list(reversed(trace))


def macroexpand(rt, code):
    expanded = macroexpand1(rt, code)
    if expanded == code:
        return code
    return macroexpand(rt, expanded)


def evaluate(rt, code):
    stack_top = DispatchStackFrame(rt.current_ns().scope(), parent=None, form=code)
    while True:
        try:
            frame_or_value = stack_top.frame_or_value(rt)
            if isinstance(frame_or_value, StackFrame):
                # "push"
                stack_top = frame_or_value
            elif stack_top.parent is None:
                return frame_or_value
            elif isinstance(frame_or_value, TopLevelReturnValue):
                return frame_or_value.value
            else:
                # "pop"
                stack_top = stack_top.parent.with_value(rt, frame_or_value)
        except Exception as e:
            #stack_top = RuntimeErrorFrame(scope, stack_top, "Python error", e)
            raise

        if isinstance(stack_top, RuntimeErrorFrame):
            # todo: try/catch
            if _print_stack_trace:
                print("Stack:", file=sys.stderr)
                for frame in stacktrace(stack_top):
                    print("    {}".format(frame), file=sys.stderr)
                if stack_top.has_detail():
                    print("Details:", rt.as_string(stack_top.detail), file=sys.stderr)
            raise RuntimeError("Exception evaluating {}: {}".format(rt.as_string(code), stack_top))
