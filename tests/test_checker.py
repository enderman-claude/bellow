import unittest

from bellow.checker import check_source


def msgs(src):
    return [p.message for p in check_source(src)]


class CheckerTests(unittest.TestCase):
    def test_valid_polite(self):
        self.assertEqual(msgs("kind A\n    do x()\n    thank you\nthank you\n"), [])

    def test_mixed_siblings_rejected(self):
        src = "start\n    do a()\n    thank you\n    do b()\n    fuck you\nthank you\n"
        self.assertTrue(any("MIXED THEMES" in m for m in msgs(src)))

    def test_print_must_match_theme(self):
        self.assertTrue(any("PRINT FORM" in m for m in msgs("start\n    pt(hi)\nthank you\n")))

    def test_impatient_print_ok_in_now(self):
        self.assertEqual(msgs("now do f()\n    pt(x)\ncool bye!\n"), [])

    def test_cool_bye_needs_now(self):
        self.assertTrue(any("ONLY CLOSES NOW" in m for m in msgs("do a()\ncool bye!\n")))

    def test_now_must_close_cool_bye(self):
        self.assertTrue(any("COOL BYE" in m for m in msgs("now do f()\nfuck you\n")))

    def test_raw_not_allowed_in_now(self):
        src = "now do f()\n    raw\n        syscall exit(0)\n    thank you\ncool bye!\n"
        self.assertTrue(any("RAW CANNOT BE JIT" in m for m in msgs(src)))

    def test_syscall_needs_raw(self):
        self.assertTrue(any("SYSCALL OUTSIDE" in m for m in msgs("start\n    syscall exit(0)\nthank you\n")))

    def test_balance_rejects_too_rude(self):
        self.assertTrue(any("TOO RUDE" in m for m in msgs("do a()\nfuck you\n")))

    def test_unclosed_block(self):
        self.assertTrue(any("UNCLOSED" in m for m in msgs("start\n")))

    def test_stray_closer(self):
        self.assertTrue(any("STRAY CLOSER" in m for m in msgs("thank you\n")))


if __name__ == "__main__":
    unittest.main()
