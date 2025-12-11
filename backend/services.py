from database import SessionLocal, engine, Base
from models import Passenger
from ai_parser import parse_ai_message

# تأكد من إنشاء الجداول عند التشغيل
Base.metadata.create_all(bind=engine)

def save_raw_message(message_text: str, phone: str = None):
    db = SessionLocal()
    p = Passenger(raw_message=message_text)
    db.add(p)
    db.commit()
    db.refresh(p)
    db.close()
    return {"status": "saved", "id": p.id}

def process_message_and_create_request(message_text: str, phone: str = None):
    parsed = parse_ai_message(message_text)
    db = SessionLocal()
    p = Passenger(
        raw_message=message_text,
        name=parsed.get("name"),
        destination=parsed.get("destination"),
        date=parsed.get("date")
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    db.close()
    return {"status": "created", "passenger_id": p.id, "parsed": parsed}

def find_passengers_recent(limit: int = 20):
    db = SessionLocal()
    rows = db.query(Passenger).order_by(Passenger.id.desc()).limit(limit).all()
    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "raw_message": r.raw_message,
            "name": r.name,
            "destination": r.destination,
            "date": r.date
        })
    db.close()
    return result
