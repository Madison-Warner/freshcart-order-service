# Warehouse Service - FastAPI Microservice

## Overview
The Warehouse Service is a FastAPI-based microservice that consumes stock reservation events from RabbitMQ, simulates picking and packing orders, and publishes order packed events. It's part of the FreshCart event-driven microservice architecture.

## Architecture

### Event Flow
```
Inventory Service → StockReserved Event → stock_reserved Queue
                                              ↓
                                      Warehouse Service
                                  (creates pick list & packs)
                                              ↓
                                      OrderPacked Event → order_packed Queue
                                              ↓
                                  Downstream Services (e.g., Shipping Service)
```

## Project Structure
```
warehouse-service/
├── app/
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # FastAPI application entry point
│   ├── rabbitmq_config.py          # RabbitMQ configuration and constants
│   ├── rabbitmq_consumer.py        # Message consumer for stock events
│   └── rabbitmq_publisher.py       # Message publisher for packed events
├── requirements.txt                # Python dependencies
└── Dockerfile                      # Docker container definition
```

## Features

### ✅ Core Functionality
- **Event Consumer**: Listens to `stock_reserved` queue for stock reservation events
- **Pick List Creation**: Simulates generating warehouse pick lists
- **Order Packing**: Simulates packing orders for shipment
- **Event Publisher**: Publishes `OrderPacked` events to `order_packed` queue
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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

### Docker
```bash
# Build image
docker build -t warehouse-service .

# Run container
docker run -p 8003:8003 \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_PORT=5672 \
  -e RABBITMQ_USER=guest \
  -e RABBITMQ_PASSWORD=guest \
  warehouse-service
```

### Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f warehouse-service

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
  "service": "warehouse-service",
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
  "service": "Warehouse Service",
  "description": "Manages order picking and packing",
  "endpoints": {
    "health": "/health",
    "docs": "/docs"
  }
}
```

## Event Schemas

### StockReserved Event (Input)
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
  "timestamp": "2026-05-25T16:02:01.123Z"
}
```

### OrderPacked Event (Output)
**Queue:** `order_packed`
```json
{
  "event_type": "OrderPacked",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust123",
  "amount": 99.99,
  "pick_list_id": "PICK-12345-67890",
  "tracking_number": "TRACK-550e8400-e29b-41d4-a716-446655440000-FDX",
  "status": "PACKED",
  "timestamp": "2026-05-25T16:02:01.456Z"
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
- **stock_reserved**: Durable queue for incoming stock reservation events
- **order_packed**: Durable queue for order packed notifications

## Testing the Service

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Check Health
```bash
curl http://localhost:8003/health
```

### 3. Create an Order
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

### 4. View Event Flow in Logs
```bash
docker-compose logs -f warehouse-service
```

Example output:
```
[APP] Starting Warehouse Service...
[APP] RabbitMQ consumer started in background thread
[WAREHOUSE SERVICE] Consumer started. Listening on queue: stock_reserved
[CONSUMER] Connection attempt 1/10 to RabbitMQ at rabbitmq:5672
[CONSUMER] Successfully connected to RabbitMQ

[WAREHOUSE SERVICE] ===== Received StockReserved event =====
[WAREHOUSE SERVICE] Order ID: 550e8400-e29b-41d4-a716-446655440000
[WAREHOUSE SERVICE] Customer ID: cust123
[WAREHOUSE SERVICE] Amount: $99.99
[WAREHOUSE] Creating pick list for 1 items...
[WAREHOUSE]   Pick: Product prod001 - Qty 2 units
[WAREHOUSE] Pick list created: PICK-12345-67890
[WAREHOUSE] Packing order 550e8400-e29b-41d4-a716-446655440000...
[WAREHOUSE]   Pack: 2x Apple
[WAREHOUSE] Order packed with tracking: TRACK-550e8400-e29b-41d4-a716-446655440000-FDX
[WAREHOUSE SERVICE] Order packing complete
[PUBLISHER] OrderPacked event published to order_packed
[WAREHOUSE SERVICE] ===== OrderPacked published for order 550e8400-e29b-41d4-a716-446655440000 =====
```

## Troubleshooting

### Consumer Not Receiving Messages
- Check RabbitMQ: `docker-compose logs rabbitmq`
- Verify Inventory Service is publishing to `stock_reserved` queue

### Connection Timeout
- Ensure RabbitMQ is healthy: `docker-compose ps`
- Check network settings

### Message Processing Fails
- Check logs: `docker-compose logs warehouse-service`
- Verify event schema

## Performance Considerations

- **Prefetch Count**: Set to 1 for sequential processing
- **Heartbeat**: 600s interval for connection stability
- **Scaling**: Consider horizontal scaling with multiple warehouse instances

## License
Part of the FreshCart microservice architecture assessment.
