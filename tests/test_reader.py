import unittest

import sgml.reader
import sgml.rt

from tests.utils import assert_forms_equal


class TestReadList(unittest.TestCase):
    def test_dotted_pair(self):
        input_code = sgml.reader.StringStream("(a . u)")
        expected = sgml.rt.cons(sgml.rt.symbol("a"), sgml.rt.symbol("u"))
        actual = sgml.reader.read_one(sgml.reader.INITIAL_MACROS, input_code)
        assert_forms_equal(self, expected, actual)

