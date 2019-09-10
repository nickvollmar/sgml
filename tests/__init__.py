import sgml.interpreter
import sgml.reader
import sgml.rt
from sgml.reader.streams import StringStream
import unittest


class SgmlTestCase(unittest.TestCase):
    def assertFormsEqual(self, expected, actual, msg=None):
        if not sgml.rt.eq(expected, actual):
            standard_msg = 'expected {} != actual {}'.format(expected, actual)
            msg = self._formatMessage(msg, standard_msg)
            raise self.failureException(msg)

    def assertEval(self, code: str, expected):
        input_form = sgml.reader.read(
            sgml.reader.INITIAL_MACROS,
            StringStream(code)
        )
        actual = sgml.interpreter.evaluate(input_form, sgml.rt.base_env())
        self.assertEqual(expected, actual)

    def assertBothEval(self, code: str, expected_code: str):
        input_code = sgml.reader.read(
            sgml.reader.INITIAL_MACROS,
            StringStream(code)
        )
        expected = sgml.reader.read_one(
            sgml.reader.INITIAL_MACROS,
            StringStream(expected_code)
        )
        actual = sgml.interpreter.evaluate(input_code, sgml.rt.base_env())
        self.assertFormsEqual(expected, actual)
