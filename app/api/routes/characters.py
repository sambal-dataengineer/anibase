from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.media import Media, MediaCharacter
from app.api.schemas import CharacterOut
from typing import Optional

router = APIRouter(prefix="/media", tags=["Characters"])


@router.get("/{media_id}/characters", response_model=list[CharacterOut])
def get_characters(
    media_id: int,
    role: Optional[str] = Query(None, description="MAIN, SUPPORTING, or BACKGROUND"),
    db: Session = Depends(get_db)
):
    """
    Get all characters for a media item.
    Optionally filter by role.
    MAIN characters come first.
    """
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    query = (
        db.query(MediaCharacter)
        .options(joinedload(MediaCharacter.character))
        .filter(MediaCharacter.media_id == media_id)
    )

    if role:
        query = query.filter(MediaCharacter.role == role.upper())

    # Sort: MAIN first, then SUPPORTING, then BACKGROUND
    role_order = {"MAIN": 0, "SUPPORTING": 1, "BACKGROUND": 2}
    rows = query.all()
    rows.sort(key=lambda r: role_order.get(r.role, 99))

    # Flatten: merge character fields + role into one object
    result = []
    for row in rows:
        c = row.character
        result.append(CharacterOut(
            id=c.id,
            name_full=c.name_full,
            name_native=c.name_native,
            image_url=c.image_url,
            role=row.role
        ))

    return result