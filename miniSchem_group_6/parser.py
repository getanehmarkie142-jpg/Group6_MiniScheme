from dataclasses import dataclass, fields, is_dataclass
from lexer import tokenize, LexError


class ParseError(Exception):
    pass


# ---------- AST nodes ----------
@dataclass
class Number:
    value: object

@dataclass
class Boolean:
    value: bool

@dataclass
class Symbol:
    name: str
    line: int = 0

@dataclass
class Quote:
    datum: object

@dataclass
class If:
    test: object
    then: object
    orelse: object

@dataclass
class Lambda:
    params: list
    body: list

@dataclass
class Define:
    name: str
    value: object

@dataclass
class Binding:
    name: str
    value: object

@dataclass
class Let:
    bindings: list
    body: list

@dataclass
class Call:
    func: object
    args: list
    line: int = 0

@dataclass
class Program:
    exprs: list


# ---------- Parser ----------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def next(self):
        t = self.tokens[self.pos]
        if t.type != "EOF":
            self.pos += 1
        return t

    def at_close(self, open_tok):
        t = self.peek()
        if t.type == "EOF":
            raise ParseError(
                f"Line {open_tok.line}: missing ')' for '(' opened here")
        return t.type == "RPAREN"

    def expect_close(self, open_tok):
        if not self.at_close(open_tok):
            t = self.peek()
            raise ParseError(
                f"Line {t.line}: expected ')' but found {t.value!r}")
        self.next()

    # program -> expr*
    def parse_program(self):
        exprs = []
        while self.peek().type != "EOF":
            exprs.append(self.parse_expr())
        return Program(exprs)

    # expr -> atom | ( expr* )
    def parse_expr(self):
        t = self.next()
        if t.type == "NUMBER":
            return Number(t.value)
        if t.type == "BOOLEAN":
            return Boolean(t.value)
        if t.type == "SYMBOL":
            return Symbol(t.value, t.line)
        if t.type == "QUOTE":
            return Quote(self.parse_datum())
        if t.type == "LPAREN":
            return self.parse_list(t)
        if t.type == "RPAREN":
            raise ParseError(f"Line {t.line}: unexpected ')'")
        if t.type == "KEYWORD":
            raise ParseError(
                f"Line {t.line}: keyword '{t.value}' cannot be used as a value")
        raise ParseError(
            f"Line {t.line}: unexpected end of input (missing ')')")

    def parse_list(self, open_tok):
        t = self.peek()
        if t.type == "RPAREN":
            raise ParseError(f"Line {t.line}: empty expression ()")
        if t.type == "KEYWORD":
            self.next()
            return self.parse_special(t, open_tok)
        func = self.parse_expr()
        args = []
        while not self.at_close(open_tok):
            args.append(self.parse_expr())
        self.next()
        return Call(func, args, open_tok.line)

    def parse_special(self, kw, open_tok):
        name = kw.value

        if name == "if":
            test = self.parse_expr()
            then = self.parse_expr()
            orelse = self.parse_expr()
            self.expect_close(open_tok)
            return If(test, then, orelse)

        if name == "define":
            t = self.next()
            if t.type == "SYMBOL":                 # (define x expr)
                value = self.parse_expr()
                self.expect_close(open_tok)
                return Define(t.value, value)
            if t.type == "LPAREN":                 # (define (f a b) body...)
                name_tok = self.next()
                if name_tok.type != "SYMBOL":
                    raise ParseError(
                        f"Line {name_tok.line}: function name expected")
                params = self.parse_params(t)
                body = self.parse_body(open_tok)
                return Define(name_tok.value, Lambda(params, body))
            raise ParseError(f"Line {t.line}: bad 'define' form")

        if name == "lambda":
            t = self.next()
            if t.type != "LPAREN":
                raise ParseError(
                    f"Line {t.line}: lambda needs a parameter list")
            params = self.parse_params(t)
            body = self.parse_body(open_tok)
            return Lambda(params, body)

        if name == "let":
            t = self.next()
            if t.type != "LPAREN":
                raise ParseError(f"Line {t.line}: let needs a binding list")
            bindings = []
            while not self.at_close(t):
                b = self.next()
                if b.type != "LPAREN":
                    raise ParseError(
                        f"Line {b.line}: binding must look like (name value)")
                n = self.next()
                if n.type != "SYMBOL":
                    raise ParseError(f"Line {n.line}: variable name expected")
                v = self.parse_expr()
                self.expect_close(b)
                bindings.append(Binding(n.value, v))
            self.next()
            body = self.parse_body(open_tok)
            return Let(bindings, body)

        if name == "quote":
            d = self.parse_datum()
            self.expect_close(open_tok)
            return Quote(d)

        raise ParseError(f"Line {kw.line}: unknown keyword '{name}'")

    def parse_params(self, open_tok):
        params = []
        while not self.at_close(open_tok):
            t = self.next()
            if t.type != "SYMBOL":
                raise ParseError(
                    f"Line {t.line}: parameter must be a name, got {t.value!r}")
            params.append(t.value)
        self.next()
        return params

    def parse_body(self, open_tok):
        body = []
        while not self.at_close(open_tok):
            body.append(self.parse_expr())
        if not body:
            raise ParseError(f"Line {open_tok.line}: empty body")
        self.next()
        return body

    # quoted data: raw values and python lists
    def parse_datum(self):
        t = self.next()
        if t.type in ("NUMBER", "BOOLEAN", "SYMBOL", "KEYWORD"):
            return t.value
        if t.type == "QUOTE":
            return ["quote", self.parse_datum()]
        if t.type == "LPAREN":
            items = []
            while not self.at_close(t):
                items.append(self.parse_datum())
            self.next()
            return items
        raise ParseError(f"Line {t.line}: unexpected {t.value!r} in quote")


def parse_source(src):
    return Parser(tokenize(src)).parse_program()


# ---------- pretty printer ----------
def show(node, indent=0):
    pad = "  " * indent
    if not is_dataclass(node):
        print(pad + repr(node))
        return
    scalars, children = [], []
    for f in fields(node):
        if f.name == "line":
            continue
        v = getattr(node, f.name)
        if is_dataclass(v) or (isinstance(v, list) and v
                               and all(is_dataclass(x) for x in v)):
            children.append((f.name, v))
        else:
            scalars.append(f"{f.name}={v!r}")
    print(f"{pad}{type(node).__name__}({', '.join(scalars)})")
    for name, v in children:
        print(f"{pad}  {name}:")
        for item in (v if isinstance(v, list) else [v]):
            show(item, indent + 2)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            source = f.read()
    else:
        source = "(+ 1 (* 2 3))"
    try:
        show(parse_source(source))
    except (LexError, ParseError) as e:
        print("Error:", e)