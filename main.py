import stripe
import time
import os
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
    <title>LYNIX PRECISION CHECKER V4</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: #eee; text-align: center; padding: 10px; }
        .container { max-width: 1000px; margin: auto; background: #151515; padding: 20px; border-radius: 15px; border: 1px solid #333; }
        textarea { width: 95%; height: 120px; background: #222; color: #0f0; border: 1px solid #444; padding: 10px; border-radius: 8px; font-family: monospace; margin-bottom: 10px; }
        button { background: #3498db; color: white; border: none; padding: 12px 50px; cursor: pointer; border-radius: 25px; font-size: 18px; font-weight: bold; margin-bottom: 20px; }
        
        .results-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 10px; }
        .box { background: #111; border-radius: 10px; padding: 10px; height: 350px; overflow-y: auto; border: 1px solid #222; text-align: left; position: relative; }
        .box-title { position: sticky; top: 0; background: #111; padding: 5px; font-weight: bold; text-align: center; border-bottom: 1px solid #333; margin-bottom: 10px; }
        
        .hit-box { border-top: 4px solid #2ecc71; color: #2ecc71; }
        .live-box { border-top: 4px solid #f1c40f; color: #f1c40f; }
        .dead-box { border-top: 4px solid #e74c3c; color: #e74c3c; }
        
        .card-entry { font-size: 12px; margin-bottom: 5px; padding: 5px; background: #1a1a1a; border-radius: 4px; word-break: break-all; border: 1px solid #222; }
        #status { color: #3498db; font-weight: bold; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 LYNIX CHECKER V4</h1>
        <div id="status">جاهز للفحص</div>
        
        <textarea id="cardList" placeholder="أدخل اللستة هنا..."></textarea><br>
        <button onclick="startCheck()">🚀 بدء الفحص (5s)</button>

        <div class="results-grid">
            <div class="box hit-box">
                <div class="box-title">✅ HITS (رصيد) [<span id="count-hit">0</span>]</div>
                <div id="hits-res"></div>
            </div>
            <div class="box live-box">
                <div class="box-title">✔️ LIVE (صفر) [<span id="count-live">0</span>]</div>
                <div id="live-res"></div>
            </div>
            <div class="box dead-box">
                <div class="box-title">💀 DEAD (مرفوض) [<span id="count-dead">0</span>]</div>
                <div id="dead-res"></div>
            </div>
        </div>
    </div>

    <script>
        let counts = {hit: 0, live: 0, dead: 0};

        async function startCheck() {
            const list = document.getElementById('cardList').value.split('\\n');
            const status = document.getElementById('status');
            
            // تصغير العدادات
            counts = {hit: 0, live: 0, dead: 0};
            ['hit', 'live', 'dead'].forEach(t => {
                document.getElementById(`${t}s-res`).innerHTML = '';
                document.getElementById(`count-${t}`).innerText = '0';
            });

            for (let i = 0; i < list.length; i++) {
                let card = list[i].trim();
                if (!card || !card.includes('|')) continue;
                
                status.innerHTML = `⏳ فحص ${i+1} من ${list.length}...`;
                
                try {
                    const response = await fetch('/check', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({card: card})
                    });
                    const data = await response.json();
                    
                    const type = data.status.toLowerCase(); // hit, live, or dead
                    counts[type]++;
                    document.getElementById(`count-${type}`).innerText = counts[type];
                    
                    const div = document.createElement('div');
                    div.className = 'card-entry';
                    div.innerHTML = `<code>${card}</code><br><small>${data.msg}</small>`;
                    document.getElementById(`${type}s-res`).prepend(div);
                    
                } catch (e) { console.error(e); }
                
                if (i < list.length - 1) {
                    await new Promise(r => setTimeout(r, 5000));
                }
            }
            status.innerHTML = "🏁 اكتمل الفحص!";
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
        parts = [p.strip() for p in card_raw.split('|')]
        num, mm, yy, cvc = parts[0], parts[1], parts[2], parts[3]
        if len(yy) == 2: yy = "20" + yy

        token = stripe.Token.create(
            card={"number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc}
        )
        stripe.Charge.create(amount=50, currency="usd", source=token.id)
        return jsonify({"status": "HIT", "msg": "شغالة وبها رصيد!"})

    except stripe.error.CardError as e:
        err = e.json_body.get('error', {})
        if err.get('code') == "insufficient_funds":
            return jsonify({"status": "LIVE", "msg": "رصيد غير كافٍ"})
        return jsonify({"status": "DEAD", "msg": err.get('message', 'مرفوضة')})
    except Exception:
        return jsonify({"status": "DEAD", "msg": "خطأ في البيانات"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
