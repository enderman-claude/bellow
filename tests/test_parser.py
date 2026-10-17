import os
import unittest

from bellow.parser import (Attr, Block, Call, BinOp, Length, Name, Num, ParseError,
                           PrintStmt, Str, Syscall, parse_expr, parse_source)

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "examples", "main.exe")


class ExprTests(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(parse_expr("1 + 2 * 3", 1),
                         BinOp("+", Num("1"), BinOp("*", Num("2"), Num("3"))))

    def test_call_and_attr(self):
        self.assertEqual(parse_expr('Greeter.new("world")', 1),
                         Call(Attr(Name("Greeter"), "new"), [Str(["world"])]))

    def test_length_of(self):
        self.assertEqual(parse_expr("length of s", 1), Length(Name("s")))

    def test_interpolation(self):
        self.assertEqual(parse_expr('"a{x}b"', 1), Str(["a", Name("x"), "b"]))

    def test_bad_expression(self):
        with self.assertRaises(ParseError):
            parse_expr("1 +", 1)


class SourceTests(unittest.TestCase):
    def test_example_structure(self):
        with open(EXAMPLE, encoding="utf-8") as fh:
            top = parse_source(fh.read())
        self.assertEqual([b.kind for b in top], ["kind", "do", "start"])
        self.assertTrue(top[1].now)
        self.assertEqual(top[1].theme, "impatient")
        start = top[2]
        self.assertEqual(start.theme, "polite")
        self.assertIsInstance(start.body[1], PrintStmt)
        raw = start.body[2]
        self.assertIsInstance(raw, Block)
        self.assertIsInstance(raw.body[0], Syscall)

    def test_unclosed_block(self):
        with self.assertRaises(ParseError):
            parse_source("start\n")

    def test_stray_closer(self):
        with self.assertRaises(ParseError):
            parse_source("thank you\n")

    def test_function_header(self):
        top = parse_source("do new(name as text) gives text\nthank you\n")
        self.assertEqual(top[0].name, "new")
        self.assertEqual(top[0].params, [("name", "text")])
        self.assertEqual(top[0].returns, "text")


if __name__ == "__main__":
    unittest.main()
