from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.media import Media
from app.api.schemas import MediaSummary, MediaDetail
from typing import Optional

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/", response_model=list[MediaSummary])
def list_media(
    type: Optional[str] = Query(None, description="ANIME or MANGA"),
    genre: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List media with optional filters.
    Sorted by popularity descending.
    """
    query = db.query(Media)

    if type:
        query = query.filter(Media.type == type.upper())
    if status:
        query = query.filter(Media.status == status.upper())
    if genre:
        query = query.filter(Media.genres.any(name=genre))

    offset = (page - 1) * page_size
    results = query.order_by(Media.popularity.desc()).offset(offset).limit(page_size).all()
    return results


@router.get("/search", response_model=list[MediaSummary])
def search_media(
    q: str = Query(..., min_length=1, description="Search by title"),
    db: Session = Depends(get_db)
):
    """
    Search media by title (romaji or english).
    Case-insensitive partial match.
    """
    pattern = f"%{q}%"
    results = (
        db.query(Media)
        .filter(
            Media.title_romaji.ilike(pattern) |
            Media.title_english.ilike(pattern)
        )
        .order_by(Media.popularity.desc())
        .limit(20)
        .all()
    )
    return results


@router.get("/{media_id}", response_model=MediaDetail)
def get_media(media_id: int, db: Session = Depends(get_db)):
    """
    Get full details for one media item.
    Loads all relationships in one query.
    """
    media = (
        db.query(Media)
        .options(
            joinedload(Media.details),
            joinedload(Media.genres),
            joinedload(Media.tags),
            joinedload(Media.links),
        )
        .filter(Media.id == media_id)
        .first()
    )
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


@router.get("/{media_id}/links", response_model=list[dict])
def get_links(media_id: int, db: Session = Depends(get_db)):
    """
    Get all streaming/reading links for a media item.
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return [{"site": l.site, "url": l.url, "type": l.type} for l in media.links]