import asyncio
import re
from flask import Flask, request, jsonify, render_template_string
from playwright.async_api import async_playwright

app = Flask(__name__)

# واجهة المستخدم الاحترافية
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ELITE SNIPER V12</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: auto; border: 1px solid #0f0; padding: 20px; box-shadow: 0 0 20px #0f0; }
        input { width: 90%; padding: 15px; background: #000; border: 1px solid #0f0; color: #fff; margin-bottom: 20px; }
        button { width: 100%; padding: 15px; background: #0f0; color: #000; font-weight: bold; cursor: pointer; border: none; }
        .results-table { width: 100%; margin-top: 20px; border-collapse: collapse; background: #111; }
        .results-table td { border: 1px solid #333; padding: 12px; text-align: right; }
        .val { color: #fff; word-break: break-all; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX GOD-MODE V12 ]</h1>
        <input type="text" id="url" placeholder="الصق رابط صفحة الدفع هنا...">
        <button onclick="fetchData()">بدء القنص العميق ⚡</button>
        <div id="status" style="margin-top:15px; color: yellow;"></div>
        <div id="output"></div>
    </div>
    <script>
        async function fetchData() {
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            
            status.innerHTML = "⏳ جاري تشغيل المتصفح في الخلفية وانتظار البيانات...";
            output.innerHTML = "";
            
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                status.innerHTML = "✅ اكتمل القنص!";
                
                let html = `<table class="results-table">
                    <tr><td>المتجر (Merchant)</td><td class="val">${data.merchant}</td></tr>
                    <tr><td>المبلغ (Amount)</td><td class="val" style="color:#0f0;">${data.amount}</td></tr>
                    <tr><td>الـ PK (Live)</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                    <tr><td>ID الجلسة</td><td class="val">${data.session_id}</td></tr>
                </table>`;
                output.innerHTML = html;
            } catch (e) {
                status.innerHTML = "❌ حدث خطأ في الاتصال.";
            }
        }
    </script>
</body>
</html>
"""

async def scrape_stripe(target_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # استخراج الـ Session ID من الرابط
        sid_match = re.search(r'cs_live_[a-zA-Z0-9]{30,}', target_url)
        sid = sid_match.group(0) if sid_match else "N/A"
        
        try:
            # فتح الموقع والانتظار حتى يستقر تماماً
            await page.goto(target_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000) # انتظار إضافي لتشغيل الـ JS
            
            # قنص الـ PK من كود الصفحة الكامل
            content = await page.content()
            pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', content)
            pk = pk_match.group(0) if pk_match else "Not Found"
            
            # قنص المبلغ واسم المتجر من واجهة المستخدم (DOM)
            merchant = await page.title()
            amount = "Unknown"
            
            # محاولة العثور على المبلغ بأكثر من طريقة
            amount_selectors = ['.Checkout-Status-Amount', '.total-amount', 'span:has-text("$")']
            for selector in amount_selectors:
                el = await page.query_selector(selector)
                if el:
                    amount = await el.inner_text()
                    break

            await browser.close()
            return {"merchant": merchant, "amount": amount, "pk": pk, "session_id": sid}
        except Exception as e:
            await browser.close()
            return {"error": str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/scan', methods=['POST'])
def scan():
    url = request.json.get('url')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(scrape_stripe(url))
    return jsonify(data if "error" not in data else {"status": "Error", "message": data["error"]}, status="Success" if "error" not in data else "Error")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
