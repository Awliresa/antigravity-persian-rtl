# antigravity_rtl_daemon.py
"""
Antigravity Persian RTL Daemon v2.3.0
Clean, high-performance, zero-lag RTL and Vazirmatn font injection for Google Antigravity.
"""

import time
import os
import sys
import urllib.request
import json
import argparse
import cdp_client

# Suppress console errors when running under pythonw
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")


INJECTION_SCRIPT = r"""
(() => {
    // 1. Google Fonts: Vazirmatn
    if (!document.getElementById('ag-vazirmatn-font')) {
        const link = document.createElement('link');
        link.id   = 'ag-vazirmatn-font';
        link.rel  = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap';
        document.head.appendChild(link);
    }

    // 2. CSS Styles
    let style = document.getElementById('ag-complete-rtl-vazir-style');
    if (!style) {
        style = document.createElement('style');
        style.id = 'ag-complete-rtl-vazir-style';
        document.head.appendChild(style);
        style.textContent = `
            /* Persian text: RTL + Vazirmatn */
            .persian-rtl-block {
                direction: rtl !important;
                text-align: right !important;
                unicode-bidi: plaintext !important;
                font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                line-height: 1.85 !important;
            }

            /* Persian lists */
            ul.persian-rtl-list, ol.persian-rtl-list {
                direction: rtl !important;
                text-align: right !important;
                padding-right: 26px !important;
                padding-left: 0px !important;
            }

            /* Input box: native auto direction and Vazirmatn - zero JS lag */
            [role="combobox"][contenteditable="true"] {
                font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                unicode-bidi: plaintext !important;
            }

            /* Code: strict LTR */
            pre, code, pre *, code *,
            .monaco-editor, [class*="code-block"], [class*="terminal"] {
                direction: ltr !important;
                text-align: left !important;
                unicode-bidi: isolate !important;
                font-family: 'Consolas', 'Fira Code', 'Courier New', monospace !important;
            }

            /* Inline code inside Persian text */
            p code, li code, td code,
            h1 code, h2 code, h3 code, h4 code, h5 code, h6 code {
                direction: ltr !important;
                display: inline-block !important;
                unicode-bidi: isolate !important;
                font-family: 'Consolas', 'Fira Code', monospace !important;
                margin: 0 4px !important;
            }
        `;
    }

    const PERSIAN_REGEX = /[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
    const LATIN_REGEX   = /[a-zA-Z]/;

    // Detect direction, ignoring leading number prefixes like "3. " or "۳. "
    function detectDirection(text) {
        if (!text) return 'ltr';
        const trimmed = text.trim();
        if (!trimmed) return 'ltr';

        const cleaned = trimmed.replace(/^[\u06F0-\u06F9\d]+[.)،\-\s]*\s*/, '');
        const checkText = cleaned.length > 0 ? cleaned : trimmed;

        const pCount = (checkText.match(new RegExp(PERSIAN_REGEX.source, 'g')) || []).length;
        const lCount = (checkText.match(new RegExp(LATIN_REGEX.source, 'g')) || []).length;

        if (pCount === 0) return 'ltr';
        if (pCount >= 2 || pCount >= lCount) return 'rtl';
        return 'ltr';
    }

    function applyLtr(el) {
        el.classList.remove('persian-rtl-block');
        el.setAttribute('dir', 'ltr');
        el.style.setProperty('direction', 'ltr', 'important');
        el.style.setProperty('text-align', 'left', 'important');
        el.style.setProperty('unicode-bidi', 'isolate', 'important');
    }

    function applyRtl(el) {
        el.classList.add('persian-rtl-block');
        el.setAttribute('dir', 'rtl');
        el.style.setProperty('direction', 'rtl', 'important');
        el.style.setProperty('text-align', 'right', 'important');
        el.style.setProperty('unicode-bidi', 'plaintext', 'important');
    }

    function processElement(el) {
        if (!el || el.nodeType !== 1) return;

        // Code blocks: always LTR
        if (
            el.tagName === 'CODE' || el.tagName === 'PRE' ||
            el.closest('pre, code, .monaco-editor, [class*="terminal"]')
        ) {
            applyLtr(el);
            return;
        }

        // Input box: set dir="auto" once and let browser handle typing natively without JS events
        if (
            el.isContentEditable ||
            el.getAttribute('role') === 'combobox' ||
            el.tagName === 'TEXTAREA'
        ) {
            if (el.getAttribute('dir') !== 'auto') {
                el.setAttribute('dir', 'auto');
            }
            return;
        }

        // Paragraphs, headings, lists, table cells
        if (/^(P|H[1-6]|LI|TD|TH|BLOCKQUOTE)$/.test(el.tagName)) {
            const text = el.textContent || '';
            const dir = detectDirection(text);
            if (dir === 'rtl') {
                applyRtl(el);
                if (
                    el.tagName === 'LI' &&
                    el.parentElement &&
                    /^(UL|OL)$/.test(el.parentElement.tagName)
                ) {
                    el.parentElement.classList.add('persian-rtl-list');
                    el.parentElement.style.setProperty('direction', 'rtl', 'important');
                    el.parentElement.style.setProperty('text-align', 'right', 'important');
                }
            } else {
                // If it was marked RTL before but text is now LTR, reset it
                if (el.classList.contains('persian-rtl-block')) {
                    applyLtr(el);
                }
            }
        }
    }

    // Process all existing elements
    document.querySelectorAll(
        'p, h1, h2, h3, h4, h5, h6, li, td, th, blockquote, [role="combobox"], [contenteditable="true"]'
    ).forEach(processElement);

    document.querySelectorAll('pre, code').forEach(applyLtr);

    // MutationObserver: processes streaming AI messages when new nodes appear
    // Attached strictly once
    if (!window.__ag_vazir_observer) {
        window.__ag_vazir_observer = new MutationObserver(mutations => {
            for (const m of mutations) {
                for (const n of m.addedNodes) {
                    if (n.nodeType !== 1) continue;
                    processElement(n);
                    if (n.querySelectorAll) {
                        n.querySelectorAll(
                            'p, h1, h2, h3, h4, h5, h6, li, td, th, blockquote, [role="combobox"], [contenteditable="true"]'
                        ).forEach(processElement);
                        n.querySelectorAll('pre, code').forEach(applyLtr);
                    }
                }
            }
        });

        window.__ag_vazir_observer.observe(
            document.body || document.documentElement,
            { childList: true, subtree: true }
        );
    }

    return { status: 'OK', version: '2.3.0' };
})()
"""


