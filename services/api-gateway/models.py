from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Basic identifier, could be an Apple ID, Google Auth token, or device ID later
    device_id = Column(String, unique=True, index=True) 
    
    # This JSON column will hold our AI's "Passive Memory" persona!
    # e.g., {"diet": "vegan", "allergies": ["peanuts"]}
    persona = Column(JSON, default={}) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
