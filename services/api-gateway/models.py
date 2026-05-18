from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True) 
    persona = Column(JSON, default={}) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location_lat = Column(Float)
    location_lon = Column(Float)
    items = relationship("MenuItem", back_populates="restaurant")

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    attributes = Column(JSON, default={})
    
    # NEW: The Vector column for semantic search! (384 dimensions for the MiniLM model)
    embedding = Column(Vector(384))
    
    restaurant = relationship("Restaurant", back_populates="items")
