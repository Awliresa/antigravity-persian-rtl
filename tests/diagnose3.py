"""بررسی وضعیت لود فونت و override های احتمالی"""
import sys
sys.path.insert(0, 'daemon')
import cdp_client, urllib.request, json, os

port_file = os.path.expandvars(r'%APPDATA%\Antigravity\DevToolsActivePort')
with open(port_file) as f:
    port = f.readline().strip()

tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2).read())
page_tab = next((t for t in tabs if t.get('type') == 'page'), None)
ws_url = page_tab['webSocketDebuggerUrl']

# چک کردن FontFace API
test_js = r"""
(async () => {
    // 1. آیا Vazirmatn در document.fonts هست؟
    const fonts = [];
    for (const f of document.fonts) {
        if (f.family.includes('Vazirmatn')) {
            fonts.push({ family: f.family, status: f.status });
        }
    }
    
    // 2. آیا Google Fonts لود شده؟
    const fontLink = document.getElementById('ag-vazirmatn-font');
    const linkLoaded = fontLink ? fontLink.sheet !== null : false;
    
    // 3. یک element با فونت مستقیم تست
    const testEl = document.createElement('span');
    testEl.style.fontFamily = "'Vazirmatn', sans-serif";
    testEl.textContent = "test";
    document.body.appendChild(testEl);
    const cs = window.getComputedStyle(testEl);
    const testFont = cs.fontFamily;
    document.body.removeChild(testEl);
    
    // 4. آیا هیچ style دیگری direction را override می‌کند؟
    const firstBlock = document.querySelector('.persian-rtl-block');
    let overrideCheck = null;
    if (firstBlock) {
        const rules = [];
        for (const sheet of document.styleSheets) {
            try {
                for (const rule of sheet.cssRules || []) {
                    if (rule.style && (rule.style.direction || rule.style.fontFamily)) {
                        if (firstBlock.matches && firstBlock.matches(rule.selectorText || '')) {
                            rules.push(rule.selectorText + ': dir=' + rule.style.direction);
                        }
                    }
                }
            } catch(e) {}
        }
        overrideCheck = rules.slice(0, 5).join(' | ');
    }
    
    return {
        vazirmatnFonts: fonts,
        googleFontSheetLoaded: linkLoaded,
        testElementFont: testFont.substring(0, 60),
        potentialOverrides: overrideCheck
    };
})()
"""

res = cdp_client.send_cdp_command(ws_url, 'Runtime.evaluate', {'expression': test_js, 'returnByValue': True, 'awaitPromise': True}, timeout=15.0)
val = res.get('result', {}).get('result', {}).get('value', {})
print('Font & Override check:')
import pprint
pprint.pprint(val)
