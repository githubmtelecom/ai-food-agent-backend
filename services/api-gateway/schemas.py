from pydantic import BaseModel
from typing import Dict, Any

class UserCreate(BaseModel):
    device_id: str

class PersonaUpdate(BaseModel):
    persona: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    device_id: str
    persona: Dict[str, Any]

    # This tells Pydantic to read the data directly from our SQLAlchemy database model
    model_config = {"from_attributes": True}
