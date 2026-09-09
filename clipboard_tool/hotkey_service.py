# hotkey_service.py
import time
import winsound
import threading
import ctypes
from ctypes import wintypes

from persian_bidi_engine import process_text_bidi, visual_bidi_reorder
from clipboard_helper import (
    simulate_copy,
    simulate_paste,
    get_clipboard_text,
    set_clipboard_text
)

user32 = ctypes.windll.user32

# Modifiers
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Virtual Key codes
VK_F = 0x46
VK_R = 0x52

class HotkeyService:
    def __init__(self, callback_on_fix=None):
        self.is_running = False
        self.thread = None
        self.hotkey_id = 101
        self.callback_on_fix = callback_on_fix
        self.options = {
            'fix_english': True,
            'fix_punctuation': True,
            'fix_brackets': True,
            'normalize_chars': True,
            'convert_digits': 'none',
            'visual_mode': False,
        }

    def update_options(self, **kwargs):
        self.options.update(kwargs)

    def trigger_fix(self):
        """عملیات اصلاح متن انتخاب‌شده یا متن موجود در کلیپ‌بورد"""
        old_clip = get_clipboard_text()
        
        # ۱. تلاش برای کپی کردن متن انتخاب شده کاربر
        simulate_copy()
        current_text = get_clipboard_text()
        
        if not current_text:
            current_text = old_clip

        if not current_text:
            return

        # ۲. پردازش بر اساس موتور
        if self.options.get('visual_mode', False):
            fixed_text = visual_bidi_reorder(current_text)
        else:
            fixed_text = process_text_bidi(
                current_text,
                fix_english=self.options.get('fix_english', True),
                fix_punctuation=self.options.get('fix_punctuation', True),
                fix_brackets=self.options.get('fix_brackets', True),
                normalize_chars=self.options.get('normalize_chars', True),
                convert_digits=self.options.get('convert_digits', 'none')
            )

        # ۳. ذخیره در کلیپ‌بورد و پیست مستقیم
        set_clipboard_text(fixed_text)
        simulate_paste()

        # بازخورد صوتی کوچک
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

        if self.callback_on_fix:
            try:
                self.callback_on_fix(current_text, fixed_text)
            except Exception:
                pass

    def _loop(self):
        # ثبت کلید میانبر Ctrl + Alt + F
        modifiers = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
        success = user32.RegisterHotKey(None, self.hotkey_id, modifiers, VK_F)
        if not success:
            # در صورت اشغال بودن، تلاش با Ctrl + Shift + R
            modifiers = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
            success = user32.RegisterHotKey(None, self.hotkey_id, modifiers, VK_R)

        msg = wintypes.MSG()
        while self.is_running:
            # بررسی پیام‌های ویندوز با تایم‌اوت بدون بلاک کامل
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                if msg.message == 0x0312:  # WM_HOTKEY
                    if msg.wParam == self.hotkey_id:
                        threading.Thread(target=self.trigger_fix, daemon=True).start()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.05)

        user32.UnregisterHotKey(None, self.hotkey_id)

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
