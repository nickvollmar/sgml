import sgml.reader
import sgml.rt
import tests


class TestReadList(tests.SgmlTestCase):
    def test_dotted_pair(self):
        input_code = sgml.reader.streams.StringStream("(a . u)")
        expected = sgml.rt.cons(sgml.rt.symbol("a"), sgml.rt.symbol("u"))
        actual = sgml.reader.read_one(sgml.reader.INITIAL_MACROS, input_code)
        self.assertFormsEqual(expected, actual)

