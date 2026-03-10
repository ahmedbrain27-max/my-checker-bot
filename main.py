import stripe
import telebot
import os
import time
from flask import Flask
from threading import Thread

# 1. إعداد سيرفر وهمي صغير جداً لإرضاء Render ومنع إغلاق البوت
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running...", 200

def run_flask():
    # Render يطلب المنفذ 10000 كخيار افتراضي
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. بيانات المحرك والبوت (تأكد من صحتها)
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"
bot = telebot.TeleBot("8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🚀 <b>نظام LYNIX متصل الآن!</b>\nأرسل اللستة وسأبدأ الفحص فوراً.", parse_mode="HTML")

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
            
            stripe.Charge.create(
                amount=100, currency="usd",
                source={"object": "card", "number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc}
            )
            stats["hit"] += 1
            bot.send_message(message.chat.id, f"✅ <b>HIT!</b>\n<code>{card_clean}</code>", parse_mode="HTML")
        except stripe.error.CardError as e:
            err = e.json_body.get('error', {})
            if err.get('code') == "insufficient_funds":
                stats["live"] += 1
                bot.send_message(message.chat.id, f"✔️ <b>LIVE</b>\n<code>{card_clean}</code>", parse_mode="HTML")
            else: stats["dead"] += 1
        except Exception: stats["dead"] += 1

    bot.edit_message_text(f"🏁 <b>اكتمل الفحص!</b>\n\n✅ HITS: {stats['hit']}\n⚡ LIVE: {stats['live']}\n💀 DEAD: {stats['dead']}", message.chat.id, status_msg.message_id, parse_mode="HTML")

# 3. تشغيل السيرفر الوهمي في الخلفية وتشغيل البوت
if __name__ == "__main__":
    # تشغيل Flask لتجنب خطأ الـ Port Scan
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("🚀 Starting Bot Polling...")
    # تشغيل البوت للأبد
    bot.infinity_polling()
