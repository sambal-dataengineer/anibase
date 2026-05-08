from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.media import User, UserList, ListItem
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Response schema ──────────────────────────────────────────
class ProfileResponse(BaseModel):
    username: str
    email: str
    created_at: str
    total_lists: int
    total_items: int
    favourite_genre: Optional[str]
    favourite_type: Optional[str]

    class Config:
        from_attributes = True

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# ── GET /users/me ────────────────────────────────────────────
@router.get("/me", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Total lists
    total_lists = db.query(func.count(UserList.id))\
        .filter(UserList.user_id == current_user.id).scalar() or 0

    # Total items across all lists
    total_items = db.query(func.count(ListItem.media_id))\
        .join(UserList, UserList.id == ListItem.list_id)\
        .filter(UserList.user_id == current_user.id).scalar() or 0

    # Favourite genre — most common genre across all listed media
    favourite_genre = None
    genre_row = db.execute(text("""
        SELECT g.name, COUNT(*) as cnt
        FROM users.list_items li
        JOIN users.lists l ON l.id = li.list_id
        JOIN catalog.media_genres mg ON mg.media_id = li.media_id
        JOIN catalog.genres g ON g.id = mg.genre_id
        WHERE l.user_id = :uid
        GROUP BY g.name
        ORDER BY cnt DESC
        LIMIT 1
    """), {"uid": current_user.id}).fetchone()
    if genre_row:
        favourite_genre = genre_row[0]

    # Favourite type — ANIME or MANGA, whichever dominates their lists
    favourite_type = None
    type_row = db.execute(text("""
        SELECT m.type, COUNT(*) as cnt
        FROM users.list_items li
        JOIN users.lists l ON l.id = li.list_id
        JOIN media.media m ON m.id = li.media_id
        WHERE l.user_id = :uid
        GROUP BY m.type
        ORDER BY cnt DESC
        LIMIT 1
    """), {"uid": current_user.id}).fetchone()
    if type_row:
        favourite_type = type_row[0]

    return ProfileResponse(
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.strftime("%B %d, %Y"),
        total_lists=total_lists,
        total_items=total_items,
        favourite_genre=favourite_genre,
        favourite_type=favourite_type,
    )

# ── PUT /users/me ────────────────────────────────────────────
@router.put("/me")
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.username:
        # Check username not taken by another user
        existing = db.query(User).filter(
            User.username == payload.username,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = payload.username

    if payload.email:
        existing = db.query(User).filter(
            User.email == payload.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = payload.email

    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully"}

# ── PUT /users/me/password ───────────────────────────────────
@router.put("/me/password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not pwd_context.verify(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = pwd_context.hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


# ── DELETE /users/me ─────────────────────────────────────────
@router.delete("/me")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}