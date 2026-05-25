"""
RabbitMQ Publisher Module
Publishes OrderPacked events to the order_packed queue
"""

import pika
import json
from datetime import datetime
from app.rabbitmq_config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    ORDER_PACKED_QUEUE,
)


def publish_order_packed(event_data):
    """
    Publish an OrderPacked event to RabbitMQ
    Adds timestamp to event if not already present
    
    Args:
        event_data (dict): Order packed event data to publish
    """
    try:
        # Add timestamp if not already present
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Create connection and channel
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
        )
        channel = connection.channel()

        # Declare the queue (idempotent - safe to call multiple times)
        channel.queue_declare(queue=ORDER_PACKED_QUEUE, durable=True)

        # Convert event data to JSON
        message = json.dumps(event_data)

        # Publish message with persistence
        channel.basic_publish(
            exchange="",
            routing_key=ORDER_PACKED_QUEUE,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),  # Make message persistent
        )

        print(f"[PUBLISHER] OrderPacked event published to {ORDER_PACKED_QUEUE}")

        connection.close()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"[PUBLISHER] Failed to connect to RabbitMQ: {e}")
    except Exception as e:
        print(f"[PUBLISHER] Error publishing event: {e}")
