from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from contextlib import asynccontextmanager

from app import models
from app.routers import documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="OCR Document Processing Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(documents.router)