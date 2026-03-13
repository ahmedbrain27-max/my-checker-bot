import requests
import re
import json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# واجهة مستخدم احترافية وسريعة
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX FAST SNIPER V17</title>
    <style>
        body { background: #0a0a0a; color: #00ff41; font-family: monospace; padding: 20px; text-align: center; }
        .container { max-width: 750px; margin: auto; border: 1px solid #00ff41; padding: 25px; box-shadow: 0 0 20px #00ff41; background: #000; border-radius: 10px; }
        input { width: 90%; padding: 15px; background: #111; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; font-size: 1rem; }
        button { width: 100%; padding: 15px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; font-size: 1.2rem; }
        .res-table { width: 100%; margin-top: 25px; border-collapse: collapse; }
        .res-table td { border: 1px solid #222; padding: 12px; text-align: right; }
        .val { color: #fff; word-break: break-all; }
        .highlight { color: #00ff41; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX FAST SNIPER V17 ]</h1>
        <p>نظام القنص البرمجي المباشر (بدون متصفح)</p>
        <input type="text" id="url" placeholder="الصق رابط cs_live هنا...">
        <button onclick="fastScan()">بدء القنص السريع ⚡</button>
        <div id="status" style="margin-top:15px; color: yellow;"></div>
        <div id="output"></div>
    </div>
    <script>
        async function fastScan() {
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            
            status.innerHTML = "⏳ جاري اعتراض بيانات Stripe مباشرة...";
            output.innerHTML = "";
            
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                
                if(data.status === "Success") {
                    status.innerHTML = "✅ تم القنص بنجاح!";
                    output.innerHTML = `<table class="res-table">
                        <tr><td>المتجر (Merchant)</td><td class="val highlight">${data.merchant}</td></tr>
                        <tr><td>المبلغ (Amount)</td><td class="val highlight" style="color:#0f0;">${data.amount} ${data.currency}</td></tr>
                        <tr><td>الـ PK (Live)</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td>ID الجلسة</td><td class="val">${data.session_id}</td></tr>
                    </table>`;
                } else {
                    status.innerHTML = "❌ خطأ: " + data.message;
                }
            } catch(e) { status.innerHTML = "❌ فشل الاتصال."; }
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
    # محاكاة متصفح موبايل لتجنب الحظر وجلب البيانات المخفية
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        # تتبع الرابط وسحب محتواه بالكامل
        session = requests.Session()
        res = session.get(target_url, headers=headers, timeout=15, allow_redirects=True)
        
        # 1. استخراج الـ PK باستخدام بحث ذكي
        pk = "Not Found"
        pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', res.text)
        if pk_match: pk = pk_match.group(0)

        # 2. استخراج المبلغ والعملة من بيانات الـ JSON المدمجة في الصفحة
        amount = "--"
        currency = "USD"
        # Stripe يضع البيانات المالية غالباً في سطر JSON يبدأ بـ total أو amount
        money_match = re.search(r'\"amount\":(\d+),\"currency\":\"([a-z]{3})\"', res.text)
        if not money_match:
            money_match = re.search(r'\"total\":(\d+),\"currency\":\"([a-z]{3})\"', res.text)
            
        if money_match:
            amount = f"{int(money_match.group(1)) / 100:.2f}"
            currency = money_match.group(2).upper()

        # 3. استخراج اسم المتجر من عنوان الصفحة
        merchant = "Unknown Merchant"
        title = re.search(r'<title>(.*?)</title>', res.text)
        if title:
            merchant = title.group(1).replace("Pay ", "").split('|')[0].strip()

        # 4. معرف الجلسة من الرابط
        sid = re.search(r'cs_live_[a-zA-Z0-9]{30,}', target_url)

        return jsonify({
            "status": "Success",
            "pk": pk,
            "amount": amount,
            "currency": currency,
            "merchant": merchant,
            "session_id": sid.group(0) if sid else "N/A"
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
