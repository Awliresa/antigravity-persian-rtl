"""بررسی که JS خطا ندارد"""
import sys
sys.path.insert(0, 'daemon')
import cdp_client, urllib.request, json, os

port_file = os.path.expandvars(r'%APPDATA%\Antigravity\DevToolsActivePort')
with open(port_file) as f:
    port = f.readline().strip()

tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2).read())
page_tab = next((t for t in tabs if t.get('type') == 'page'), None)
ws_url = page_tab['webSocketDebuggerUrl']

# بررسی exception در نتیجه inject
res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {
    'expression': 'window.__ag_vazir_observer ? "observer_ok" : "no_observer"',
    'returnByValue': True
})
print('Observer:', res.get('result',{}).get('result',{}).get('value'))

res2 = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {
    'expression': 'window.__ag_input_listener_registered ? "listener_ok" : "no_listener"',
    'returnByValue': True
})
print('Input listener:', res2.get('result',{}).get('result',{}).get('value'))

res3 = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {
    'expression': 'document.querySelectorAll(".persian-rtl-block").length',
    'returnByValue': True
})
print('Persian blocks:', res3.get('result',{}).get('result',{}).get('value'))

# بررسی exceptionDetails
res4 = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {
    'expression': 'document.getElementById("ag-complete-rtl-vazir-style")?.dataset?.written',
    'returnByValue': True
})
print('Style written flag:', res4.get('result',{}).get('result',{}).get('value'))
