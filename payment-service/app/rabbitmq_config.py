"""
RabbitMQ Configuration Module
Centralizes RabbitMQ connection settings and queue/exchange definitions
"""

import os

# RabbitMQ Connection Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# Queue and Exchange Names
ORDER_CREATED_QUEUE = "order_created"
PAYMENT_CONFIRMED_QUEUE = "payment_confirmed"
EXCHANGE_NAME = "orders"
