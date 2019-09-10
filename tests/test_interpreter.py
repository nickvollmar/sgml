import tests

class TestInterpreter(tests.SgmlTestCase):
    def test_let(self):
        self.assertEval("(let ((x 1)) (+ x 1))", 2)
        self.assertEval("(let ((x nil) (x 19)) x)", 19)
        self.assertEval("(let ((x 1) (x (+ x 1))) x)", 2)

    def test_macro(self):
        self.assertEval("((macro (x y) _ (eval (list + x y))) 2 (+ 1 1))", 4)

    def test_wrap(self):
        self.assertEval("((wrap +) 2 2)", 4)

    def test_let2(self):
        self.assertEval("""
            (let ((lambda (macro (formals body) env
                            (wrap (eval (list macro formals _ body)
                                        env))))
                  (f (lambda (x y) (+ x y))))
              (f 2 17))
        """, 19)


