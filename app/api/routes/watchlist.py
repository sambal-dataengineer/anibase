from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.media import User, Watchlist, Media
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

# ── Pydantic Schemas ────────────────────────────────────────────

class WatchlistAddRequest(BaseModel):
    media_id: int
    status: Optional[str] = None

class WatchlistUpdateRequest(BaseModel):
    status: Optional[str] = None

class WatchlistResponse(BaseModel):
    id: int
    media_id: int
    title: str
    cover_image_url: Optional[str]
    status: Optional[str]

    class Config:
        from_attributes = True

# ── Endpoints ───────────────────────────────────────────────────

@router.get("/", response_model=list[WatchlistResponse])
def get_watchlist(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Watchlist).filter(Watchlist.user_id == current_user.id)
    if status:
        query = query.filter(Watchlist.status == status)
    entries = query.all()

    return [
        WatchlistResponse(
            id=entry.id,
            media_id=entry.media_id,
            title=entry.media.title_romaji or entry.media.title_english,
            cover_image_url=entry.media.cover_image_url,
            status=entry.status
        )
        for entry in entries
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check media exists
    media = db.query(Media).filter(Media.id == payload.media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Check not already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.media_id == payload.media_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")

    entry = Watchlist(
        user_id=current_user.id,
        media_id=payload.media_id,
        status=payload.status
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"message": "Added to watchlist", "id": entry.id}


@router.patch("/{media_id}")
def update_watchlist_status(
    media_id: int,
    payload: WatchlistUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.media_id == media_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not in watchlist")

    entry.status = payload.status
    db.commit()
    return {"message": "Status updated"}


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.media_id == media_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not in watchlist")

    db.delete(entry)
    db.commit()