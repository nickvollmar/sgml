import unittest


import sgml.interpreter
import sgml.reader
import sgml.rt

from tests.utils import assert_forms_equal


# ($define! $lambda
# ($vau (formals . body) env
# (wrap (eval (list* $vau formals #ignore body) env))))
in1 = """
(let ((lambda (macro (formals body) env
                (wrap (eval (list macro formals _ body) env))))
     (f (lambda (x y) (+ x y))))
  (f 2 2))
"""

out1 = """((a . u) (b . v) (c . w) (d . x) (e . y))"""


class TestInterpreter(unittest.TestCase):
    def test_let(self):
        input_code = sgml.reader.read(
            sgml.reader.INITIAL_MACROS,
            sgml.reader.StringStream("(let ((x 1)) (+ x 1))")
        )
        actual = sgml.interpreter.evaluate(input_code, sgml.rt.base_env())
        self.assertEqual(actual, 2)

    def test_macro(self):
        input_code = sgml.reader.read(
            sgml.reader.INITIAL_MACROS,
            sgml.reader.StringStream("((macro (x y) _ (eval (list + x y))) 2 (+ 1 1))")
        )
        actual = sgml.interpreter.evaluate(input_code, sgml.rt.base_env())
        self.assertEqual(actual, 4)

    def test_wrap(self):
        input_code = sgml.reader.read(
            sgml.reader.INITIAL_MACROS,
            sgml.reader.StringStream("((wrap +) 2 2)")
        )
        actual = sgml.interpreter.evaluate(input_code, sgml.rt.base_env())
        self.assertEqual(actual, 4)


    def test_let2(self):
        lambda_input_code = sgml.reader.read(
            sgml.reader.INITIAL_MACROS,
            sgml.reader.StringStream("""
                (let ((lambda (macro (formals body) env
                                (wrap (eval (list macro formals _ body)
                                            env))))
                      (f (lambda (x y) (+ x y))))
                  (f 2 17))
            """)
        )
        actual = sgml.interpreter.evaluate(lambda_input_code, sgml.rt.base_env())
        self.assertEqual(actual, 19)


