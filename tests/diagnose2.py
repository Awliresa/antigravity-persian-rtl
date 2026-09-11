"""بررسی دقیق‌تر - آیا فونت واقعاً لود شده؟ آیا style اعمال شده؟"""
import sys
sys.path.insert(0, 'daemon')
import cdp_client, urllib.request, json, os

port_file = os.path.expandvars(r'%APPDATA%\Antigravity\DevToolsActivePort')
with open(port_file) as f:
    port = f.readline().strip()

tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2).read())
page_tab = next((t for t in tabs if t.get('type') == 'page'), None)
ws_url = page_tab['webSocketDebuggerUrl']

test_js = r"""
(() => {
    // بررسی computed style یک element فارسی واقعی
    const blocks = document.querySelectorAll('.persian-rtl-block');
    if (blocks.length === 0) return { noBlocks: true };
    
    const el = blocks[0];
    const cs = window.getComputedStyle(el);
    
    // محتوای style tag
    const styleEl = document.getElementById('ag-complete-rtl-vazir-style');
    const styleContent = styleEl ? styleEl.textContent.substring(0, 100) : 'NOT FOUND';
    
    // بررسی font link
    const fontLink = document.getElementById('ag-vazirmatn-font');
    const fontHref = fontLink ? fontLink.href : 'NOT FOUND';
    
    return {
        elementTag: el.tagName,
        elementText: (el.textContent || '').substring(0, 30),
        computedDirection: cs.direction,
        computedTextAlign: cs.textAlign,
        computedFontFamily: cs.fontFamily.substring(0, 60),
        styleContentStart: styleContent,
        fontHref: fontHref
    };
})()
"""

res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': test_js, 'returnByValue': True})
val = res.get('result', {}).get('result', {}).get('value', {})
print('Computed style check:')
for k, v in val.items():
    print(f'  {k}: {v}')
