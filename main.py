import stripe
import telebot
import os
import time
from flask import Flask
from threading import Thread

# --- إعداد سيرفر بسيط لإرضاء Render ومنع التوقف ---
app = Flask(__name__)
@app.route('/')
def health(): return "ONLINE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- بياناتك الخاصة ---
stripe.api_key = "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"
bot = telebot.TeleBot("8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🚀 <b>تم تشغيل النظام بنجاح!</b>\n\nأرسل لستة البطاقات الآن للفحص.\nالتنسيق: <code>CARD|MM|YY|CVV</code>", parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    if message.from_user.id != ADMIN_ID: return
    
    cards = message.text.strip().split('\n')
    status_msg = bot.reply_to(message, f"⏳ جاري فحص {len(cards)} بطاقة...")
    stats = {"hit": 0, "live": 0, "dead": 0}

    for card in cards:
        try:
            card_clean = card.strip().replace(" ", "")
            if "|" not in card_clean: continue
            num, mm, yy, cvc = card_clean.split('|')
            
            # محاولة الفحص عبر Stripe
            stripe.Charge.create(
                amount=100, currency="usd",
                source={"object": "card", "number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc}
            )
            stats["hit"] += 1
            bot.send_message(message.chat.id, f"✅ <b>HIT!</b>\n<code>{card_clean}</code>\n💰 الحالة: رصيد مؤكد", parse_mode="HTML")

        except stripe.error.CardError as e:
            err = e.json_body.get('error', {})
            if err.get('code') == "insufficient_funds":
                stats["live"] += 1
                bot.send_message(message.chat.id, f"✔️ <b>LIVE</b>\n<code>{card_clean}</code>\n⚡ الحالة: رصيد صفر", parse_mode="HTML")
            else:
                stats["dead"] += 1
        except Exception:
            stats["dead"] += 1

    bot.edit_message_text(f"🏁 <b>اكتمل الفحص!</b>\n\n✅ HITS: {stats['hit']}\n⚡ LIVE: {stats['live']}\n💀 DEAD: {stats['dead']}", message.chat.id, status_msg.message_id, parse_mode="HTML")

# --- تشغيل البرنامج ---
if __name__ == "__main__":
    # تشغيل سيرفر الـ Health Check
    Thread(target=run_flask, daemon=True).start()
    
    # حل مشكلة Conflict 409: تنظيف الاتصالات القديمة
    print("🧹 Cleaning old Telegram sessions...")
    bot.remove_webhook()
    time.sleep(2)
    
    print("🚀 Starting Bot Polling...")
    # بدء العمل
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
