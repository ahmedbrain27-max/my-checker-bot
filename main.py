import asyncio
import re
from flask import Flask, request, jsonify, render_template_string
from playwright.async_api import async_playwright

app = Flask(__name__)

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX PRO ULTRA | V14</title>
    <style>
        body { background: #000; color: #00ff41; font-family: 'Segoe UI', sans-serif; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: auto; border: 2px solid #00ff41; padding: 30px; box-shadow: 0 0 50px #00ff41; background: #050505; border-radius: 15px; }
        input { width: 90%; padding: 18px; background: #000; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; font-size: 1.1rem; }
        button { width: 100%; padding: 15px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; font-size: 1.3rem; border-radius: 8px; }
        .data-table { width: 100%; margin-top: 30px; border-collapse: collapse; }
        .data-table td { border: 1px solid #222; padding: 15px; text-align: right; }
        .val { color: #fff; font-family: monospace; word-break: break-all; }
        .highlight { color: #00ff41; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX PRO ULTRA V14 ]</h1>
        <p>نظام القنص العميق (Full Headless Engine)</p>
        <input type="text" id="url" placeholder="الصق رابط الدفع هنا...">
        <button onclick="fetchData()">إطلاق القنص الاحترافي ⚡</button>
        <div id="status" style="margin-top:20px; color: yellow;"></div>
        <div id="output"></div>
    </div>
    <script>
        async function fetchData() {
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            status.innerHTML = "⏳ جاري تشغيل المحرك الاحترافي وانتزاع البيانات...";
            output.innerHTML = "";
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                if (data.status === "Success") {
                    status.innerHTML = "✅ تم القنص بنجاح!";
                    output.innerHTML = `<table class="data-table">
                        <tr><td>المتجر</td><td class="val highlight">${data.merchant}</td></tr>
                        <tr><td>المبلغ</td><td class="val" style="color:#0f0;">${data.amount}</td></tr>
                        <tr><td>الـ PK</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td>Session ID</td><td class="val">${data.session_id}</td></tr>
                    </table>`;
                } else { status.innerHTML = "❌ خطأ: " + data.message; }
            } catch (e) { status.innerHTML = "❌ فشل السيرفر."; }
        }
    </script>
</body>
</html>
"""

async def run_pro_scanner(url):
    async with async_playwright() as p:
        # تشغيل المتصفح بأقصى قدرات رامات الـ Pro Ultra
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.new_page()
        
        try:
            # فتح الصفحة والانتظار حتى انتهاء كل الحركات والـ JS
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)

            content = await page.content()
            
            # استخراج الـ PK
            pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', content)
            
            # استخراج المبلغ من واجهة المستخدم مباشرة
            amount = "Unknown"
            selectors = ['.Checkout-Status-Amount', 'span:has-text("$")', '.total-amount']
            for s in selectors:
                el = await page.query_selector(s)
                if el:
                    amount = await el.inner_text()
                    break

            merchant = await page.title()
            sid = re.search(r'cs_live_[a-zA-Z0-9]{30,}', url)

            await browser.close()
            return {
                "merchant": merchant.replace("Pay ", "").split('|')[0].strip(),
                "amount": amount,
                "pk": pk_match.group(0) if pk_match else "Not Found",
                "session_id": sid.group(0) if sid else "N/A"
            }
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
        data = asyncio.run(run_pro_scanner(url))
        if "error" in data: return jsonify({"status": "Error", "message": data["error"]})
        return jsonify({**data, "status": "Success"})
    except Exception as e: return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
