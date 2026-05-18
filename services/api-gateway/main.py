from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any
from pydantic import BaseModel
import models, schemas
from database import engine, get_db
from ai_agent import process_user_intent
from worker import build_delivery_cart

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Food Agent API Gateway", version="1.0.5")

# --- Schemas ---
class ChatRequest(BaseModel):
    device_id: str
    message: str

class OrderRequest(BaseModel):
    device_id: str
    restaurant_name: str
    items: list

# --- Endpoints ---
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    user_count = db.query(models.User).count()
    return {"status": "healthy", "database_connected": True, "total_users": user_count}

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
        # HERE IS THE FIX: We are now passing request.device_id as the 3rd argument
        ai_response = process_user_intent(request.message, db_user.persona, request.device_id)
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.post("/trigger-bot")
def trigger_automation_bot(request: OrderRequest):
    task = build_delivery_cart.delay(request.device_id, request.restaurant_name, request.items)
    return {"message": "Bot dispatched successfully!", "task_id": task.id}

@app.websocket("/ws/voice")
async def voice_stream(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Connection established. AI Butler listening...")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"AI backend received: {data}")
    except WebSocketDisconnect:
        print("Mobile client disconnected.")
