"""
RabbitMQ Consumer Module for Delivery Service
Listens for OrderPacked events from the order_packed queue
Includes retry logic for RabbitMQ connection resilience
"""

import pika
import json
import time
from datetime import datetime, timedelta
from app.rabbitmq_config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    ORDER_PACKED_QUEUE,
)
from app.rabbitmq_publisher import publish_delivery_scheduled


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


def assign_driver():
    """
    Simulate assigning a delivery driver to the order
    In a real system, this would check driver availability and assign based on location
    
    Returns:
        Driver information dictionary
    """
    # Simulate driver assignment
    drivers = [
        {"id": "DRV001", "name": "John Smith", "vehicle": "Van A"},
        {"id": "DRV002", "name": "Sarah Johnson", "vehicle": "Van B"},
        {"id": "DRV003", "name": "Mike Davis", "vehicle": "Van C"},
    ]
    
    # Simple rotation - in production, use location-based assignment
    assigned_driver = drivers[hash("driver") % len(drivers)]
    print(f"[DELIVERY] Driver assigned: {assigned_driver['name']} (ID: {assigned_driver['id']}) - Vehicle: {assigned_driver['vehicle']}")
    return assigned_driver


def schedule_delivery_slot():
    """
    Simulate scheduling a delivery time slot
    In a real system, this would check vehicle capacity and driver schedule
    
    Returns:
        Delivery slot information with date and time window
    """
    # Simulate scheduling a delivery 2-3 days in the future
    delivery_date = datetime.utcnow() + timedelta(days=2)
    delivery_window = f"{delivery_date.strftime('%Y-%m-%d')} 09:00 AM - 12:00 PM"
    
    print(f"[DELIVERY] Scheduling delivery slot: {delivery_window}")
    return {
        "date": delivery_date.isoformat(),
        "window": delivery_window,
        "slot_id": f"SLOT-{datetime.utcnow().timestamp():.0f}"
    }


def process_order_packed_event(body):
    """
    Process an OrderPacked event
    Assigns driver, schedules delivery, and publishes DeliveryScheduled event
    """
    try:
        # Parse the order packed event from JSON
        packed_data = json.loads(body)
        order_id = packed_data.get("order_id")
        customer_id = packed_data.get("customer_id")
        amount = packed_data.get("amount")
        tracking_number = packed_data.get("tracking_number")
        
        print(f"\n[DELIVERY SERVICE] ===== Received OrderPacked event =====")
        print(f"[DELIVERY SERVICE] Order ID: {order_id}")
        print(f"[DELIVERY SERVICE] Customer ID: {customer_id}")
        print(f"[DELIVERY SERVICE] Amount: ${amount}")
        print(f"[DELIVERY SERVICE] Tracking Number: {tracking_number}")

        # Assign a driver
        driver = assign_driver()
        
        # Schedule delivery slot
        delivery_slot = schedule_delivery_slot()
        
        print(f"[DELIVERY SERVICE] Delivery scheduling complete")
        
        # Create DeliveryScheduled event
        delivery_event = {
            "event_type": "DeliveryScheduled",
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": amount,
            "tracking_number": tracking_number,
            "driver_id": driver["id"],
            "driver_name": driver["name"],
            "vehicle": driver["vehicle"],
            "delivery_date": delivery_slot["date"],
            "delivery_window": delivery_slot["window"],
            "slot_id": delivery_slot["slot_id"],
            "status": "SCHEDULED",
        }

        # Publish the event
        publish_delivery_scheduled(delivery_event)
        print(f"[DELIVERY SERVICE] ===== DeliveryScheduled published for order {order_id} =====\n")

    except json.JSONDecodeError as e:
        print(f"[DELIVERY SERVICE] Error parsing message: {e}")
    except Exception as e:
        print(f"[DELIVERY SERVICE] Error processing order packed event: {e}")


def callback(ch, method, properties, body):
    """
    Callback function invoked when a message is received from the queue
    """
    process_order_packed_event(body)

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
        channel.queue_declare(queue=ORDER_PACKED_QUEUE, durable=True)

        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)

        # Register the callback function
        channel.basic_consume(queue=ORDER_PACKED_QUEUE, on_message_callback=callback)

        print(f"[DELIVERY SERVICE] Consumer started. Listening on queue: {ORDER_PACKED_QUEUE}")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"[DELIVERY SERVICE] Failed to connect to RabbitMQ after retries: {e}")
    except KeyboardInterrupt:
        print("[DELIVERY SERVICE] Consumer interrupted by user")
    except Exception as e:
        print(f"[DELIVERY SERVICE] Consumer error: {e}")
