from .database import SessionLocal, engine
from .models import Base, Passenger, Itinerary, Segment, Booking
from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)

def create_sample():
    db = SessionLocal()
    try:
        p = Passenger(full_name="Ammar Yasser", phone="+967771234567", email="ammar@example.com")
        db.add(p); db.commit(); db.refresh(p)

        it = Itinerary(pnr="PNR001", passenger_id=p.id)
        db.add(it); db.commit(); db.refresh(it)

        seg = Segment(
            itinerary_id=it.id,
            origin="عدن",
            destination="القاهرة",
            scheduled_departure=datetime.utcnow() - timedelta(days=1),
            scheduled_arrival=(datetime.utcnow() - timedelta(days=1)) + timedelta(hours=3)
        )
        db.add(seg); db.commit()

        bk = Booking(itinerary_id=it.id, ticket_number="TKT001")
        db.add(bk); db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample()
