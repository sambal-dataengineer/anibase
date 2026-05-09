from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import media as media_router
from app.api.routes import characters as characters_router
from app.api.routes import relations as relations_router
from app.auth.routes import router as auth_router
from app.api.routes.lists import router as lists_router
from app.api.routes import users as users_router  
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent  # points to anibase/

app = FastAPI(
    title="AniBase API",
    description="Anime and manga discovery platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None   # disables ReDoc, keeps only Swagger — cleaner for a portfolio project
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # TODO: restrict to deployed domain before going live
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(media_router.router)
app.include_router(characters_router.router)
app.include_router(relations_router.router)
app.include_router(auth_router)
app.include_router(lists_router)
app.include_router(users_router.router)

# ── 404 handler ───────────────────────────────────────────
# Catches any request that doesn't match a route or static file
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return FileResponse(BASE_DIR / "frontend" / "404.html", status_code=404)

app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")