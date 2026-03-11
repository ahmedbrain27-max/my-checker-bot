import stripe
import time
import os
import re
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- المفتاح الخاص بك ---
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LYNIX SECURE CHECKER V7</title>
    <style>
        :root { --bg: #050505; --card-bg: #111; --border: #222; --accent: #0088ff; --hit: #00ff88; --live: #ffcc00; --dead: #ff4444; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: #fff; margin: 0; padding: 15px; text-align: right; }
        .wrapper { max-width: 1200px; margin: auto; }
        header { text-align: center; padding: 20px; border-bottom: 1px solid var(--border); }
        .input-section { background: var(--card-bg); padding: 20px; border-radius: 12px; border: 1px solid var(--border); margin-top: 20px; }
        textarea { width: 100%; height: 100px; background: #000; color: #0f0; border: 1px solid var(--border); padding: 12px; border-radius: 8px; font-family: monospace; direction: ltr; text-align: left; }
        .controls { display: flex; align-items: center; gap: 15px; margin-top: 15px; }
        button { background: var(--accent); color: #fff; border: none; padding: 12px 40px; border-radius: 30px; cursor: pointer; font-weight: bold; }
        .results-container { display: flex; gap: 15px; margin-top: 20px; }
        .column { flex: 1; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); height: 500px; display: flex; flex-direction: column; }
        .column-header { padding: 12px; background: rgba(255,255,255,0.03); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; font-weight: bold; }
        .column-content { padding: 10px; overflow-y: auto; flex-grow: 1; }
        .card-row { background: #000; border-right: 4px solid transparent; padding: 10px; margin-bottom: 8px; border-radius: 4px; text-align: right; }
        .hit-line { border-right-color: var(--hit); color: var(--hit); }
        .live-line { border-right-color: var(--live); color: var(--live); }
        .dead-line { border-right-color: var(--dead); color: var(--dead); }
        @media (max-width: 900px) { .results-container { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="wrapper">
        <header><h1>LYNIX SECURE V7</h1></header>
        <div class="input-section">
            <textarea id="cardList" placeholder="أدخل اللستة هنا..."></textarea>
            <div class="controls">
                <button id="startBtn" onclick="processCards()">🚀 فحص آمن</button>
                <span id="status-label">الحالة: جاهز</span>
            </div>
        </div>
        <div class="results-container">
            <div class="column col-hit"><div class="column-header"><span>✅ HITS</span> <span id="count-hit">0</span></div><div id="content-hit" class="column-content"></div></div>
            <div class="column col-live"><div class="column-header"><span>⚡ LIVE</span> <span id="count-live">0</span></div><div id="content-live" class="column-content"></div></div>
            <div class="column col-dead"><div class="column-header"><span>❌ DEAD</span> <span id="count-dead">0</span></div><div id="content-dead" class="column-content"></div></div>
        </div>
    </div>
    <script>
        let isRunning = false;
        async function processCards() {
            if(isRunning) return;
            const input = document.getElementById('cardList').value.trim();
            if(!input) return;
            const lines = input.split('\\n').filter(l => l.includes('|'));
            isRunning = true;
            for (let i = 0; i < lines.length; i++) {
                document.getElementById('status-label').innerText = `جاري الفحص الآمن ${i+1}/${lines.length}...`;
                try {
                    const response = await fetch('/check', { 
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'}, 
                        body: JSON.stringify({ card: lines[i] }) 
                    });
                    const res = await response.json();
                    const type = res.status.toLowerCase();
                    const row = document.createElement('div');
                    row.className = `card-row ${type}-line`;
                    row.innerHTML = `<b style="direction:ltr; display:block;">${lines[i]}</b><small>${res.msg}</small>`;
                    document.getElementById('content-' + type).prepend(row);
                    document.getElementById('count-' + type).innerText = parseInt(document.getElementById('count-' + type).innerText) + 1;
                } catch (e) { console.error(e); }
                if (i < lines.length - 1) await new Promise(r => setTimeout(r, 5000));
            }
            isRunning = false;
            document.getElementById('status-label').innerText = "✅ انتهى";
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
    card_raw = data.get('card', '')
    try:
        digits = re.findall(r'\d+', card_raw)
        if len(digits) < 4: return jsonify({"status": "DEAD", "msg": "بيانات ناقصة"})
        num, mm, yy, cvc = digits[0], digits[1], digits[2], digits[3]
        if len(yy) == 2: yy = "20" + yy

        # --- التعديل الجوهري لتجاوز القفل ---
        # استخدام PaymentMethod بدلاً من Token مباشر
        pm = stripe.PaymentMethod.create(
            type="card",
            card={"number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc},
        )
        
        # محاولة عمل "تثبيت" للبطاقة للتأكد من رصيدها
        stripe.PaymentIntent.create(
            amount=50,
            currency="usd",
            payment_method=pm.id,
            confirm=True,
            off_session=True,
        )
        return jsonify({"status": "HIT", "msg": "✅ رصيد مؤكد"})

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        if err.get('code') == "insufficient_funds":
            return jsonify({"status": "LIVE", "msg": "⚡ رصيد 0"})
        return jsonify({"status": "DEAD", "msg": f"❌ {err.get('message', 'مرفوضة')}"})
    except Exception as e:
        # إذا استمر الخطأ، سنعرض رسالة مفصلة
        error_msg = str(e)
        if "Sending credit card numbers directly" in error_msg:
            return jsonify({"status": "DEAD", "msg": "⚠️ الحساب يتطلب تفعيل PCI من الإعدادات"})
        return jsonify({"status": "DEAD", "msg": f"⚠️ خطأ: {error_msg[:50]}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
