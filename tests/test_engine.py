import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'clipboard_tool'))

import unittest
from persian_bidi_engine import (
    process_text_bidi,
    visual_bidi_reorder,
    remove_bidi_marks,
    is_code_or_pure_ltr,
    RLM,
    LRM,
    LRI,
    PDI
)

class TestPersianBidiEngine(unittest.TestCase):
    def test_pure_english_unaltered(self):
        code_line = "const greeting = 'hello world';"
        result = process_text_bidi(code_line)
        self.assertEqual(result, code_line, "Pure English / code should remain unchanged")

    def test_persian_anchored_with_rlm(self):
        persian_line = "سلام دنیا"
        result = process_text_bidi(persian_line)
        self.assertTrue(result.startswith(RLM), "Persian line must start with RLM")
        self.assertEqual(remove_bidi_marks(result), persian_line)

    def test_embedded_english_isolated(self):
        mixed = "دستور npm run dev را اجرا کنید."
        result = process_text_bidi(mixed)
        self.assertIn(f"{LRM}npm run dev{LRM}", result)
        self.assertTrue(result.endswith(RLM))

    def test_brackets_around_english(self):
        text = "برنامه (Google Antigravity) عالی است."
        result = process_text_bidi(text)
        self.assertIn(f"{RLM}({LRM}Google Antigravity{LRM}){RLM}", result)

    def test_arabic_char_normalization(self):
        arabic_text = "كتاب يوسف"
        result = process_text_bidi(arabic_text)
        clean = remove_bidi_marks(result)
        self.assertEqual(clean, "کتاب یوسف")

    def test_multiline_mixed_document(self):
        doc = "مقدمه و راهنمای نصب\nبرای نصب کتابخانه دستور زیر را وارد کنید:\nnpm install axios\nسپس برنامه را اجرا نمایید."
        result = process_text_bidi(doc)
        lines = result.split('\n')
        self.assertTrue(lines[0].startswith(RLM))
        self.assertTrue(lines[1].startswith(RLM))
        self.assertFalse(lines[2].startswith(RLM), "Pure terminal command line should NOT have RLM")
        self.assertTrue(lines[3].startswith(RLM))

if __name__ == '__main__':
    unittest.main()
