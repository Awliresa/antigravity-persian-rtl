<div dir="rtl">

# 🖋️ Antigravity Persian RTL — راست‌چین هوشمند فارسی برای Google Antigravity

</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/Font-Vazirmatn-orange" alt="Vazirmatn Font">
</p>

---

<details open>
<summary><b>🇮🇷 توضیحات فارسی</b></summary>

<div dir="rtl">

## مشکل چیست؟

Google Antigravity (و بسیاری از برنامه‌های مدرن) از راست‌چین کردن خودکار متن فارسی پشتیبانی نمی‌کنند. این باعث می‌شود:

- متن فارسی از چپ نوشته شود (ناخوانا)
- کلمات انگلیسی داخل جمله فارسی جابجا شوند
- علائم نگارشی (نقطه، پرانتز، ویرگول) در جای اشتباه قرار بگیرند
- تیترها و لیست‌ها معکوس نمایش داده شوند

## راه‌حل

این پروژه دو ابزار مکمل ارائه می‌دهد:

### ۱. 🚀 Daemon اصلی (توصیه‌شده)

یک سرویس پس‌زمینه که از طریق **Chrome DevTools Protocol (CDP)** به Antigravity وصل می‌شود و به‌صورت زنده و خودکار:
- فونت زیبای **وزیرمتن** را برای متون فارسی اعمال می‌کند
- پاراگراف‌ها، تیترها، لیست‌ها و پیام‌های AI را راست‌چین می‌کند  
- بلوک‌های کد را چپ‌چین نگه می‌دارد
- پیام‌های در حال پخش (streaming) را real-time پردازش می‌کند
- تیترهایی که با عدد شروع می‌شوند (مثل `۳. آیا...`) را درست تشخیص می‌دهد

### ۲. 🛠️ ابزار کلیپ‌بورد (برای سایر برنامه‌ها)

یک GUI با کلید میانبر سراسری **Ctrl+Alt+F** که:
- متن انتخاب‌شده را می‌خواند، علائم Unicode BiDi اضافه می‌کند و paste می‌کند
- کلمات انگلیسی میان متن فارسی را ایزوله می‌کند
- پرانتزها و علائم نگارشی را در جهت صحیح قرار می‌دهد

## نصب سریع

```bat
:: اجرای یک‌بار install.bat (با دسترسی معمولی)
install.bat
```

یا دستی:
```bash
python daemon/antigravity_rtl_daemon.py --install
```

## نیازمندی‌ها

- ویندوز ۱۰ یا ۱۱
- Python 3.8 یا جدیدتر
- Google Antigravity (باید قبل از daemon باز باشد)
- اینترنت (برای بارگذاری فونت وزیرمتن از Google Fonts)

## ساختار پروژه

```
antigravity-persian-rtl/
├── daemon/
│   ├── antigravity_rtl_daemon.py   ← سرویس اصلی CDP
│   └── cdp_client.py               ← WebSocket کلاینت سبک
├── clipboard_tool/
│   ├── persian_bidi_engine.py      ← موتور پردازش BiDi
│   ├── gui_app.py                  ← رابط گرافیکی تاریک
│   ├── hotkey_service.py           ← کلید میانبر Win32
│   ├── clipboard_helper.py         ← مدیریت کلیپ‌بورد
│   └── cli.py                      ← رابط خط فرمان
├── tests/
│   └── test_engine.py
├── install.bat                     ← نصب در Startup ویندوز
├── uninstall.bat
├── run_daemon.bat                  ← اجرای مستقیم daemon
└── run_clipboard_tool.bat          ← اجرای ابزار کلیپ‌بورد
```

## نحوه کار daemon

```
Antigravity (Electron) ──CDP WebSocket──► antigravity_rtl_daemon.py
                                              │
                                              ▼
                                    تزریق JavaScript:
                                    - فونت وزیرمتن
                                    - CSS راست‌چین
                                    - MutationObserver
                                    - Input listener
```

Daemon هر ۲ ثانیه یک‌بار inject را اجرا می‌کند. اگر Antigravity بسته باشد، daemon منتظر می‌ماند و با باز شدن مجدد دوباره inject می‌کند.

</div>
</details>

---

<details>
<summary><b>🇬🇧 English Documentation</b></summary>

## Problem Statement

Google Antigravity (and many modern LTR-first applications) don't support automatic right-to-left rendering for Persian/Arabic text. This causes:

