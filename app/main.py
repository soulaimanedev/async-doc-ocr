from fastapi import FastAPI
from .database import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="OCR Document Processing Service", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok"}