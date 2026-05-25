"""
RabbitMQ Configuration Module for Warehouse Service
Centralizes RabbitMQ connection settings and queue/exchange definitions
"""

import os

# RabbitMQ Connection Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# Queue Names
STOCK_RESERVED_QUEUE = "stock_reserved"
ORDER_PACKED_QUEUE = "order_packed"
