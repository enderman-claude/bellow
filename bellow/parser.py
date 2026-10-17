"""Parser for Bellow: source text -> AST. Stdlib only.

Blocks are matched by their closers. Expressions use a Pratt parser.
"""
import re
from dataclasses import dataclass, field


class ParseError(Exception):
    def __init__(self, line, message):
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message


# ---- AST: expressions -------------------------------------------------------

@dataclass
class Num:
    value: str

@dataclass
class Str:
    parts: list  # str pieces and Expr nodes (from {...} interpolation)

@dataclass
class Name:
    id: str

@dataclass
class Attr:
    obj: object
    name: str

@dataclass
class Call:
    func: object
    args: list

@dataclass
class BinOp:
    op: str
    left: object
    right: object

@dataclass
class Unary:
    op: str
    operand: object

@dataclass
class Length:
    operand: object


# ---- AST: statements and blocks --------------------------------------------

@dataclass
class Have:
    name: str
    value: object

@dataclass
class Assign:
    target: object
    value: object

@dataclass
class Give:
    value: object

@dataclass
class Yell:
    value: object

@dataclass
class Scream:
    value: object

@dataclass
class PrintStmt:
    theme: str
    value: object

@dataclass
class Syscall:
    call: object

@dataclass
class Field:
    name: str
    type: str

@dataclass
class ExprStmt:
    value: object

@dataclass
class Block:
    kind: str                 # kind | do | start | raw | when | again
    line: int
    name: str = None
    params: list = field(default_factory=list)  # (name, type)
    returns: str = None
    cond: object = None
    now: bool = False
    theme: str = None         # set from the closer
    body: list = field(default_factory=list)


# ---- tokens -----------------------------------------------------------------

TOKEN_RE = re.compile(
    r'\s*(?:(?P<num>\d+(?:\.\d+)?)|(?P<str>"(?:\\.|[^"\\])*")'
    r'|(?P<id>[A-Za-z_]\w*)|(?P<op>==|!=|<=|>=|[-+*/<>=().,]))'
)
BINOPS = {"or": 1, "and": 2, "==": 3, "!=": 3, "<": 3, ">": 3, "<=": 3, ">=": 3,
          "+": 4, "-": 4, "*": 5, "/": 5}
CLOSERS = {"thank you": "polite", "fuck you": "rude", "cool bye!": "impatient"}
PRINT_PREFIXES = {"please print": "polite", "damn print": "rude", "pt": "impatient"}


def tokenize(src, line):
    toks, pos = [], 0
    src = src.rstrip()
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise ParseError(line, f"UNKNOWN CHARACTER {src[pos:].lstrip()[:1]!r}. SPEAK PLAINLY")
        pos = m.end()
        if m.group("num"):
            toks.append(("num", m.group("num")))
        elif m.group("str"):
            toks.append(("str", m.group("str")[1:-1]))
        elif m.group("id"):
            w = m.group("id")
            toks.append(("op" if w in ("and", "or") else "id", w))
        else:
            toks.append(("op", m.group("op")))
    return toks


class _ExprParser:
    def __init__(self, toks, line):
        self.t, self.i, self.line = toks, 0, line

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self):
        tok = self.peek()
        if tok is None:
            raise ParseError(self.line, "UNFINISHED. WHAT WAS THAT?")
        self.i += 1
        return tok

    def expect(self, val):
        tok = self.take()
        if tok[1] != val:
            raise ParseError(self.line, f"EXPECTED {val!r}. READ BEFORE YOU WRITE")

    def expr(self, minbp=0):
        left = self.prefix()
        while True:
            tok = self.peek()
            if tok is None or tok[0] != "op" or tok[1] not in BINOPS or BINOPS[tok[1]] <= minbp:
                break
            self.take()
            left = BinOp(tok[1], left, self.expr(BINOPS[tok[1]]))
        return left

    def prefix(self):
        kind, val = self.take()
        if kind == "num":
            node = Num(val)
        elif kind == "str":
            node = Str(interpolate(val, self.line))
        elif kind == "id" and val == "length" and self.peek() == ("id", "of"):
            self.take()
            return Length(self.expr(6))
        elif kind == "id" and val == "not":
            return Unary("not", self.expr(6))
        elif kind == "id":
            node = Name(val)
        elif kind == "op" and val == "-":
            return Unary("-", self.expr(6))
        elif kind == "op" and val == "(":
            node = self.expr(0)
            self.expect(")")
        else:
            raise ParseError(self.line, f"UNEXPECTED {val!r}")
        return self.postfix(node)

    def postfix(self, node):
        while True:
            tok = self.peek()
            if tok == ("op", "("):
                self.take()
                args = []
                if self.peek() != ("op", ")"):
                    while True:
                        args.append(self.expr(0))
                        if self.peek() == ("op", ","):
                            self.take()
                            continue
                        break
                self.expect(")")
                node = Call(node, args)
            elif tok == ("op", "."):
                self.take()
                kind, name = self.take()
                if kind != "id":
                    raise ParseError(self.line, "A DOT NEEDS A NAME AFTER IT")
                node = Attr(node, name)
            else:
                return node


