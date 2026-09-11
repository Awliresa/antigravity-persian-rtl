"""بررسی خطاهای JS از داخل Antigravity"""
import sys
sys.path.insert(0, 'daemon')
import cdp_client, urllib.request, json, os

port_file = os.path.expandvars(r'%APPDATA%\Antigravity\DevToolsActivePort')
with open(port_file) as f:
    port = f.readline().strip()

tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2).read())
page_tab = next((t for t in tabs if t.get('type') == 'page'), None)
ws_url = page_tab['webSocketDebuggerUrl']

# تست ساده‌ترین حالت ممکن
test_js = r"""
(() => {
    try {
        // آیا style قبلی وجود دارد؟
        const hasStyle = !!document.getElementById('ag-complete-rtl-vazir-style');
        const hasFont = !!document.getElementById('ag-vazirmatn-font');
        const hasObserver = !!window.__ag_vazir_observer;
        const hasInputGuard = !!window.__ag_input_listener_registered;
        
        // چند element فارسی وجود دارد؟
        const persianBlocks = document.querySelectorAll('.persian-rtl-block').length;
        const allP = document.querySelectorAll('p').length;
        
        return {
            ok: true,
            hasStyle,
            hasFont,
            hasObserver,
            hasInputGuard,
            persianBlocks,
            allP
        };
    } catch(e) {
        return { ok: false, error: e.message };
    }
})()
"""

res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': test_js, 'returnByValue': True})
val = res.get('result', {}).get('result', {}).get('value', {})
print('Diagnostic:')
for k, v in val.items():
    print(f'  {k}: {v}')
