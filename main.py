import stripe
import telebot
import os
import time
from flask import Flask
from threading import Thread

# --- سيرفر صغير لمنع إغلاق الخدمة في Render ---
app = Flask(__name__)
@app.route('/')
def health(): return "SYSTEM ONLINE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- بياناتك المحدثة بالتوكن الجديد والمفتاح الحالي ---
stripe.api_key = "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"
bot = telebot.TeleBot("8551972896:AAGcP_yrXZgx-GvHDPda_tYVEq12L84H2hI")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "✅ <b>تم تفعيل التوكن الجديد بنجاح!</b>\nالبوت الآن يعمل بمفرده ولا يوجد أي تعارض.\nأرسل اللستة للفحص الآن.", parse_mode="HTML")

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
            bot.send_message(message.chat.id, f"✅ <b>HIT!</b>\n<code>{card_clean}</code>\n💰 الحالة: رصيد مؤكد", parse_mode="HTML")

        except stripe.error.CardError as e:
            err = e.json_body.get('error', {})
            if err.get('code') == "insufficient_funds":
                stats["live"] += 1
                bot.send_message(message.chat.id, f"✔️ <b>LIVE</b>\n<code>{card_clean}</code>\n⚡ الحالة: رصيد صفر", parse_mode="HTML")
            else: stats["dead"] += 1
        except Exception: stats["dead"] += 1

    bot.edit_message_text(f"🏁 <b>اكتمل الفحص!</b>\n\n✅ HITS: {stats['hit']}\n⚡ LIVE: {stats['live']}\n💀 DEAD: {stats['dead']}", message.chat.id, status_msg.message_id, parse_mode="HTML")

if __name__ == "__main__":
    # تشغيل السيرفر الوهمي
    Thread(target=run_flask, daemon=True).start()
    
    # تنظيف الجلسة والبدء
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 Bot is starting with the NEW TOKEN...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
