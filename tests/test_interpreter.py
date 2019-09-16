import tests


class TestInterpreter(tests.SgmlTestCase):
    def test_let(self):
        self.assertEqual(2, self.eval("(let ((x 1)) (+ x 1))"))
        self.assertEqual(19, self.eval("(let ((x nil) (x 19)) x)"))
        self.assertEqual(2, self.eval("(let ((x 1) (x (+ x 1))) x)"))

    def test_macro(self):
        self.assertEqual(4, self.eval("((macro (x y) _ (eval (list + x y))) 2 (+ 1 1))"))

    def test_wrap(self):
        self.assertEqual(4, self.eval("((wrap +) 2 2)"))

    def test_let2(self):
        self.assertEqual(19, self.eval("""
            (let ((lambda (macro (formals body) env
                            (wrap (eval (list macro formals _ body)
                                        env))))
                  (f (lambda (x y) (+ x y))))
              (f 2 17))
        """))


