from pydantic import BaseModel
from datetime import datetime

class AttendanceCreate(BaseModel):
    name: str
    type: str

class AttendanceResponse(BaseModel):
    name: str
    type: str
    timestamp: datetime

    class Config:
        orm_mode = True
