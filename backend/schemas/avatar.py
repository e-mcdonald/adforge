from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AvatarCreate(BaseModel):
    name: str
    age_demo: str
    core_pain: str
    dream_outcome: str
    emotional_triggers: str
    sophistication_level: str
    existing_beliefs: Optional[str] = None
    raw_language: Optional[str] = None
    awareness_stage: int = 1


class AvatarUpdate(BaseModel):
    name: Optional[str] = None
    age_demo: Optional[str] = None
    core_pain: Optional[str] = None
    dream_outcome: Optional[str] = None
    emotional_triggers: Optional[str] = None
    sophistication_level: Optional[str] = None
    existing_beliefs: Optional[str] = None
    raw_language: Optional[str] = None
    awareness_stage: Optional[int] = None


class AvatarResponse(BaseModel):
    id: str
    name: str
    age_demo: str
    core_pain: str
    dream_outcome: str
    emotional_triggers: str
    sophistication_level: str
    existing_beliefs: Optional[str] = None
    raw_language: Optional[str] = None
    awareness_stage: int
    created_at: datetime

    model_config = {"from_attributes": True}
