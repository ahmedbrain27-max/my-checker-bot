import requests
import re
import json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX FULL EXTRACTOR V21</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: auto; border: 1px solid #0f0; padding: 25px; box-shadow: 0 0 20px #0f0; background: #050505; }
        .res-table { width: 100%; margin-top: 20px; border-collapse: collapse; background: #111; }
        .res-table td { border: 1px solid #333; padding: 12px; text-align: right; color: #fff; }
        .highlight { color: #0f0; font-weight: bold; }
        .label { color: #888; width: 30%; }
        input { width: 90%; padding: 15px; background: #000; border: 1px solid #0f0; color: #fff; margin-bottom: 20px; }
        button { width: 100%; padding: 15px; background: #0f0; color: #000; font-weight: bold; border: none; cursor: pointer; font-size: 1.1rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX FULL SNIPER V21 ]</h1>
        <p>استخراج شامل: المبلغ، الـ PK، والإيميل 🎯</p>
        <input type="text" id="url" placeholder="الصق رابط cs_live هنا...">
        <button onclick="extract()">إطلاق الاستخراج الشامل ⚡</button>
        <div id="status" style="margin-top:20px; color: yellow;"></div>
        <div id="out"></div>
    </div>
    <script>
        async function extract() {
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            const out = document.getElementById('out');
            status.innerHTML = "⏳ جاري التنقيب عن البيانات والإيميلات المخفية...";
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
                        <tr><td class="label">المتجر</td><td class="highlight">${data.merchant}</td></tr>
                        <tr><td class="label">المبلغ</td><td class="highlight" style="color:#0f0;">${data.amount} ${data.currency}</td></tr>
                        <tr><td class="label">البريد (Email)</td><td class="highlight" style="color:#00bcff;">${data.email}</td></tr>
                        <tr><td class="label">الـ PK (Live)</td><td class="highlight" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td class="label">وصف العملية</td><td class="highlight">${data.statement}</td></tr>
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
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        
        # 1. استخراج الإيميل (Email)
        # نبحث عن نمط الإيميل داخل كود الـ JSON المدمج
        email_match = re.search(r'\"email\":\"(.*?)\"', res.text)
        email = email_match.group(1) if email_match else "غير متوفر (Not Provided)"

        # 2. استخراج المبلغ والعملة
        amount = "--"
        money_data = re.search(r'\"amount_total\":(\d+)', res.text)
        if money_data:
            amount = f"{int(money_data.group(1)) / 100:.2f}"
        
        # 3. استخراج الـ PK
        pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', res.text)
        
        # 4. استخراج وصف الفاتورة (Statement Descriptor)
        statement = "N/A"
        st_match = re.search(r'\"statement_descriptor\":\"(.*?)\"', res.text)
        if st_match: statement = st_match.group(1)

        return jsonify({
            "status": "Success",
            "merchant": "BLACKBOX AI" if "blackbox" in res.text.lower() else "Stripe Merchant",
            "amount": amount,
            "currency": "USD",
            "email": email,
            "pk": pk_match.group(0) if pk_match else "Not Found",
            "statement": statement
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
