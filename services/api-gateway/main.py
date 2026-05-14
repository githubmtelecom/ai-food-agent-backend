from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any
import models, schemas
from database import engine, get_db

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Food Agent API Gateway", version="1.0.2")

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    user_count = db.query(models.User).count()
    return {"status": "healthy", "database_connected": True, "total_users": user_count}

@app.post("/users/", response_model=schemas.UserResponse)
def get_or_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new device or retrieves an existing user."""
    db_user = db.query(models.User).filter(models.User.device_id == user.device_id).first()
    
    if db_user:
        return db_user # User already exists, welcome back!
        
    # Create new user
    new_user = models.User(device_id=user.device_id, persona={})
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.put("/users/{device_id}/persona", response_model=schemas.UserResponse)
def update_persona(device_id: str, persona_update: schemas.PersonaUpdate, db: Session = Depends(get_db)):
    """Updates the AI's passive memory (persona) for a specific user."""
    db_user = db.query(models.User).filter(models.User.device_id == device_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Update the JSON persona
    db_user.persona = persona_update.persona
    db.commit()
    db.refresh(db_user)
    return db_user

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
