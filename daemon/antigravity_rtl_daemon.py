# antigravity_rtl_daemon.py
"""
سرویس دائمی راست‌چین و فونت وزیرمتن برای Google Antigravity
================================================================
قابلیت‌ها:
  1. فونت زیبای وزیرمتن (Vazirmatn) برای تمام متون فارسی
  2. راست‌چین کامل پاراگراف‌ها، تیترها، لیست‌ها (متن کاربر و AI)
  3. چپ‌چین اجباری برای کدها، pre، code و ترمینال
  4. تشخیص هوشمند فارسی/لاتین با نادیده گرفتن پیشوند عدد+نقطه
  5. MutationObserver برای پیام‌های streaming (real-time)
  6. input listener برای جعبه تایپ

نصب خودکار در Startup ویندوز:
  python antigravity_rtl_daemon.py --install

اجرای مستقیم:
  python antigravity_rtl_daemon.py
  pythonw antigravity_rtl_daemon.py   ← بدون پنجره کنسول
"""

import time
import os
import sys
import urllib.request
import json
import argparse
import cdp_client

# ───────────────────────────────────────────────────────────────────────────────
# suppress stdout/stderr when running as pythonw (no console)
# ───────────────────────────────────────────────────────────────────────────────
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


# ═══════════════════════════════════════════════════════════════════════════════
#  اسکریپت تزریق JavaScript
# ═══════════════════════════════════════════════════════════════════════════════
INJECTION_SCRIPT = r"""
(() => {
    // ─── 1. بارگذاری فونت وزیرمتن از Google Fonts ───────────────────────────
    if (!document.getElementById('ag-vazirmatn-font')) {
        const link = document.createElement('link');
        link.id   = 'ag-vazirmatn-font';
        link.rel  = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap';
        document.head.appendChild(link);
    }

    // ─── 2. استایل‌های CSS ───────────────────────────────────────────────────
    let style = document.getElementById('ag-complete-rtl-vazir-style');
    if (!style) {
        style = document.createElement('style');
        style.id = 'ag-complete-rtl-vazir-style';
        document.head.appendChild(style);
    }

    // فقط اگر CSS هنوز نوشته نشده بنویس (جلوگیری از reflow هر 5 ثانیه)
    // ولی element scan را همیشه انجام بده
    if (!style.dataset.written) {
        style.dataset.written = '1';
        style.textContent = `
        /* ── متن فارسی: راست‌چین + وزیرمتن ── */
        .persian-rtl-block {
            direction: rtl !important;
            text-align: right !important;
            unicode-bidi: plaintext !important;
            font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont,
                         'Segoe UI', Roboto, sans-serif !important;
            line-height: 1.9 !important;
        }

        /* ── لیست‌های فارسی ── */
        ul.persian-rtl-list, ol.persian-rtl-list {
            direction: rtl !important;
            text-align: right !important;
            padding-right: 26px !important;
            padding-left:  0   !important;
        }

        /* ── جعبه ورودی کاربر ── */
        [role="combobox"][contenteditable="true"] {
            font-family: 'Vazirmatn', sans-serif !important;
            unicode-bidi: plaintext !important;
        }
        [role="combobox"].persian-rtl-block {
            direction: rtl !important;
            text-align: right !important;
        }

        /* ── کد: LTR اجباری بدون استثناء ── */
        pre, code, pre *, code *,
        .monaco-editor, [class*="code-block"], [class*="terminal"] {
            direction:    ltr      !important;
            text-align:   left     !important;
            unicode-bidi: isolate  !important;
            font-family:  'Consolas', 'Fira Code', 'Courier New', monospace !important;
        }

        /* ── کد درون‌خطی داخل پاراگراف فارسی ── */
        p code, li code, td code,
        h1 code, h2 code, h3 code, h4 code, h5 code, h6 code {
            direction:    ltr          !important;
            display:      inline-block !important;
            unicode-bidi: isolate      !important;
            font-family:  'Consolas', 'Fira Code', monospace !important;
            margin: 0 4px !important;
        }
    `;
    } // end if (!style.dataset.written)

    // ─── 3. Regex پایه ────────────────────────────────────────────────────────
    const PERSIAN = /[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
    const LATIN   = /[a-zA-Z]/;

    // ─── 4. تابع تشخیص جهت متن ───────────────────────────────────────────────
    /**
     * detectDirection(text) → 'rtl' | 'ltr'
     *
     * باگ‌ fix: تیترهایی که با عدد+نقطه یا شماره+پرانتز شروع می‌شوند
     * (مثل "۳. آیا..." یا "10. Is this...") قبل از شمارش حروف پاک می‌شوند
     * تا عدد خنثی باعث تشخیص اشتباه LTR نشود.
     */
    function detectDirection(text) {
        if (!text) return 'ltr';
        let trimmed = text.trim();
        if (!trimmed) return 'ltr';

        // حذف پیشوند: عدد فارسی/لاتین + نقطه/پرانتز/خط‌تیره  (مثل "۳. " یا "10) " یا "2- ")
        // این پیشوندها هیچ اطلاعات جهتی ندارند (BiDi Neutral)
        const cleaned = trimmed.replace(/^[\u06F0-\u06F9\d]+[.)،\-\s]*\s*/, '');
        const checkText = cleaned.length > 0 ? cleaned : trimmed;

        const pCount = (checkText.match(new RegExp(PERSIAN.source, 'g')) || []).length;
        const lCount = (checkText.match(new RegExp(LATIN.source,   'g')) || []).length;

        if (pCount === 0) return 'ltr';
        if (pCount >= 2 || pCount >= lCount) return 'rtl';
        return 'ltr';
    }

    // ─── 5. اعمال/حذف کلاس بر روی یک element ────────────────────────────────
    function applyLtr(el) {
        el.classList.remove('persian-rtl-block');
        el.setAttribute('dir', 'ltr');
        el.style.setProperty('direction',   'ltr',     'important');
        el.style.setProperty('text-align',  'left',    'important');
        el.style.setProperty('unicode-bidi','isolate',  'important');
    }

    function applyRtl(el) {
        el.classList.add('persian-rtl-block');
        el.setAttribute('dir', 'rtl');
        el.style.setProperty('direction',   'rtl',      'important');
        el.style.setProperty('text-align',  'right',    'important');
        el.style.setProperty('unicode-bidi','plaintext', 'important');
    }

    // ─── 6. پردازش یک element ────────────────────────────────────────────────
    function processElement(el) {
        if (!el || el.nodeType !== 1) return;

        // کدها همیشه LTR
        if (
            el.tagName === 'CODE' || el.tagName === 'PRE' ||
            el.closest('pre, code, .monaco-editor, [class*="terminal"]')
        ) {
            applyLtr(el);
            return;
        }

        // جعبه تایپ کاربر
        if (
            el.isContentEditable ||
            el.getAttribute('role') === 'combobox' ||
            el.tagName === 'TEXTAREA'
        ) {
            const dir = detectDirection(el.innerText || el.textContent || el.value || '');
            dir === 'rtl' ? applyRtl(el) : applyLtr(el);
            return;
        }

        // پاراگراف‌ها، تیترها، لیست‌ها، جداول
        if (/^(P|H[1-6]|LI|TD|TH|BLOCKQUOTE)$/.test(el.tagName)) {
            const dir = detectDirection(el.textContent || '');
            if (dir === 'rtl') {
                applyRtl(el);
                // راست‌چین کردن والد UL/OL نیز
                if (
                    el.tagName === 'LI' &&
                    el.parentElement &&
                    /^(UL|OL)$/.test(el.parentElement.tagName)
                ) {
                    el.parentElement.classList.add('persian-rtl-list');
                    el.parentElement.style.setProperty('direction',  'rtl',   'important');
                    el.parentElement.style.setProperty('text-align', 'right', 'important');
                }
            }
        }
    }

    // ─── 7. اجرای اولیه روی همه عناصر موجود ─────────────────────────────────
    document.querySelectorAll(
        'p, h1, h2, h3, h4, h5, h6, li, td, th, blockquote, ' +
        '[role="combobox"], [contenteditable="true"]'
    ).forEach(processElement);

    document.querySelectorAll('pre, code').forEach(applyLtr);

    // ─── 8. Debounced input listener (فقط یک‌بار register می‌شود) ────────────
    // بدون debounce، هر keystroke یک reflow می‌زند و تایپ را کند می‌کند.
    // با debounce 400ms، فقط بعد از توقف تایپ پردازش انجام می‌شود.
    if (!window.__ag_input_listener_registered) {
        window.__ag_input_listener_registered = true;

        let _inputTimer = null;
        document.addEventListener('input', e => {
            const target = e.target;
            // فقط برای input boxes پردازش real-time انجام می‌شود
            if (!target || !(target.isContentEditable || target.getAttribute('role') === 'combobox' || target.tagName === 'TEXTAREA')) return;
            clearTimeout(_inputTimer);
            _inputTimer = setTimeout(() => processElement(target), 400);
        }, true);

        // keyup فقط برای Enter (submit) — بلافاصله
        document.addEventListener('keyup', e => {
            if (e.key === 'Enter' && e.target) {
                processElement(e.target);
            }
        }, true);
    }

    // ─── 9. MutationObserver: پیام‌های AI (فقط برای nodes جدید) ─────────────
    // characterData حذف شد — آن باعث trigger بر هر کاراکتر می‌شد.
    if (!window.__ag_vazir_observer) {
        let _mutationTimer = null;
        const _pendingNodes = new Set();

        window.__ag_vazir_observer = new MutationObserver(mutations => {
            for (const m of mutations) {
                for (const n of m.addedNodes) {
                    if (n.nodeType !== 1) continue;
                    _pendingNodes.add(n);
                }
            }
            // batch پردازش بعد از 100ms (نه بلافاصله)
            clearTimeout(_mutationTimer);
            _mutationTimer = setTimeout(() => {
                for (const n of _pendingNodes) {
                    processElement(n);
                    if (n.querySelectorAll) {
                        n.querySelectorAll(
                            'p, h1, h2, h3, h4, h5, h6, li, td, th, blockquote, ' +
                            '[role="combobox"], [contenteditable="true"]'
                        ).forEach(processElement);
                        n.querySelectorAll('pre, code').forEach(applyLtr);
                    }
                }
                _pendingNodes.clear();
            }, 100);
        });

        window.__ag_vazir_observer.observe(
            document.body || document.documentElement,
            { childList: true, subtree: true }
            // characterData: true حذف شد
        );
    }

    return { status: 'OK', version: '2.2.0' };
})()
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  منطق اتصال و تزریق
# ═══════════════════════════════════════════════════════════════════════════════

def get_devtools_port() -> str | None:
    """شماره پورت DevTools Antigravity را از فایل می‌خواند."""
    port_file = os.path.expandvars(r"%APPDATA%\Antigravity\DevToolsActivePort")
    if not os.path.exists(port_file):
        return None
    try:
        with open(port_file, "r") as f:
            return f.readline().strip()
    except Exception:
        return None


def check_and_inject() -> bool:
    """
    به Antigravity وصل می‌شود و اسکریپت RTL را inject می‌کند.
    True برمی‌گرداند اگر حداقل یک tab با موفقیت inject شده باشد.
    """
    port = get_devtools_port()
    if not port:
        return False

    try:
        url = f"http://127.0.0.1:{port}/json"
        req = urllib.request.urlopen(url, timeout=2.0)
        tabs = json.loads(req.read().decode())
    except Exception:
        return False

    injected = False
    for tab in tabs:
        if tab.get("type") != "page":
            continue
        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            continue
        try:
            res = cdp_client.send_cdp_command(
                ws_url,
                "Runtime.evaluate",
                {
                    "expression":    INJECTION_SCRIPT,
                    "returnByValue": True,
                }
            )
            val = (res or {}).get("result", {}).get("result", {}).get("value", {})
            if isinstance(val, dict) and val.get("status") == "OK":
                injected = True
        except Exception:
            pass

    return injected


# ═══════════════════════════════════════════════════════════════════════════════
#  نصب خودکار در Startup ویندوز
# ═══════════════════════════════════════════════════════════════════════════════

def install_startup():
    """یک فایل VBScript در پوشه Startup ویندوز ایجاد می‌کند."""
    daemon_path = os.path.abspath(__file__)
    # مسیر pythonw.exe در کنار python.exe
    python_dir   = os.path.dirname(sys.executable)
    pythonw_path = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable  # fallback

    startup_dir = os.path.expandvars(
        r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    )
    vbs_path = os.path.join(startup_dir, "antigravity_rtl.vbs")

    vbs_content = f'''Set objShell = CreateObject("WScript.Shell")
objShell.Run Chr(34) & "{pythonw_path}" & Chr(34) & " " & Chr(34) & "{daemon_path}" & Chr(34), 0, False
'''
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        print(f"✓ نصب موفق! فایل startup در:\n  {vbs_path}")
        print("  daemon دفعه بعد از ورود به ویندوز به‌صورت خودکار اجرا می‌شود.")
    except Exception as e:
        print(f"✗ خطا در نصب: {e}")


def uninstall_startup():
    """فایل VBScript startup را حذف می‌کند."""
    startup_dir = os.path.expandvars(
        r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    )
    vbs_path = os.path.join(startup_dir, "antigravity_rtl.vbs")
    if os.path.exists(vbs_path):
        os.remove(vbs_path)
        print(f"✓ فایل startup حذف شد:\n  {vbs_path}")
    else:
        print("فایل startup یافت نشد.")


# ═══════════════════════════════════════════════════════════════════════════════
#  حلقه اصلی
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="سرویس راست‌چین و فونت وزیرمتن برای Google Antigravity"
    )
    parser.add_argument(
        "--install",   action="store_true",
        help="نصب خودکار در Startup ویندوز"
    )
    parser.add_argument(
        "--uninstall", action="store_true",
        help="حذف از Startup ویندوز"
    )
    parser.add_argument(
        "--interval",  type=float, default=3.0,
        help="فاصله زمانی بین هر inject به ثانیه (پیش‌فرض: 3.0)"
    )
    args = parser.parse_args()

    if args.install:
        install_startup()
        return
    if args.uninstall:
        uninstall_startup()
        return

    print("⚡ Antigravity RTL Daemon v2.1.0 — در حال اجرا...")
    print("   (برای توقف: Ctrl+C)")

    while True:
        try:
            check_and_inject()
        except Exception:
            pass
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
