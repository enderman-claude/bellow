# Bellow

A compiled, object-oriented language that doesn't care what your files are called.

## Design rules (so far)

- File types are declared only in `bellow.toml`. Source files never announce their type.
- A file missing from the manifest fails the build with a rude message.
- `yell` prints to stderr in caps; `scream` is the formatted print.
- Targets: Windows, Linux, macOS, plus UNIX, DOS, and others.
- Programs can be compiled, or run directly by the `bellow` runner without compiling.

## Status

Pre-alpha. The grammar does not exist yet. CI only checks the manifest.