def parse_expr(text, line):
    p = _ExprParser(tokenize(text, line), line)
    node = p.expr(0)
    if p.peek() is not None:
        raise ParseError(line, f"LEFTOVER {p.peek()[1]!r}. ONE THING AT A TIME")
    return node


def interpolate(body, line):
    parts, buf, i = [], "", 0
    while i < len(body):
        if body[i] == "{":
            j = body.find("}", i)
            if j == -1:
                raise ParseError(line, "UNCLOSED BRACE IN STRING")
            if buf:
                parts.append(buf)
                buf = ""
            parts.append(parse_expr(body[i + 1:j], line))
            i = j + 1
        else:
            buf += body[i]
            i += 1
    if buf or not parts:
        parts.append(buf)
    return parts


HEADER_RE = re.compile(r"(\w+)\((.*)\)(?:\s+gives\s+(\w+))?$")
FIELD_RE = re.compile(r"(\w+) as (\w+)$")
HAVE_RE = re.compile(r"have (\w+) be (.+)$")
ASSIGN_RE = re.compile(r"(.+?) is (.+)$")


def _params(text, line):
    out = []
    for p in text.split(","):
        p = p.strip()
        if not p:
            continue
        m = FIELD_RE.match(p)
        if not m:
            raise ParseError(line, f"PARAMETER {p!r} NEEDS 'name as type'")
        out.append((m.group(1), m.group(2)))
    return out


def _open_block(s, line):
    if s == "start":
        return Block("start", line)
    if s == "raw":
        return Block("raw", line)
    if s.startswith("now do "):
        b = _do_header(s[len("now do "):], line)
        b.now = True
        return b
    if s.startswith("do "):
        return _do_header(s[3:], line)
    if s.startswith("kind "):
        return Block("kind", line, name=s[5:].strip())
    if s.startswith("when "):
        return Block("when", line, cond=parse_expr(s[5:], line))
    if s.startswith("again "):
        return Block("again", line, cond=parse_expr(s[6:], line))
    return None


def _do_header(text, line):
    m = HEADER_RE.match(text.strip())
    if not m:
        raise ParseError(line, "BAD FUNCTION HEADER. NAME(PARAMS) gives TYPE")
    return Block("do", line, name=m.group(1), params=_params(m.group(2), line),
                 returns=m.group(3))


def _statement(s, line):
    for prefix, theme in PRINT_PREFIXES.items():
        if s.startswith(prefix) and s[len(prefix):].lstrip().startswith("("):
            return PrintStmt(theme, parse_expr(s[len(prefix):], line))
    if s.startswith("have "):
        m = HAVE_RE.match(s)
        if not m:
            raise ParseError(line, "HAVE NEEDS 'have NAME be VALUE'")
        return Have(m.group(1), parse_expr(m.group(2), line))
    if s.startswith("give "):
        return Give(parse_expr(s[5:], line))
    if s.startswith("yell "):
        return Yell(parse_expr(s[5:], line))
    if s.startswith("scream "):
        return Scream(parse_expr(s[7:], line))
    if s.startswith("syscall "):
        call = parse_expr(s[8:], line)
        if not isinstance(call, Call):
            raise ParseError(line, "SYSCALL NEEDS A CALL, LIKE write(1, ...)")
        return Syscall(call)
    m = FIELD_RE.match(s)
    if m:
        return Field(m.group(1), m.group(2))
    m = ASSIGN_RE.match(s)
    if m:
        return Assign(parse_expr(m.group(1), line), parse_expr(m.group(2), line))
    return ExprStmt(parse_expr(s, line))


def parse_source(text):
    top, stack = [], []

    def add(node):
        (stack[-1].body if stack else top).append(node)

    for lineno, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith(("#", "//")):
            continue
        if s in CLOSERS:
            if not stack:
                raise ParseError(lineno, "STRAY CLOSER. WHAT ARE YOU THANKING?")
            stack.pop().theme = CLOSERS[s]
            continue
        block = _open_block(s, lineno)
        if block is not None:
            add(block)
            stack.append(block)
            continue
        add(_statement(s, lineno))

    if stack:
        raise ParseError(stack[-1].line, "UNCLOSED BLOCK. YOU STARTED IT, FINISH IT")
    return top
