from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Avatar
from schemas.avatar import AvatarCreate, AvatarResponse, AvatarUpdate

router = APIRouter(prefix="/api/avatars", tags=["avatars"])


@router.post("", response_model=AvatarResponse, status_code=201)
def create_avatar(avatar: AvatarCreate, db: Session = Depends(get_db)):
    db_avatar = Avatar(**avatar.model_dump())
    db.add(db_avatar)
    db.commit()
    db.refresh(db_avatar)
    return db_avatar


@router.get("", response_model=List[AvatarResponse])
def list_avatars(db: Session = Depends(get_db)):
    return db.query(Avatar).order_by(Avatar.created_at.desc()).all()


@router.get("/{avatar_id}", response_model=AvatarResponse)
def get_avatar(avatar_id: str, db: Session = Depends(get_db)):
    avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar


@router.put("/{avatar_id}", response_model=AvatarResponse)
def update_avatar(avatar_id: str, update: AvatarUpdate, db: Session = Depends(get_db)):
    avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(avatar, field, value)
    db.commit()
    db.refresh(avatar)
    return avatar


@router.delete("/{avatar_id}", status_code=204)
def delete_avatar(avatar_id: str, db: Session = Depends(get_db)):
    avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    db.delete(avatar)
    db.commit()
