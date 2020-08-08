import tests

class TestCallCC(tests.SgmlTestCase):
    def test_from_wikipedia1(self):
        """
        Adapted from the Wikipedia article https://en.wikipedia.org/wiki/Call-with-current-continuation
        """
        self.eval("""
            (defn f (return)
              (return 2)
              3)
        """, self.env)
        self.assertEqual(3, self.eval("(f (lambda (x) x))"))
        self.assertEqual(2, self.eval("(call/cc f)"))

    def test_from_wikipedia2(self):
        """
        Adapted from the Wikipedia article https://en.wikipedia.org/wiki/Call-with-current-continuation
        """
        self.eval("""
            ;; [LISTOF X] -> ( -> X u 'you-fell-off-the-end)
            (defn generate-one-element-at-a-time (lst)
              ;; Both internal functions are closures over lst

              ;; Internal variable/Function which passes the current element in a list
              ;; to its return argument (which is a continuation), or passes an end-of-list marker
              ;; if no more elements are left. On each step the function name is
              ;; rebound to a continuation which points back into the function body,
              ;; while return is rebound to whatever continuation the caller specifies.
              (defn control-state (return)
                (for-each
                 (lambda (element)
                           (define return (call/cc
                                          (lambda (resume-here)
                                            ;; Grab the current continuation
                                           (set! control-state resume-here)
                                           (return element))))) ;; (return element) evaluates to next return
                 lst)
                (return "you-fell-off-the-end"))

              ;; (-> X u 'you-fell-off-the-end)
              ;; This is the actual generator, producing one item from lst at a time.
              (defn generator ()
                (call/cc control-state))

              ;; Return the generator
              generator)

            (define generate-digit
              (generate-one-element-at-a-time (quote (0 1 2))))
        """, self.env)
        self.assertEqual(0, self.eval("(generate-digit)"))
        self.assertEqual(1, self.eval("(generate-digit)"))
        self.assertEqual(2, self.eval("(generate-digit)"))
        self.assertEqual("you-fell-off-the-end", self.eval("(generate-digit)"))

    def test_from_scheme_spec1(self):
        """
        Adapted from the Scheme spec:
        https://schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-9.html#%_idx_566
        """
        self.assertEqual(-3, self.eval("""
            (call/cc
              (lambda (exit)
                (for-each (lambda (x)
                            (if (negative? x)
                                (exit x)
                                _))
                          (list 54 0 37 (- 0 3) 245 19))
                t))
        """))

    def test_from_scheme_spec2(self):
        """
        Adapted from the Scheme spec:
        https://schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-9.html#%_idx_566
        """
        self.eval("""
            (define list-length
              (lambda (obj)
                (call/cc
                  (lambda (return)
                    (let ((r
                              (label r' (lambda (obj)
                                (cond ((null obj) 0)
                                      ((null (atom obj)) (+ (r' (cdr obj)) 1))
                                      (t (return nil)))))))
                      (r obj))))))
        """, self.env)

        self.assertEqual(4, self.eval("(list-length (quote (1 2 3 4)))"))
        self.assertEqual(self.rt.null(), self.eval("(list-length (quote (a b . c)))"))
