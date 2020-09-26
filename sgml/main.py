import sys

import sgml.interpreter
import sgml.reader
import sgml.rt

USAGE = "Usage: python3 -m sgml.main [ -c <command> ] | [filename]"


def main(args):
    command = None
    filename = None
    i = 1
    while i < len(args):
        if args[i] in ("-h", "-help", "--help", "-?"):
            print(USAGE)
            return
        if args[i] in ("-c", "-command", "--command"):
            if command:
                print(USAGE)
                return 1
            i += 1
            command = args[i]
        else:
            if filename:
                print(USAGE)
                return 1
            filename = args[i]
        i += 1

    if command is None and filename is None:
        print(USAGE)
        return

    if command is not None:
        stream = sgml.reader.streams.StringStream(command)
        form = sgml.reader.read_one(sgml.rt, sgml.reader.INITIAL_MACROS, stream)
        sgml.interpreter.evaluate(sgml.rt, form, sgml.rt.stdlib_ns().scope())
        return 0

    if filename is not None:
        with open(filename, 'r') as f:
            stream = sgml.reader.streams.LineNumberingStream(sgml.reader.streams.FileStream(f))
            forms = sgml.reader.read_many(sgml.rt, sgml.reader.INITIAL_MACROS, stream)
            scope = sgml.rt.stdlib_ns().scope()
            sgml.interpreter._debug = True
            for form in sgml.rt.iter_elements(forms):
                sgml.interpreter.evaluate(sgml.rt, form, scope)
        return 0
    return 0


if __name__ == "__main__":
    sgml.interpreter._print_stack_trace = True
    sys.exit(main(sys.argv))
