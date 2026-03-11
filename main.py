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
    <title>LYNIX PREMIUM CHECKER</title>
    <style>
        :root { --bg: #050505; --card-bg: #111; --border: #222; --accent: #3498db; --hit: #2ecc71; --live: #f1c40f; --dead: #e74c3c; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: #fff; margin: 0; padding: 20px; }
        .wrapper { max-width: 1200px; margin: auto; }
        
        /* الهيدر */
        header { text-align: right; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
        header h1 { margin: 0; font-size: 24px; color: var(--accent); }
        
        /* منطقة المدخلات */
        .input-section { background: var(--card-bg); padding: 20px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px; }
        textarea { width: 100%; height: 120px; background: #000; color: #0f0; border: 1px solid var(--border); padding: 15px; border-radius: 8px; font-family: monospace; box-sizing: border-box; resize: vertical; }
        
        .controls { display: flex; align-items: center; gap: 15px; margin-top: 15px; }
        button { background: var(--accent); color: #fff; border: none; padding: 12px 35px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        button:hover { opacity: 0.8; }
        #status-label { font-size: 14px; color: #888; }

        /* منطقة النتائج - ترتيب أفقي */
        .results-container { display: flex; flex-direction: row; gap: 15px; justify-content: space-between; align-items: flex-start; }
        .column { flex: 1; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); height: 500px; display: flex; flex-direction: column; overflow: hidden; }
        
        .column-header { padding: 15px; background: rgba(255,255,255,0.03); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; font-weight: bold; }
        .column-content { padding: 10px; overflow-y: auto; flex-grow: 1; font-family: monospace; font-size: 12px; }

        /* ألوان الأعمدة */
        .col-hit { border-top: 3px solid var(--hit); }
        .col-live { border-top: 3px solid var(--live); }
        .col-dead { border-top: 3px solid var(--dead); }
        
        .card-row { background: #000; border: 1px solid var(--border); padding: 8px; margin-bottom: 8px; border-radius: 4px; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .hit-text { color: var(--hit); }
        .live-text { color: var(--live); }
        .dead-text { color: var(--dead); }

        @media (max-width: 768px) { .results-container { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <h1>LYNIX PRECISION <span>V5</span></h1>
        </header>

        <div class="input-section">
            <textarea id="cardList" placeholder="أدخل البطاقات هنا... التنسيق: 4444555566667777|MM|YY|CVV"></textarea>
            <div class="controls">
                <button onclick="processCards()">بدء الفحص</button>
                <span id="status-label">الحالة: جاهز</span>
            </div>
        </div>

        <div class="results-container">
            <div class="column col-hit">
                <div class="column-header"><span>✅ HITS</span> <span id="count-hit">0</span></div>
                <div id="content-hit" class="column-content"></div>
            </div>

            <div class="column col-live">
                <div class="column-header"><span>⚡ LIVE</span> <span id="count-live">0</span></div>
                <div id="content-live" class="column-content"></div>
            </div>

            <div class="column col-dead">
                <div class="column-header"><span>❌ DEAD</span> <span id="count-dead">0</span></div>
                <div id="content-dead" class="column-content"></div>
            </div>
        </div>
    </div>

    <script>
        let isRunning = false;
        async function processCards() {
            if(isRunning) return;
            const input = document.getElementById('cardList').value.trim();
            if(!input) return alert("من فضلك أدخل البطاقات أولاً");

            const lines = input.split('\\n').filter(l => l.includes('|'));
            isRunning = true;
            const statusLabel = document.getElementById('status-label');
            
            // تصغير العدادات وتنظيف القوائم
            const types = ['hit', 'live', 'dead'];
            types.forEach(t => {
                document.getElementById('content-' + t).innerHTML = '';
                document.getElementById('count-' + t).innerText = '0';
            });

            for (let i = 0; i < lines.length; i++) {
                let card = lines[i].trim();
                statusLabel.innerText = `جاري فحص ${i+1} من ${lines.length}...`;

                try {
                    const response = await fetch('/check', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ card: card })
                    });
                    const res = await response.json();
                    
                    const type = res.status.toLowerCase();
                    const container = document.getElementById('content-' + type);
                    const counter = document.getElementById('count-' + type);
                    
                    // إضافة النتيجة فوراً للواجهة
                    const row = document.createElement('div');
                    row.className = 'card-row';
                    row.innerHTML = `<span class="${type}-text">▶ ${card}</span><br><small style="color:#666">${res.msg}</small>`;
                    container.prepend(row);
                    
                    // تحديث العداد
                    counter.innerText = parseInt(counter.innerText) + 1;

                } catch (err) {
                    console.error("Error checking card:", err);
                }

                if (i < lines.length - 1) {
                    await new Promise(r => setTimeout(r, 5000)); // فاصل 5 ثوانٍ
                }
            }
            isRunning = false;
            statusLabel.innerText = "الحالة: اكتمل الفحص ✅";
        }
    </script>
</body>
</html>
