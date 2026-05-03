from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.media import Media, MediaRelation, Recommendation
from app.api.schemas import RelatedMediaOut, RecommendationOut

router = APIRouter(prefix="/media", tags=["Relations"])


@router.get("/{media_id}/relations", response_model=list[RelatedMediaOut])
def get_relations(media_id: int, db: Session = Depends(get_db)):
    """
    Get all related media (sequels, prequels, spin-offs, etc.)
    for a media item.
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    rows = (
        db.query(MediaRelation)
        .options(joinedload(MediaRelation.related_media))
        .filter(MediaRelation.media_id == media_id)
        .all()
    )

    result = []
    for row in rows:
        m = row.related_media
        result.append(RelatedMediaOut(
            id=m.id,
            title_romaji=m.title_romaji,
            title_english=m.title_english,
            type=m.type,
            format=m.format,
            cover_image_url=m.cover_image_url,
            relation_type=row.relation_type
        ))

    return result


@router.get("/{media_id}/recommendations", response_model=list[RecommendationOut])
def get_recommendations(media_id: int, db: Session = Depends(get_db)):
    """
    Get community recommendations for a media item.
    Sorted by rating descending — highest rated suggestions first.
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    rows = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.recommended_media))
        .filter(Recommendation.media_id == media_id)
        .order_by(Recommendation.rating.desc())
        .all()
    )

    result = []
    for row in rows:
        m = row.recommended_media
        result.append(RecommendationOut(
            id=m.id,
            title_romaji=m.title_romaji,
            title_english=m.title_english,
            type=m.type,
            format=m.format,
            cover_image_url=m.cover_image_url,
            average_score=m.average_score,
            rating=row.rating
        ))

    return result