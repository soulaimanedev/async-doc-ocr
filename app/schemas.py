from pydantic import BaseModel
from app.models import Status

class DocumentStatusResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    status: Status

class DocumentResultResponse(BaseModel):
    id: int
    status: Status
    message: str | None = None
    result: str | None = None