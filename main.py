import asyncio
import re
import os
from flask import Flask, request, jsonify, render_template_string
from playwright.async_api import async_playwright

app = Flask(__name__)

# --- واجهة المستخدم الاحترافية (Dark Pro UI) ---
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LYNIX PRO ULTRA | V15</title>
    <style>
        body { background: #000; color: #00ff41; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; text-align: center; }
        .container { max-width: 850px; margin: auto; border: 1px solid #00ff41; padding: 30px; box-shadow: 0 0 40px #00ff41; background: #050505; border-radius: 12px; }
        h1 { letter-spacing: 5px; text-shadow: 0 0 10px #00ff41; margin-bottom: 30px; }
        input { width: 90%; padding: 18px; background: #111; border: 1px solid #00ff41; color: #fff; margin-bottom: 20px; font-size: 1.1rem; border-radius: 5px; outline: none; }
        button { width: 100%; padding: 18px; background: #00ff41; color: #000; font-weight: bold; cursor: pointer; font-size: 1.3rem; border-radius: 5px; transition: 0.3s; border: none; }
        button:hover { background: #fff; box-shadow: 0 0 20px #fff; }
        .data-table { width: 100%; margin-top: 30px; border-collapse: collapse; background: #0a0a0a; border-radius: 8px; overflow: hidden; }
        .data-table td { border: 1px solid #222; padding: 18px; text-align: right; }
        .label { color: #888; width: 35%; font-weight: bold; }
        .val { color: #fff; font-family: 'Courier New', monospace; word-break: break-all; }
        .highlight { color: #00ff41; font-weight: bold; }
        #status { margin-top: 20px; font-size: 1.1rem; color: #ffff00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[ LYNIX PRO ULTRA V15 ]</h1>
        <p>نظام القنص العميق المعتمد على المحرك الذهبي (Headless Engine)</p>
        <input type="text" id="targetUrl" placeholder="الصق رابط cs_live أو صفحة الدفع هنا...">
        <button onclick="startScraping()">إطلاق القنص العميق ⚡</button>
        <div id="status"></div>
        <div id="output"></div>
    </div>

    <script>
        async function startScraping() {
            const url = document.getElementById('targetUrl').value;
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            
            if(!url) return alert("يرجى وضع الرابط أولاً!");

            status.innerHTML = "⏳ جاري تشغيل المتصفح الخفي وانتزاع البيانات من السيرفر...";
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
                    let html = `<table class="data-table">
                        <tr><td class="label">المتجر (Merchant)</td><td class="val highlight">${data.merchant}</td></tr>
                        <tr><td class="label">المبلغ (Amount)</td><td class="val" style="color:#0f0; font-size:1.4rem;">${data.amount}</td></tr>
                        <tr><td class="label">المفتاح (PK Live)</td><td class="val" style="color:yellow;">${data.pk}</td></tr>
                        <tr><td class="label">Session ID</td><td class="val">${data.session_id}</td></tr>
                    </table>`;
                    output.innerHTML = html;
                } else {
                    status.innerHTML = "❌ خطأ في النظام: " + data.message;
                }
            } catch (e) {
                status.innerHTML = "❌ فشل الاتصال بسيرفر Render.";
            }
        }
    </script>
</body>
</html>
"""

async def run_pro_scanner(url):
    async with async_playwright() as p:
        # إعدادات قوية لمحاكاة متصفح حقيقي وتجاوز الحماية
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # الدخول للموقع مع مهلة انتظار طويلة (60 ثانية) للروابط الثقيلة
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000) # انتظار إضافي لتأكيد تحميل الـ UI

            # 1. استخراج محتوى الصفحة الكامل
            content = await page.content()
            
            # 2. اصطياد الـ PK باستخدام Regex متقدم
            pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', content)
            pk = pk_match.group(0) if pk_match else "لم يتم العثور عليه"

            # 3. اصطياد اسم المتجر والمبلغ من واجهة المستخدم (DOM)
            merchant = await page.title()
            merchant = merchant.replace("Pay ", "").split('|')[0].strip()
            
            amount = "Unknown"
            # قائمة العناصر التي يضع فيها Stripe المبالغ عادةً
            selectors = [
                '.Checkout-Status-Amount', 
                'span[data-test="payment-amount"]', 
                '.total-amount', 
                'div[aria-label*="Amount"]',
                'span:has-text("$")'
            ]
            
            for s in selectors:
                try:
                    el = await page.query_selector(s)
                    if el:
                        amount = await el.inner_text()
                        if "$" in amount or "€" in amount or "£" in amount:
                            break
                except: continue

            # 4. استخراج الـ Session ID من الرابط الأصلي
            sid_match = re.search(r'cs_live_[a-zA-Z0-9]{30,}', url)
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
    if not url: return jsonify({"status": "Error", "message": "URL missing"})
    
    try:
        import asyncio
        # تشغيل المحرك في حلقة حدث جديدة لضمان الاستقرار على Render
        result = asyncio.run(run_pro_scanner(url))
        if "error" in result:
            return jsonify({"status": "Error", "message": result["error"]})
        return jsonify({**result, "status": "Success"})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)})

if __name__ == "__main__":
    # تشغيل السيرفر على المنفذ الافتراضي لـ Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
