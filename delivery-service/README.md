# Delivery Service - FastAPI Microservice

## Overview
The Delivery Service is a FastAPI-based microservice that consumes order packed events from RabbitMQ, simulates assigning drivers and scheduling delivery slots, and publishes delivery scheduled events. It's part of the FreshCart event-driven microservice architecture.

## Architecture

### Event Flow
```
Warehouse Service → OrderPacked Event → order_packed Queue
                                             ↓
                                    Delivery Service
                            (assigns driver & schedules slot)
                                             ↓
                                    DeliveryScheduled Event → delivery_scheduled Queue
                                             ↓
                                  Downstream Services (e.g., Notification Service)
```

## Project Structure
```
delivery-service/
├── app/
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # FastAPI application entry point
│   ├── rabbitmq_config.py          # RabbitMQ configuration and constants
│   ├── rabbitmq_consumer.py        # Message consumer for packed orders
│   └── rabbitmq_publisher.py       # Message publisher for delivery events
├── requirements.txt                # Python dependencies
└── Dockerfile                      # Docker container definition
```

## Features

### ✅ Core Functionality
- **Event Consumer**: Listens to `order_packed` queue for order packed events
- **Driver Assignment**: Simulates assigning available drivers to deliveries
- **Delivery Scheduling**: Simulates scheduling delivery time slots
- **Event Publisher**: Publishes `DeliveryScheduled` events to `delivery_scheduled` queue
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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

### Docker
```bash
# Build image
docker build -t delivery-service .

# Run container
docker run -p 8004:8004 \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_PORT=5672 \
  -e RABBITMQ_USER=guest \
  -e RABBITMQ_PASSWORD=guest \
  delivery-service
```

### Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f delivery-service

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
  "service": "delivery-service",
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
  "service": "Delivery Service",
  "description": "Manages delivery scheduling and driver assignment",
  "endpoints": {
    "health": "/health",
    "docs": "/docs"
  }
}
```

## Event Schemas

### OrderPacked Event (Input)
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
  "timestamp": "2026-05-25T16:54:19.123Z"
}
```

### DeliveryScheduled Event (Output)
**Queue:** `delivery_scheduled`
```json
{
  "event_type": "DeliveryScheduled",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust123",
  "amount": 99.99,
  "tracking_number": "TRACK-550e8400-e29b-41d4-a716-446655440000-FDX",
  "driver_id": "DRV001",
  "driver_name": "John Smith",
  "vehicle": "Van A",
  "delivery_date": "2026-05-27T00:00:00",
  "delivery_window": "2026-05-27 09:00 AM - 12:00 PM",
  "slot_id": "SLOT-1779723859",
  "status": "SCHEDULED",
  "timestamp": "2026-05-25T16:54:19.456Z"
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
- **order_packed**: Durable queue for incoming order packed events
- **delivery_scheduled**: Durable queue for delivery scheduled notifications

## Testing the Service

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Check Health
```bash
curl http://localhost:8004/health
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

### 4. View Complete Event Flow in Logs
```bash
docker-compose logs -f delivery-service
```

Example output:
```
[APP] Starting Delivery Service...
[APP] RabbitMQ consumer started in background thread
[DELIVERY SERVICE] Consumer started. Listening on queue: order_packed
[CONSUMER] Connection attempt 1/10 to RabbitMQ at rabbitmq:5672
[CONSUMER] Successfully connected to RabbitMQ

[DELIVERY SERVICE] ===== Received OrderPacked event =====
[DELIVERY SERVICE] Order ID: 550e8400-e29b-41d4-a716-446655440000
[DELIVERY SERVICE] Customer ID: cust123
[DELIVERY SERVICE] Amount: $99.99
[DELIVERY SERVICE] Tracking Number: TRACK-550e8400-e29b-41d4-a716-446655440000-FDX
[DELIVERY] Driver assigned: John Smith (ID: DRV001) - Vehicle: Van A
[DELIVERY] Scheduling delivery slot: 2026-05-27 09:00 AM - 12:00 PM
[DELIVERY SERVICE] Delivery scheduling complete
[PUBLISHER] DeliveryScheduled event published to delivery_scheduled
[DELIVERY SERVICE] ===== DeliveryScheduled published for order 550e8400-e29b-41d4-a716-446655440000 =====
```

## Troubleshooting

### Consumer Not Receiving Messages
- Check RabbitMQ: `docker-compose logs rabbitmq`
- Verify Warehouse Service is publishing to `order_packed` queue

### Connection Timeout
- Ensure RabbitMQ is healthy: `docker-compose ps`
- Check network settings

### Message Processing Fails
- Check logs: `docker-compose logs delivery-service`
- Verify event schema

## Performance Considerations

- **Prefetch Count**: Set to 1 for sequential processing
- **Heartbeat**: 600s interval for connection stability
- **Scaling**: Consider horizontal scaling with multiple delivery service instances

## License
Part of the FreshCart microservice architecture assessment.
