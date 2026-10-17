# Bellow

A compiled, object-oriented language that doesn't care what your files are called.

## Design rules (so far)

- Every source file has a sibling manifest, `<file>.bellow.toml`, that declares its type. The source file itself carries no type information.
- A source file with no sibling manifest fails the build with a rude message.
- Output binaries are ordinary executables for their target (ELF, PE, Mach-O). No polyglots in the output.
- `yell` prints to stderr in caps; `scream` is the formatted print.
- Targets: Windows, Linux, macOS, plus UNIX, DOS, and others.
- Programs can be compiled, or run directly by the `bellow` runner without compiling.

## Status

Pre-alpha. The grammar and CLI do not exist yet. CI only validates the example manifests.
