from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.models import Status

TEXT_PREVIEW_LENGTH = 200


class DocumentStatusResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    status: Status


class DocumentResultResponse(BaseModel):
    id: int
    status: Status
    message: str | None = None
    result: str | None = None


class DocumentSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    status: Status
    created_at: datetime | None
    extracted_text: str | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def text_preview(self) -> str | None:
        if not self.extracted_text:
            return None
        if len(self.extracted_text) <= TEXT_PREVIEW_LENGTH:
            return self.extracted_text
        return self.extracted_text[:TEXT_PREVIEW_LENGTH] + "..."


class DocumentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DocumentSummary]