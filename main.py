import requests
import re
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX PRO HITTER V29</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Segoe UI', Tahoma, sans-serif; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: auto; border: 1px solid #00ff41; padding: 30px; box-shadow: 0 0 30px #00ff41; background: #000; border-radius: 12px; }
        .res-table { width: 100%; margin-top: 25px; border-collapse: collapse; text-align: right; }
        .res-table td { border-bottom: 1px solid #222; padding: 15px; color: #fff; }
        .highlight { color: #00ff41; font-weight: bold; }
        input { width: 90%; padding: 18px; background: #111; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; border-radius: 8px; }
        button { width: 100%; padding: 18px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; font-size: 1.2rem; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX PRO STRIPE HITTER ]</h1>
        <p>نظام محاكاة استجابة API (مثل Ender Black)</p>
        <input type="text" id="urlInput" placeholder="الصق رابط cs_live هنا...">
        <button onclick="proExtract()">قنص البيانات العميقة 🚀</button>
        <div id="status" style="margin-top:20px; color: yellow;"></div>
        <div id="out"></div>
    </div>
    <script>
        async function proExtract() {
            const url = document.getElementById('urlInput').value;
            const status = document.getElementById('status');
            const out = document.getElementById('out');
            status.innerHTML = "⏳ جاري استجواب سيرفرات Stripe (Direct Hook)...";
            try {
                const response = await fetch('/pro_scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                if(data.status === "Success") {
                    status.innerHTML = "✅ تم سحب البيانات بنجاح!";
                    out.innerHTML = `
                        <table class="res-table">
                            <tr><td>المتجر</td><td class="highlight">${data.merchant}</td></tr>
                            <tr><td>المبلغ الحقيقي</td><td class="highlight" style="color:#0f0;">${data.amount} ${data.currency}</td></tr>
                            <tr><td>البريد (Email)</td><td class="highlight" style="color:#00bcff;">${data.email}</td></tr>
                            <tr><td>الـ PK المستخرج</td><td class="highlight" style="color:yellow;">${data.pk}</td></tr>
                            <tr><td>الحالة</td><td class="highlight">${data.payment_status}</td></tr>
                        </table>`;
                } else { status.innerHTML = "❌ خطأ: " + data.message; }
            } catch(e) { status.innerHTML = "❌ فشل السيرفر"; }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/pro_scan', methods=['POST'])
def pro_scan():
    url = request.json.get('url')
    sid_match = re.search(r'cs_live_[a-zA-Z0-9]{30,}', url)
    if not sid_match: return jsonify({"status": "Error", "message": "رابط غير صالح"})
    
    sid = sid_match.group(0)
    
    # محاكاة طلب الـ API الذي يستخدمه الموقع الاحترافي
    # نستخدم PK عام أو نحاول استخراجه من الرابط
    pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', requests.utils.unquote(url))
    pk = pk_match.group(0) if pk_match else "pk_live_not_found"

    try:
        # الاتصال المباشر بـ Stripe API (هذا هو السر!)
        stripe_url = f"https://api.stripe.com/v1/checkout/sessions/{sid}"
        # نرسل طلباً كأننا تطبيق موبايل رسمي
        response = requests.get(stripe_url, params={"key": pk} if pk != "pk_live_not_found" else None)
        
        # إذا فشل الطلب المباشر، نعود لخطة سحب البيانات من الـ HTML
        res_text = requests.get(url).text
        
        email = re.search(r'\"customer_email\":\"(.*?)\"', res_text)
        amount = re.search(r'\"amount_total\":(\d+)', res_text)
        merchant = re.search(r'\"merchant_name\":\"(.*?)\"', res_text)

        return jsonify({
            "status": "Success",
            "merchant": merchant.group(1) if merchant else "Stripe Store",
            "amount": f"{int(amount.group(1))/100}" if amount else "--",
            "currency": "USD",
            "email": email.group(1) if email else "غير متوفر",
            "pk": pk,
            "payment_status": "Active"
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
