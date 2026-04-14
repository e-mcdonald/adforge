from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from schemas.avatar import AvatarResponse


class CampaignCreate(BaseModel):
    name: str
    product_name: str
    product_url: Optional[str] = None
    product_price: Optional[str] = None
    avatar_id: str
    angle: Optional[str] = None
    platform_meta_feed: bool = False
    platform_meta_story: bool = False
    platform_tiktok: bool = False
    awareness_stage: int = 1
    emotional_driver: Optional[str] = None
    copy_model: str = "claude-opus-4-5"
    use_local_models: bool = True


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    product_name: Optional[str] = None
    product_url: Optional[str] = None
    product_price: Optional[str] = None
    angle: Optional[str] = None
    platform_meta_feed: Optional[bool] = None
    platform_meta_story: Optional[bool] = None
    platform_tiktok: Optional[bool] = None
    awareness_stage: Optional[int] = None
    emotional_driver: Optional[str] = None
    copy_model: Optional[str] = None
    use_local_models: Optional[bool] = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    product_name: str
    product_url: Optional[str] = None
    product_price: Optional[str] = None
    avatar_id: str
    angle: Optional[str] = None
    platform_meta_feed: bool
    platform_meta_story: bool
    platform_tiktok: bool
    awareness_stage: int
    emotional_driver: Optional[str] = None
    copy_model: str
    use_local_models: bool
    status: str
    output: Optional[str] = None
    created_at: datetime
    avatar: Optional[AvatarResponse] = None

    model_config = {"from_attributes": True}
