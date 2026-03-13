import requests
import re
import concurrent.futures
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- واجهة المستخدم الاحترافية (Hitter Style) ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX STRIPE HITTER | V8</title>
    <style>
        body { background: #0a0a0a; color: #00ff41; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; }
        .container { max-width: 1000px; margin: auto; border: 1px solid #00ff41; padding: 25px; background: rgba(0,20,0,0.9); box-shadow: 0 0 50px #00ff41; border-radius: 15px; }
        h1 { text-align: center; letter-spacing: 5px; text-transform: uppercase; border-bottom: 2px solid #00ff41; padding-bottom: 10px; }
        input { width: 90%; padding: 18px; background: #000; border: 1px solid #00ff41; color: #fff; margin: 20px 0; font-size: 1.1rem; border-radius: 5px; }
        .btn-main { width: 100%; padding: 15px; background: #00ff41; color: #000; border: none; font-weight: bold; cursor: pointer; font-size: 1.3rem; border-radius: 5px; transition: 0.3s; }
        .btn-main:hover { background: #fff; box-shadow: 0 0 20px #fff; }
        
        /* تصميم الجدول الاحترافي */
        .data-table { width: 100%; margin-top: 30px; border-collapse: collapse; background: #111; }
        .data-table th, .data-table td { border: 1px solid #333; padding: 15px; text-align: right; }
        .data-table th { background: #00ff41; color: #000; }
        .key-val { color: #fff; font-family: monospace; word-break: break-all; }
        .status-badge { padding: 5px 10px; border-radius: 4px; font-size: 0.8rem; background: #004400; color: #0f0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX HITTER PRO V8 ]</h1>
        <p style="text-align:center;">نظام تحليل جلسات الاستخلاص (Session & Gateway Decoder)</p>
        
        <input type="text" id="targetUrl" placeholder="أدخل رابط cs_live أو رابط الموقع المستهدف...">
        <button class="btn-main" onclick="startUltimateFetch()">جلب البيانات العميقة ⚡</button>
        
        <div id="loading" style="display:none; text-align:center; margin-top:20px;">⏳ جاري اختراق الجلسة وتحليل البيانات...</div>
        
        <div id="results"></div>
    </div>

    <script>
        async function startUltimateFetch() {
            const url = document.getElementById('targetUrl').value;
            const resDiv = document.getElementById('results');
            const loader = document.getElementById('loading');
            
            if(!url) return alert("يرجى إدخال الرابط أولاً!");
            
            loader.style.display = "block";
            resDiv.innerHTML = "";
            
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                loader.style.display = "none";
                
                if (data.status === "Success") {
                    let html = `<table class="data-table">
                        <tr><th>المعلومة</th><th>القيمة المستخرجة</th></tr>
                        <tr><td>المتجر (Merchant)</td><td class="key-val">${data.details.merchant || 'Unknown'}</td></tr>
                        <tr><td>المبلغ (Amount)</td><td class="key-val">${data.details.amount || '--'}</td></tr>
                        <tr><td>العملة (Currency)</td><td class="key-val">${data.details.currency || '--'}</td></tr>
                        <tr><td>البريد (Email)</td><td class="key-val">${data.details.email || 'Not Provided'}</td></tr>
                        <tr><td>PK (Live)</td><td class="key-val">${data.keys_found['LIVE Publishable Key'] || 'Not Found'}</td></tr>
                        <tr><td>Session ID</td><td class="key-val">${data.details.session_id || 'N/A'}</td></tr>
                    </table>`;
                    resDiv.innerHTML = html;
                } else {
                    resDiv.innerHTML = "<p style='color:red; text-align:center;'>❌ فشل التحليل: " + data.message + "</p>";
                }
            } catch (err) {
                loader.style.display = "none";
                alert("فشل الاتصال بالسيرفر");
            }
        }
    </script>
</body>
</html>
"""

# --- منطق التحليل العميق (Decoding Logic) ---
def get_session_details(session_id):
    """محاكاة استخراج البيانات من جلسة Stripe (يحتاج API Key حقيقي للعمل الكامل)"""
    # في هذه المرحلة، نقوم بفك تشفير الـ Session ID لاستخراج البيانات المتاحة علنياً
    try:
        # هنا يمكن إضافة طلب مباشر لـ Stripe API إذا كان لديك Secret Key
        # حالياً سنقوم باستخراج البيانات المتوفرة في رابط الجلسة نفسه
        return {
            "amount": "TBD (Analyze in Hitter)",
            "currency": "USD",
            "merchant": "Detected via URL",
            "session_id": session_id
        }
    except: return {}

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/scan', methods=['POST'])
def scan():
    base_url = request.json.get('url')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
    all_found_keys = {}
    details = {"merchant": urlparse(base_url).netloc}

    # اكتشاف الـ Session ID من الرابط مباشرة
    session_match = re.search(r'cs_live_[a-zA-Z0-9]{40,}', base_url)
    if session_match:
        details["session_id"] = session_match.group(0)

    try:
        res = requests.get(base_url, headers=headers, timeout=10)
        
        # البحث عن الأنماط
        patterns = {
            'LIVE Publishable Key': r'pk_live_[a-zA-Z0-9]{24,}',
            'Stripe Account ID': r'acct_[a-zA-Z0-9]{16,}'
        }
        
        for label, pattern in patterns.items():
            matches = re.findall(pattern, res.text)
            if matches: all_found_keys[label] = list(set(matches))[0] # نأخذ أول مفتاح فريد

        return jsonify({
            "status": "Success",
            "keys_found": all_found_keys,
            "details": details
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
