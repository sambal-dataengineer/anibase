from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import media as media_router
from app.api.routes import characters as characters_router   # NEW
from app.api.routes import relations as relations_router     # NEW

app = FastAPI(
    title="AniBase API",
    description="Anime and manga discovery platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(media_router.router)
app.include_router(characters_router.router)    # NEW
app.include_router(relations_router.router)     # NEW

@app.get("/")
def root():
    return {"message": "AniBase API is running"}