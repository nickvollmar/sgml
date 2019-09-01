import unittest


import sgml.interpreter
import sgml.reader
import sgml.rt

from tests.utils import assert_forms_equal


in1 = """
((label pairlis (lambda (x y a)
  (cond ((null x) a)
        (t (cons (cons (car x) (car y))
                 (pairlis (cdr x) (cdr y) a))))))
 (quote (a b c))
 (quote (u v w))
 (quote ((d . x) (e . y))))
"""

out1 = """((a . u) (b . v) (c . w) (d . x) (e . y))"""


class TestMisc(unittest.TestCase):
    def test1(self):
        input_code = sgml.reader.read(
            sgml.reader.INITIAL_MACROS,
            sgml.reader.StringStream(in1)
        )
        expected = sgml.reader.read_one(
            sgml.reader.INITIAL_MACROS,
            sgml.reader.StringStream(out1)
        )
        actual = sgml.interpreter.evaluate(input_code, sgml.rt.base_env())
        assert_forms_equal(self, expected, actual)
