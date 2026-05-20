import pika
import json

# Publish an OrderCreated event to RabitMQ so downstream services can consume it
def publish_order_created_event(event_data):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")
        )

        channel = connection.channel()

        # Create the queue if it does not already exist
        channel.queue_declare(queue="order_created", durable=True)

        channel.basic_publish(
            exchange="",
            routing_key="order_created",
            body=json.dumps(event_data, default=str),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        connection.close()

    except Exception as error:
        print(f"RabbitMQ publish failed: {error}")