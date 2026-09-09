# persian_bidi_engine.py
import re
import unicodedata

# Unicode Bidirectional Control Characters
RLM = '\u200F'  # Right-to-Left Mark
LRM = '\u200E'  # Left-to-Right Mark
ALM = '\u061C'  # Arabic Letter Mark
LRI = '\u2066'  # Left-to-Right Isolate
RLI = '\u2067'  # Right-to-Left Isolate
FSI = '\u2068'  # First Strong Isolate
PDI = '\u2069'  # Pop Directional Isolate
ZWNJ = '\u200C' # Zero-Width Non-Joiner

PERSIAN_CHARS_REGEX = re.compile(r'[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]')
LATIN_CHARS_REGEX = re.compile(r'[a-zA-Z]')
CODE_FENCE_REGEX = re.compile(r'^(```|~~~| {4}|\t|#include|import |from |const |let |var |def |class |function )')

EN_TO_FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
FA_TO_EN_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')

ARABIC_TO_PERSIAN_MAP = {
    'ي': 'ی',
    'ى': 'ی',
    'ك': 'ک',
    'ة': 'ه',
    'ۀ': 'ه‌ی',
    'ـ': '',
}

def normalize_persian_chars(text: str) -> str:
    for ar, fa in ARABIC_TO_PERSIAN_MAP.items():
        text = text.replace(ar, fa)
    return text

def clean_redundant_bidi(text: str) -> str:
    """حذف علائم تکراری پشت سر هم"""
    text = re.sub(f'{LRM}+', LRM, text)
    text = re.sub(f'{RLM}+', RLM, text)
    text = re.sub(f'({RLM}{LRM})+', f'{RLM}{LRM}', text)
    text = re.sub(f'({LRM}{RLM})+', f'{LRM}{RLM}', text)
    return text

def is_persian_dominant(line: str) -> bool:
    persian_count = len(PERSIAN_CHARS_REGEX.findall(line))
    latin_count = len(LATIN_CHARS_REGEX.findall(line))
    if persian_count == 0:
        return False
    return persian_count >= latin_count or persian_count >= 3

def is_code_or_pure_ltr(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if CODE_FENCE_REGEX.match(stripped):
        return True
    persian_count = len(PERSIAN_CHARS_REGEX.findall(line))
    return persian_count == 0

def fix_inline_code_and_links(persian_line: str) -> str:
    """اصلاح کدهای درون‌خطی و لینک‌های مارک‌داون"""
    # 1. کدهای درون‌خطی مثل `code`
    def isolate_code(match):
        code_content = match.group(1)
        return f"{LRM}`{code_content}`{LRM}"
    
    line = re.sub(r'`([^`]+)`', isolate_code, persian_line)

    # 2. لینک‌های مارک‌داون مثل [عنوان](آدرس)
    def isolate_link(match):
        text = match.group(1)
        url = match.group(2)
        return f"[{text}]({LRM}{url}{LRM})"

    line = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', isolate_link, line)
    return line

def fix_embedded_english_terms(persian_line: str, use_isolates: bool = False) -> str:
    english_phrase_pattern = re.compile(
        r'(?<![a-zA-Z0-9_\-\./`\u200E])([a-zA-Z0-9_\-\./]+(?:[\s\t]+[a-zA-Z0-9_\-\./]+)*)(?![a-zA-Z0-9_\-\./`\u200E])'
    )

    def isolate_match(match):
        token = match.group(1)
        if token.isdigit():
            return token
        if not LATIN_CHARS_REGEX.search(token):
            return token
        if use_isolates:
            return f"{LRI}{token}{PDI}"
        else:
            return f"{LRM}{token}{LRM}"

    return english_phrase_pattern.sub(isolate_match, persian_line)

def fix_brackets_and_parentheses(text: str) -> str:
    def fix_parens(match):
        open_bracket = match.group(1)
        content = match.group(2)
        close_bracket = match.group(3)
        if LATIN_CHARS_REGEX.search(content):
            return f"{RLM}{open_bracket}{LRM}{content.strip(LRM)}{LRM}{close_bracket}{RLM}"
        return f"{open_bracket}{content}{close_bracket}"

    bracket_pattern = re.compile(r'([\(\[\{])([^\(\)\[\]\{\}]+)([\)\]\}])')
    return bracket_pattern.sub(fix_parens, text)

def fix_trailing_punctuation(line: str) -> str:
    stripped = line.rstrip()
    trailing_whitespace = line[len(stripped):]
    if not stripped:
        return line

    punctuation_chars = '.!؟?:;،,()[]{}»«"\'…'
    if stripped[-1] in punctuation_chars:
        if not stripped.endswith(RLM):
            return stripped + RLM + trailing_whitespace
    return line

def process_text_bidi(
    text: str,
    fix_english: bool = True,
    fix_punctuation: bool = True,
    fix_brackets: bool = True,
    normalize_chars: bool = True,
    convert_digits: str = 'none',
    use_isolates: bool = False
) -> str:
    if not text:
        return ""

    if normalize_chars:
        text = normalize_persian_chars(text)

    if convert_digits == 'to_persian':
        text = text.translate(EN_TO_FA_DIGITS)
    elif convert_digits == 'to_english':
        text = text.translate(FA_TO_EN_DIGITS)

    lines = text.split('\n')
    processed_lines = []

    for line in lines:
        if is_code_or_pure_ltr(line):
            processed_lines.append(line)
            continue

        processed_line = line

        # 1. کدهای درون‌خطی و لینک‌ها
        processed_line = fix_inline_code_and_links(processed_line)

        # 2. اصلاح پرانتزها و علائم احاطه‌کننده
        if fix_brackets:
            processed_line = fix_brackets_and_parentheses(processed_line)

        # 3. ایزوله‌سازی کلمات و عبارات انگلیسی داخل جمله فارسی
        if fix_english:
            processed_line = fix_embedded_english_terms(processed_line, use_isolates=use_isolates)

        # 4. تثبیت علامت انتهای خط
        if fix_punctuation:
            processed_line = fix_trailing_punctuation(processed_line)

        # پاک‌سازی علائم تکراری
        processed_line = clean_redundant_bidi(processed_line)

        # 5. هدایت جهت پاراگراف با RLM در ابتدای خط
        if not processed_line.startswith(RLM):
            # بررسی لیست‌ها یا فاصله‌های اول سطر (مثل - یا * یا شماره)
            list_match = re.match(r'^(\s*[-*•]|\s*\d+[\.\)])\s*', processed_line)
            if list_match:
                prefix = list_match.group(0)
                rest = processed_line[len(prefix):]
                processed_line = f"{RLM}{prefix}{RLM}{rest}"
            else:
                match_indent = re.match(r'^(\s*)', processed_line)
                indent = match_indent.group(1) if match_indent else ""
                rest = processed_line[len(indent):]
                processed_line = f"{indent}{RLM}{rest}"

        processed_lines.append(processed_line)

    return '\n'.join(processed_lines)

def visual_bidi_reorder(text: str) -> str:
    if not text:
        return ""
    lines = text.split('\n')
    result_lines = []
    for line in lines:
        if is_code_or_pure_ltr(line):
            result_lines.append(line)
            continue
        tokens = re.split(r'(\s+)', line)
        result_lines.append("".join(tokens[::-1]))
    return '\n'.join(result_lines)

def remove_bidi_marks(text: str) -> str:
    bidi_marks = [RLM, LRM, ALM, LRI, RLI, FSI, PDI]
    clean = text
    for mark in bidi_marks:
        clean = clean.replace(mark, '')
    return clean
