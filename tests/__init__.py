import sgml.interpreter
import sgml.reader
import sgml.rt
from sgml.reader.streams import StringStream
import unittest


def _eval(code: str, env=None):
    if env is None:
        env = sgml.rt.base_env()
    forms = sgml.reader.read_many(sgml.reader.INITIAL_MACROS, StringStream(code))
    result = None
    for form in sgml.rt.iter_elements(forms):
        result = sgml.interpreter.evaluate(form, env)
    return result


class SgmlTestCase(unittest.TestCase):
    def assertFormsEqual(self, expected, actual, msg=None):
        if not sgml.rt.eq(expected, actual):
            standard_msg = 'expected {} != actual {}'.format(expected, actual)
            msg = self._formatMessage(msg, standard_msg)
            raise self.failureException(msg)

    def assertEval(self, code: str, expected):
        input_form = sgml.reader.read_one(
            sgml.reader.INITIAL_MACROS,
            StringStream(code)
        )
        actual = sgml.interpreter.evaluate(input_form, sgml.rt.base_env())
        self.assertEqual(expected, actual)

    def assertBothEval(self, code: str, expected_code: str):
        expected = _eval(expected_code)
        actual = _eval(code)
        self.assertFormsEqual(expected, actual)
