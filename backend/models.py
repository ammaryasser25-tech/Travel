from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Passenger(Base):
    __tablename__ = "passengers"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True)
    opt_out = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Itinerary(Base):
    __tablename__ = "itineraries"
    id = Column(Integer, primary_key=True, index=True)
    pnr = Column(String, nullable=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id"))
    passenger = relationship("Passenger")
    created_at = Column(DateTime, default=datetime.utcnow)

class Segment(Base):
    __tablename__ = "segments"
    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    itinerary = relationship("Itinerary")
    airline_code = Column(String, nullable=True)
    flight_number = Column(String, nullable=True)
    origin = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    scheduled_departure = Column(DateTime, nullable=True)
    scheduled_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    segment_index = Column(Integer, default=0)
    status = Column(String, default="SCHEDULED")
    created_at = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    ticket_number = Column(String, nullable=True)
    booking_status = Column(String, default="CONFIRMED")
    created_at = Column(DateTime, default=datetime.utcnow)

class RawMessage(Base):
    __tablename__ = "raw_messages"
    id = Column(Integer, primary_key=True, index=True)
    from_number = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    message = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

class NotificationSent(Base):
    __tablename__ = "notifications_sent"
    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer)
    itinerary_id = Column(Integer)
    passenger_id = Column(Integer)
    medium = Column(String)
    body = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
