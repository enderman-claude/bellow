"""Structural checks for Bellow source.

Themes: polite (closed by `thank you`), rude (`fuck you`), impatient (`cool bye!`).
Impatient is only valid on `now do` blocks and must be JIT-compilable (no raw).
"""
from dataclasses import dataclass, field

POLITE, RUDE, IMPATIENT = "polite", "rude", "impatient"
CLOSERS = {"thank you": POLITE, "fuck you": RUDE, "cool bye!": IMPATIENT}
PRINT_FORMS = {"please print(": POLITE, "damn print(": RUDE, "pt(": IMPATIENT}
NOW_OPENER = "now do "


@dataclass
class Frame:
    line: int
    now: bool
    children: list = field(default_factory=list)
    prints: list = field(default_factory=list)  # (line, theme)


@dataclass
class Problem:
    line: int  # 0 means file-level
    message: str


def _is_opener(s):
    return s == "raw" or s == "start" or s.startswith(("kind ", "do ", "when ", "again "))


def check_source(text):
    problems = []

    def err(line, msg):
        problems.append(Problem(line, msg))

    stack = []
    polite = rude = 0

    for lineno, raw_line in enumerate(text.splitlines(), 1):
        s = raw_line.strip()
        if not s or s.startswith(("#", "//")):
            continue

        if s in CLOSERS:
            if not stack:
                err(lineno, "STRAY CLOSER. WHAT ARE YOU THANKING?")
                continue
            frame = stack.pop()
            theme = CLOSERS[s]
            if frame.now and theme != IMPATIENT:
                err(lineno, "NOW BLOCK MUST CLOSE WITH COOL BYE!")
            if theme == IMPATIENT and not frame.now:
                err(lineno, "COOL BYE! ONLY CLOSES NOW BLOCKS")
            for pline, ptheme in frame.prints:
                if ptheme != theme:
                    err(pline, f"PRINT FORM DOES NOT FIT THIS {theme.upper()} BLOCK")
            if len(set(frame.children)) > 1:
                err(frame.line, "MIXED THEMES IN ONE SCOPE. PICK A SIDE")
            if stack:
                stack[-1].children.append(theme)
            impatient_context = frame.now or any(f.now for f in stack)
            if not impatient_context:
                if theme == POLITE:
                    polite += 1
                elif theme == RUDE:
                    rude += 1
            continue

        if s.startswith(NOW_OPENER):
            stack.append(Frame(lineno, now=True))
            continue

        if s == "raw":
            if any(f.now for f in stack):
                err(lineno, "RAW CANNOT BE JIT. KEEP IT OUT OF NOW BLOCKS")
            stack.append(Frame(lineno, now=False))
            continue

        if _is_opener(s):
            stack.append(Frame(lineno, now=False))
            continue

        if s.startswith("syscall "):
            if not any(f.line and f.now is False and _raw_line(text, f.line) for f in stack):
                err(lineno, "SYSCALL OUTSIDE A RAW BLOCK")
            continue

        for form, theme in PRINT_FORMS.items():
            if s.startswith(form):
                if stack:
                    stack[-1].prints.append((lineno, theme))
                else:
                    err(lineno, "PRINT OUTSIDE A BLOCK")
                break

    for frame in stack:
        err(frame.line, "UNCLOSED BLOCK. YOU STARTED IT, FINISH IT")

    if rude > polite:
        err(0, f"TOO RUDE: {rude} FUCK YOU, {polite} THANK YOU. ADD MANNERS")

    return problems


def _raw_line(text, lineno):
    return text.splitlines()[lineno - 1].strip() == "raw"
