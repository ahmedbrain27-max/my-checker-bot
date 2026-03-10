import stripe
import time

# المفتاح الخاص بك (المحرك الفعلي)
stripe.api_key = "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"

def start_engine():
    # العدادات الإحصائية
    stats = {"total": 0, "hit": 0, "live": 0, "dead": 0}
    
    # قائمة البطاقات للفحص (يمكنك تعديلها من هاتفك وعمل Commit)
    card_list = [
        "4246040000000000|01|28|000", # مثال
    ]

    print(f"🚀 LYNIX GIT ENGINE ┃ جاري فحص {len(card_list)} بطاقة...")

    for card in card_list:
        try:
            stats["total"] += 1
            num, mm, yy, cvc = card.strip().split('|')
            
            # فحص حقيقي عبر Stripe API
            charge = stripe.Charge.create(
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
            stats["hit"] += 1
            print(f"✅ [HIT] ➜ {card}")

        except stripe.error.CardError as e:
            err = e.json_body.get('error', {})
            if err.get('code') == "insufficient_funds":
                stats["live"] += 1
                print(f"✔️ [LIVE] ➜ {card}")
            else:
                stats["dead"] += 1
                print(f"❌ [DEAD] ➜ {card}")
        except Exception:
            stats["dead"] += 1

    # التقرير النهائي (الإحصائيات)
    print("-" * 30)
    print(f"📊 النتائج: إجمالي {stats['total']} | حية {stats['hit']} | رصيد صفر {stats['live']} | ميتة {stats['dead']}")

if __name__ == "__main__":
    start_engine()
