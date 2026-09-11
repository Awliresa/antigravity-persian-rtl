import sys
sys.path.insert(0, r'C:\Users\Virus-CO\.gemini\antigravity\scratch\antigravity-persian-rtl\daemon')
import cdp_client, urllib.request, json, os

port_file = os.path.expandvars(r'%APPDATA%\Antigravity\DevToolsActivePort')
with open(port_file) as f:
    port = f.readline().strip()

tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2).read())
page_tab = next((t for t in tabs if t.get('type') == 'page'), None)
ws_url = page_tab['webSocketDebuggerUrl']

# Test setting dir="auto" on the input box
test_js = r"""
(() => {
    const input = document.querySelector('[role="combobox"][contenteditable="true"]');
    if (!input) return "No input found";
    input.setAttribute('dir', 'auto');
    input.style.fontFamily = "'Vazirmatn', sans-serif";
    return {
        dirAttr: input.getAttribute('dir'),
        computedDir: window.getComputedStyle(input).direction,
        font: window.getComputedStyle(input).fontFamily
    };
})()
"""
res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': test_js, 'returnByValue': True})
import pprint
pprint.pprint(res.get('result', {}).get('result', {}).get('value', {}))
