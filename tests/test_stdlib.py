import tests


class TestStdlib(tests.SgmlTestCase):
    def test_subst(self):
        """
        subst[(X . A); B; ((A . B) . C)] = ((A . (X . A)) . C)
        """
        self.assertBothEval("""
            (let ((subst-target '(x . a))
                  (subst-source 'b)
                  (expr '((a . b) . c)))
              (subst subst-target subst-source expr))
        """, """
            '((a . (x . a)) . c)
        """)

    def test_pairlis(self):
        self.assertBothEval("""
            (pairlis
              '(a b c)
              '(u v w)
              '((d . x) (e . y)))
        """, """
            '((a . u) (b . v) (c . w) (d . x) (e . y))
        """)

    def test_assoc(self):
        self.assertBothEval("""
            (assoc
              'b
              '((a . (m n)) (b . (car x)) (c . m) (c . (cdr x))))
        """, """
            '(b . (car x))
        """)

    def test_if(self):
        self.assertEqual(2, self.eval("""
            (let ((x 1))
              (if nil (/ x 0) (+ 1 x)))
        """))

    def test_apply(self):
        self.assertEqual(6, self.eval("""
            (let ((f (lambda (x y z) (* x y z)))
                  (args '(1 2 3)))
              (apply f args))
        """))

    def test_maplist(self):
        self.assertBothEval("""
            (let ((f (lambda (j) (cons j 'x)))
                  (input '(a b (c . d))))
              (maplist input f))
        """, """
            '((a . x) (b . x) ((c . d) . x))
        """)

        self.assertBothEval("""
            (let ((x 2)
                  (f (lambda ((a b c)) (+ (* a (* x x)) (* b x) c)))
                  (coeffs '((1 0 1) (3 2 1))))
             (maplist coeffs f))
        """, """
            (list 5 17)
        """)

    def test_length(self):
        self.assertEqual(self.eval("(length nil)"), 0)
        self.assertEqual(self.eval("(length t)"), 0)
        self.assertEqual(self.eval("(length (list t))"), 1)
        self.assertEqual(self.eval("(length (list t t))"), 2)
        self.assertEqual(self.eval("(length (list t t t))"), 3)

    def test_and(self):
        self.assertBothEval("(and t)", "t")
        self.assertBothEval("(and nil t)", "nil")
        self.assertBothEval("(and 0 nil)", "nil")
        self.assertBothEval("(and 0 1)", "1")
        self.assertBothEval("(apply (wrap and) (list 0 1))", "1")
        self.assertBothEval("""
            (let ((f (lambda (x y) (/ x y))))
              (and nil (f 1 0)))
        """, "nil")

        def f():
            self.eval("""
                (let ((f (lambda (x y) (/ x y))))
                  (and t (f 1 0) nil))
            """)
        self.assertRaises(Exception, f)

        def g():
            self.eval("""
                (and t (/ 1 0) nil)
            """)
        self.assertRaises(Exception, g)

    def test_append_star(self):
        self.assertBothEval(
            "(append* '(1 2) '(3) '(4 5 6) '(7 8))",
            "'(1 2 3 4 5 6 7 8)")
