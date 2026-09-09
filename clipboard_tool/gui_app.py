# gui_app.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from persian_bidi_engine import (
    process_text_bidi,
    visual_bidi_reorder,
    remove_bidi_marks
)
from clipboard_helper import get_clipboard_text, set_clipboard_text
from hotkey_service import HotkeyService

class PersianRtlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("دستیار هوشمند راست‌چین و متن ترکیبی فارسی/انگلیسی")
        self.root.geometry("820x680")
        self.root.minsize(650, 520)

        # استایل‌های تم
        self.bg_color = "#1e1e2e"
        self.card_bg = "#252538"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.btn_bg = "#313244"
        self.btn_active = "#45475a"

        self.root.configure(bg=self.bg_color)

        # متغیرهای تنظیمات
        self.fix_english_var = tk.BooleanVar(value=True)
        self.fix_punctuation_var = tk.BooleanVar(value=True)
        self.fix_brackets_var = tk.BooleanVar(value=True)
        self.normalize_chars_var = tk.BooleanVar(value=True)
        self.digits_mode_var = tk.StringVar(value="none") # 'none', 'to_persian', 'to_english'
        self.visual_mode_var = tk.BooleanVar(value=False)
        self.live_mode_var = tk.BooleanVar(value=True)
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.hotkey_enabled_var = tk.BooleanVar(value=True)

        # سرویس هات‌کی
        self.hotkey_service = HotkeyService(callback_on_fix=self.on_hotkey_triggered)
        if self.hotkey_enabled_var.get():
            self.hotkey_service.start()

        self._build_ui()
        self.update_options_in_service()

    def _build_ui(self):
        # هدر اصلی
        header_frame = tk.Frame(self.root, bg=self.bg_color, pady=10, padx=15)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="✨ دستیار راست‌چین و اصلاح متن فارسی در برنامه‌های چپ‌چین",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        title_lbl.pack(anchor="e")

        subtitle_lbl = tk.Label(
            header_frame,
            text="حل مشکل جابجایی کلمات انگلیسی، علائم نگارشی و پرانتزها در Google Antigravity و سایر محیط‌های LTR",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg="#a6adc8"
        )
        subtitle_lbl.pack(anchor="e")

        # نوار ابزار بالا
        toolbar = tk.Frame(self.root, bg=self.card_bg, padx=10, pady=8)
        toolbar.pack(fill=tk.X, padx=15, pady=5)

        # دکمه‌های سریع
        btn_clip_fix = tk.Button(
            toolbar,
            text="⚡ اصلاح و کپی مستقیم کلیپ‌بورد",
            font=("Segoe UI", 10, "bold"),
            bg="#b4befe",
            fg="#11111b",
            activebackground="#cdd6f4",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self.fix_clipboard_direct
        )
        btn_clip_fix.pack(side=tk.RIGHT, padx=5)

        btn_paste = tk.Button(
            toolbar,
            text="📥 الصاق متن (Paste)",
            font=("Segoe UI", 9),
            bg=self.btn_bg,
            fg=self.fg_color,
            activebackground=self.btn_active,
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.paste_to_input
        )
        btn_paste.pack(side=tk.RIGHT, padx=5)

        btn_clear = tk.Button(
            toolbar,
            text="🧹 پاک‌سازی",
            font=("Segoe UI", 9),
            bg=self.btn_bg,
            fg=self.fg_color,
            activebackground=self.btn_active,
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.clear_all
        )
        btn_clear.pack(side=tk.RIGHT, padx=5)

        chk_top = tk.Checkbutton(
            toolbar,
            text="📌 روی همه پنجره‌ها",
            variable=self.always_on_top_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            activebackground=self.card_bg,
            activeforeground=self.fg_color,
            command=self.toggle_always_on_top
        )
        chk_top.pack(side=tk.LEFT, padx=5)

        chk_live = tk.Checkbutton(
            toolbar,
            text="⚡ پردازش زنده",
            variable=self.live_mode_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            activebackground=self.card_bg,
            activeforeground=self.fg_color,
            command=self.on_text_change
        )
        chk_live.pack(side=tk.LEFT, padx=5)

        # فریم اصلی متون
        content_frame = tk.Frame(self.root, bg=self.bg_color, padx=15, pady=5)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # باکس ورودی
        in_frame = tk.LabelFrame(
            content_frame,
            text=" متن ورودی (اینجا تایپ کنید یا پیست کنید) ",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.accent_color,
            padx=8,
            pady=6
        )
        in_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.input_text = tk.Text(
            in_frame,
            font=("Segoe UI", 11),
            bg="#181825",
            fg=self.fg_color,
            insertbackground="white",
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.bind("<KeyRelease>", lambda e: self.on_text_change())

        # باکس خروجی
        out_frame = tk.LabelFrame(
            content_frame,
            text=" متن اصلاح‌شده و استاندارد BiDi (آماده قرار دادن در Antigravity یا ویرایشگر) ",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.success_color,
            padx=8,
            pady=6
        )
        out_frame.pack(fill=tk.BOTH, expand=True)

        self.output_text = tk.Text(
            out_frame,
            font=("Segoe UI", 11),
            bg="#181825",
            fg=self.fg_color,
            insertbackground="white",
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # نوار ابزار خروجی
        out_toolbar = tk.Frame(out_frame, bg=self.card_bg, pady=4)
        out_toolbar.pack(fill=tk.X)

        self.copy_btn = tk.Button(
            out_toolbar,
            text="📋 کپی متن خروجی",
            font=("Segoe UI", 10, "bold"),
            bg=self.success_color,
            fg="#11111b",
            activebackground="#94e2d5",
            cursor="hand2",
            padx=14,
            pady=3,
            command=self.copy_output
        )
        self.copy_btn.pack(side=tk.RIGHT, padx=5)

        self.status_lbl = tk.Label(
            out_toolbar,
            text="",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.success_color
        )
        self.status_lbl.pack(side=tk.LEFT, padx=10)

        # پنل تنظیمات پایین
        settings_frame = tk.LabelFrame(
            self.root,
            text=" تنظیمات منطق هوشمند ",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg,
            fg=self.fg_color,
            padx=10,
            pady=5
        )
        settings_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

        # ردیف اول تنظیمات
        row1 = tk.Frame(settings_frame, bg=self.card_bg)
        row1.pack(fill=tk.X, pady=2)

        chk_eng = tk.Checkbutton(
            row1,
            text="حفظ جهت کلمات انگلیسی در متن فارسی",
            variable=self.fix_english_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            command=self.on_settings_change
        )
        chk_eng.pack(side=tk.RIGHT, padx=10)

        chk_punct = tk.Checkbutton(
            row1,
            text="تثبیت علائم نگارشی (. ! ؟ :)",
            variable=self.fix_punctuation_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            command=self.on_settings_change
        )
        chk_punct.pack(side=tk.RIGHT, padx=10)

        chk_brackets = tk.Checkbutton(
            row1,
            text="اصلاح پرانتزها و کروشه‌ها () []",
            variable=self.fix_brackets_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            command=self.on_settings_change
        )
        chk_brackets.pack(side=tk.RIGHT, padx=10)

        # ردیف دوم تنظیمات
        row2 = tk.Frame(settings_frame, bg=self.card_bg)
        row2.pack(fill=tk.X, pady=2)

        chk_norm = tk.Checkbutton(
            row2,
            text="استانداردسازی 'ک' و 'ی'",
            variable=self.normalize_chars_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            command=self.on_settings_change
        )
        chk_norm.pack(side=tk.RIGHT, padx=10)

        chk_visual = tk.Checkbutton(
            row2,
            text="حالت بازچینی بصری (برای ترمینال‌های قدیمی)",
            variable=self.visual_mode_var,
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            command=self.on_settings_change
        )
        chk_visual.pack(side=tk.RIGHT, padx=10)

        hotkey_lbl = tk.Label(
            row2,
            text="⌨ کلید میانبر سراسری ویندوز: Ctrl + Alt + F (انتخاب متن و فشردن کلید)",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_color
        )
        hotkey_lbl.pack(side=tk.LEFT, padx=10)

    def on_hotkey_triggered(self, original_text, fixed_text):
        """زمانی که هات‌کی زده می‌شود، باکس ورودی و خروجی را هم آپدیت کن"""
        def update():
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", original_text)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", fixed_text)
            self.show_status("⚡ متن با کلید میانبر اصلاح شد!")
        self.root.after(0, update)

    def update_options_in_service(self):
        self.hotkey_service.update_options(
            fix_english=self.fix_english_var.get(),
            fix_punctuation=self.fix_punctuation_var.get(),
            fix_brackets=self.fix_brackets_var.get(),
            normalize_chars=self.normalize_chars_var.get(),
            convert_digits=self.digits_mode_var.get(),
            visual_mode=self.visual_mode_var.get()
        )

    def on_settings_change(self):
        self.update_options_in_service()
        self.process_content()

    def on_text_change(self):
        if self.live_mode_var.get():
            self.process_content()

    def process_content(self):
        content = self.input_text.get("1.0", tk.END).rstrip('\r\n')
        if not content:
            self.output_text.delete("1.0", tk.END)
            return

        if self.visual_mode_var.get():
            processed = visual_bidi_reorder(content)
        else:
            processed = process_text_bidi(
                content,
                fix_english=self.fix_english_var.get(),
                fix_punctuation=self.fix_punctuation_var.get(),
                fix_brackets=self.fix_brackets_var.get(),
                normalize_chars=self.normalize_chars_var.get(),
                convert_digits=self.digits_mode_var.get()
            )

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", processed)

    def copy_output(self):
        content = self.output_text.get("1.0", tk.END).rstrip('\r\n')
        if not content:
            return
        set_clipboard_text(content)
        self.show_status("✓ متن خروجی در کلیپ‌بورد کپی شد!")

    def paste_to_input(self):
        text = get_clipboard_text()
        if text:
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", text)
            self.process_content()

    def fix_clipboard_direct(self):
        text = get_clipboard_text()
        if not text:
            self.show_status("کلیپ‌بورد خالی است!")
            return
        
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", text)
        self.process_content()
        self.copy_output()

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.show_status("پاک شد.")

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def show_status(self, msg):
        self.status_lbl.config(text=msg)
        self.root.after(3000, lambda: self.status_lbl.config(text=""))

def main():
    root = tk.Tk()
    app = PersianRtlApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
