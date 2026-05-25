# Payment Service - FastAPI Microservice

## Overview
The Payment Service is a FastAPI-based microservice that consumes order events from RabbitMQ, processes simulated payments, and publishes payment confirmation events downstream. It's part of the FreshCart microservice architecture.

## Architecture

### Event Flow
```
Order Service → OrderCreated Event → order_created Queue
                                          ↓
                                  Payment Service
                                   (processes)
                                          ↓
                                  PaymentConfirmed Event → payment_confirmed Queue
                                          ↓
                                  Downstream Services (e.g., Notification Service)
```

## Project Structure
```
payment-service/
├── app/
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # FastAPI application entry point
│   ├── rabbitmq_config.py          # RabbitMQ configuration and constants
│   ├── rabbitmq_consumer.py        # Message consumer for order events
│   └── rabbitmq_publisher.py       # Message publisher for payment events
├── requirements.txt                # Python dependencies
└── Dockerfile                      # Docker container definition
```

## Features

### ✅ Core Functionality
- **Event Consumer**: Listens to `order_created` queue for incoming order events
- **Payment Processing**: Simulates payment processing (always succeeds for demo)
- **Event Publisher**: Publishes `PaymentConfirmed` events to `payment_confirmed` queue
- **Health Check Endpoint**: `/health` for monitoring and orchestration
- **Async Background Processing**: Runs consumer in background thread while API remains responsive

### ✅ Production Ready
- Proper error handling and logging
- Configurable RabbitMQ connection parameters (via environment variables)
- Health checks for container orchestration
- Message persistence (durable queues)
- Graceful shutdown handling
- Modular, readable code structure

## Installation & Running

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional - defaults to localhost)
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export RABBITMQ_USER=guest
export RABBITMQ_PASSWORD=guest

# Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker
```bash
# Build image
docker build -t payment-service .

# Run container
docker run -p 8001:8001 \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_PORT=5672 \
  -e RABBITMQ_USER=guest \
  -e RABBITMQ_PASSWORD=guest \
  payment-service
```

### Docker Compose (Recommended)
```bash
# Start all services (RabbitMQ + Order Service + Payment Service)
docker-compose up -d

# View logs
docker-compose logs -f payment-service

# Stop services
docker-compose down
```

## API Endpoints

### Health Check
```bash
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "payment-service",
  "version": "1.0.0"
}
```

### Service Info
```bash
GET /
```
**Response:**
```json
{
  "service": "Payment Service",
  "description": "Processes payments for orders",
  "endpoints": {
    "health": "/health",
    "docs": "/docs"
  }
}
```

### API Documentation
```
http://localhost:8001/docs
```
Interactive Swagger UI with all endpoints and schemas.

## Event Schemas

### OrderCreated Event (Input)
**Queue:** `order_created`
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust123",
  "total_price": 99.99,
  "items": [
    {
      "product_id": "prod001",
      "quantity": 2,
      "unit_price": 29.99
    }
  ],
  "timestamp": "2024-05-25T04:31:58Z"
}
```

### PaymentConfirmed Event (Output)
**Queue:** `payment_confirmed`
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust123",
  "amount": 99.99,
  "payment_status": "SUCCESS",
  "transaction_id": "TXN-550e8400-e29b-41d4-a716-446655440000-12345"
}
```

## Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_HOST` | localhost | RabbitMQ broker hostname |
| `RABBITMQ_PORT` | 5672 | RabbitMQ broker port |
| `RABBITMQ_USER` | guest | RabbitMQ username |
| `RABBITMQ_PASSWORD` | guest | RabbitMQ password |
| `DEBUG` | false | Debug mode (optional) |

### Queue Configuration
- **order_created**: Durable queue for incoming order events
- **payment_confirmed**: Durable queue for payment confirmations

## Code Modules

### main.py
FastAPI application with lifespan management. Starts the RabbitMQ consumer in a background thread on startup and handles graceful shutdown.

**Key Components:**
- `lifespan()`: Async context manager for startup/shutdown
- `health_check()`: Returns service health status
- `root()`: Returns service information

### rabbitmq_config.py
Centralized configuration module for RabbitMQ settings.

**Exports:**
- `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`
- `ORDER_CREATED_QUEUE`, `PAYMENT_CONFIRMED_QUEUE`, `EXCHANGE_NAME`

### rabbitmq_consumer.py
Implements the message consumer that listens for OrderCreated events.

**Key Functions:**
- `get_connection()`: Establishes RabbitMQ connection
- `process_order_event()`: Processes incoming order, simulates payment, publishes confirmation
- `callback()`: RabbitMQ callback for received messages
- `start_consumer()`: Starts the consumer loop (runs indefinitely)

### rabbitmq_publisher.py
Handles publishing PaymentConfirmed events to RabbitMQ.

**Key Functions:**
- `publish_payment_confirmed()`: Publishes payment event to queue

## Testing the Service

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Check Health
```bash
curl http://localhost:8001/health
```

### 3. Publish Test Order Event (using Order Service API)
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust123",
    "items": [
      {
        "product_id": "prod001",
        "product_name": "Apple",
        "quantity": 2,
        "unit_price": 1.50
      }
    ]
  }'
```

### 4. View Logs
```bash
# Payment Service logs
docker-compose logs -f payment-service

# Example log output:
# [APP] Starting Payment Service...
# [APP] RabbitMQ consumer started in background thread
# [PAYMENT SERVICE] Consumer started. Listening on queue: order_created
# [PAYMENT SERVICE] Message received from queue
# [PAYMENT SERVICE] Received order event: 550e8400-e29b-41d4-a716-446655440000
# [PAYMENT SERVICE] Processing payment for amount: $99.99
# [PAYMENT SERVICE] Payment processed: SUCCESS
# [PUBLISHER] Event published to payment_confirmed: {...}
# [PAYMENT SERVICE] PaymentConfirmed published for order: 550e8400-e29b-41d4-a716-446655440000
```

## Extending the Service

### Adding Real Payment Processing
Replace the simulated payment in `rabbitmq_consumer.py`:
```python
# Instead of:
payment_status = "SUCCESS"

# Call actual payment gateway:
payment_status = process_payment_with_gateway(order_id, amount, api_key)
```

### Adding Database Persistence
Store payment records in SQLite or PostgreSQL:
```python
# In process_order_event():
save_payment_record(order_id, payment_status, transaction_id)
```

### Adding Error Handling
Implement retry logic and dead-letter queues for failed payments:
```python
if payment_status == "FAILED":
    # Publish to dead-letter queue for manual review
    publish_payment_failed(payment_event)
```

## Troubleshooting

### Consumer Not Receiving Messages
- Check RabbitMQ is running: `docker-compose logs rabbitmq`
- Verify connection parameters in environment variables
- Confirm Order Service is publishing to `order_created` queue

### Connection Timeout
- Ensure RabbitMQ container is healthy: `docker-compose ps`
- Check firewall/network settings

### Message Processing Fails
- Check logs: `docker-compose logs payment-service`
- Verify event schema matches expected structure
- Check consumer logs for parsing errors

## Performance Considerations

- **Prefetch Count**: Set to 1 (`prefetch_count=1`) to process one message at a time
- **Heartbeat**: 600s heartbeat interval to maintain connection stability
- **Connection Pooling**: Consider implementing connection pooling for high-throughput scenarios
- **Async Processing**: Messages are processed sequentially; consider async processing for scale

## License
Part of the FreshCart microservice architecture assessment.
