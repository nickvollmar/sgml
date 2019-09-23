import tests

import sgml.rt.error


class TestInterpreter(tests.SgmlTestCase):
    def test_arity_error(self):
        def f():
            self.eval("""
                (define supergreat
                  (lambda (x y z)
                    (print x y z)))
                
                (supergreat 1 2)
            """)
        self.assertRaises(sgml.rt.error.RuntimeException, f)

    def test_let(self):
        self.assertEqual(2, self.eval("(let ((x 1)) (+ x 1))"))
        self.assertEqual(19, self.eval("(let ((x nil) (x 19)) x)"))
        self.assertEqual(2, self.eval("(let ((x 1) (x (+ x 1))) x)"))

    def test_apply(self):
        self.assertEqual(2, self.eval("(apply (lambda (x) (+ x 1)) (list 1))"))
        self.assertEqual(2, self.eval("(apply (lambda (x) (+ x 1)) (list 1))"))

    def test_macro(self):
        self.assertEqual(4, self.eval("((macro (x y) _ (eval (list + x y))) 2 (+ 1 1))"))

    def test_wrap(self):
        self.assertEqual(4, self.eval("((wrap +) 2 2)"))

    def test_let2(self):
        self.assertEqual(19, self.eval("""
            (let ((lambda2 (macro (formals body) env
                             (wrap (eval (list macro formals _ body)
                                         env))))
                  (f (lambda2 (x y) (+ x y))))
              (f 2 17))
        """))


