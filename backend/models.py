from sqlalchemy import Column, Integer, String
from database import Base

class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, index=True)
    raw_message = Column(String, index=True)
    name = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    date = Column(String, nullable=True)
