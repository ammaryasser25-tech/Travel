from database import SessionLocal, engine, Base
from models import Passenger
from sample_data import create_sample
from ai_parser import parse_ai_message

# إنشاء الجداول إذا لم تكن موجودة
Base.metadata.create_all(bind=engine)

def save_raw_message(message_text: str):
    """حفظ الرسالة النصية الخام في قاعدة البيانات"""
    db = SessionLocal()
    passenger = Passenger(raw_message=message_text)
    db.add(passenger)
    db.commit()
    db.refresh(passenger)
    db.close()
    return passenger

def process_message_and_create_request(message_text: str):
    """تحليل رسالة المستخدم واستخراج البيانات منها"""
    parsed = parse_ai_message(message_text)

    db = SessionLocal()
    passenger = Passenger(
        raw_message=message_text,
        name=parsed.get("name"),
        destination=parsed.get("destination"),
        date=parsed.get("date")
    )
    db.add(passenger)
    db.commit()
    db.refresh(passenger)
    db.close()
    return passenger

def find_passengers_recent(limit: int = 20):
    """إرجاع آخر المسافرين المسجلين"""
    db = SessionLocal()
    passengers = db.query(Passenger).order_by(Passenger.id.desc()).limit(limit).all()
    db.close()
    return passengers
