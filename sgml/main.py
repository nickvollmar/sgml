import sys
import sgml.interpreter
import sgml.reader
import sgml.rt as rt


def main(args):
    i = 0
    command = None
    filename = None
    while i < len(args):
        if args[i] in ("-c", "-command", "--command"):
            i += 1
            command = args[i]
        else:
            filename = args[i]
        i += 1

    if command is not None:
        stream = sgml.reader.StringStream(command)
        form = sgml.reader.read_one(sgml.reader.INITIAL_MACROS, stream)
        result = sgml.interpreter.evaluate(form, rt.base_env())
        if result is not None:
            print(rt.as_string(result))
        return 0

    if filename is not None:
        with open(filename, 'r') as f:
            stream = sgml.reader.LineNumberingStream(sgml.reader.FileStream(f))
            forms = sgml.reader.read_many(sgml.reader.INITIAL_MACROS, stream)
            env = rt.base_env()
            for form in rt.iter_elements(forms):
                result = sgml.interpreter.evaluate(form, env)
                if result is not None:
                    print(rt.as_string(result))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
