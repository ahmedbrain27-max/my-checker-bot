import telebot
import requests
import os

# --- الإعدادات الخاصة بك ---
API_TOKEN = '8551972896:AAFOysETMd4tuyuArnqPA8-uM2Iz6z4fWuw'
MY_CHAT_ID = '5473153501'

# مفاتيح العمل (Stripe & EVX)
SK_KEY = "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"
EVX_KEY = "Evx-sk-83c05aa41c83fc570c7b5a5252b93cbbd1eb020790736be0"

bot = telebot.TeleBot(API_TOKEN)

# --- حل مشكلة التعارض (Conflict 409) ---
# هذا السطر يحذف أي ارتباطات قديمة للبوت ليتمكن من العمل على السيرفر الجديد
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(message):
    if str(message.chat.id) == MY_CHAT_ID:
        bot.reply_to(message, "🚀 أهلاً بك يا سيد أحمد.\nالبوت متصل الآن بسيرفر Render وجاهز للفحص.\n\nأرسل البطاقات بتنسيق: `رقم|شهر|سنة|CVC`")
    else:
        bot.reply_to(message, "⚠️ عذراً، هذا البوت خاص بالمطور فقط.")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    if str(message.chat.id) != MY_CHAT_ID:
        return

    cards = message.text.split('\n')
    for card in cards:
        if '|' not in card: continue
        
        c_data = card.split('|')
        if len(c_data) < 4: continue
        
        msg = bot.reply_to(message, f"⏳ جاري فحص: {c_data[0].strip()}...")
        
        try:
            # إرسال الطلب إلى Stripe API
            url = "https://api.stripe.com/v1/tokens"
            headers = {
                'Authorization': f'Bearer {SK_KEY}',
                'X-EVX-Key': EVX_KEY,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            payload = {
                'card[number]': c_data[0].strip(),
                'card[exp_month]': c_data[1].strip(),
                'card[exp_year]': c_data[2].strip(),
                'card[cvc]': c_data[3].strip()
            }
            
            response = requests.post(url, data=payload, headers=headers)
            res = response.json()
            
            if 'id' in res:
                bot.edit_message_text(f"✅ [LIVE]\n💳 البطاقة: {card}\n🔥 الحالة: بنجاح (Token Generated)", message.chat.id, msg.message_id)
            else:
                error_msg = res.get('error', {}).get('message', 'خطأ غير معروف')
                bot.edit_message_text(f"❌ [DEAD]\n💳 البطاقة: {c_data[0].strip()}\n⚠️ السبب: {error_msg}", message.chat.id, msg.message_id)
                
        except Exception as e:
            bot.edit_message_text(f"⚠️ خطأ فني أثناء الفحص: {str(e)}", message.chat.id, msg.message_id)

# تشغيل البوت بشكل مستمر
if __name__ == "__main__":
    print("Bot is starting on Render...")
    bot.infinity_polling()
