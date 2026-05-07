from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.media import User, UserList, ListItem, Media
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/lists", tags=["Lists"])

# ── Pydantic Schemas ────────────────────────────────────────────

class ListCreateRequest(BaseModel):
    name: str

class ListResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ListItemResponse(BaseModel):
    media_id: int
    title: str
    cover_image_url: Optional[str]
    media_type: Optional[str]    # ← add
    media_format: Optional[str]  # ← add

    class Config:
        from_attributes = True

class ListItemAddRequest(BaseModel):
    media_id: int

# ── Endpoints ───────────────────────────────────────────────────

@router.get("/", response_model=list[ListResponse])
def get_lists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(UserList).filter(UserList.user_id == current_user.id).all()


@router.post("/", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
def create_list(
    payload: ListCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_list = UserList(
        user_id=current_user.id,
        name=payload.name
    )
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_list = db.query(UserList).filter(
        UserList.id == list_id,
        UserList.user_id == current_user.id
    ).first()
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")

    db.delete(user_list)
    db.commit()


@router.get("/{list_id}/items", response_model=list[ListItemResponse])
def get_list_items(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_list = db.query(UserList).filter(
        UserList.id == list_id,
        UserList.user_id == current_user.id
    ).first()
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")

    return [
        ListItemResponse(
            media_id=item.media_id,
            title=item.media.title_romaji or item.media.title_english,
            cover_image_url=item.media.cover_image_url,
            media_type=item.media.type,     # ← add
            media_format=item.media.format  # ← add
        )
        for item in user_list.list_items
    ]


@router.post("/{list_id}/items", status_code=status.HTTP_201_CREATED)
def add_item_to_list(
    list_id: int,
    payload: ListItemAddRequest,          # ← change this
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_list = db.query(UserList).filter(
        UserList.id == list_id,
        UserList.user_id == current_user.id
    ).first()
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")

    media = db.query(Media).filter(Media.id == payload.media_id).first()  # ← update
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    existing = db.query(ListItem).filter(
        ListItem.list_id == list_id,
        ListItem.media_id == payload.media_id                             # ← update
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in list")

    item = ListItem(list_id=list_id, media_id=payload.media_id)          # ← update
    db.add(item)
    db.commit()
    return {"message": "Added to list"}


@router.delete("/{list_id}/items/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_list(
    list_id: int,
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_list = db.query(UserList).filter(
        UserList.id == list_id,
        UserList.user_id == current_user.id
    ).first()
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")

    item = db.query(ListItem).filter(
        ListItem.list_id == list_id,
        ListItem.media_id == media_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in list")

    db.delete(item)
    db.commit()