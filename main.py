import requests
import re
import concurrent.futures
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# واجهة المستخدم (محدثة لتنبيهك بنوع المفتاح)
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX SNIPER V7 | CLEAN & DEEP</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: auto; border: 2px solid #0f0; padding: 30px; box-shadow: 0 0 40px #0f0; background: rgba(0,10,0,0.95); }
        input { width: 85%; padding: 15px; background: #000; border: 1px solid #0f0; color: #fff; margin-bottom: 20px; }
        button { padding: 15px 50px; background: #0f0; color: #000; border: none; font-weight: bold; cursor: pointer; }
        .key-box { background: #111; padding: 10px; border-right: 5px solid #0f0; margin-bottom: 10px; word-break: break-all; color: #fff; text-align: left; direction: ltr; }
        .live-key { border-right: 5px solid #00ff00; color: #00ff00; font-weight: bold; }
        .test-key { border-right: 5px solid #ffff00; color: #ffff00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX SNIPER V7 ]</h1>
        <p>نظام القنص المحدث (تصفير الذاكرة + تجاهل الروابط الوهمية)</p>
        <input type="text" id="targetUrl" placeholder="أدخل رابط الموقع الجديد هنا...">
        <br>
        <button onclick="startCleanScan()">إطلاق القنص النظيف ⚡</button>
        <div id="results" style="margin-top: 30px;"></div>
    </div>
    <script>
        async function startCleanScan() {
            const url = document.getElementById('targetUrl').value;
            const resDiv = document.getElementById('results');
            resDiv.innerHTML = "⏳ جاري الفحص النظيف للموقع الجديد...";
            const response = await fetch('/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            });
            const data = await response.json();
            if (data.status === "Success") {
                let html = `<h3>النتائج للموقع: ${url}</h3>`;
                for (const [type, keys] of Object.entries(data.keys_found)) {
                    html += `<b>${type}:</b>`;
                    keys.forEach(k => {
                        let cls = k.includes('live') ? 'live-key' : 'test-key';
                        html += `<div class="key-box ${cls}">${k}</div>`;
                    });
                }
                resDiv.innerHTML = html;
            }
        }
    </script>
</body>
</html>
"""

PATTERNS = {
    'LIVE Publishable Key': r'pk_live_[a-zA-Z0-9]{24,}',
    'TEST Publishable Key': r'pk_test_[a-zA-Z0-9]{24,}',
    'Client Secret (CS)': r'pi_[a-zA-Z0-9]{15,}_secret_[a-zA-Z0-9]{20,}',
    'Stripe Account ID': r'acct_[a-zA-Z0-9]{16,}'
}

def extract_keys(text):
    found = {}
    for label, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            # فلترة المفاتيح الوهمية المشهورة لشركة Stripe
            filtered = [m for m in matches if "mpqEd" not in m and "syKB" not in m]
            if filtered: found[label] = list(set(filtered))
    return found

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/scan', methods=['POST'])
def scan():
    # تصفير المتغيرات داخل الدالة لضمان عدم تكرار النتائج القديمة
    all_found_keys = {} 
    base_url = request.json.get('url')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
    
    try:
        res = requests.get(base_url, headers=headers, timeout=10)
        all_found_keys.update(extract_keys(res.text))
        
        soup = BeautifulSoup(res.text, 'html.parser')
        assets = set()
        for s in soup.find_all('script'):
            src = s.get('src')
            if src:
                full_asset_url = urljoin(base_url, src)
                # تجاهل روابط Stripe الرسمية لأنها تحتوي على مفاتيح Test ثابتة
                if 'js.stripe.com' not in full_asset_url:
                    assets.add(full_asset_url)

        def fetch_now(link):
            try:
                r = requests.get(link, headers=headers, timeout=5)
                return extract_keys(r.text)
            except: return {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for result in executor.map(fetch_now, list(assets)):
                for label, keys in result.items():
                    if label in all_found_keys:
                        all_found_keys[label] = list(set(all_found_keys[label] + keys))
                    else:
                        all_found_keys[label] = keys

        return jsonify({"status": "Success", "keys_found": all_found_keys})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
