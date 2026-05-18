from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any
from pydantic import BaseModel
import models, schemas
from database import engine, get_db
from ai_agent import process_user_intent

# Enable pgvector extension BEFORE creating tables
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Food Agent API Gateway", version="1.0.6")

class ChatRequest(BaseModel):
    device_id: str
    message: str

class LocationScanRequest(BaseModel):
    lat: float
    lon: float

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database_connected": True}

@app.post("/users/", response_model=schemas.UserResponse)
def get_or_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.device_id == user.device_id).first()
    if db_user:
        return db_user
    new_user = models.User(device_id=user.device_id, persona={})
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.put("/users/{device_id}/persona", response_model=schemas.UserResponse)
def update_persona(device_id: str, persona_update: schemas.PersonaUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.device_id == device_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.persona = persona_update.persona
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/chat")
def chat_with_butler(request: ChatRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.device_id == request.device_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found. Register device first.")
    try:
        ai_response = process_user_intent(request.message, db_user.persona, request.device_id)
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.post("/restaurants/scan")
def scan_location(request: LocationScanRequest):
    from worker import ingest_local_menus
    task = ingest_local_menus.delay(request.lat, request.lon)
    return {"message": "Crawler dispatched.", "task_id": task.id}
