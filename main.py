import asyncio
import re
from flask import Flask, request, jsonify, render_template_string
from playwright.async_api import async_playwright

app = Flask(__name__)

# --- واجهة المستخدم الاحترافية (Dark Sniper UI) ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX ELITE SNIPER V12 | HEADLESS</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }
        .container { max-width: 850px; margin: auto; border: 1px solid #00ff41; padding: 30px; box-shadow: 0 0 30px #00ff41; background: #000; border-radius: 10px; }
        h1 { letter-spacing: 5px; text-shadow: 0 0 10px #00ff41; }
        input { width: 90%; padding: 15px; background: #111; border: 1px solid #00ff41; color: #fff; margin: 20px 0; font-size: 1rem; }
        button { width: 100%; padding: 15px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; border: none; font-size: 1.2rem; transition: 0.3s; }
        button:hover { background: #fff; box-shadow: 0 0 20px #fff; }
        .results-table { width: 100%; margin-top: 30px; border-collapse: collapse; background: #0a0a0a; }
        .results-table td { border: 1px solid #333; padding: 15px; text-align: right; font-size: 1rem; }
        .label { color: #888; width: 30%; }
        .val { color: #fff; word-break: break-all; font-family: sans-serif; }
        .highlight { color: #00ff41; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX HEADLESS SNIPER ]</h1>
        <p>نظام القنص العميق باستخدام المتصفح الخفي (V12)</p>
        <input type="text" id="targetUrl" placeholder="الصق رابط cs_live هنا...">
        <button onclick="startScraping()">قنص البيانات العميقة ⚡</button>
        <div id="status" style="margin-top:20px; color: yellow;"></div>
        <div id="output"></div>
    </div>

    <script>
        async function startScraping() {
            const url = document.getElementById('targetUrl').value;
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            
            if(!url) return alert("ضع الرابط أولاً!");

            status.innerHTML = "⏳ جاري تشغيل المتصفح الخفي وانتظار رد Stripe...";
            output.innerHTML = "";
            
            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();
                
                if (data.status === "Success") {
                    status.innerHTML = "✅ اكتمل الاستخراج بنجاح!";
                    let html = `<table class="results-table">
                        <tr><td class="label">المتجر (Merchant)</td><td class="val highlight">${data.merchant}</td></tr>
                        <tr><td class="label">المبلغ (Amount)</td><td class="val" style="color:#0f0;">${data.amount}</td></tr>
                        <tr><td class="label">الـ PK (Live)</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td class="label">Session ID</td><td class="val">${data.session_id}</td></tr>
                    </table>`;
                    output.innerHTML = html;
                } else {
                    status.innerHTML = "❌ خطأ: " + data.message;
                }
            } catch (e) {
                status.innerHTML = "❌ فشل الاتصال بالسيرفر.";
            }
        }
    </script>
</body>
</html>
"""

async def scrape_stripe(target_url):
    async with async_playwright() as p:
        # تشغيل كروميوم مع إعدادات التخفي
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        try:
            # الذهاب للموقع والانتظار حتى انتهاء تحميل الشبكة
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000) # انتظار إضافي لتأكيد تشغيل الجافا سكريبت

            # 1. استخراج الـ PK من محتوى الصفحة بالكامل
            content = await page.content()
            pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', content)
            pk = pk_match.group(0) if pk_match else "لم يتم العثور عليه"

            # 2. استخراج المبلغ واسم المتجر من الواجهة
            merchant = await page.title()
            merchant = merchant.replace("Pay ", "").split('|')[0].strip()
            
            amount = "Unknown"
            # البحث عن المبلغ في عناصر الصفحة الشائعة في Stripe
            selectors = ['.Checkout-Status-Amount', 'span[data-test="payment-amount"]', '.total-amount', 'span:has-text("$")']
            for selector in selectors:
                el = await page.query_selector(selector)
                if el:
                    amount = await el.inner_text()
                    break

            # 3. استخراج الـ Session ID من الرابط
            sid_match = re.search(r'cs_live_[a-zA-Z0-9]{30,}', target_url)
            sid = sid_match.group(0) if sid_match else "N/A"

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
    try:
        # تشغيل المتصفح الخفي بطريقة متوافقة مع Flask
        import asyncio
        result = asyncio.run(scrape_stripe(url))
        if "error" in result:
            return jsonify({"status": "Error", "message": result["error"]})
        return jsonify({**result, "status": "Success"})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
