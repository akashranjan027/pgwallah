"""
Event publishing utilities for Orders service.

For now this is a lightweight logger-based publisher. It can be extended to
publish to RabbitMQ/Kafka by reading RABBITMQ_URL and using aio-pika, etc.
"""
import json
import os
from typing import Any, Dict

import structlog

logger = structlog.get_logger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")


async def publish_order_event(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Publish an order-related domain event.

    In development this logs the event. In production you can replace this with
    an async publisher (e.g., aio-pika) to RabbitMQ/Kafka.
    """
    try:
        logger.info(
            "order_event",
            event_type=event_type,
            payload=payload,
            transport="logger" if not RABBITMQ_URL else "rabbitmq",
        )
        # Example skeleton for future MQ integration:
        # if RABBITMQ_URL:
        #     import aio_pika
        #     conn = await aio_pika.connect_robust(RABBITMQ_URL)
        #     async with conn:
        #         channel = await conn.channel()
        #         exchange = await channel.declare_exchange(
        #             "orders.events", aio_pika.ExchangeType.TOPIC, durable=True
        #         )
        #         await exchange.publish(
        #             aio_pika.Message(body=json.dumps({"type": event_type, "payload": payload}).encode("utf-8")),
        #             routing_key=f"orders.{event_type}",
        #         )
    except Exception as e:
        logger.error("order_event_publish_failed", error=str(e), event_type=event_type, payload=json.dumps(payload))