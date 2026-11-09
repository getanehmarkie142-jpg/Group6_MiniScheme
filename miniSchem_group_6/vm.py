import sys
from codegen import Const, PRIMS, ARITH, show_value

sys.setrecursionlimit(20000)


class VMError(Exception):
    pass


class Frame:
    """Variables of one function call. 'parent' gives lexical scoping."""
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent


class Closure:
    """A function + the frame where it was created (this makes closures work)."""
    def __init__(self, func, env):
        self.func = func
        self.env = env

    def __str__(self):
        return f"#<procedure {self.func.name}>"


class Builtin:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"#<builtin {self.name}>"


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


class VM:
    def __init__(self, funcs):
        self.funcs = funcs
        self.labels = {}
        for name, f in funcs.items():
            self.labels[name] = {ins[1]: i for i, ins in enumerate(f.code)
                                 if ins[0] == "label"}

    def run(self):
        return self.exec(self.funcs["main"], Frame())

    # operand -> value
    def value(self, frame, operand):
        if isinstance(operand, Const):
            return operand.value
        f = frame
        while f is not None:
            if operand in f.vars:
                return f.vars[operand]
            f = f.parent
        if operand in PRIMS:
            return Builtin(operand)
        raise VMError(f"undefined variable '{operand}'")

    def exec(self, func, frame):
        code = func.code
        labels = self.labels[func.name]
        pc = 0
        while pc < len(code):
            ins = code[pc]
            op = ins[0]
            pc += 1
            if op == "label":
                continue
            elif op == "mov":
                frame.vars[ins[1]] = self.value(frame, ins[2])
            elif op == "closure":
                frame.vars[ins[1]] = Closure(self.funcs[ins[2]], frame)
            elif op == "jmp":
                pc = labels[ins[1]]
            elif op == "iffalse":
                if self.value(frame, ins[1]) is False:
                    pc = labels[ins[2]]
            elif op == "prim":
                args = [self.value(frame, a) for a in ins[3]]
                frame.vars[ins[1]] = self.prim(ins[2], args)
            elif op == "call":
                fn = self.value(frame, ins[2])
                args = [self.value(frame, a) for a in ins[3]]
                frame.vars[ins[1]] = self.apply(fn, args)
            elif op == "ret":
                return self.value(frame, ins[1])
        return None

    def apply(self, fn, args):
        if isinstance(fn, Builtin):
            return self.prim(fn.name, args)
        if not isinstance(fn, Closure):
            raise VMError(f"{show_value(fn)} is not a function")
        params = fn.func.params
        if len(params) != len(args):
            raise VMError(f"{fn.func.name} expects {len(params)} "
                          f"argument(s) but got {len(args)}")
        frame = Frame(fn.env)
        for p, v in zip(params, args):
            frame.vars[p] = v
        return self.exec(fn.func, frame)

    def prim(self, name, a):
        try:
            return self._prim(name, a)
        except ValueError:
            raise VMError(f"wrong number of arguments for '{name}'")

    def _prim(self, name, a):
        if name in ARITH or name in ("=", "<", ">"):
            x, y = a
            if not (is_num(x) and is_num(y)):
                raise VMError(f"'{name}' needs numbers, got "
                              f"{show_value(x)} and {show_value(y)}")
            if name == "+":
                return x + y
            if name == "-":
                return x - y
            if name == "*":
                return x * y
            if name == "/":
                if y == 0:
                    raise VMError("division by zero")
                if isinstance(x, int) and isinstance(y, int) and x % y == 0:
                    return x // y
                return x / y
            if name == "=":
                return x == y
            if name == "<":
                return x < y
            return x > y
        if name == "cons":
            x, y = a
            if not isinstance(y, list):
                raise VMError("'cons' second argument must be a list")
            return [x] + y
        if name == "car":
            (x,) = a
            if not isinstance(x, list) or not x:
                raise VMError("'car' needs a non-empty list")
            return x[0]
        if name == "cdr":
            (x,) = a
            if not isinstance(x, list) or not x:
                raise VMError("'cdr' needs a non-empty list")
            return x[1:]
        if name == "null?":
            (x,) = a
            return isinstance(x, list) and len(x) == 0
        if name == "list":
            return list(a)
        if name == "length":
            (x,) = a
            if not isinstance(x, list):
                raise VMError("'length' needs a list")
            return len(x)
        if name == "map":
            fn, values = a
            if not isinstance(values, list):
                raise VMError("'map' second argument must be a list")
            return [self.apply(fn, [value]) for value in values]
        if name == "not":
            (x,) = a
            return x is False
        if name == "print":
            (x,) = a
            print(show_value(x))
            return x
        raise VMError(f"unknown operation '{name}'")