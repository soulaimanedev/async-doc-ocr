import logging
import aio_pika

from app.config import settings

logger = logging.getLogger("ocr_service.rabbitmq")


async def publish_job(document_id: int) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(settings.queue_name, durable=True)

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=str(document_id).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )
        logger.info(f"job_published document_id={document_id}")