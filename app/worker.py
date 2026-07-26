import asyncio
import logging

import aio_pika

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Document, Status
from app.services.ocr import extract_text_from_pdf, OCRProcessingError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ocr_service.worker")


async def process_document(document_id: int) -> None:
    """Fetch the document, run OCR, persist the result (or the failure)."""
    async with AsyncSessionLocal() as session:
        document = await session.get(Document, document_id)

        if document is None:
            logger.warning(f"Document with ID={document_id} not found.")
            return

        document.status = Status.running
        await session.commit()
        logger.info(f"job_started document_id={document_id} name={document.name}")

        try:
            extracted_text = await asyncio.to_thread(extract_text_from_pdf, document.file_path)
            document.status = Status.success
            document.extracted_text = extracted_text
            document.error_message = None
            logger.info(f"job_succeeded document_id={document_id}")
        except OCRProcessingError as exc:
            document.status = Status.failed
            document.error_message = str(exc)
            logger.error(f"job_failed document_id={document_id} error={exc}")
        finally:
            await session.commit()


async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Called automatically by aio-pika once per incoming message."""
    async with message.process():
        document_id = int(message.body.decode())
        await process_document(document_id)


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(settings.queue_name, durable=True)

        logger.info("worker_started")
        await queue.consume(on_message)

        await asyncio.Future()  # run forever, until the process is killed


if __name__ == "__main__":
    asyncio.run(main())