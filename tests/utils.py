import sgml.rt


def assert_forms_equal(test_case, expected, actual, msg=None):
    if not sgml.rt.eq(expected, actual):
        standard_msg = 'expected {} != actual {}'.format(expected, actual)
        msg = test_case._formatMessage(msg, standard_msg)
        raise test_case.failureException(msg)
