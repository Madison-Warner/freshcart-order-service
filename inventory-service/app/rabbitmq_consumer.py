"""
RabbitMQ Consumer Module for Inventory Service
Listens for PaymentConfirmed events from the payment_confirmed queue
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
    PAYMENT_CONFIRMED_QUEUE,
)
from app.rabbitmq_publisher import publish_stock_reserved


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


def check_stock_availability(order_items):
    """
    Simulate checking stock availability for order items
    In a real system, this would query a database
    
    Args:
        order_items: List of order items to check
        
    Returns:
        Boolean indicating if all items are in stock
    """
    # Simulate stock check - assume all items are available
    # In production, query inventory database
    print(f"[INVENTORY] Checking stock for {len(order_items)} items...")
    for item in order_items:
        product_id = item.get("product_id", "unknown")
        quantity = item.get("quantity", 0)
        print(f"[INVENTORY]   - Product {product_id}: {quantity} units")
    
    # For this demo, always return True (stock available)
    return True


def process_payment_confirmed_event(body):
    """
    Process a PaymentConfirmed event
    Checks stock and publishes StockReserved event if available
    """
    try:
        # Parse the payment event from JSON
        payment_data = json.loads(body)
        order_id = payment_data.get("order_id")
        customer_id = payment_data.get("customer_id")
        amount = payment_data.get("amount")
        
        print(f"\n[INVENTORY SERVICE] ===== Received PaymentConfirmed event =====")
        print(f"[INVENTORY SERVICE] Order ID: {order_id}")
        print(f"[INVENTORY SERVICE] Customer ID: {customer_id}")
        print(f"[INVENTORY SERVICE] Amount: ${amount}")

        # Extract order items (fallback if not in payment event)
        order_items = payment_data.get("items", [])
        
        # Check stock availability
        stock_available = check_stock_availability(order_items)

        if stock_available:
            print(f"[INVENTORY SERVICE] Stock is available - reserving inventory")
            
            # Create StockReserved event
            stock_event = {
                "event_type": "StockReserved",
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": amount,
                "items": order_items,
                "status": "RESERVED",
            }

            # Publish the event
            publish_stock_reserved(stock_event)
            print(f"[INVENTORY SERVICE] ===== StockReserved published for order {order_id} =====\n")
        else:
            print(f"[INVENTORY SERVICE] Stock not available - order {order_id} cannot be fulfilled\n")

    except json.JSONDecodeError as e:
        print(f"[INVENTORY SERVICE] Error parsing message: {e}")
    except Exception as e:
        print(f"[INVENTORY SERVICE] Error processing payment event: {e}")


def callback(ch, method, properties, body):
    """
    Callback function invoked when a message is received from the queue
    """
    process_payment_confirmed_event(body)

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
        channel.queue_declare(queue=PAYMENT_CONFIRMED_QUEUE, durable=True)

        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)

        # Register the callback function
        channel.basic_consume(queue=PAYMENT_CONFIRMED_QUEUE, on_message_callback=callback)

        print(f"[INVENTORY SERVICE] Consumer started. Listening on queue: {PAYMENT_CONFIRMED_QUEUE}")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"[INVENTORY SERVICE] Failed to connect to RabbitMQ after retries: {e}")
    except KeyboardInterrupt:
        print("[INVENTORY SERVICE] Consumer interrupted by user")
    except Exception as e:
        print(f"[INVENTORY SERVICE] Consumer error: {e}")
