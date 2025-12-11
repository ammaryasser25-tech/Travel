import re

def parse_ai_message(text: str):
    """
    دالة بسيطة تحاول استخراج name, destination, date من نص الرسالة.
    ليست ذكية جداً لكنها تعطي نتيجة جيدة للتجربة.
    """
    res = {"name": None, "destination": None, "date": None}

    # استخراج التاريخ
    date_match = re.search(r"(\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b)", text)
    if date_match:
        res["date"] = date_match.group(1)

    # استخراج الوجهة
    places = [
        "عدن", "القاهرة", "مصر", "السعودية", "الرياض", "جدة",
        "عمّان", "الأردن", "أمريكا", "الولايات المتحدة",
        "cairo", "egypt", "riyadh", "jeddah", "amman"
    ]

    for p in places:
        if p.lower() in text.lower():
            res["destination"] = p
            break

    # استخراج اسم
    name_match = re.search(
        r"(?:اسمي|أنا|My name is|Mr\.|Ms\.)\s*([A-Za-z\u0600-\u06FF ]{2,40})",
        text,
        re.IGNORECASE
    )

    if name_match:
        candidate = name_match.group(1).strip()
        candidate = re.sub(r"\s+(اريد|أريد|طلب|حجز).*", "", candidate)
        res["name"] = candidate
