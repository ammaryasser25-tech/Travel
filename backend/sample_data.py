from database import SessionLocal, engine, Base
from models import Passenger

def create_sample():
    # إنشاء الجداول إذا لم تكن موجودة
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    samples = [
        Passenger(
            raw_message="اسمي احمد واريد حجز من عدن الى القاهرة 20/12",
            name="احمد",
            destination="القاهرة",
            date="20/12"
        ),
        Passenger(
            raw_message="My name is Sara. I want to travel to Riyadh on 05/01",
            name="Sara",
            destination="الرياض",
            date="05/01"
        ),
        Passenger(
            raw_message="Ammar flight to Cairo 2025-12-30",
            name="Ammar",
            destination="cairo",
            date="2025-12-30"
        )
    ]

    for s in samples:
        db.add(s)

    db.commit()
    db.close()