def get_devtools_port() -> str | None:
    port_file = os.path.expandvars(r"%APPDATA%\Antigravity\DevToolsActivePort")
    if not os.path.exists(port_file):
        return None
    try:
        with open(port_file, "r") as f:
            return f.readline().strip()
    except Exception:
        return None


def check_and_inject() -> bool:
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
                    "expression": INJECTION_SCRIPT,
                    "returnByValue": True,
                }
            )
            val = (res or {}).get("result", {}).get("result", {}).get("value", {})
            if isinstance(val, dict) and val.get("status") == "OK":
                injected = True
        except Exception:
            pass

    return injected


def install_startup():
    daemon_path = os.path.abspath(__file__)
    python_dir   = os.path.dirname(sys.executable)
    pythonw_path = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable

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
        print(f"[OK] Startup registered: {vbs_path}")
    except Exception as e:
        print(f"[ERROR] Startup registration failed: {e}")


def uninstall_startup():
    startup_dir = os.path.expandvars(
        r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    )
    vbs_path = os.path.join(startup_dir, "antigravity_rtl.vbs")
    if os.path.exists(vbs_path):
        try:
            os.remove(vbs_path)
            print("[OK] Startup removed")
        except Exception as e:
            print(f"[ERROR] Could not remove: {e}")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Persian RTL Daemon")
    parser.add_argument("--install", action="store_true", help="Install to Windows Startup")
    parser.add_argument("--uninstall", action="store_true", help="Remove from Windows Startup")
    parser.add_argument("--interval", type=float, default=2.0, help="Check interval in seconds")
    args = parser.parse_args()

    if args.install:
        install_startup()
        return
    if args.uninstall:
        uninstall_startup()
        return

    # Main daemon loop (minimal CPU usage, simple sleep)
    while True:
        try:
            check_and_inject()
        except Exception:
            pass
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
