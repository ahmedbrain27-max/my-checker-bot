import requests
import re
import json
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import urlparse

app = Flask(__name__)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX PRO ULTRA V19</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: monospace; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: auto; border: 1px solid #00ff41; padding: 25px; box-shadow: 0 0 30px #00ff41; background: #000; }
        input { width: 90%; padding: 15px; background: #111; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; }
        button { width: 100%; padding: 15px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; font-size: 1.2rem; }
        .res-table { width: 100%; margin-top: 30px; border-collapse: collapse; }
        .res-table td { border: 1px solid #222; padding: 15px; text-align: right; }
        .val { color: #fff; word-break: break-all; }
        .success { color: #0f0; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX ULTRA V19 ]</h1>
        <p>نظام القنص البرمجي المباشر (بدون متصفح - مستقر 100%)</p>
        <input type="text" id="url" placeholder="الصق رابط cs_live هنا...">
        <button onclick="scan()">إطلاق القنص ⚡</button>
        <div id="status" style="margin-top:20px;"></div>
        <div id="out"></div>
    </div>
    <script>
        async function scan() {
            const url = document.getElementById('url').value;
            const out = document.getElementById('out');
            const status = document.getElementById('status');
            status.innerHTML = "⏳ جاري استخلاص البيانات من خوادم Stripe...";
            out.innerHTML = "";
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                if(data.status === "Success") {
                    status.innerHTML = "✅ تم القنص!";
                    out.innerHTML = `<table class="res-table">
                        <tr><td>المتجر</td><td class="val">${data.merchant}</td></tr>
                        <tr><td>المبلغ</td><td class="val success">${data.amount} ${data.currency}</td></tr>
                        <tr><td>الـ PK</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td>Session ID</td><td class="val">${data.session_id}</td></tr>
                    </table>`;
                } else { status.innerHTML = "❌ فشل: " + data.message; }
            } catch(e) { status.innerHTML = "❌ خطأ في السيرفر"; }
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
    url = request.json.get('url')
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://checkout.stripe.com/'
    }

    try:
        session = requests.Session()
        # الخطوة 1: الدخول للرابط وسحب الكود
        res = session.get(url, headers=headers, timeout=20)
        
        # الخطوة 2: استخراج الـ PK (نبحث عنه في كل الصفحة)
        pk = "Not Found"
        pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', res.text)
        if pk_match:
            pk = pk_match.group(0)

        # الخطوة 3: استخراج المبلغ والعملة (نبحث في مصفوفة JSON المدمجة)
        amount = "--"
        currency = "USD"
        # نبحث عن أنماط Stripe المالية المشهورة
        json_patterns = [
            r'\"amount\":(\d+)',
            r'\"total\":(\d+)',
            r'\"unit_amount\":(\d+)'
        ]
        
        for p in json_patterns:
            m = re.search(p, res.text)
            if m:
                amount = f"{int(m.group(1)) / 100:.2f}"
                break
                
        curr_match = re.search(r'\"currency\":\"([a-z]{3})\"', res.text, re.I)
        if curr_match:
            currency = curr_match.group(1).upper()

        # الخطوة 4: استخراج اسم المتجر
        merchant = urlparse(url).netloc
        title = re.search(r'<title>(.*?)</title>', res.text)
        if title:
            merchant = title.group(1).replace("Pay ", "").split('|')[0].strip()

        return jsonify({
            "status": "Success",
            "merchant": merchant,
            "amount": amount,
            "currency": currency,
            "pk": pk,
            "session_id": re.search(r'cs_live_[a-zA-Z0-9]{30,}', url).group(0) if "cs_live" in url else "N/A"
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
