import sgml.reader
import tests


class TestReadList(tests.SgmlTestCase):
    def test_dotted_pair(self):
        input_code = sgml.reader.streams.StringStream("(a . u)")
        expected = self.rt.cons(self.rt.symbol("a"), self.rt.symbol("u"))
        actual = sgml.reader.read_one(
            self.rt,
            sgml.reader.INITIAL_MACROS,
            input_code
        )
        self.assertFormsEqual(expected, actual)

