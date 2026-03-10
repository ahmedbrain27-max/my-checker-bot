import stripe
import telebot
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# 1. إعداد سيرفر فوري جداً لإقناع Render أننا نملك موقعاً
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"LYNIX ENGINE IS ONLINE")

def run_health_server():
    # Render يطلب المنفذ 10000 افتراضياً
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"✅ Health Check Server started on port {port}")
    server.serve_forever()

# تشغيل سيرفر الـ Port في خيط مستقل (Thread) قبل بدء البوت
Thread(target=run_health_server, daemon=True).start()

# 2. بيانات المحرك والبوت الخاصة بك
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"
bot = telebot.TeleBot("8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🚀 <b>تم تخطي حماية Render بنجاح!</b>\nالبوت الآن يعمل 24/7. أرسل اللستة للفحص المباشر.", parse_mode="HTML")

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
            
            # الفحص الحقيقي عبر Stripe
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
                bot.send_message(message.chat.id, f"✔️ <b>LIVE (No Funds)</b>\n<code>{card_clean}</code>", parse_mode="HTML")
            else: stats["dead"] += 1
        except Exception: stats["dead"] += 1

    bot.edit_message_text(f"🏁 <b>اكتمل الفحص!</b>\n\n✅ HITS: {stats['hit']}\n⚡ LIVE: {stats['live']}\n💀 DEAD: {stats['dead']}", message.chat.id, status_msg.message_id, parse_mode="HTML")

# 3. بدء تشغيل البوت للأبد
if __name__ == "__main__":
    print("🚀 Starting LYNIX Telegram Bot...")
    bot.infinity_polling()
