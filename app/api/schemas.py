from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class GenreOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class LinkOut(BaseModel):
    id: int
    site: str
    url: str
    type: Optional[str]

    model_config = {"from_attributes": True}


class DetailsOut(BaseModel):
    description: Optional[str]
    episodes: Optional[int]
    chapters: Optional[int]
    volumes: Optional[int]
    duration: Optional[int]
    season: Optional[str]
    season_year: Optional[int]
    source: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    next_airing_at: Optional[datetime]
    next_airing_episode: Optional[int]

    model_config = {"from_attributes": True}


# Used in list views — lightweight, no nested data
class MediaSummary(BaseModel):
    id: int
    title_romaji: Optional[str]
    title_english: Optional[str]
    type: str
    format: Optional[str]
    status: Optional[str]
    cover_image_url: Optional[str]
    average_score: Optional[int]
    popularity: Optional[int]

    model_config = {"from_attributes": True}


# Used in detail view — full data with all relationships
class MediaDetail(MediaSummary):
    details: Optional[DetailsOut]
    genres: list[GenreOut] = []
    tags: list[TagOut] = []
    links: list[LinkOut] = []


class CharacterOut(BaseModel):
    id:          int
    name_full:   Optional[str]
    name_native: Optional[str]
    image_url:   Optional[str]
    role:        str                # MAIN / SUPPORTING / BACKGROUND

    model_config = {"from_attributes": True}


class RelatedMediaOut(BaseModel):
    id:              int
    title_romaji:    Optional[str]
    title_english:   Optional[str]
    type:            str
    format:          Optional[str]
    cover_image_url: Optional[str]
    relation_type:   str

    model_config = {"from_attributes": True}


class RecommendationOut(BaseModel):
    id:              int
    title_romaji:    Optional[str]
    title_english:   Optional[str]
    type:            str
    format:          Optional[str]
    cover_image_url: Optional[str]
    average_score:   Optional[int]
    rating:          int            # community recommendation score

    model_config = {"from_attributes": True}