import stripe
import telebot
import os
import time

# إعدادات المفاتيح
stripe.api_key = os.getenv("STRIPE_SK")
bot = telebot.TeleBot("8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 أهلاً بك في بوت LYNIX V54\nأرسل لستة البطاقات الآن للفحص المباشر\nالتنسيق: <code>CARD|MM|YY|CVV</code>", parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    # التأكد أنك أنت فقط من يستخدم البوت
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ عذراً، هذا البوت خاص فقط بصاحبه.")
        return

    cards = message.text.split('\n')
    total = len(cards)
    msg = bot.reply_to(message, f"⏳ جاري بدء فحص {total} بطاقة... يرجى الانتظار.")
    
    stats = {"hit": 0, "live": 0, "dead": 0}

    for card in cards:
        try:
            # تنظيف البيانات
            data = card.strip().replace(" ", "").split('|')
            if len(data) < 4: continue
            
            num, mm, yy, cvc = data
            
            # فحص حقيقي عبر Stripe
            stripe.Charge.create(
                amount=100, currency="usd",
                source={"object": "card", "number": num, "exp_month": int(mm), "exp_year": int(yy), "cvc": cvc}
            )
            stats["hit"] += 1
            bot.send_message(message.chat.id, f"✅ <b>HIT FOUND!</b>\n\n<code>{card}</code>\n💰 Charged $1", parse_mode="HTML")

        except stripe.error.CardError as e:
            err = e.json_body.get('error', {})
            if err.get('code') == "insufficient_funds":
                stats["live"] += 1
                bot.send_message(message.chat.id, f"✔️ <b>LIVE (No Funds)</b>\n<code>{card}</code>", parse_mode="HTML")
            else:
                stats["dead"] += 1
        except Exception:
            stats["dead"] += 1

    # التقرير النهائي
    report = (f"🏁 <b>اكتمل الفحص!</b>\n\n"
              f"🔍 الإجمالي: {total}\n"
              f"✅ HITS: {stats['hit']}\n"
              f"⚡ LIVE: {stats['live']}\n"
              f"💀 DEAD: {stats['dead']}")
    bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")

# تشغيل البوت للأبد
print("Bot is running...")
bot.infinity_polling()
