from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# In production, this would be an environment variable. 
# For local dev, we point it to our Docker container.
DATABASE_URL = "postgresql://admin:secretpassword@localhost:5432/food_agent_db"

# The engine is the core interface to the database
engine = create_engine(DATABASE_URL)

# SessionLocal will be used to create individual database sessions for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models to inherit from
Base = declarative_base()

# Dependency to get the database session in our API routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
