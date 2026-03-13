import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urljoin

app = Flask(__name__)

# دالة البحث عن المفاتيح (نفس المنطق السابق)
def find_keys_in_text(text):
    keys = {}
    pk = re.search(r'pk_live_[a-zA-Z0-9]{24,}', text)
    cs = re.search(r'pi_[a-zA-Z0-9]{16,}_secret_[a-zA-Z0-9]{24,}', text)
    if pk: keys['pk'] = pk.group(0)
    if cs: keys['cs'] = cs.group(0)
    return keys

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/scan', methods=['POST'])
def scan_url():
    target_url = request.json.get('url')
    if not target_url: return jsonify({"error": "No URL provided"}), 400
    
    found_data = {"pk": "Not Found", "cs": "Not Found", "js_files": []}
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(target_url, headers=headers, timeout=10)
        source = response.text
        
        # فحص الصفحة الرئيسية
        keys = find_keys_in_text(source)
        found_data.update(keys)
        
        # فحص ملفات JS
        soup = BeautifulSoup(source, 'html.parser')
        for script in soup.find_all('script'):
            src = script.get('src')
            if src:
                js_url = urljoin(target_url, src)
                found_data['js_files'].append(js_url)
                try:
                    js_res = requests.get(js_url, headers=headers, timeout=5)
                    js_keys = find_keys_in_text(js_res.text)
                    if js_keys.get('pk'): found_data['pk'] = js_keys['pk']
                    if js_keys.get('cs'): found_data['cs'] = js_keys['cs']
                except: continue
                
        return jsonify(found_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# واجهة المستخدم (HTML UI)
HTML_UI = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Stripe Key Scanner | LYNIX</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: monospace; padding: 20px; }
        .box { border: 1px solid #00ff41; padding: 20px; max-width: 700px; margin: auto; box-shadow: 0 0 15px #00ff41; }
        input { width: 80%; padding: 10px; background: #000; border: 1px solid #00ff41; color: #fff; }
        button { padding: 10px 20px; background: #00ff41; color: #000; border: none; cursor: pointer; font-weight: bold; }
        .result { margin-top: 20px; padding: 10px; border-top: 1px solid #333; }
        .key-found { color: #fff; background: #222; padding: 5px; margin: 5px 0; display: block; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🔍 STRIPE KEY SCANNER (PRO)</h2>
        <p>أدخل رابط الموقع لتحليله واستخراج المفاتيح:</p>
        <input type="text" id="targetUrl" placeholder="https://example.com/checkout">
        <button onclick="startScan()">إبدأ الفحص</button>
        <div id="results" class="result"></div>
    </div>

    <script>
        async function startScan() {
            const url = document.getElementById('targetUrl').value;
            const resDiv = document.getElementById('results');
            resDiv.innerHTML = "⏳ جاري تحليل الموقع وملفات الـ JS...";
            
            const response = await fetch('/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            });
            const data = await response.json();
            
            if(data.error) {
                resDiv.innerHTML = "❌ خطأ: " + data.error;
            } else {
                resDiv.innerHTML = `
                    <p>النتائج المستخرجة:</p>
                    <span class="key-found">PK_LIVE: ${data.pk}</span>
                    <span class="key-found">CLIENT_SECRET: ${data.cs}</span>
                    <p style="font-size:0.8rem">تم فحص ${data.js_files.length} ملفات JS.</p>
                `;
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
