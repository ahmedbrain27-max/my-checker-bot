import requests
import re
import json
import base64
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import unquote

app = Flask(__name__)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX SESSION DECODER V23</title>
    <style>
        body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: auto; border: 1px solid #00ff41; padding: 30px; box-shadow: 0 0 50px #00ff41; background: #050505; }
        .res-table { width: 100%; margin-top: 20px; border-collapse: collapse; }
        .res-table td { border: 1px solid #222; padding: 15px; text-align: right; color: #fff; }
        .highlight { color: #00ff41; font-weight: bold; }
        .label { color: #888; width: 30%; }
        input { width: 90%; padding: 15px; background: #000; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; }
        button { width: 100%; padding: 15px; background: #00ff41; color: #000; font-weight: bold; border: none; cursor: pointer; font-size: 1.2rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX SESSION SNIPER V23 ]</h1>
        <p>تحليل روابط cs_live واستخراج البيانات العميقة 🎯</p>
        <input type="text" id="url" placeholder="الصق رابط Stripe Checkout هنا...">
        <button onclick="decodeSession()">فك تشفير الجلسة ⚡</button>
        <div id="status" style="margin-top:20px; color: yellow;"></div>
        <div id="out"></div>
    </div>
    <script>
        async function decodeSession() {
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            const out = document.getElementById('out');
            status.innerHTML = "⏳ جاري تحليل الرابط وفك تشفير حزم البيانات...";
            out.innerHTML = "";
            try {
                const res = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await res.json();
                if(data.status === "Success") {
                    status.innerHTML = "✅ تم الاستخراج بنجاح!";
                    out.innerHTML = `<table class="res-table">
                        <tr><td class="label">المتجر (Merchant)</td><td class="highlight">${data.merchant}</td></tr>
                        <tr><td class="label">المبلغ (Amount)</td><td class="highlight" style="color:#0f0;">${data.amount} ${data.currency}</td></tr>
                        <tr><td class="label">البريد (Email)</td><td class="highlight" style="color:#00bcff;">${data.email}</td></tr>
                        <tr><td class="label">المفتاح (PK Live)</td><td class="highlight" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td class="label">بيان الدفع</td><td class="highlight">${data.statement}</td></tr>
                    </table>`;
                } else { status.innerHTML = "❌ خطأ: " + data.message; }
            } catch(e) { status.innerHTML = "❌ خطأ في الاتصال بالسيرفر"; }
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
    
    # محاكاة متصفح حقيقي لإجبار Stripe على إظهار البيانات
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://checkout.stripe.com/'
    }

    try:
        # الدخول للرابط وجلب محتواه
        res = requests.get(url, headers=headers, timeout=20)
        
        # 1. استخراج الـ PK (نبحث عنه في كود الصفحة وفي الروابط)
        pk = "Not Found"
        pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', res.text)
        if not pk_match:
            # محاولة البحث في الجزء المشفر من الرابط (Hash)
            pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', unquote(url))
        
        if pk_match: pk = pk_match.group(0)

        # 2. استخراج البيانات من كود الـ JSON المدمج (Bootstrapped Data)
        amount = "--"
        currency = "USD"
        email = "غير متوفر"
        merchant = "Stripe Merchant"
        statement = "N/A"

        # استخدام مصفوفة بحث لضمان جلب البيانات حتى لو تغيرت مسمياتها
        data_patterns = {
            "amount": [r'\"amount_total\":(\d+)', r'\"total\":(\d+)', r'\"amount\":(\d+)'],
            "email": [r'\"email\":\"(.*?)\"', r'\"customer_email\":\"(.*?)\"'],
            "merchant": [r'\"merchant_name\":\"(.*?)\"', r'\"display_name\":\"(.*?)\"'],
            "statement": [r'\"statement_descriptor\":\"(.*?)\"']
        }

        for key, patterns in data_patterns.items():
            for p in patterns:
                match = re.search(p, res.text)
                if match:
                    if key == "amount": amount = f"{int(match.group(1)) / 100:.2f}"
                    elif key == "email": email = match.group(1)
                    elif key == "merchant": merchant = match.group(1)
                    elif key == "statement": statement = match.group(1)
                    break

        # محاولة أخيرة لجلب اسم المتجر من الـ Title إذا فشل الـ JSON
        if merchant == "Stripe Merchant":
            title = re.search(r'<title>(.*?)</title>', res.text)
            if title: merchant = title.group(1).replace("Pay ", "").split('|')[0].strip()

        return jsonify({
            "status": "Success",
            "merchant": merchant,
            "amount": amount,
            "currency": currency,
            "email": email,
            "pk": pk,
            "statement": statement
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
