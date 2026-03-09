import telebot
import requests
import os

# المعلومات الخاصة بك
API_TOKEN = '8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw'
MY_CHAT_ID = '5473153501'

# مفاتيح Stripe و EVX
SK_KEY = "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"
EVX_KEY = "Evx-sk-83c05aa41c83fc570c7b5a5252b93cbbd1eb020790736be0"

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ البوت يعمل بنجاح على سيرفر Render!\nأرسل البطاقة للفحص.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # كود الفحص البسيط
    if '|' in message.text:
        bot.reply_to(message, "⏳ جاري الفحص...")
        # هنا تتم عملية الربط بـ Stripe (تم اختصاره للتأكد من استقرار البوت أولاً)
    else:
        bot.reply_to(message, "⚠️ يرجى إرسال البطاقة بالتنسيق الصحيح.")

# سطر التشغيل الهام جداً للسيرفرات
if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling()
