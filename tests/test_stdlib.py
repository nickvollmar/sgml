import tests


class TestStdlib(tests.SgmlTestCase):
    def test_subst(self):
        """
        subst[(X . A); B; ((A . B) . C)] = ((A . (X . A)) . C)
        """
        self.assertBothEval("""
            (let ((subst-target (quote (x . a)))
                  (subst-source (quote b))
                  (expr (quote ((a . b) . c))))
              (subst subst-target subst-source expr))
        """, """
            (quote ((a . (x . a)) . c))
        """)

    def test_pairlis(self):
        self.assertBothEval("""
            (pairlis
              (quote (a b c))
              (quote (u v w))
              (quote ((d . x) (e . y))))
        """, """
            (quote ((a . u) (b . v) (c . w) (d . x) (e . y)))
        """)

    def test_assoc(self):
        self.assertBothEval("""
            (assoc
              (quote b)
              (quote ((a . (m n)) (b . (car x)) (c . (quote m)) (c . (cdr x)))))
        """, """
            (quote (b . (car x)))
        """)

    def test_apply(self):
        self.assertEqual(6, self.eval("""
            (let ((f (lambda (x y z) (* x y z)))
                  (args (list 1 2 3)))
              (apply f args))
        """))
