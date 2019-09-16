import os
import sys

import sgml.interpreter
import sgml.reader
import sgml.rt

USAGE = "Usage: python3 -m sgml.main [ -c <command> ] | [filename]"


def bootstrap():
    env = sgml.rt.base_env()
    with open(os.path.join(os.path.dirname(__file__), "stdlib.sgml")) as f:
        stream = sgml.reader.streams.LineNumberingStream(sgml.reader.streams.FileStream(f))
        forms = sgml.reader.read_many(sgml.reader.INITIAL_MACROS, stream)
        for form in sgml.rt.iter_elements(forms):
            sgml.interpreter.evaluate(sgml.rt, form, env)
    return sgml.rt, env


def main(args):
    i = 1
    command = None
    filename = None
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
        form = sgml.reader.read_one(sgml.reader.INITIAL_MACROS, stream)
        rt, env = bootstrap()
        sgml.interpreter.evaluate(rt, form, env)
        return 0

    if filename is not None:
        with open(filename, 'r') as f:
            stream = sgml.reader.streams.LineNumberingStream(sgml.reader.streams.FileStream(f))
            forms = sgml.reader.read_many(sgml.reader.INITIAL_MACROS, stream)
            rt, env = bootstrap()
            for form in rt.iter_elements(forms):
                sgml.interpreter.evaluate(rt, form, env)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
