import asyncio
import re
import json
from flask import Flask, request, jsonify, render_template_string
from playwright.async_api import async_playwright

app = Flask(__name__)

# واجهة القنص الاحترافية
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX NETWORK SNIPER V18</title>
    <style>
        body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 850px; margin: auto; border: 1px solid #00ff41; padding: 30px; box-shadow: 0 0 40px #00ff41; background: #050505; }
        input { width: 90%; padding: 15px; background: #111; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; }
        button { width: 100%; padding: 15px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; font-size: 1.2rem; }
        .res-table { width: 100%; margin-top: 30px; border-collapse: collapse; }
        .res-table td { border: 1px solid #222; padding: 15px; text-align: right; }
        .val { color: #fff; word-break: break-all; }
        .highlight { color: #00ff41; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX PRO SNIFFER V18 ]</h1>
        <p>نظام اصطياد حزم البيانات (Network Interceptor)</p>
        <input type="text" id="url" placeholder="الصق رابط cs_live هنا...">
        <button onclick="deepScan()">إطلاق القنص العميق ⚡</button>
        <div id="status" style="margin-top:20px; color: yellow;"></div>
        <div id="output"></div>
    </div>
    <script>
        async function deepScan() {
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            status.innerHTML = "⏳ جاري التجسس على حزم البيانات في Stripe API...";
            output.innerHTML = "";
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                if(data.status === "Success") {
                    status.innerHTML = "✅ تم صيد البيانات بنجاح!";
                    output.innerHTML = `<table class="res-table">
                        <tr><td>المتجر</td><td class="val highlight">${data.merchant}</td></tr>
                        <tr><td>المبلغ</td><td class="val highlight" style="color:#0f0;">${data.amount}</td></tr>
                        <tr><td>الـ PK</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                    </table>`;
                } else { status.innerHTML = "❌ فشل الصيد: " + data.message; }
            } catch(e) { status.innerHTML = "❌ حدث خطأ بالسيرفر."; }
        }
    </script>
</body>
</html>
"""

async def run_sniffer(target_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        captured = {"pk": "Not Found", "amount": "--", "merchant": "Pending..."}

        # وظيفة لمراقبة طلبات الشبكة
        async def handle_request(request):
            # اصطياد الـ PK من روابط Stripe الرسمية
            if "api.stripe.com" in request.url:
                pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', request.url)
                if pk_match: captured["pk"] = pk_match.group(0)

        # وظيفة لمراقبة الردود (لاصطياد المبلغ)
        async def handle_response(response):
            if "checkout" in response.url and "json" in response.headers.get("content-type", ""):
                try:
                    data = await response.json()
                    # البحث عن المبلغ داخل الـ JSON الخاص بـ Stripe
                    if "total" in str(data):
                        val = data.get("total", {}).get("amount", 0) / 100
                        curr = data.get("total", {}).get("currency", "USD").upper()
                        captured["amount"] = f"${val} {curr}"
                except: pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            captured["merchant"] = await page.title()
            await asyncio.sleep(3) # وقت إضافي للصيد
            await browser.close()
            return captured
        except Exception as e:
            await browser.close()
            return {"error": str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/scan', methods=['POST'])
def scan():
    url = request.json.get('url')
    import asyncio
    try:
        data = asyncio.run(run_sniffer(url))
        return jsonify({**data, "status": "Success"})
    except Exception as e: return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
