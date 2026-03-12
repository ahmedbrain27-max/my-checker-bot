import stripe
import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ضع مفتاح الـ sk_live الخاص بك هنا
stripe.api_key = "sk_live_..." 

HTML_GATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ELITE GATE v10</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: monospace; text-align: center; padding: 50px; }
        .gate-box { border: 2px solid #00ff41; padding: 30px; display: inline-block; border-radius: 10px; box-shadow: 0 0 20px #00ff41; }
        input, button { background: #000; color: #00ff41; border: 1px solid #00ff41; padding: 10px; margin: 10px; font-weight: bold; }
        button { cursor: pointer; transition: 0.3s; background: #00ff41; color: #000; }
        button:hover { background: #fff; color: #000; }
        .status { margin-top: 20px; font-size: 1.2rem; }
    </style>
</head>
<body>
    <div class="gate-box">
        <h1>🛡️ LYNIX PRIVATE GATE</h1>
        <p>أدخل بيانات البطاقة لفتح بوابة دفع رسمية مخصصة لها</p>
        <input type="text" id="card_data" placeholder="CARD|MM|YY|CVV" style="width: 300px;">
        <br>
        <button onclick="createGate()">إنشاء بوابة دفع (Charge Gate) 🚀</button>
        <div id="res" class="status"></div>
    </div>

    <script>
        async function createGate() {
            const data = document.getElementById('card_data').value;
            const resDiv = document.getElementById('res');
            resDiv.innerHTML = "⏳ جاري تهيئة البوابة...";
            
            try {
                const response = await fetch('/generate-gate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ card: data })
                });
                const result = await response.json();
                if(result.url) {
                    resDiv.innerHTML = `<a href="${result.url}" target="_blank" style="color:white; text-decoration:none;">✅ تم تجهيز البوابة! اضغط هنا للفحص</a>`;
                    window.open(result.url, '_blank');
                } else {
                    resDiv.innerHTML = "❌ خطأ في المفتاح أو الحساب";
                }
            } catch (e) {
                resDiv.innerHTML = "⚠️ خطأ في الاتصال";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_GATE)

@app.route('/generate-gate', methods=['POST'])
def generate_gate():
    try:
        # إنشاء جلسة دفع رسمية بمبلغ محدد (مثلاً 15 دولار كما نجحت معك)
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Digital Product Access'},
                    'unit_amount': 1499, # 14.99 USD
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
