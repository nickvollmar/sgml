import unittest

import tests

in1 = """
((label pairlis (lambda (x y a)
  (cond ((null x) a)
        (t (cons (cons (car x) (car y))
                 (pairlis (cdr x) (cdr y) a))))))
 (quote (a b c))
 (quote (u v w))
 (quote ((d . x) (e . y))))
"""

out1 = """(quote ((a . u) (b . v) (c . w) (d . x) (e . y)))"""


class TestMisc(tests.SgmlTestCase):
    def test1(self):
        self.assertBothEval(in1, out1)
