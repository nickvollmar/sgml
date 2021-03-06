import sgml.main
import sgml.rt
import sgml.interpreter
from sgml.reader.streams import StringStream

import unittest


class SgmlTestCase(unittest.TestCase):
    def setUp(self):
        self.rt = sgml.rt
        self.rt.init()

    def eval(self, code: str, scope=None):
        forms = sgml.reader.read_many(
            self.rt,
            sgml.reader.INITIAL_MACROS,
            StringStream(code)
        )
        result = None
        for form in self.rt.iter_elements(forms):
            result = sgml.interpreter.evaluate(self.rt, form)
        return result

    def assertFormsEqual(self, expected, actual, msg=None):
        if not self.rt.eq(expected, actual):
            standard_msg = 'expected {} != actual {}'.format(expected, actual)
            msg = self._formatMessage(msg, standard_msg)
            raise self.failureException(msg)

    def assertBothEval(self, code: str, expected_code: str):
        expected = self.eval(expected_code)
        actual = self.eval(code)
        self.assertFormsEqual(expected, actual)
