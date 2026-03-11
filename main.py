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
    <title>LYNIX PRO CHECKER</title>
    <style>
        :root { --bg: #080808; --card-bg: #121212; --border: #222; --accent: #007bff; --hit: #2ecc71; --live: #f1c40f; --dead: #e74c3c; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: #fff; margin: 0; padding: 15px; }
        .wrapper { max-width: 1300px; margin: auto; }
        
        header { text-align: center; padding: 20px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
        header h1 { margin: 0; font-size: 26px; color: var(--accent); text-transform: uppercase; letter-spacing: 3px; }

        .input-section { background: var(--card-bg); padding: 20px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
        textarea { width: 100%; height: 100px; background: #000; color: #0f0; border: 1px solid var(--border); padding: 12px; border-radius: 8px; font-family: monospace; font-size: 14px; box-sizing: border-box; text-align: left; direction: ltr; }
        
        .controls { display: flex; align-items: center; gap: 15px; margin-top: 15px; }
        button#startBtn { background: var(--accent); color: #fff; border: none; padding: 12px 40px; border-radius: 30px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        button#startBtn:hover { background: #0056b3; transform: scale(1.02); }
        #status-label { font-size: 14px; color: #888; }

        /* توزيع الخانات بشكل أفقي */
        .results-container { display: flex; flex-direction: row; gap: 15px; margin-top: 10px; }
        .column { flex: 1; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); height: 500px; display: flex; flex-direction: column; }
        
        .column-header { padding: 12px 15px; background: rgba(255,255,255,0.03); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; font-weight: bold; font-size: 14px; }
        .column-content { padding: 10px; overflow-y: auto; flex-grow: 1; }

        .col-hit { border-top: 4px solid var(--hit); }
        .col-live { border-top: 4px solid var(--live); }
        .col-dead { border-top: 4px solid var(--dead); }

        /* شكل البطاقة داخل الخانة */
        .card-row { background: #000; border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 8px; border-radius: 6px; position: relative; text-align: right; }
        .card-data { display: block; font-family: monospace; font-size: 13px; margin-bottom: 3px; color: #ddd; direction: ltr; text-align: right; }
        .card-msg { font-size: 11px; opacity: 0.7; }
        
        .hit-line { border-right: 4px solid var(--hit); }
        .live-line { border-right: 4px solid var(--live); }
        .dead-line { border-right: 4px solid var(--dead); }

        @media (max-width: 900px) { .results-container { flex-direction: column; } .column { height: 350px; } }
    </style>
</head>
<body>
    <div class="wrapper">
        <header><h1>LYNIX PRO V6</h1></header>
        <div class="input-section">
            <textarea id="cardList" placeholder="أدخل اللستة هنا..."></textarea>
            <div class="controls">
                <button id="startBtn" onclick="processCards()">🚀 فحص اللستة</button>
                <span id="status-label">الحالة: جاهز للعمل</span>
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
            const lines = input.split('\\n').filter(l => l.trim() !== '');
            isRunning = true;
            document.getElementById('startBtn').innerText = "⏳ جاري الفحص...";
            const types = ['hit', 'live', 'dead'];
            types.forEach(t => { document.getElementById('content-' + t).innerHTML = ''; document.getElementById('count-' + t).innerText = '0'; });

            for (let i = 0; i < lines.length; i++) {
                document.getElementById('status-label').innerText = `فحص ${i+1} من ${lines.length}...`;
                try {
                    const response = await fetch('/check', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ card: lines[i] }) });
                    const res = await response.json();
                    const type = res.status.toLowerCase();
                    const container = document.getElementById('content-' + type);
                    const row = document.createElement('div');
                    row.className = `card-row ${type}-line`;
                    row.innerHTML = `<span class="card-data">${lines[i]}</span><span class="card-msg">${res.msg}</span>`;
                    container.prepend(row);
                    document.getElementById('count-' + type).innerText = parseInt(document.getElementById('count-' + type).innerText) + 1;
                } catch (e) { console.error(e); }
                if (i < lines.length - 1) await new Promise(r => setTimeout(r, 5000));
            }
            isRunning = false;
            document.getElementById('startBtn').innerText = "🚀 فحص اللستة";
            document.getElementById('status-label').innerText = "✅ اكتمل الفحص";
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
        # استخراج الأرقام فقط لضمان عدم وجود أخطاء في التنسيق
        digits = re.findall(r'\d+', card_raw)
        if len(digits) < 4:
            return jsonify({"status": "DEAD", "msg": "بيانات غير مكتملة"})
        
        num, mm, yy, cvc = digits[0], digits[1], digits[2], digits[3]
        if len(yy) == 2: yy = "20" + yy
        
        # الاتصال بـ Stripe
        token = stripe.Token.create(card={"number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc})
        stripe.Charge.create(amount=50, currency="usd", source=token.id)
        return jsonify({"status": "HIT", "msg": "✅ رصيد مؤكد"})

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        if err.get('code') == "insufficient_funds":
            return jsonify({"status": "LIVE", "msg": "⚡ رصيد صفر"})
        return jsonify({"status": "DEAD", "msg": f"❌ {err.get('message', 'مرفوضة')}"})
    except Exception as e:
        # طباعة الخطأ في سجلات Render لمعرفته
        print(f"Error: {str(e)}")
        return jsonify({"status": "DEAD", "msg": "⚠️ فشل فني في المعالجة"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
