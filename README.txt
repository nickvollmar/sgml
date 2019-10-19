References:

LISP 1.5 Programmer's Manual
John McCarthy, Paul W. Abrahams, Daniel J. Edwards, Timothy P. Hart, Michael I. Levin
The Computation Center and Research Laboratory of Electronics - Massachusetts Institute of Technology
https://web.archive.org/web/20060208074557if_/http://community.computerhistory.org:80/scc/projects/LISP/book/LISP%201.5%20Programmers%20Manual.pdf

Revised^{-1} Report on the Kernel Programming Language
John N. Shutt
Worcester Polytechnic Institute
ftp://ftp.cs.wpi.edu/pub/techreports/pdf/05-07.pdf

---

Stack Frames
Each special form gets its own type of stack frame with an immutable
"evaluend" (code to be evaluated) and mutable "values list." Each step of
evaluation ends with the stack frame returning either itself or another stack
frame that it "becomes". Descendant stack frames have parent=self; "tail
calls" have parent=self.parent. To return a value up the stack, mutate and
return self.parent.

We can't really know what type of stack frame to use until the head is
evaluated. So every combiner starts as an "unknown combiner" frame type. After
it gets its first value, it does a dispatch and returns an appropriate frame
type with same evaluend and empty values list.

Broadly speaking, each other frame type works iteratively through its
evaluend. "Let" for example -- index of "next" pred/result pair. if value list
is empty, return child stack frame to evaluate next predicate. If value list
is nonempty and first element truthy, return tail call to evaluate next
result. So we only actually need one element of value list I guess, at least
for "Let". (Maybe also dispatch on frame type for "receive value"? Or maybe we
don't need that either?)

Eval stack frame ultimately returns an "unknown" frame type with
evaluend=self.values_list!! Ha!!!
