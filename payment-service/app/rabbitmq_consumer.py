"""
RabbitMQ Consumer Module
Listens for OrderCreated events from the order_created queue
Includes retry logic for RabbitMQ connection resilience
"""

import pika
import json
import time
from app.rabbitmq_config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    ORDER_CREATED_QUEUE,
)
from app.rabbitmq_publisher import publish_payment_confirmed


def get_connection(max_retries=10, retry_delay=2):
    """
    Establish connection to RabbitMQ broker with retry logic
    Waits for RabbitMQ if it's not ready when container starts
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        A pika connection object
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[CONSUMER] Connection attempt {attempt}/{max_retries} to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                    connection_attempts=1,
                    retry_delay=1,
                )
            )
            print("[CONSUMER] Successfully connected to RabbitMQ")
            return connection
            
        except (pika.exceptions.AMQPConnectionError, Exception) as e:
            if attempt == max_retries:
                print(f"[CONSUMER] Failed to connect after {max_retries} attempts: {e}")
                raise
            print(f"[CONSUMER] Connection failed: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)


def process_order_event(body):
    """
    Process an OrderCreated event
    Simulates payment processing and publishes PaymentConfirmed event
    """
    try:
        # Parse the order event from JSON
        order_data = json.loads(body)
        order_id = order_data.get("order_id")
        amount = order_data.get("total_price")
        customer_id = order_data.get("customer_id")

        print(f"[PAYMENT SERVICE] Received order event: {order_id}")
        print(f"[PAYMENT SERVICE] Processing payment for amount: ${amount}")

        # Simulate payment processing (in real world, call payment gateway)
        # For now, we assume all payments are successful
        payment_status = "SUCCESS"
        transaction_id = f"TXN-{order_id}-12345"

        print(f"[PAYMENT SERVICE] Payment processed: {payment_status}")

        # Publish PaymentConfirmed event
        payment_event = {
            "event_type": "PaymentConfirmed",
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": amount,
            "payment_status": payment_status,
            "transaction_id": transaction_id,
        }

        publish_payment_confirmed(payment_event)
        print(f"[PAYMENT SERVICE] PaymentConfirmed published for order: {order_id}")

    except json.JSONDecodeError as e:
        print(f"[PAYMENT SERVICE] Error parsing message: {e}")
    except Exception as e:
        print(f"[PAYMENT SERVICE] Error processing order: {e}")


def callback(ch, method, properties, body):
    """
    Callback function invoked when a message is received from the queue
    """
    print("DEBUG: CALLBACK WAS TRIGGERED")
    print(f"[PAYMENT SERVICE] Message received from queue")
    process_order_event(body)

    # Acknowledge message to remove it from the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    """
    Start the RabbitMQ consumer
    This function runs indefinitely, listening for messages
    Includes retry logic to wait for RabbitMQ if not ready
    """
    try:
        connection = get_connection(max_retries=10, retry_delay=2)
        channel = connection.channel()

        # Declare the queue (idempotent - safe to call multiple times)
        channel.queue_declare(queue=ORDER_CREATED_QUEUE, durable=True)

        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)

        # Register the callback function
        channel.basic_consume(queue=ORDER_CREATED_QUEUE, on_message_callback=callback)

        print(f"[PAYMENT SERVICE] Consumer started. Listening on queue: {ORDER_CREATED_QUEUE}")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"[PAYMENT SERVICE] Failed to connect to RabbitMQ after retries: {e}")
    except KeyboardInterrupt:
        print("[PAYMENT SERVICE] Consumer interrupted by user")
    except Exception as e:
        print(f"[PAYMENT SERVICE] Consumer error: {e}")
