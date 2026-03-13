import requests
import re
from flask import Flask, request, jsonify, render_template_string
from urllib.parse import unquote

app = Flask(__name__)

# واجهة القنص الاحترافية النهائية
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX MASTER SNIPER V28</title>
    <style>
        body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: auto; border: 2px solid #00ff41; padding: 30px; box-shadow: 0 0 50px #00ff41; background: #050505; border-radius: 15px; }
        .res-table { width: 100%; margin-top: 30px; border-collapse: collapse; background: #0a0a0a; }
        .res-table td { border: 1px solid #222; padding: 18px; text-align: right; color: #fff; font-size: 1.1rem; }
        .highlight { color: #00ff41; font-weight: bold; }
        .label { color: #888; width: 30%; }
        input { width: 90%; padding: 18px; background: #111; border: 1px solid #00ff41; color: #fff; margin-bottom: 25px; font-size: 1rem; border-radius: 5px; }
        button { width: 100%; padding: 18px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; font-size: 1.4rem; border-radius: 5px; transition: 0.3s; }
        button:hover { background: #fff; box-shadow: 0 0 20px #fff; }
        #status { margin-top: 20px; font-size: 1.2rem; color: yellow; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX MASTER SNIPER V28 ]</h1>
        <p>النظام النهائي لتحليل الروابط المشفرة (Stripe & Blackbox Support)</p>
        <input type="text" id="urlInput" placeholder="الصق رابط cs_live هنا...">
        <button onclick="masterCapture()">إطلاق القنص النهائي ⚡</button>
        <div id="status"></div>
        <div id="out"></div>
    </div>

    <script>
        async function masterCapture() {
            const url = document.getElementById('urlInput').value;
            const status = document.getElementById('status');
            const out = document.getElementById('out');
            
            if(!url) return;
            status.innerHTML = "⏳ جاري كسر تشفير الرابط واعتراض البيانات من Stripe API...";
            out.innerHTML = "";

            try {
                // نرسل الرابط للسيرفر للمعالجة العميقة
                const response = await fetch('/scan_v28', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();

                if(data.status === "Success") {
                    status.innerHTML = "✅ تم القنص بنجاح!";
                    out.innerHTML = `
                        <table class="res-table">
                            <tr><td class="label">المتجر</td><td class="highlight">${data.merchant}</td></tr>
                            <tr><td class="label">المبلغ</td><td class="highlight" style="color:#0f0; font-size:1.5rem;">${data.amount} ${data.currency}</td></tr>
                            <tr><td class="label">البريد (Email)</td><td class="highlight" style="color:#00bcff;">${data.email}</td></tr>
                            <tr><td class="label">المفتاح (PK Live)</td><td class="highlight" style="color:yellow;">${data.pk}</td></tr>
                            <tr><td class="label">رقم الحساب</td><td class="highlight">${data.account_id}</td></tr>
                        </table>`;
                } else {
                    status.innerHTML = "❌ فشل: " + data.message;
                }
            } catch (e) {
                status.innerHTML = "❌ خطأ في السيرفر";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/scan_v28', methods=['POST'])
def scan_v28():
    full_url = request.json.get('url')
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    try:
        # 1. فك تشفير الرابط (لأن الـ PK موجود في الـ Hash الذي تضعه)
        decoded_url = unquote(full_url)
        
        # 2. استخراج الـ PK باستخدام Regex جبار يبحث في كل مكان
        pk = "Not Found"
        pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', decoded_url)
        if pk_match: pk = pk_match.group(0)

        # 3. محاكاة طلب حقيقي لصفحة Stripe
        res = requests.get(full_url, headers=headers, timeout=15)
        
        # إذا لم يجد الـ PK في الرابط، يبحث في محتوى الصفحة
        if pk == "Not Found":
            pk_page = re.search(r'pk_live_[a-zA-Z0-9]{24,}', res.text)
            if pk_page: pk = pk_page.group(0)

        # 4. استخراج المبلغ والإيميل (تنقيب عميق في ملفات الـ JSON)
        email = "N/A"
        amount = "0.00"
        currency = "USD"
        account_id = "N/A"

        # أنماط Stripe الحديثة جداً (2025/2026)
        email_find = re.search(r'\"(?:customer_)?email\":\"(.*?)\"', res.text)
        if email_find: email = email_find.group(1)

        amount_find = re.search(r'\"amount_(?:total|subtotal)\":(\d+)', res.text)
        if not amount_find: amount_find = re.search(r'\"total\":(\d+)', res.text)
        if amount_find: amount = f"{int(amount_find.group(1)) / 100:.2f}"

        curr_find = re.search(r'\"currency\":\"([a-z]{3})\"', res.text, re.I)
        if curr_find: currency = curr_find.group(1).upper()
        
        acct_find = re.search(r'acct_[a-zA-Z0-9]{16,}', res.text)
        if acct_find: account_id = acct_find.group(0)

        # اسم المتجر
        merchant = "Stripe Merchant"
        title = re.search(r'<title>(.*?)</title>', res.text)
        if title: merchant = title.group(1).replace("Pay ", "").split('|')[0].strip()

        return jsonify({
            "status": "Success",
            "merchant": merchant,
            "amount": amount,
            "currency": currency,
            "email": email,
            "pk": pk,
            "account_id": account_id
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