- Persian text rendered left-to-right (unreadable)
- English words within Persian sentences displaced
- Punctuation marks (`.`, `()`, `,`) appearing on the wrong side
- Numbered headings reversed (e.g., `3. Text` shows as `txeT .3`)

## Solution

This project provides two complementary tools:

### 1. 🚀 RTL Daemon (Recommended)

A background service connecting to Antigravity via **Chrome DevTools Protocol (CDP)** that automatically:

- Loads **Vazirmatn** font (a beautiful open-source Persian typeface)
- Applies `direction: rtl` to paragraphs, headings (`h1`–`h6`), list items, table cells
- Forces `direction: ltr` on all `pre`, `code`, terminal, and Monaco Editor blocks
- Uses a `MutationObserver` to process streaming AI responses in real-time
- Correctly detects Persian-dominant lines — stripping leading `number.` prefixes before classification (bug fix for numbered headings)

### 2. 🛠️ Clipboard BiDi Tool (For Other Apps)

A standalone GUI with system-wide hotkey **Ctrl+Alt+F** that:

- Reads selected text via `Ctrl+C`, processes it, and pastes it back via `Ctrl+V`
- Inserts Unicode BiDi control characters (`RLM`, `LRM`, `LRI`/`PDI`) at the correct positions
- Isolates embedded English tokens within Persian sentences
- Works in **any** LTR application (Notepad, Word, Slack, etc.)

## Quick Start

```bat
:: Run install.bat (no admin rights needed)
install.bat
```

Or manually:

```bash
# Install daemon to Windows Startup:
python daemon/antigravity_rtl_daemon.py --install

# Run daemon now:
pythonw daemon/antigravity_rtl_daemon.py

# Run clipboard GUI:
python clipboard_tool/gui_app.py

# CLI usage:
python clipboard_tool/cli.py --clipboard   # Fix clipboard content
python clipboard_tool/cli.py "متن فارسی"  # Fix inline text
python clipboard_tool/cli.py -i in.txt -o out.txt  # Fix file
```

## Requirements

- Windows 10 / 11
- Python 3.8+
- Google Antigravity (must be open when daemon runs)
- Internet access (to load Vazirmatn font from Google Fonts)
- No external Python packages required (uses only stdlib + tkinter)

## How the Daemon Works

1. **Port discovery**: reads `%APPDATA%\Antigravity\DevToolsActivePort`
2. **CDP connection**: calls `/json` HTTP endpoint to get WebSocket URLs
3. **Script injection**: sends `Runtime.evaluate` over WebSocket to inject JS
4. **Live monitoring**: MutationObserver + input events cover real-time changes
5. **Loop**: repeats every 2 seconds to re-inject after page reloads

## Technical Notes

### Direction Detection Algorithm

```
detectDirection(text):
  1. Strip leading number+dot prefix (e.g., "۳. ", "10. ") — these are BiDi Neutral
  2. Count Persian chars (U+0600–U+06FF, U+FB50–U+FDFF, U+FE70–U+FEFF)
  3. Count Latin chars (a-z, A-Z)
  4. If persianCount == 0 → LTR
  5. If persianCount >= 2 OR persianCount >= latinCount → RTL
  6. Otherwise → LTR
```

### Why inject every 2 seconds?

Antigravity is a React/SPA app. New chat messages are added dynamically. While the MutationObserver handles most cases, re-injecting ensures the observer is active even after full page navigations or updates.

## Project Structure

```
antigravity-persian-rtl/
├── daemon/
│   ├── antigravity_rtl_daemon.py   — Main CDP daemon service
│   └── cdp_client.py               — Lightweight pure-Python WebSocket client
├── clipboard_tool/
│   ├── persian_bidi_engine.py      — Core BiDi processing engine
│   ├── gui_app.py                  — Dark-themed Tkinter GUI
│   ├── hotkey_service.py           — Win32 RegisterHotKey wrapper
│   ├── clipboard_helper.py         — Tkinter-based clipboard I/O
│   └── cli.py                      — Argparse CLI
├── tests/
│   └── test_engine.py              — Unit tests for BiDi engine (6 cases)
├── install.bat                     — Add daemon to Windows Startup + launch
├── uninstall.bat                   — Remove from Startup
├── run_daemon.bat                  — Launch daemon directly (background)
└── run_clipboard_tool.bat          — Launch clipboard GUI
```

## Running Tests

```bash
cd tests
python -m pytest test_engine.py -v
# or
python test_engine.py
```

</details>

---

## License

MIT — see [LICENSE](LICENSE)
