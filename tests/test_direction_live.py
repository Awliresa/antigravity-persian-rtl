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
    const PERSIAN = /[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
    const LATIN = /[a-zA-Z]/;
    
    function detectDirection(text) {
        if (!text) return 'ltr';
        let trimmed = text.trim();
        if (!trimmed) return 'ltr';
        // حذف پیشوند عدد+نقطه
        const cleaned = trimmed.replace(/^[\u06F0-\u06F9\d]+[.)،\-\s]*\s*/, '');
        const checkText = cleaned.length > 0 ? cleaned : trimmed;
        const pCount = (checkText.match(new RegExp(PERSIAN.source, 'g')) || []).length;
        const lCount = (checkText.match(new RegExp(LATIN.source,   'g')) || []).length;
        if (pCount === 0) return 'ltr';
        if (pCount >= 2 || pCount >= lCount) return 'rtl';
        return 'ltr';
    }
    
    return {
        'pure_persian': detectDirection('\u0622\u06CC\u0627 \u0627\u06CC\u0646 \u06CC\u06A9 \u0628\u0631\u0646\u0627\u0645\u0647 \u0627\u0633\u062A\u061F'),
        'latin_num_persian': detectDirection('3. \u0622\u06CC\u0627 \u0627\u06CC\u0646 \u06CC\u06A9 \u0628\u0631\u0646\u0627\u0645\u0647 \u0627\u0633\u062A\u061F'),
        'persian_num_persian': detectDirection('\u06F3. \u0622\u06CC\u0627 \u0627\u06CC\u0646 \u06CC\u06A9 \u0628\u0631\u0646\u0627\u0645\u0647 \u0627\u0633\u062A\u061F'),
        'pure_english': detectDirection('Hello World'),
        'num_english': detectDirection('10. Is this a program?')
    };
})()
"""

res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': test_js, 'returnByValue': True})
print('Test results:')
import pprint
pprint.pprint(res.get('result', {}).get('result', {}).get('value', {}))
