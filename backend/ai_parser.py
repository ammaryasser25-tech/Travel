import re
from datetime import datetime

def extract_intent_and_slots(text: str):
    text_lower = text.lower()

    result = {
        "intent": None,
        "origin": None,
        "destination": None,
        "date": None,
        "passengers": 1
    }

    # نية الحجز — تحديد نوع الطلب
    if any(w in text_lower for w in ["تذكرة", "ticket", "flight", "حجز"]):
        result["intent"] = "flight_booking"

    elif any(w in text_lower for w in ["hotel", "فندق"]):
        result["intent"] = "hotel_booking"

    # استخراج التاريخ (بسيط)
    m = re.search(r"(\d{1,2}[/\-]\d{1,2}[/\-]?\d{0,4})", text)
    if m:
        date_str = m.group(1)
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m", "%d-%m", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                result["date"] = dt.strftime("%Y-%m-%d")
                break
            except:
                continue

    # قائمة مدن بسيطة (MVP)
    cities = [
        "عدن", "صنعاء", "مصر", "القاهرة", "جدة", "الرياض", "دبي", "الدوحة",
        "الاردن", "عمان", "usa", "america", "aden", "cairo"
    ]

    for c in cities:
        if c in text_lower:
            if not result["origin"]:
                result["origin"] = c
            else:
                result["destination"] = c

    # صيغة "من كذا إلى كذا"
    m2 = re.search(r"من\s+(\w+)\s+إلى\s+(\w+)", text)
    if m2:
        result["origin"] = m2.group(1)
        result["destination"] = m2.group(2)

    return result
