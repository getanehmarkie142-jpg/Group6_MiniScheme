
import sys
from lexer import LexError
from parser import ParseError
from semantic import analyze_source
from codegen import CodeGen, format_program
from vm import VM, VMError


def main():
    args = sys.argv[1:]
    show_tac = "--tac" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print("Usage: python main.py <file.scm> [--tac]")
        return 1

    with open(files[0], encoding="utf-8") as f:
        source = f.read()

    try:
        program, analyzer, errors = analyze_source(source)
    except (LexError, ParseError) as e:
        print("Error:", e)
        return 1

    if errors:
        print("Semantic errors:")
        for e in errors:
            print("  " + e)
        return 1

    funcs = CodeGen().generate(program)

    if show_tac:
        print("=== Three-Address Code ===")
        print(format_program(funcs))
        print("=== Output ===")

    try:
        VM(funcs).run()
    except VMError as e:
        print("Runtime error:", e)
        return 1
    except RecursionError:
        print("Runtime error: recursion too deep")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())