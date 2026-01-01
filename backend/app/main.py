import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging before anything else
from app.core.logging_config import setup_logging
logger = setup_logging()

# Import models so Alembic sees them
from app.models import user, temple, pooja, festival, announcement, contact, visitor
from app.api.v1.api import api_router

ENV = os.getenv("ENV", "development")

app = FastAPI(
    title="Temple Management Backend",
    version="1.0.0",
    docs_url=None if ENV == "production" else "/docs",
    redoc_url=None if ENV == "production" else "/redoc",
    openapi_url=None if ENV == "production" else "/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://svvdthorur.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
