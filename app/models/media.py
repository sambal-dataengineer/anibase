from sqlalchemy import (
    Column, Integer, String, Text, SmallInteger,
    Date, TIMESTAMP, ForeignKey, UniqueConstraint, PrimaryKeyConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# ── Junction tables ──────────────────────────────────────────────
class MediaGenre(Base):
    __tablename__ = "media_genres"
    __table_args__ = {"schema": "catalog"}

    media_id  = Column(Integer, ForeignKey("media.media.id"),    primary_key=True)
    genre_id  = Column(Integer, ForeignKey("catalog.genres.id"), primary_key=True)


class MediaTag(Base):
    __tablename__ = "media_tags"
    __table_args__ = {"schema": "catalog"}

    media_id  = Column(Integer, ForeignKey("media.media.id"),   primary_key=True)
    tag_id    = Column(Integer, ForeignKey("catalog.tags.id"),  primary_key=True)
    tag_rank  = Column(SmallInteger)


# ── Core tables ──────────────────────────────────────────────────
class Media(Base):
    __tablename__ = "media"
    __table_args__ = {"schema": "media"}

    id              = Column(Integer, primary_key=True)
    title_romaji    = Column(String(255))
    title_english   = Column(String(255))
    type            = Column(String(10))
    format          = Column(String(20))
    status          = Column(String(30))
    cover_image_url = Column(Text)
    average_score   = Column(SmallInteger)
    popularity      = Column(Integer)
    created_at      = Column(TIMESTAMP)
    updated_at      = Column(TIMESTAMP)

    details = relationship("Details", back_populates="media", uselist=False)
    genres  = relationship("Genre", secondary="catalog.media_genres", back_populates="media_items")
    tags    = relationship("Tag",   secondary="catalog.media_tags",   back_populates="media_items")
    links   = relationship("Link",  back_populates="media")


class Details(Base):
    __tablename__ = "details"
    __table_args__ = {"schema": "metadata"}

    id                   = Column(Integer, primary_key=True)
    media_id             = Column(Integer, ForeignKey("media.media.id"), unique=True)
    description          = Column(Text)
    episodes             = Column(SmallInteger)
    chapters             = Column(SmallInteger)
    volumes              = Column(SmallInteger)
    duration             = Column(SmallInteger)
    season               = Column(String(10))
    season_year          = Column(SmallInteger)
    source               = Column(String(30))
    trailer_id           = Column(String(100))
    start_date           = Column(Date)
    end_date             = Column(Date)
    next_airing_at       = Column(TIMESTAMP)
    next_airing_episode  = Column(SmallInteger)
    created_at           = Column(TIMESTAMP)
    updated_at           = Column(TIMESTAMP)

    media = relationship("Media", back_populates="details")


class Genre(Base):
    __tablename__ = "genres"
    __table_args__ = {"schema": "catalog"}

    id   = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    media_items = relationship("Media", secondary="catalog.media_genres", back_populates="genres")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {"schema": "catalog"}

    id   = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    media_items = relationship("Media", secondary="catalog.media_tags", back_populates="tags")


class Link(Base):
    __tablename__ = "links"
    __table_args__ = {"schema": "external_links"}

    id         = Column(Integer, primary_key=True)
    media_id   = Column(Integer, ForeignKey("media.media.id"))
    site       = Column(String(100), nullable=False)
    url        = Column(Text, nullable=False)
    type       = Column(String(20))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    media = relationship("Media", back_populates="links")


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = {"schema": "characters"}

    id          = Column(Integer, primary_key=True)
    name_full   = Column(String(255))
    name_native = Column(String(255))
    image_url   = Column(Text)
    created_at  = Column(TIMESTAMP)
    updated_at  = Column(TIMESTAMP)

    media_roles = relationship("MediaCharacter", back_populates="character")


class MediaCharacter(Base):
    __tablename__ = "media_characters"
    __table_args__ = {"schema": "characters"}

    media_id     = Column(Integer, ForeignKey("media.media.id"),          primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.characters.id"), primary_key=True)
    role         = Column(String(20))

    character = relationship("Character", back_populates="media_roles")
    media     = relationship("Media")


class MediaRelation(Base):
    __tablename__ = "media_relations"
    __table_args__ = {"schema": "relations"}

    id               = Column(Integer, primary_key=True)
    media_id         = Column(Integer, ForeignKey("media.media.id"))
    related_media_id = Column(Integer, ForeignKey("media.media.id"))
    relation_type    = Column(String(30))

    related_media = relationship("Media", foreign_keys=[related_media_id])


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = {"schema": "relations"}

    id                  = Column(Integer, primary_key=True)
    media_id            = Column(Integer, ForeignKey("media.media.id"))
    recommended_media_id = Column(Integer, ForeignKey("media.media.id"))
    rating              = Column(Integer)

    recommended_media = relationship("Media", foreign_keys=[recommended_media_id])

# ── Users Schema ────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "users"}

    id            = Column(Integer, primary_key=True)
    username      = Column(String(50), unique=True, nullable=False)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at    = Column(TIMESTAMP, server_default=func.now())

    watchlist  = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    lists      = relationship("UserList", back_populates="user", cascade="all, delete-orphan")


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "media_id"),
        {"schema": "users"}
    )

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False)
    media_id   = Column(Integer, ForeignKey("media.media.id", ondelete="CASCADE"), nullable=False)
    status     = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    user  = relationship("User", back_populates="watchlist")
    media = relationship("Media")


class UserList(Base):
    __tablename__ = "lists"
    __table_args__ = {"schema": "users"}

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False)
    name       = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user       = relationship("User", back_populates="lists")
    list_items = relationship("ListItem", back_populates="user_list", cascade="all, delete-orphan")


class ListItem(Base):
    __tablename__ = "list_items"
    __table_args__ = (
        PrimaryKeyConstraint("list_id", "media_id"),
        {"schema": "users"}
    )

    list_id  = Column(Integer, ForeignKey("users.lists.id", ondelete="CASCADE"), nullable=False)
    media_id = Column(Integer, ForeignKey("media.media.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(TIMESTAMP, server_default=func.now())

    user_list = relationship("UserList", back_populates="list_items")
    media     = relationship("Media")