import re
import sys

KEYWORDS = {"define", "lambda", "if", "let", "quote"}


class LexError(Exception):
    pass


class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"{self.type:8} {self.value!r:12} (line {self.line})"


TOKEN_SPEC = [
    ("COMMENT",  r";[^\n]*"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t\r]+"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("QUOTE",    r"'"),
    ("BOOLEAN",  r"#[tf](?=[\s()';]|$)"),
    ("NUMBER",   r"[+-]?(?:\d+\.\d+|\d+|\.\d+)(?=[\s()';]|$)"),
    ("SYMBOL",   r"[^\s()';#\"][^\s()';\"]*"),
    ("MISMATCH", r"."),
]

MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))


def tokenize(src):
    tokens = []
    line = 1
    for m in MASTER.finditer(src):
        kind = m.lastgroup
        text = m.group()
        if kind == "NEWLINE":
            line += 1
        elif kind in ("SKIP", "COMMENT"):
            continue
        elif kind == "MISMATCH":
            raise LexError(f"Line {line}: unexpected character {text!r}")
        elif kind == "NUMBER":
            value = float(text) if "." in text else int(text)
            tokens.append(Token("NUMBER", value, line))
        elif kind == "BOOLEAN":
            tokens.append(Token("BOOLEAN", text == "#t", line))
        elif kind == "SYMBOL":
            if text in KEYWORDS:
                tokens.append(Token("KEYWORD", text, line))
            else:
                tokens.append(Token("SYMBOL", text, line))
        else:
            tokens.append(Token(kind, text, line))
    tokens.append(Token("EOF", None, line))
    return tokens


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            source = f.read()
    else:
        source = "(+ 1 (* 2 3))"
    try:
        for t in tokenize(source):
            print(t)
    except LexError as e:
        print("Lexical error:", e)