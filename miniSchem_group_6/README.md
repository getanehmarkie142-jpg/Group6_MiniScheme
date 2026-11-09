# Group 6 – Functional MiniScheme Compiler

Mekdela Amba University – Compiler Design Semester Project

## Requirements
- Python 3.8 or newer
- No third-party Python packages

## Run the compiler

```bash
python main.py tests/test3.scm
```

Show generated Three-Address Code (TAC) before execution:

```bash
python main.py tests/test3.scm --tac
```

Run an individual phase:

```bash
python lexer.py tests/test3.scm
python parser.py tests/test3.scm
python semantic.py tests/test3.scm
```

## Project phases
1. `lexer.py` – lexical analysis / tokenization
2. `parser.py` – syntax analysis and AST construction
3. `semantic.py` – symbol table, scopes, arity and type checks
4. `codegen.py` – Three-Address Code generation
5. `vm.py` – executes the generated TAC
6. `main.py` – connects the compiler phases

## Supported language features
- Numbers and Boolean values
- `define`, `lambda`, `if`, `let`, and `quote`
- Function calls, recursion, and lexical closures
- Arithmetic and comparisons
- Lists: `list`, `cons`, `car`, `cdr`, `null?`
- `not` and `print`
- Additional higher-order/list utilities: `map` and `length`

Strings, `set!`, vectors, macros, and tail-call optimization are not implemented.

## Tests

```bash
python main.py tests/test3.scm  # factorial / recursion
python main.py tests/test4.scm  # lambda, closure, lists, let
python main.py tests/test5.scm  # Fibonacci, map, list length
```

Error tests (non-zero exit status is expected):

```bash
python main.py tests/bad1.scm
python main.py tests/bad2.scm
python main.py tests/bad_sem.scm
```
