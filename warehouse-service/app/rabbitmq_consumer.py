"""
RabbitMQ Consumer Module for Warehouse Service
Listens for StockReserved events from the stock_reserved queue
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
    STOCK_RESERVED_QUEUE,
)
from app.rabbitmq_publisher import publish_order_packed


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


def create_pick_list(order_items):
    """
    Simulate creating a pick list from reserved stock
    In a real system, this would generate a warehouse pick list
    
    Args:
        order_items: List of items to pick
        
    Returns:
        Generated pick list ID
    """
    print(f"[WAREHOUSE] Creating pick list for {len(order_items)} items...")
    for item in order_items:
        product_id = item.get("product_id", "unknown")
        quantity = item.get("quantity", 0)
        print(f"[WAREHOUSE]   Pick: Product {product_id} - Qty {quantity} units")
    
    # Simulate generating a pick list ID
    pick_list_id = "PICK-12345-67890"
    print(f"[WAREHOUSE] Pick list created: {pick_list_id}")
    return pick_list_id


def pack_order(order_id, order_items):
    """
    Simulate packing the order for shipment
    In a real system, this would update warehouse management system
    
    Args:
        order_id: The order ID
        order_items: Items to pack
        
    Returns:
        Tracking number for shipment
    """
    print(f"[WAREHOUSE] Packing order {order_id}...")
    for item in order_items:
        product_name = item.get("product_name", "unknown")
        quantity = item.get("quantity", 0)
        print(f"[WAREHOUSE]   Pack: {quantity}x {product_name}")
    
    # Simulate generating a tracking number
    tracking_number = f"TRACK-{order_id}-FDX"
    print(f"[WAREHOUSE] Order packed with tracking: {tracking_number}")
    return tracking_number


def process_stock_reserved_event(body):
    """
    Process a StockReserved event
    Creates pick list, packs order, and publishes OrderPacked event
    """
    try:
        # Parse the stock reserved event from JSON
        stock_data = json.loads(body)
        order_id = stock_data.get("order_id")
        customer_id = stock_data.get("customer_id")
        amount = stock_data.get("amount")
        
        print(f"\n[WAREHOUSE SERVICE] ===== Received StockReserved event =====")
        print(f"[WAREHOUSE SERVICE] Order ID: {order_id}")
        print(f"[WAREHOUSE SERVICE] Customer ID: {customer_id}")
        print(f"[WAREHOUSE SERVICE] Amount: ${amount}")

        # Extract order items
        order_items = stock_data.get("items", [])
        
        # Create pick list
        pick_list_id = create_pick_list(order_items)
        
        # Pack the order
        tracking_number = pack_order(order_id, order_items)
        
        print(f"[WAREHOUSE SERVICE] Order packing complete")
        
        # Create OrderPacked event
        packed_event = {
            "event_type": "OrderPacked",
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": amount,
            "pick_list_id": pick_list_id,
            "tracking_number": tracking_number,
            "status": "PACKED",
        }

        # Publish the event
        publish_order_packed(packed_event)
        print(f"[WAREHOUSE SERVICE] ===== OrderPacked published for order {order_id} =====\n")

    except json.JSONDecodeError as e:
        print(f"[WAREHOUSE SERVICE] Error parsing message: {e}")
    except Exception as e:
        print(f"[WAREHOUSE SERVICE] Error processing stock reserved event: {e}")


def callback(ch, method, properties, body):
    """
    Callback function invoked when a message is received from the queue
    """
    process_stock_reserved_event(body)

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
        channel.queue_declare(queue=STOCK_RESERVED_QUEUE, durable=True)

        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)

        # Register the callback function
        channel.basic_consume(queue=STOCK_RESERVED_QUEUE, on_message_callback=callback)

        print(f"[WAREHOUSE SERVICE] Consumer started. Listening on queue: {STOCK_RESERVED_QUEUE}")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"[WAREHOUSE SERVICE] Failed to connect to RabbitMQ after retries: {e}")
    except KeyboardInterrupt:
        print("[WAREHOUSE SERVICE] Consumer interrupted by user")
    except Exception as e:
        print(f"[WAREHOUSE SERVICE] Consumer error: {e}")
