import enum

from sqlalchemy import Column, Integer, Text, DateTime, String, Enum
from sqlalchemy.sql import func
from app.database import Base

class Status(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class Document(Base):
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=None, onupdate=func.now())
    file_path = Column(String, nullable=False)
    name = Column(String, nullable=False)
    extracted_text = Column(Text)
    status = Column(Enum(Status), default=Status.pending)
    error_message = Column(Text, nullable=True)