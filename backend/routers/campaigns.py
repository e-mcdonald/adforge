import asyncio
import json
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Avatar, Campaign
from schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])
logger = logging.getLogger(__name__)


@router.post("", response_model=CampaignResponse, status_code=201)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    avatar = db.query(Avatar).filter(Avatar.id == campaign.avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    db_campaign = Campaign(**campaign.model_dump())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


@router.get("", response_model=List[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).order_by(Campaign.created_at.desc()).all()


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = (
        db.query(Campaign).filter(Campaign.id == campaign_id).first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str, update: CampaignUpdate, db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(campaign, field, value)
    db.commit()
    db.refresh(campaign)
    return campaign


async def _run_pipeline_bg(campaign_id: str):
    """Run the full agent pipeline in the background."""
    from database import SessionLocal
    from agents.orchestrator import run_pipeline

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found for pipeline run")
            return

        avatar = db.query(Avatar).filter(Avatar.id == campaign.avatar_id).first()

        platforms = []
        if campaign.platform_meta_feed:
            platforms.append("meta_feed")
        if campaign.platform_meta_story:
            platforms.append("meta_story")
        if campaign.platform_tiktok:
            platforms.append("tiktok")

        campaign_data = {
            "campaign_id": campaign.id,
            "product_name": campaign.product_name,
            "product_url": campaign.product_url or "",
            "product_price": campaign.product_price or "",
            "avatar": {
                "id": avatar.id,
                "name": avatar.name,
                "age_demo": avatar.age_demo,
                "core_pain": avatar.core_pain,
                "dream_outcome": avatar.dream_outcome,
                "emotional_triggers": avatar.emotional_triggers,
                "sophistication_level": avatar.sophistication_level,
                "existing_beliefs": avatar.existing_beliefs or "",
                "raw_language": avatar.raw_language or "",
                "awareness_stage": avatar.awareness_stage,
            },
            "angle": campaign.angle or "",
            "awareness_stage": campaign.awareness_stage,
            "emotional_driver": campaign.emotional_driver or "Desire",
            "platforms": platforms,
            "copy_model": campaign.copy_model,
            "use_local_models": campaign.use_local_models,
        }

        campaign.status = "running"
        db.commit()

        result = await run_pipeline(campaign_data)

        campaign.status = "complete"
        campaign.output = json.dumps(result)
        db.commit()
        logger.info(f"Campaign {campaign_id} pipeline complete")

    except Exception as e:
        logger.error(f"Pipeline failed for campaign {campaign_id}: {e}", exc_info=True)
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/{campaign_id}/run", status_code=202)
async def run_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == "running":
        raise HTTPException(status_code=409, detail="Campaign is already running")

    background_tasks.add_task(_run_pipeline_bg, campaign_id)
    return {"message": "Pipeline started", "campaign_id": campaign_id}
