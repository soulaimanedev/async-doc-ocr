import os
import uuid

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Document, Status
from app.config import settings
from app.schemas import DocumentStatusResponse, DocumentResultResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted!")

    os.makedirs(settings.upload_dir, exist_ok=True)

    stored_filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(settings.upload_dir, stored_filename)

    content = await file.read()
    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)

    document = Document(
        name=file.filename,
        file_path=file_path,
        status=Status.pending,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    return {"id": document.id, "name": document.name, "status": document.status}

@router.get("/{id}/status", response_model=DocumentStatusResponse)
async def get_doc_status(
        id: int,
        db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, id)

    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found!")

    return doc


@router.get("/{id}/result", response_model=DocumentResultResponse)
async def get_doc_ocr_res(
        id: int,
        db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, id)

    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found!")

    message: str | None = None
    result: str | None = None

    if doc.status == Status.failed:
        message = doc.error_message
    elif doc.status == Status.pending:
        message = "Document is queued for processing..."
    elif doc.status == Status.running:
        message = "Document is currently being processed..."
    elif doc.status == Status.success:
        message = "Processing succeeded"
        result = doc.extracted_text

    return DocumentResultResponse(id=doc.id, status=doc.status, message=message, result=result)