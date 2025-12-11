from .database import SessionLocal, engine, Base
from .models import Passenger, Itinerary, Segment, Booking, RawMessage, NotificationSent
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .ai_parser import extract_intent_and_slots

Base.metadata.create_all(bind=engine)

def save_raw_message(from_number, display_name, message):
    db = SessionLocal()
    try:
        rm = RawMessage(from_number=from_number, display_name=display_name, message=message)
        db.add(rm)
        db.commit()
        db.refresh(rm)
        return rm
    finally:
        db.close()

def process_message_and_create_request(raw_msg):
    db = SessionLocal()
    try:
        parsed = extract_intent_and_slots(raw_msg.message)

        # إنشاء أو جلب المسافر
        p = db.query(Passenger).filter(Passenger.phone == raw_msg.from_number).first()
        if not p:
            p = Passenger(full_name=raw_msg.display_name or None, phone=raw_msg.from_number)
            db.add(p)
            db.commit()
            db.refresh(p)

        # إنشاء رحلة (PNR)
        it = Itinerary(pnr=None, passenger_id=p.id)
        db.add(it)
        db.commit()
        db.refresh(it)

        # إنشاء Segment (رحلة واحدة كنسخة تجريبية)
        seg = Segment(
            itinerary_id=it.id,
            origin=parsed.get("origin"),
            destination=parsed.get("destination"),
            segment_index=0
        )

        if parsed.get("date"):
            try:
                seg.scheduled_departure = datetime.fromisoformat(parsed["date"])
                seg.scheduled_arrival = seg.scheduled_departure + timedelta(hours=3)
            except:
                pass

        db.add(seg)
        db.commit()
        db.refresh(seg)

        # إنشاء حجز
        bk = Booking(itinerary_id=it.id, ticket_number=None, booking_status="REQUEST")
        db.add(bk)
        db.commit()
        db.refresh(bk)

        # وسم الرسالة بأنها "معالجة"
        raw_msg.processed = True
        db.add(raw_msg)
        db.commit()

        return {
            "passenger": p,
            "itinerary": it,
            "segment": seg,
            "booking": bk,
            "parsed": parsed
        }
    finally:
        db.close()

def find_passengers_recent(months=3):
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30 * months)

        q = (
            db.query(Passenger)
            .join(Itinerary, Itinerary.passenger_id == Passenger.id)
            .join(Segment, Segment.itinerary_id == Itinerary.id)
            .filter(Segment.scheduled_departure >= cutoff)
            .distinct()
        )

        return q.all()
    finally:
        db.close()
