# Bellow grammar (draft 0)

Not Python. Blocks are closed explicitly, statements end with `;`, and indentation means nothing.

## Keywords

| keyword     | role                                              |
|-------------|---------------------------------------------------|
| `kind`      | declares a type with fields and methods           |
| `do`        | declares a function                               |
| `please`    | marks a constructor inside a `kind`               |
| `now`       | marks a `do` for JIT when possible                |
| `have`      | immutable binding                                 |
| `give`      | return a value                                    |
| `when`      | conditional, closed by `thank you`                |
| `again`     | loop, closed by `thank you`                       |
| `raw`       | low-level block, allows `syscall`                 |
| `syscall`   | direct kernel call, per-target number mapping     |
| `yell`      | print one value to stderr, uppercased             |
| `scream`    | formatted print with `{}` interpolation to stdout |
| `thank you` | closes any block; the only block terminator       |

## Shape

    program     := item* ;
    item        := kind_decl | do_decl | main_decl ;
    kind_decl   := "kind" IDENT "{" field* ctor? method* "}" ;
    field       := IDENT ":" TYPE ";" ;
    ctor        := "please" IDENT "(" params? ")" block ;
    do_decl     := "now"? "do" IDENT "(" params? ")" ("->" TYPE)? block ;
    main_decl   := "do" "main" "(" ")" block ;
    block       := "{" stmt* "}" "thank you" ;
    stmt        := have_stmt | give_stmt | when_stmt | again_stmt
                 | yell_stmt | scream_stmt | raw_stmt | expr ";" ;
    have_stmt   := "have" IDENT "=" expr ";" ;
    give_stmt   := "give" expr ";" ;
    when_stmt   := "when" expr block ("else" block)? ;
    again_stmt  := "again" expr block ;
    yell_stmt   := "yell" expr ";" ;
    scream_stmt := "scream" STRING ";" ;
    raw_stmt    := "raw" "{" syscall_call* "}" "thank you" ;
    syscall_call:= "syscall" IDENT "(" args? ")" ";" ;

## Semantics notes

- `now` is a hint. The compiler JITs the function when it can. A `now` function that uses `raw` is compiled ahead of time, since the JIT cannot prove the syscalls are safe.
- `thank you` is a required terminator. Missing it is a compile error with a rude message, not a warning.
- `yell` uppercases its output and writes to stderr. `scream` writes to stdout.
- `syscall` names resolve through a per-target table. Linux, Windows, macOS, and DOS each have their own.
- Statements end with `;`. Newlines are whitespace.

## Example

    kind Greeter {
        name: str;
        please new(name: str) {
            self.name = name;
        } thank you
        do greet() -> str {
            give "hello, {self.name}";
        } thank you
    } thank you

    now do fast_len(s: str) -> int {
        give len(s);
    } thank you

    do main() {
        have g = Greeter.new("world");
        yell g.greet();
        scream "length: {fast_len(g.name)}";
        raw {
            syscall write(1, "raw write\n", 10);
            syscall exit(0);
        } thank you
    } thank you

## Politeness balance

Let `n[polite]` be the number of `thank you` terminators in a file, and `n[rude]` the number of `fuck you` terminators. Blocks inside a `now` function are not counted.

A file builds only if `n[rude] <= n[polite]`. Otherwise the build fails with a rude message on stderr.

Consequences:
- A file of only `now` functions has zero counted terminators, so it always passes. It can be 100% impatient.
- A file with `fuck you` and no `thank you` outside `now` fails.
- Politeness is per file, not per program. Each file is checked on its own.

## Theme per scope

Each block has a theme set by its terminator: polite (`thank you`) or rude (`fuck you`). A block's theme applies to its own direct child blocks.

- All direct child blocks inside one scope must share a theme. Mixing polite and rude children in one scope is a compile error ("the compiler is confused").
- A nested block may have a different theme from its parent. Each scope is checked on its own.
- `now` blocks are exempt from the theme check, as before.
- The file-level balance rule above still applies to the counts.

## Builtin variants

Core builtins like `print` have three forms: polite, rude, and impatient. A builtin must use the form matching its enclosing scope's theme. Impatient is the form used inside `now` blocks.

Variant names are placeholders until decided:
- polite: `please print(...)`
- rude: `damn print(...)`
- impatient: `print(...)` (bare)

Using the wrong form for the scope is a compile error.

## Now blocks

`now` blocks are not theme-checked. Instead they are budgeted:
- A `now` block may lean polite or lean rude, but not mix both within the same block.
- The compiler estimates the JIT cost of the block. If the block wastes too much time (for example, too many `raw` syscalls or repeated recompilation), it is rejected with a rude message, and the author must rewrite or drop `now`.
- Lean is decided by the dominant terminator of the block's direct children.
