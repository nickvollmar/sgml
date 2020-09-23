import sgml.reader
import tests


class TestReader(tests.SgmlTestCase):
    def read_one(self, code: str):
        return sgml.reader.read_one(
            self.rt,
            sgml.reader.INITIAL_MACROS,
            sgml.reader.streams.StringStream(code)
        )

    def test_dotted_pair(self):
        self.assertFormsEqual(
            self.rt.cons(self.rt.symbol("a"), self.rt.symbol("u")),
            self.read_one("(a . u)")
        )

    def test_quote(self):
        self.assertFormsEqual(
            self.rt.forms_to_list([self.rt.QUOTE, self.rt.symbol("a")]),
            self.read_one("'a"))
        self.assertFormsEqual(
            self.rt.forms_to_list([self.rt.QUOTE, self.rt.forms_to_list([self.rt.QUOTE, self.rt.symbol("a")])]),
            self.read_one("''a"))
        self.assertFormsEqual(
            self.rt.forms_to_list([self.rt.QUOTE, self.rt.forms_to_list([self.rt.symbol("quote"), self.rt.symbol("a")])]),
            self.read_one("'(quote a)"))
        self.assertFormsEqual(
            self.rt.forms_to_list([self.rt.QUOTE, self.read_one("(1 2 3 4)")]),
            self.read_one("'(1 2 3 4)")
        )

