# Inventory Service - FastAPI Microservice

## Overview
The Inventory Service is a FastAPI-based microservice that consumes payment confirmation events from RabbitMQ, checks stock availability, and publishes stock reservation events. It's part of the FreshCart event-driven microservice architecture.

## Architecture

### Event Flow
```
Payment Service → PaymentConfirmed Event → payment_confirmed Queue
                                                ↓
                                        Inventory Service
                                    (checks stock availability)
                                                ↓
                                        StockReserved Event → stock_reserved Queue
                                                ↓
                                  Downstream Services (e.g., Fulfillment Service)
```

## Project Structure
```
inventory-service/
├── app/
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # FastAPI application entry point
│   ├── rabbitmq_config.py          # RabbitMQ configuration and constants
│   ├── rabbitmq_consumer.py        # Message consumer for payment events
│   └── rabbitmq_publisher.py       # Message publisher for stock events
├── requirements.txt                # Python dependencies
└── Dockerfile                      # Docker container definition
```

## Features

### ✅ Core Functionality
- **Event Consumer**: Listens to `payment_confirmed` queue for payment confirmation events
- **Stock Checking**: Simulates stock availability verification (easily replaceable with database queries)
- **Event Publisher**: Publishes `StockReserved` events to `stock_reserved` queue
- **Health Check Endpoint**: `/health` for monitoring and orchestration
- **Async Background Processing**: Runs consumer in background thread while API remains responsive

### ✅ Production Ready
- Proper error handling and logging with clear print statements
- Configurable RabbitMQ connection parameters (via environment variables)
- Health checks for container orchestration
- Message persistence (durable queues)
- Graceful shutdown handling
- Connection retry logic with exponential backoff

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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker
```bash
# Build image
docker build -t inventory-service .

# Run container
docker run -p 8002:8002 \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_PORT=5672 \
  -e RABBITMQ_USER=guest \
  -e RABBITMQ_PASSWORD=guest \
  inventory-service
```

### Docker Compose (Recommended)
```bash
# Start all services (RabbitMQ + Order Service + Payment Service + Inventory Service)
docker-compose up -d

# View logs
docker-compose logs -f inventory-service

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
  "service": "inventory-service",
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
  "service": "Inventory Service",
  "description": "Manages stock reservation for orders",
  "endpoints": {
    "health": "/health",
    "docs": "/docs"
  }
}
```

### API Documentation
```
http://localhost:8002/docs
```
Interactive Swagger UI with all endpoints and schemas.

## Event Schemas

### PaymentConfirmed Event (Input)
**Queue:** `payment_confirmed`
```json
{
  "event_type": "PaymentConfirmed",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust123",
  "amount": 99.99,
  "payment_status": "SUCCESS",
  "transaction_id": "TXN-550e8400-e29b-41d4-a716-446655440000-12345",
  "timestamp": "2026-05-25T15:51:44.123Z",
  "items": [
    {
      "product_id": "prod001",
      "product_name": "Apple",
      "quantity": 2,
      "unit_price": 1.50
    }
  ]
}
```

### StockReserved Event (Output)
**Queue:** `stock_reserved`
```json
{
  "event_type": "StockReserved",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust123",
  "amount": 99.99,
  "items": [
    {
      "product_id": "prod001",
      "product_name": "Apple",
      "quantity": 2,
      "unit_price": 1.50
    }
  ],
  "status": "RESERVED",
  "timestamp": "2026-05-25T15:51:44.456Z"
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
- **payment_confirmed**: Durable queue for incoming payment confirmation events
- **stock_reserved**: Durable queue for stock reservation notifications

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
- `PAYMENT_CONFIRMED_QUEUE`, `STOCK_RESERVED_QUEUE`

### rabbitmq_consumer.py
Implements the message consumer that listens for PaymentConfirmed events.

**Key Functions:**
- `get_connection()`: Establishes RabbitMQ connection with retry logic
- `check_stock_availability()`: Simulates stock verification
- `process_payment_confirmed_event()`: Processes payment events and publishes stock reservations
- `callback()`: RabbitMQ callback for received messages
- `start_consumer()`: Starts the consumer loop (runs indefinitely)

### rabbitmq_publisher.py
Handles publishing StockReserved events to RabbitMQ.

**Key Functions:**
- `publish_stock_reserved()`: Publishes stock reservation event to queue

## Testing the Service

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Check Health
```bash
curl http://localhost:8002/health
```

### 3. Create an Order (via Order Service)
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
# Inventory Service logs
docker-compose logs -f inventory-service

# Example log output:
# [APP] Starting Inventory Service...
# [APP] RabbitMQ consumer started in background thread
# [INVENTORY SERVICE] Consumer started. Listening on queue: payment_confirmed
# [CONSUMER] Connection attempt 1/10 to RabbitMQ at rabbitmq:5672
# [CONSUMER] Successfully connected to RabbitMQ
# [INVENTORY SERVICE] ===== Received PaymentConfirmed event =====
# [INVENTORY SERVICE] Order ID: 550e8400-e29b-41d4-a716-446655440000
# [INVENTORY SERVICE] Customer ID: cust123
# [INVENTORY SERVICE] Amount: $99.99
# [INVENTORY] Checking stock for 2 items...
# [INVENTORY]   - Product prod001: 2 units
# [INVENTORY SERVICE] Stock is available - reserving inventory
# [PUBLISHER] StockReserved event published to stock_reserved
# [INVENTORY SERVICE] ===== StockReserved published for order 550e8400-e29b-41d4-a716-446655440000 =====
```

## Extending the Service

### Adding Real Stock Database Query
Replace the simulated stock check in `rabbitmq_consumer.py`:
```python
def check_stock_availability(order_items):
    """Query actual inventory database"""
    for item in order_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity")
        # Query database
        available = db.query_stock(product_id)
        if available < quantity:
            return False
    return True
```

### Adding Order Tracking
Store processed orders in a database:
```python
# In process_payment_confirmed_event():
save_inventory_record(order_id, items, status="RESERVED")
```

### Adding Stock Deduction
Actually deduct inventory from stock:
```python
if stock_available:
    for item in order_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity")
        db.deduct_stock(product_id, quantity)
```

## Troubleshooting

### Consumer Not Receiving Messages
- Check RabbitMQ is running: `docker-compose logs rabbitmq`
- Verify connection parameters in environment variables
- Confirm Payment Service is publishing to `payment_confirmed` queue

### Connection Timeout
- Ensure RabbitMQ container is healthy: `docker-compose ps`
- Check firewall/network settings

### Message Processing Fails
- Check logs: `docker-compose logs inventory-service`
- Verify event schema matches expected structure
- Check consumer logs for parsing errors

## Performance Considerations

- **Prefetch Count**: Set to 1 (`prefetch_count=1`) to process one message at a time
- **Heartbeat**: 600s heartbeat interval to maintain connection stability
- **Connection Pooling**: Consider implementing connection pooling for high-throughput scenarios
- **Async Processing**: Messages are processed sequentially; consider async processing for scale

## License
Part of the FreshCart microservice architecture assessment.
