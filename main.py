import stripe
import time
import os
import re
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- مفتاح Stripe الخاص بك ---
stripe.api_key = "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"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LYNIX PREMIUM CHECKER</title>
    <style>
        :root { --bg: #0a0a0a; --card-bg: #111; --border: #222; --accent: #3498db; --hit: #2ecc71; --live: #f1c40f; --dead: #e74c3c; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: #fff; margin: 0; padding: 20px; text-align: right; }
        .wrapper { max-width: 1200px; margin: auto; }
        header { text-align: center; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
        header h1 { margin: 0; font-size: 28px; color: var(--accent); letter-spacing: 2px; }
        .input-section { background: var(--card-bg); padding: 25px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 25px; }
        textarea { width: 100%; height: 120px; background: #000; color: #00ff41; border: 1px solid var(--border); padding: 15px; border-radius: 8px; font-family: monospace; box-sizing: border-box; font-size: 15px; text-align: left; direction: ltr; }
        .controls { display: flex; align-items: center; gap: 20px; margin-top: 15px; }
        button { background: var(--accent); color: #fff; border: none; padding: 14px 45px; border-radius: 30px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s; }
        #status-label { font-size: 15px; color: #aaa; }
        
        /* التنسيق الأفقي للأعمدة */
        .results-container { display: flex; flex-direction: row; gap: 15px; justify-content: center; }
        .column { flex: 1; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); height: 550px; display: flex; flex-direction: column; overflow: hidden; }
        .column-header { padding: 15px; background: rgba(255,255,255,0.05); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; font-weight: bold; }
        .column-content { padding: 12px; overflow-y: auto; flex-grow: 1; text-align: right; direction: rtl; }
        
        .col-hit { border-top: 5px solid var(--hit); }
        .col-live { border-top: 5px solid var(--live); }
        .col-dead { border-top: 5px solid var(--dead); }
        
        .card-row { background: #050505; border: 1px solid #222; padding: 10px; margin-bottom: 10px; border-radius: 6px; animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        /* جعل أرقام البطاقة تظهر بوضوح من اليمين */
        .card-num { display: block; font-family: monospace; font-size: 14px; margin-bottom: 4px; direction: ltr; text-align: right; }
        .hit-text { color: var(--hit); }
        .live-text { color: var(--live); }
        .dead-text { color: var(--dead); }
        
        @media (max-width: 900px) { .results-container { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="wrapper">
        <header><h1>LYNIX PREMIUM CHECKER</h1></header>
        <div class="input-section">
            <textarea id="cardList" placeholder="أدخل اللستة هنا (CARD|MM|YY|CVV)"></textarea>
            <div class="controls">
                <button onclick="processCards()">🚀 بدء الفحص</button>
                <span id="status-label">الحالة: جاهز</span>
            </div>
        </div>
        <div class="results-container">
            <div class="column col-hit">
                <div class="column-header"><span>✅ HITS</span> <span id="count-hit">0</span></div>
                <div id="content-hit" class="column-content"></div>
            </div>
            <div class="column col-live">
                <div class="column-header"><span>⚡ LIVE</span> <span id="count-live">0</span></div>
                <div id="content-live" class="column-content"></div>
            </div>
            <div class="column col-dead">
                <div class="column-header"><span>❌ DEAD</span> <span id="count-dead">0</span></div>
                <div id="content-dead" class="column-content"></div>
            </div>
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
            const statusLabel = document.getElementById('status-label');
            const types = ['hit', 'live', 'dead'];
            types.forEach(t => {
                document.getElementById('content-' + t).innerHTML = '';
                document.getElementById('count-' + t).innerText = '0';
            });
            for (let i = 0; i < lines.length; i++) {
                let card = lines[i].trim();
                statusLabel.innerText = `⏳ جاري فحص ${i+1} من ${lines.length}...`;
                try {
                    const response = await fetch('/check', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ card: card })
                    });
                    const res = await response.json();
                    const type = res.status.toLowerCase();
                    const container = document.getElementById('content-' + type);
                    const counter = document.getElementById('count-' + type);
                    
                    const row = document.createElement('div');
                    row.className = 'card-row ' + type + '-text';
                    row.innerHTML = `<span class="card-num">${card}</span><small style="color:#888">${res.msg}</small>`;
                    container.prepend(row);
                    
                    counter.innerText = parseInt(counter.innerText) + 1;
                } catch (err) { console.error(err); }
                if (i < lines.length - 1) await new Promise(r => setTimeout(r, 5000));
            }
            isRunning = false;
            statusLabel.innerText = "✅ اكتمل الفحص!";
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
        token = stripe.Token.create(card={"number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc})
        stripe.Charge.create(amount=50, currency="usd", source=token.id)
        return jsonify({"status": "HIT", "msg": "رصيد مؤكد"})
    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        if err.get('code') == "insufficient_funds":
            return jsonify({"status": "LIVE", "msg": "رصيد صفر"})
        return jsonify({"status": "DEAD", "msg": err.get('message', 'مرفوضة')})
    except Exception:
        return jsonify({"status": "DEAD", "msg": "خطأ في المعالجة"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
