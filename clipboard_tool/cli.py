# cli.py
import sys
import argparse
from persian_bidi_engine import process_text_bidi, visual_bidi_reorder, remove_bidi_marks
from clipboard_helper import get_clipboard_text, set_clipboard_text

def main():
    parser = argparse.ArgumentParser(description="ابزار خط فرمان اصلاح و راست‌چین‌سازی هوشمند متن فارسی")
    parser.add_argument("text", nargs="?", default=None, help="متن ورودی جهت اصلاح")
    parser.add_argument("-c", "--clipboard", action="store_true", help="خواندن و اصلاح مستقیم متن کلیپ‌بورد")
    parser.add_argument("-v", "--visual", action="store_true", help="استفاده از حالت بازچینی بصری")
    parser.add_argument("-s", "--strip", action="store_true", help="حذف تمام علائم BiDi یونیکد")
    parser.add_argument("-i", "--input-file", help="مسیر فایل ورودی")
    parser.add_argument("-o", "--output-file", help="مسیر فایل خروجی")

    args = parser.parse_args()

    content = ""
    if args.clipboard:
        content = get_clipboard_text()
    elif args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.text:
        content = args.text
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(0)

    if args.strip:
        res = remove_bidi_marks(content)
    elif args.visual:
        res = visual_bidi_reorder(content)
    else:
        res = process_text_bidi(content)

    if args.clipboard:
        set_clipboard_text(res)
        print("✓ متن کلیپ‌بورد با موفقیت اصلاح شد.")
    elif args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(res)
        print(f"✓ خروجی در {args.output_file} ذخیره شد.")
    else:
        # چاپ امن خروجی
        sys.stdout.buffer.write(res.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")

if __name__ == "__main__":
    main()
