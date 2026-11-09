from parser import (Number, Boolean, Symbol, Quote, If, Lambda,
                    Define, Let, Call)

PRIMS = {"+", "-", "*", "/", "=", "<", ">",
         "cons", "car", "cdr", "null?", "list", "not", "print",
         "length", "map"}
ARITH = {"+", "-", "*", "/"}
INFIX = {"+", "-", "*", "/", "=", "<", ">"}


def show_value(v):
    """How a runtime value is displayed."""
    if v is True:
        return "#t"
    if v is False:
        return "#f"
    if v is None:
        return "void"
    if isinstance(v, list):
        return "(" + " ".join(show_value(x) for x in v) + ")"
    return str(v)


class Const:
    """A literal value inside TAC (variables are plain strings)."""
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        v = self.value
        if isinstance(v, str):
            return "'" + v
        if isinstance(v, list):
            return "'" + show_value(v)
        return show_value(v)


class Func:
    def __init__(self, name, params, code):
        self.name = name
        self.params = params
        self.code = code


class CodeGen:
    def __init__(self):
        self.funcs = {}
        self.used = set()
        self.labels = 0
        self.lambdas = 0
        self.code = []
        self.temps = 0
        self.scopes = [set()]

    # ---------- helpers ----------
    def new_temp(self):
        self.temps += 1
        return f"%t{self.temps}"

    def new_label(self):
        self.labels += 1
        return f"L{self.labels}"

    def emit(self, *ins):
        self.code.append(ins)

    def is_user(self, name):
        return any(name in s for s in self.scopes)

    def unique(self, base):
        name, n = base, 1
        while name in self.used:
            n += 1
            name = f"{base}_{n}"
        self.used.add(name)
        return name

    def hoist(self, exprs):
        for e in exprs:
            if isinstance(e, Define):
                self.scopes[-1].add(e.name)

    # ---------- entry ----------
    def generate(self, program):
        self.used.add("main")
        self.code, self.temps = [], 0
        self.hoist(program.exprs)
        for e in program.exprs:
            self.gen(e)
        self.emit("ret", Const(None))
        result = {"main": Func("main", [], self.code)}
        result.update(self.funcs)
        return result

    def gen_function(self, fname, params, body):
        saved = (self.code, self.temps)
        self.code, self.temps = [], 0
        self.scopes.append(set(params))
        self.hoist(body)
        result = None
        for e in body:
            result = self.gen(e)
        self.emit("ret", result)
        self.scopes.pop()
        self.funcs[fname] = Func(fname, params, self.code)
        self.code, self.temps = saved

    # ---------- expressions ----------
    def gen(self, node):
        if isinstance(node, Number):
            return Const(node.value)
        if isinstance(node, Boolean):
            return Const(node.value)
        if isinstance(node, Quote):
            return Const(node.datum)
        if isinstance(node, Symbol):
            return node.name
        if isinstance(node, If):
            return self.gen_if(node)
        if isinstance(node, Lambda):
            return self.gen_lambda(node)
        if isinstance(node, Define):
            return self.gen_define(node)
        if isinstance(node, Let):
            return self.gen_let(node)
        if isinstance(node, Call):
            return self.gen_call(node)
        raise ValueError(f"cannot generate code for {node!r}")

    def gen_if(self, node):
        test = self.gen(node.test)
        res = self.new_temp()
        l_else, l_end = self.new_label(), self.new_label()
        self.emit("iffalse", test, l_else)
        a = self.gen(node.then)
        self.emit("mov", res, a)
        self.emit("jmp", l_end)
        self.emit("label", l_else)
        b = self.gen(node.orelse)
        self.emit("mov", res, b)
        self.emit("label", l_end)
        return res

    def gen_lambda(self, node):
        self.lambdas += 1
        fname = self.unique(f"lambda_{self.lambdas}")
        self.gen_function(fname, node.params, node.body)
        dst = self.new_temp()
        self.emit("closure", dst, fname)
        return dst

    def gen_define(self, node):
        self.scopes[-1].add(node.name)
        if isinstance(node.value, Lambda):
            fname = self.unique(node.name)
            self.gen_function(fname, node.value.params, node.value.body)
            self.emit("closure", node.name, fname)
        else:
            v = self.gen(node.value)
            self.emit("mov", node.name, v)
        return node.name

    def gen_let(self, node):
        # (let ((a 1) (b 2)) body)  ==  ((lambda (a b) body) 1 2)
        lam = Lambda([b.name for b in node.bindings], node.body)
        return self.gen_call(Call(lam, [b.value for b in node.bindings], 0))

    def gen_call(self, node):
        f = node.func
        if (isinstance(f, Symbol) and f.name in PRIMS
                and not self.is_user(f.name)):
            args = [self.gen(a) for a in node.args]
            return self.gen_prim(f.name, args)
        fn = self.gen(f)
        args = [self.gen(a) for a in node.args]
        dst = self.new_temp()
        self.emit("call", dst, fn, args)
        return dst

    def gen_prim(self, name, args):
        if name in ARITH and len(args) > 2:      # (+ 1 2 3) -> (1+2)+3
            acc = args[0]
            for nxt in args[1:]:
                t = self.new_temp()
                self.emit("prim", t, name, [acc, nxt])
                acc = t
            return acc
        dst = self.new_temp()
        self.emit("prim", dst, name, args)
        return dst


# ---------- printing the TAC ----------
def format_instr(ins):
    op = ins[0]
    if op == "label":
        return f"{ins[1]}:"
    if op == "mov":
        return f"  {ins[1]} = {ins[2]}"
    if op == "closure":
        return f"  {ins[1]} = closure {ins[2]}"
    if op == "jmp":
        return f"  goto {ins[1]}"
    if op == "iffalse":
        return f"  if_false {ins[1]} goto {ins[2]}"
    if op == "ret":
        return f"  return {ins[1]}"
    if op == "call":
        args = ", ".join(str(a) for a in ins[3])
        return f"  {ins[1]} = call {ins[2]}({args})"
    if op == "prim":
        dst, name, args = ins[1], ins[2], ins[3]
        if name in INFIX and len(args) == 2:
            sym = "==" if name == "=" else name
            return f"  {dst} = {args[0]} {sym} {args[1]}"
        return f"  {dst} = {name}({', '.join(str(a) for a in args)})"
    return f"  {ins}"


def format_program(funcs):
    lines = []
    for f in funcs.values():
        lines.append(f"func {f.name}({', '.join(f.params)}):")
        for ins in f.code:
            lines.append(format_instr(ins))
        lines.append("")
    return "\n".join(lines)