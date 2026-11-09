# Group 6 MiniScheme Compiler – Code Audit Report

## Audit basis
The uploaded Python source archive was checked against the Group 6 Functional MiniScheme assignment guideline and the supplied MiniScheme project description.

## Baseline verification
- Python source compilation completed successfully with `python -m compileall -q .`.
- `tests/test3.scm` passed: factorial recursion printed `120`.
- `tests/test4.scm` passed: lambda, closure, let, recursion and list examples printed `25`, `7`, `15`, `15`, `(1 2 3)`, and `6`.
- `tests/bad1.scm` correctly reported a missing closing parenthesis.
- `tests/bad2.scm` correctly reported an empty expression.
- `tests/bad_sem.scm` correctly reported argument-count, undefined-function and type errors.
- Additional checks passed for multi-operand arithmetic, empty lists, `not`, lexical scope, closure capture, Fibonacci recursion and division-by-zero reporting.

## Findings and changes

### 1. Missing test file / inconsistent documented feature list
The supplied project description referred to `tests/test5.scm` and described Fibonacci, `map`, and list length results, but the uploaded source archive did not contain `tests/test5.scm`. The original implementation also did not provide `map` or `length` as built-ins.

**Changes made:**
- Added `map` and `length` to the semantic built-in table.
- Added `map` and `length` to the compiler's primitive operation set.
- Implemented runtime behavior for `map` (including use with closures and lambda functions) and `length`.
- Added `tests/test5.scm`.

### 2. Documentation
Added this `README.md` with setup, run commands, architecture, supported features and tests.

## Verification after changes
All tests below passed after the changes:

| Test | Expected / observed output | Result |
|---|---|---|
| `test3.scm` | `120` | PASS |
| `test4.scm` | `25`, `7`, `15`, `15`, `(1 2 3)`, `6` | PASS |
| `test5.scm` | `55`, `(1 4 9 16)`, `4` | PASS |
| `bad1.scm` | Missing `)` syntax error | PASS |
| `bad2.scm` | Empty expression syntax error | PASS |
| `bad_sem.scm` | Semantic errors reported | PASS |
| Higher-order `map` with closure | `(6 7 8)` | PASS |
| Invalid `map` argument type | Semantic type error | PASS |
| Division by zero | Runtime error reported | PASS |

## Remaining recommendations
These are possible future improvements, not confirmed assignment failures:
- Add automated regression tests for every built-in and grammar form.
- Improve command-line handling for missing or unreadable source files.
- Add duplicate-definition checks if required by the instructor's language rules.
- Consider an AST visualizer or improved source-code error highlighting as optional presentation enhancements.
- Confirm with the instructor whether the optional `map` and `length` extensions should remain in the final submission.

## Scope note
The required assignment features remain the priority: Scanner, Parser/AST, Semantic Analysis, TAC Code Generation, Virtual Machine execution, lambda expressions, recursion and list operations. The added `map` and `length` functions are optional extensions intended to make the supplied project description's test5 example executable.
