from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String)  # Punch-In / Punch-Out
