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
    const blocks = document.querySelectorAll('.persian-rtl-block');
    return {
        count: blocks.length,
        samples: Array.from(blocks).slice(0, 5).map(el => ({
            tag: el.tagName,
            text: (el.textContent || '').substring(0, 40),
            dir: window.getComputedStyle(el).direction,
            align: window.getComputedStyle(el).textAlign,
            font: window.getComputedStyle(el).fontFamily.substring(0, 20)
        }))
    };
})()
"""
res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': query_js, 'returnByValue': True})
import pprint
pprint.pprint(res.get('result', {}).get('result', {}).get('value', {}))
