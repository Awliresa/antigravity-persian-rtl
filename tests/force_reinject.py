"""Force-clear all guards and re-inject everything fresh"""
import sys
sys.path.insert(0, 'daemon')
import cdp_client, urllib.request, json, os

port_file = os.path.expandvars(r'%APPDATA%\Antigravity\DevToolsActivePort')
with open(port_file) as f:
    port = f.readline().strip()

tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2).read())
page_tab = next((t for t in tabs if t.get('type') == 'page'), None)
ws_url = page_tab['webSocketDebuggerUrl']

# پاک کردن همه guard ها و style ها برای inject تازه
clear_js = r"""
(() => {
    // پاک کردن همه guardها
    delete window.__ag_vazir_observer;
    delete window.__ag_input_listener_registered;
    
    // پاک کردن style و font link
    const old = document.getElementById('ag-complete-rtl-vazir-style');
    if (old) old.remove();
    const oldFont = document.getElementById('ag-vazirmatn-font');
    if (oldFont) oldFont.remove();
    
    // پاک کردن همه persian-rtl-block ها
    document.querySelectorAll('.persian-rtl-block').forEach(el => {
        el.classList.remove('persian-rtl-block', 'persian-rtl-list');
        el.removeAttribute('dir');
        el.style.removeProperty('direction');
        el.style.removeProperty('text-align');
        el.style.removeProperty('unicode-bidi');
        el.style.removeProperty('font-family');
    });
    
    return 'cleared';
})()
"""

res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': clear_js, 'returnByValue': True})
print('Clear:', res.get('result', {}).get('result', {}).get('value'))

# حالا inject مجدد
import antigravity_rtl_daemon as d
result = d.check_and_inject()
print('Re-inject:', 'SUCCESS' if result else 'FAILED')
