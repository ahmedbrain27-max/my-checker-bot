import requests
import re
import concurrent.futures
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- واجهة المستخدم (الواجهة المظلمة الاحترافية) ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ULTIMATE SCANNER | V6</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 950px; margin: auto; border: 2px solid #0f0; padding: 30px; box-shadow: 0 0 40px #0f0; background: rgba(0,20,0,0.95); }
        h1 { letter-spacing: 10px; text-shadow: 0 0 20px #0f0; }
        input { width: 90%; padding: 15px; background: #000; border: 1px solid #0f0; color: #fff; margin-bottom: 20px; font-size: 1.1rem; }
        button { padding: 15px 60px; background: #0f0; color: #000; border: none; font-weight: bold; cursor: pointer; font-size: 1.3rem; transition: 0.5s; }
        button:hover { background: #fff; box-shadow: 0 0 30px #fff; transform: scale(1.02); }
        .log-area { margin-top: 20px; background: #050505; height: 150px; overflow-y: auto; text-align: left; padding: 10px; font-size: 0.8rem; border: 1px solid #333; color: #888; }
        #results { margin-top: 30px; text-align: right; }
        .key-box { background: #111; padding: 15px; border-right: 5px solid #0f0; margin-bottom: 10px; word-break: break-all; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX GOD-MODE SCANNER ]</h1>
        <p>نظام القنص الشامل: فحص الـ HTML، الـ JS، الـ CSS، والـ Network Endpoints</p>
        <input type="text" id="targetUrl" placeholder="أدخل رابط المتجر أو صفحة الدفع...">
        <br>
        <button onclick="startGodScan()">إطلاق القنص الشامل ⚡</button>
        <div class="log-area" id="logs">بانتظار الأوامر...</div>
        <div id="results"></div>
    </div>

    <script>
        async function startGodScan() {
            const url = document.getElementById('targetUrl').value;
            const logs = document.getElementById('logs');
            const resDiv = document.getElementById('results');
            logs.innerHTML = "[SYSTEM] تفعيل رادار الاختراق...<br>";
            resDiv.innerHTML = "";
            
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                
                if (data.status === "Success") {
                    logs.innerHTML += `[SUCCESS] تم فحص ${data.total_scanned} ملفاً بنجاح.<br>`;
                    let html = `<h3>✅ النتائج المستخرجة:</h3>`;
                    if (Object.keys(data.keys_found).length === 0) {
                        html += "<p style='color:red'>لم يتم العثور على مفاتيح مكشوفة، الموقع محمي جيداً أو المفتاح مشفر.</p>";
                    }
                    for (const [type, keys] of Object.entries(data.keys_found)) {
                        html += `<b style="color:#0f0">${type}:</b>`;
                        keys.forEach(k => { html += `<div class="key-box">${k}</div>`; });
                    }
                    resDiv.innerHTML = html;
                } else {
                    logs.innerHTML += `[ERROR] ${data.message}<br>`;
                }
            } catch (err) {
                logs.innerHTML += "[FATAL ERROR] فشل الاتصال بالسيرفر.<br>";
            }
        }
    </script>
</body>
</html>
"""

# --- رادار البحث الشامل (The Master Key Radar) ---
PATTERNS = {
    'Secret Key (SK)': r'sk_live_[a-zA-Z0-9]{24,}',
    'Publishable Key (PK)': r'pk_live_[a-zA-Z0-9]{20,}',
    'Client Secret (CS)': r'pi_[a-zA-Z0-9]{15,}_secret_[a-zA-Z0-9]{20,}',
    'Setup Intent (SI)': r'seti_[a-zA-Z0-9]{15,}_secret_[a-zA-Z0-9]{20,}',
    'Stripe Account': r'acct_[a-zA-Z0-9]{16,}',
    'Encrypted/Obfuscated PK': r'pk_(?:live|test)_[a-zA-Z0-9]{10,}'
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
    scanned_links = set()

    try:
        # 1. المرحلة الأولى: فحص الصفحة الرئيسية وجلب الروابط
        res = requests.get(base_url, headers=headers, timeout=10)
        all_found_keys.update(extract_keys(res.text))
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # جمع كل ما هو مشكوك فيه (JS, CSS, API Endpoints)
        to_scan = set()
        for tag in soup.find_all(['script', 'link', 'a']):
            attr = 'src' if tag.name == 'script' else 'href'
            link = tag.get(attr)
            if link:
                full_url = urljoin(base_url, link)
                # فحص الروابط التي تنتمي لنفس الموقع أو روابط Stripe فقط
                if urlparse(full_url).netloc == urlparse(base_url).netloc or 'stripe' in full_url:
                    to_scan.add(full_url)

        # إضافة روابط تخمينية (Brute-force common paths)
        common_paths = ['/js/stripe.js', '/api/config', '/v1/keys', '/static/main.js']
        for p in common_paths: to_scan.add(urljoin(base_url, p))

        # 2. المرحلة الثانية: الفحص المتوازي العميق (15 Threads)
        def fetch_and_scan(link):
            if link in scanned_links: return {}
            scanned_links.add(link)
            try:
                r = requests.get(link, headers=headers, timeout=5)
                return extract_keys(r.text)
            except: return {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(fetch_and_scan, to_scan)
            for res_dict in results:
                for label, keys in res_dict.items():
                    all_found_keys[label] = list(set(all_found_keys.get(label, []) + keys))

        return jsonify({
            "status": "Success", 
            "total_scanned": len(scanned_links), 
            "keys_found": all_found_keys
        })

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
