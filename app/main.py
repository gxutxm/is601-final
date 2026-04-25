"""FastAPI application entrypoint wiring user + calculation routers + static frontend."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.db.database import Base, engine
from app.models.user import User  # noqa: F401  (register table)
from app.models.calculation import Calculation  # noqa: F401  (register table)
from app.routers import calculations, users

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FastAPI Calculator + Users (Module 13)",
    description="JWT auth + BREAD calculations + HTML/JS front-end.",
    version="0.13.0",
    lifespan=lifespan,
)

# CORS — permissive for dev; tighten origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(calculations.router)

# Front-end: serve the static folder under /static/* and expose friendly URLs
# for the pages Playwright will drive.
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/register", include_in_schema=False)
    def register_page():
        return FileResponse(STATIC_DIR / "register.html")

    @app.get("/login", include_in_schema=False)
    def login_page():
        return FileResponse(STATIC_DIR / "login.html")

    @app.get("/dashboard", include_in_schema=False)
    def dashboard_page():
        return FileResponse(STATIC_DIR / "dashboard.html")

    @app.get("/stats", include_in_schema=False)
    def stats_page():
        return FileResponse(STATIC_DIR / "stats.html")
