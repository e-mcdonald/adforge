import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Avatar(Base):
    __tablename__ = "avatars"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    age_demo = Column(String, nullable=False)
    core_pain = Column(String, nullable=False)
    dream_outcome = Column(String, nullable=False)
    emotional_triggers = Column(String, nullable=False)  # comma-separated
    sophistication_level = Column(String, nullable=False)  # Low / Medium / High
    existing_beliefs = Column(Text, nullable=True)
    raw_language = Column(Text, nullable=True)
    awareness_stage = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="avatar")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    product_url = Column(String, nullable=True)
    product_price = Column(String, nullable=True)
    avatar_id = Column(String, ForeignKey("avatars.id"), nullable=False)
    angle = Column(Text, nullable=True)
    platform_meta_feed = Column(Boolean, default=False)
    platform_meta_story = Column(Boolean, default=False)
    platform_tiktok = Column(Boolean, default=False)
    awareness_stage = Column(Integer, nullable=False, default=1)
    emotional_driver = Column(String, nullable=True)
    copy_model = Column(String, default="claude-opus-4-5")
    use_local_models = Column(Boolean, default=True)
    status = Column(String, default="pending")  # pending / running / complete / failed
    output = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    avatar = relationship("Avatar", back_populates="campaigns")
