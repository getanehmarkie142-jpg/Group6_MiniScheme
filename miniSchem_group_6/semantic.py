import sys
from lexer import LexError
from parser import (parse_source, ParseError, Number, Boolean, Symbol,
                    Quote, If, Lambda, Define, Let, Call)

# name: (min_args, max_args, [arg types], return type)
BUILTINS = {
    "+":     (2, None, ["num"], "num"),
    "-":     (2, None, ["num"], "num"),
    "*":     (2, None, ["num"], "num"),
    "/":     (2, None, ["num"], "num"),
    "=":     (2, 2, ["num"], "bool"),
    "<":     (2, 2, ["num"], "bool"),
    ">":     (2, 2, ["num"], "bool"),
    "cons":  (2, 2, ["any", "list"], "list"),
    "car":   (1, 1, ["list"], "any"),
    "cdr":   (1, 1, ["list"], "list"),
    "null?": (1, 1, ["list"], "bool"),
    "list":  (0, None, ["any"], "list"),
    "not":   (1, 1, ["any"], "bool"),
    "print": (1, 1, ["any"], "any"),
    "length": (1, 1, ["list"], "num"),
    "map":    (2, 2, ["func", "list"], "list"),
}


class Scope:
    """One level of the symbol table."""
    def __init__(self, parent=None):
        self.parent = parent
        self.names = {}

    def declare(self, name, info):
        self.names[name] = info

    def lookup(self, name):
        s = self
        while s is not None:
            if name in s.names:
                return s.names[name]
            s = s.parent
        return None


def datum_type(d):
    if isinstance(d, list):
        return "list"
    if isinstance(d, bool):
        return "bool"
    if isinstance(d, (int, float)):
        return "num"
    return "symbol"


def compatible(expected, actual):
    return expected == "any" or actual == "any" or expected == actual


def arity_text(mn, mx):
    if mx is None:
        return f"at least {mn}"
    if mn == mx:
        return f"{mn}"
    return f"{mn} to {mx}"


class Analyzer:
    def __init__(self):
        self.errors = []
        self.globals = Scope()
        for name in BUILTINS:
            self.globals.declare(name, {"type": "func", "builtin": True})

    def error(self, line, msg):
        self.errors.append(f"Line {line}: {msg}" if line else msg)

    def run(self, program):
        self.check_body(program.exprs, self.globals)
        return self.errors

    # declare all (define ...) names first, so functions can call
    # each other and themselves (recursion)
    def hoist(self, exprs, scope):
        for e in exprs:
            if isinstance(e, Define):
                if isinstance(e.value, Lambda):
                    scope.declare(e.name, {"type": "func",
                                           "arity": len(e.value.params)})
                else:
                    scope.declare(e.name, {"type": "any"})

    def check_body(self, exprs, scope):
        self.hoist(exprs, scope)
        t = "any"
        for e in exprs:
            t = self.check(e, scope)
        return t

    def check(self, node, scope):
        if isinstance(node, Number):
            return "num"
        if isinstance(node, Boolean):
            return "bool"
        if isinstance(node, Quote):
            return datum_type(node.datum)
        if isinstance(node, Symbol):
            info = scope.lookup(node.name)
            if info is None:
                self.error(node.line, f"undefined variable '{node.name}'")
                return "any"
            return info["type"]
        if isinstance(node, If):
            self.check(node.test, scope)
            a = self.check(node.then, scope)
            b = self.check(node.orelse, scope)
            return a if a == b else "any"
        if isinstance(node, Lambda):
            return self.check_lambda(node, scope)
        if isinstance(node, Define):
            return self.check_define(node, scope)
        if isinstance(node, Let):
            inner = Scope(scope)
            for b in node.bindings:
                t = self.check(b.value, scope)
                inner.declare(b.name, {"type": t})
            return self.check_body(node.body, inner)
        if isinstance(node, Call):
            return self.check_call(node, scope)
        return "any"

    def check_lambda(self, node, scope):
        inner = Scope(scope)
        seen = set()
        for p in node.params:
            if p in seen:
                self.error(0, f"duplicate parameter '{p}'")
            seen.add(p)
            inner.declare(p, {"type": "any"})
        self.check_body(node.body, inner)
        return "func"

    def check_define(self, node, scope):
        if isinstance(node.value, Lambda):
            scope.declare(node.name, {"type": "func",
                                      "arity": len(node.value.params)})
            self.check_lambda(node.value, scope)
        else:
            if node.name not in scope.names:
                scope.declare(node.name, {"type": "any"})
            t = self.check(node.value, scope)
            scope.declare(node.name, {"type": t})
        return "any"

    def check_call(self, node, scope):
        types = [self.check(a, scope) for a in node.args]
        n = len(node.args)
        f = node.func

        if isinstance(f, Symbol):
            info = scope.lookup(f.name)
            if info is None:
                self.error(f.line, f"undefined function '{f.name}'")
                return "any"
            if info.get("builtin"):
                return self.check_builtin(f.name, types, node.line)
            if info["type"] not in ("func", "any"):
                self.error(f.line,
                           f"'{f.name}' is a {info['type']}, not a function")
                return "any"
            arity = info.get("arity")
            if arity is not None and arity != n:
                self.error(node.line,
                           f"'{f.name}' expects {arity} argument(s) but got {n}")
            return "any"

        if isinstance(f, Lambda):
            self.check_lambda(f, scope)
            if len(f.params) != n:
                self.error(node.line,
                           f"lambda expects {len(f.params)} argument(s) but got {n}")
            return "any"

        ft = self.check(f, scope)
        if ft not in ("func", "any"):
            self.error(node.line, f"this is a {ft}, not a function")
        return "any"

    def check_builtin(self, name, types, line):
        mn, mx, arg_types, ret = BUILTINS[name]
        n = len(types)
        if n < mn or (mx is not None and n > mx):
            self.error(line, f"'{name}' expects {arity_text(mn, mx)} "
                             f"argument(s) but got {n}")
            return ret
        for i, t in enumerate(types):
            exp = arg_types[min(i, len(arg_types) - 1)]
            if not compatible(exp, t):
                self.error(line, f"'{name}' argument {i + 1} must be "
                                 f"{exp}, got {t}")
        return ret


def analyze_source(src):
    program = parse_source(src)
    a = Analyzer()
    errors = a.run(program)
    return program, a, errors


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            source = f.read()
    else:
        source = "(print (+ 1 2))"
    try:
        program, a, errors = analyze_source(source)
    except (LexError, ParseError) as e:
        print("Error:", e)
        sys.exit(1)

    if errors:
        print("Semantic errors:")
        for e in errors:
            print("  " + e)
        sys.exit(1)

    print("Semantic check passed.")
    print("Global symbol table:")
    for name, info in a.globals.names.items():
        if info.get("builtin"):
            continue
        extra = f" ({info['arity']} parameter(s))" if "arity" in info else ""
        print(f"  {name}: {info['type']}{extra}")