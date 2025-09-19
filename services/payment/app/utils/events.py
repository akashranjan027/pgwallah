"""
Event publishing utilities for payment service
"""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import aio_pika
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class EventPublisher:
    """RabbitMQ event publisher for payment events"""

    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            
            # Declare exchanges for different event types
            self.payment_exchange = await self.channel.declare_exchange(
                "payment.events", aio_pika.ExchangeType.TOPIC, durable=True
            )
            
            logger.info("Connected to RabbitMQ for event publishing")
            
        except Exception as e:
            logger.error("Failed to connect to RabbitMQ", error=str(e))
            raise

    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish_event(
        self, 
        event_type: str, 
        data: Dict[str, Any],
        routing_key: Optional[str] = None
    ):
        """Publish event to RabbitMQ"""
        
        if not self.channel:
            await self.connect()

        # Create CloudEvents-style event structure
        event = {
            "id": str(uuid.uuid4()),
            "source": "payment-service",
            "type": event_type,
            "time": datetime.utcnow().isoformat(),
            "subject": data.get("tenant_id", "unknown"),
            "data": data,
        }

        try:
            message = aio_pika.Message(
                json.dumps(event).encode(),
                content_type="application/json",
                message_id=event["id"],
                timestamp=datetime.utcnow(),
            )

            routing_key = routing_key or event_type
            
            await self.payment_exchange.publish(
                message, routing_key=routing_key
            )

            logger.info(
                "Published payment event",
                event_id=event["id"],
                event_type=event_type,
                routing_key=routing_key,
            )

        except Exception as e:
            logger.error(
                "Failed to publish event",
                event_type=event_type,
                error=str(e),
            )
            raise


# Global event publisher
event_publisher = EventPublisher()


async def publish_payment_event(event_type: str, data: Dict[str, Any]):
    """Convenience function to publish payment events"""
    try:
        await event_publisher.publish_event(event_type, data)
    except Exception as e:
        logger.error(
            "Failed to publish payment event",
            event_type=event_type,
            error=str(e),
        )
        # Don't re-raise to avoid breaking the main flow