from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.media import Media, Genre
from app.api.schemas import MediaSummary, MediaDetail, GenreOut
from typing import Optional

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/genres", response_model=list[GenreOut])
def list_genres(db: Session = Depends(get_db)):
    """
    Return all genres in the database, sorted alphabetically.
    Used to populate the Browse page sidebar.
    """
    genres = db.query(Genre).order_by(Genre.name).all()
    return genres


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
    results = (
        query
        .order_by(Media.popularity.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return results


@router.get("/search", response_model=list[MediaSummary])
def search_media(
    q: str = Query(..., min_length=1, description="Search by title"),
    type: Optional[str] = Query(None, description="ANIME or MANGA"),
    genre: Optional[str] = Query(None, description="Genre name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    pattern = f"%{q}%"
    offset  = (page - 1) * page_size

    query = (
        db.query(Media)
        .filter(
            Media.title_romaji.ilike(pattern) |
            Media.title_english.ilike(pattern)
        )
    )

    # Apply optional filters on top of search
    if type:
        query = query.filter(Media.type == type.upper())
    if genre:
        query = query.filter(Media.genres.any(name=genre))

    results = (
        query
        .order_by(Media.popularity.desc())
        .offset(offset)
        .limit(page_size)
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


@router.get("/{media_id}/characters")
def get_characters(
    media_id: int,
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    from app.models.media import MediaCharacter, Character
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    query = (
        db.query(MediaCharacter)
        .filter(MediaCharacter.media_id == media_id)
        .join(Character)
    )
    if role:
        query = query.filter(MediaCharacter.role == role.upper())

    rows = query.all()
    role_order = {"MAIN": 0, "SUPPORTING": 1, "BACKGROUND": 2}
    rows.sort(key=lambda r: role_order.get(r.role, 99))

    from app.api.schemas import CharacterOut
    return [
        CharacterOut(
            id=r.character.id,
            name_full=r.character.name_full,
            name_native=r.character.name_native,
            image_url=r.character.image_url,
            role=r.role
        )
        for r in rows
    ]


@router.get("/{media_id}/relations")
def get_relations(media_id: int, db: Session = Depends(get_db)):
    from app.models.media import MediaRelation
    from app.api.schemas import RelatedMediaOut
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    rows = (
        db.query(MediaRelation)
        .filter(MediaRelation.media_id == media_id)
        .all()
    )
    return [
        RelatedMediaOut(
            id=r.related_media.id,
            title_romaji=r.related_media.title_romaji,
            title_english=r.related_media.title_english,
            type=r.related_media.type,
            format=r.related_media.format,
            cover_image_url=r.related_media.cover_image_url,
            relation_type=r.relation_type
        )
        for r in rows
    ]