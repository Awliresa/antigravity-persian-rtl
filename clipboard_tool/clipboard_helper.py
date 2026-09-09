# clipboard_helper.py
import time
import ctypes
from ctypes import wintypes
import tkinter as tk

user32 = ctypes.windll.user32
VK_CONTROL = 0x11
VK_C = 0x43
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002

def simulate_key_press(vk_code):
    user32.keybd_event(vk_code, 0, 0, 0)

def simulate_key_release(vk_code):
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

def simulate_copy():
    """شبیه‌سازی کلید Ctrl+C برای کپی کردن متن انتخاب‌شده در پنجره فعال"""
    time.sleep(0.05)
    simulate_key_press(VK_CONTROL)
    simulate_key_press(VK_C)
    simulate_key_release(VK_C)
    simulate_key_release(VK_CONTROL)
    time.sleep(0.1)

def simulate_paste():
    """شبیه‌سازی کلید Ctrl+V برای جایگزینی متن اصلاح‌شده در پنجره فعال"""
    time.sleep(0.05)
    simulate_key_press(VK_CONTROL)
    simulate_key_press(VK_V)
    simulate_key_release(VK_V)
    simulate_key_release(VK_CONTROL)
    time.sleep(0.05)

def get_clipboard_text():
    """خواندن امن محتوای متنی کلیپ‌بورد با استفاده از تیکینتر"""
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        content = root.clipboard_get()
        return content
    except Exception:
        return ""
    finally:
        if root:
            try:
                root.destroy()
            except Exception:
                pass

def set_clipboard_text(text):
    """قرار دادن متن یونیکد در کلیپ‌بورد سیستم"""
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        return True
    except Exception:
        return False
    finally:
        if root:
            try:
                root.destroy()
            except Exception:
                pass
