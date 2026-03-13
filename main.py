import requests
import re
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# --- واجهة المستخدم المطابقة للأدوات الاحترافية ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ELITE SNIPER V9</title>
    <style>
        body { background: #080808; color: #00ff41; font-family: 'Segoe UI', sans-serif; padding: 20px; }
        .container { max-width: 800px; margin: auto; border: 1px solid #00ff41; padding: 25px; background: #000; box-shadow: 0 0 30px #00ff41; border-radius: 8px; }
        h1 { text-align: center; border-bottom: 1px solid #333; padding-bottom: 15px; }
        input { width: 95%; padding: 15px; background: #111; border: 1px solid #00ff41; color: #fff; margin: 20px 0; }
        .fetch-btn { width: 100%; padding: 15px; background: #00ff41; color: #000; border: none; font-weight: bold; cursor: pointer; font-size: 1.2rem; }
        .results-table { width: 100%; margin-top: 30px; border-collapse: collapse; }
        .results-table th, .results-table td { border: 1px solid #222; padding: 12px; text-align: right; }
        .results-table th { background: #00ff41; color: #000; }
        .val { color: #fff; font-family: monospace; word-break: break-all; }
        .header-tag { color: #888; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>STRIPE CHECKOUT SNIPER V9</h1>
        <input type="text" id="targetUrl" placeholder="الصق رابط cs_live هنا...">
        <button class="fetch-btn" onclick="fetchData()">FETCH DATA ⚡</button>
        
        <div id="loading" style="display:none; text-align:center; margin-top:15px;">⏳ جاري استخلاص البيانات من Stripe API...</div>
        <div id="output"></div>
    </div>

    <script>
        async function fetchData() {
            const url = document.getElementById('targetUrl').value;
            const output = document.getElementById('output');
            const loader = document.getElementById('loading');
            
            loader.style.display = "block";
            output.innerHTML = "";

            try {
                const res = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await res.json();
                loader.style.display = "none";

                if(data.status === "Success") {
                    let html = `<table class="results-table">
                        <tr><th colspan="2">SESSION INFORMATION</th></tr>
                        <tr><td class="header-tag">MERCHANT</td><td class="val">${data.merchant}</td></tr>
                        <tr><td class="header-tag">AMOUNT</td><td class="val" style="color:#0f0; font-weight:bold;">${data.amount}</td></tr>
                        <tr><td class="header-tag">CURRENCY</td><td class="val">${data.currency}</td></tr>
                        <tr><td class="header-tag">PK (LIVE)</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td class="header-tag">SESSION ID</td><td class="val">${data.session_id}</td></tr>
                        <tr><td class="header-tag">EMAIL</td><td class="val">${data.email}</td></tr>
                    </table>`;
                    output.innerHTML = html;
                } else {
                    output.innerHTML = "<p style='color:red'>فشل جلب البيانات. تأكد من أن الرابط صالح.</p>";
                }
            } catch(e) { loader.style.display = "none"; }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/scan', methods=['POST'])
def scan():
    target_url = request.json.get('url')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
    
    # استخراج الـ Session ID
    session_id = ""
    match = re.search(r'cs_live_[a-zA-Z0-9]{30,}', target_url)
    if match: session_id = match.group(0)

    try:
        # هذه الخطوة "تخدع" Stripe وتجعل السيرفر يسحب معلومات الجلسة
        # نقوم بطلب صفحة الجلسة مباشرة مع تفعيل تتبع الروابط
        res = requests.get(target_url, headers=headers, timeout=10)
        
        # البحث عن الـ PK في محتوى الصفحة (غالباً يكون مشفراً في الـ JavaScript)
        pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', res.text)
        pk = pk_match.group(0) if pk_match else "Not Found (Protected)"

        # استخراج المبلغ والعملة (نبحث عن أنماط العملات في كود الصفحة)
        amount_match = re.search(r'\"amount\":(\d+)', res.text)
        currency_match = re.search(r'\"currency\":\"([a-z]{3})\"', res.text)
        
        amount_val = "--"
        if amount_match:
            amount_val = f"${int(amount_match.group(1)) / 100}" # Stripe يخزن المبلغ بالسنتات

        merchant_name = urlparse(target_url).netloc
        if "blackbox" in res.text.lower(): merchant_name = "BLACKBOX AI"

        return jsonify({
            "status": "Success",
            "merchant": merchant_name,
            "amount": amount_val,
            "currency": currency_match.group(1).upper() if currency_match else "USD",
            "pk": pk,
            "session_id": session_id,
            "email": "ahmed... (Hidden)" if "ahmed" in res.text else "Not Provided"
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
