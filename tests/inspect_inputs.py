import sys
sys.path.insert(0, r'C:\Users\Virus-CO\.gemini\antigravity\scratch\antigravity-persian-rtl\daemon')
import cdp_client, urllib.request, json, os

port_file = os.path.expandvars(r'%APPDATA%\Antigravity\DevToolsActivePort')
with open(port_file) as f:
    port = f.readline().strip()

tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2).read())
page_tab = next((t for t in tabs if t.get('type') == 'page'), None)
ws_url = page_tab['webSocketDebuggerUrl']

query_js = r"""
(() => {
    const inputs = document.querySelectorAll('textarea, input, [contenteditable="true"], [role="combobox"]');
    return Array.from(inputs).map(el => ({
        tag: el.tagName,
        role: el.getAttribute('role'),
        contenteditable: el.getAttribute('contenteditable'),
        classes: el.className,
        id: el.id,
        dir: el.getAttribute('dir'),
        styleDir: el.style.direction,
        computedDir: window.getComputedStyle(el).direction,
        computedFont: window.getComputedStyle(el).fontFamily.substring(0, 40)
    }));
})()
"""
res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': query_js, 'returnByValue': True})
import pprint
pprint.pprint(res.get('result', {}).get('result', {}).get('value', []))
