"""
Payment Service - FastAPI Application
Consumes order events from RabbitMQ and processes payments
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
from app.rabbitmq_consumer import start_consumer

# Global variable to hold consumer thread
consumer_thread = None


def run_consumer():
    """
    Run the RabbitMQ consumer in a separate thread
    Blocks indefinitely, listening for messages
    """
    start_consumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles startup and shutdown events
    """
    global consumer_thread
    
    # Startup: Start the RabbitMQ consumer in a background thread
    print("[APP] Starting Payment Service...")
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    print("[APP] RabbitMQ consumer started in background thread")
    
    yield
    
    # Shutdown: Cleanup
    print("[APP] Shutting down Payment Service...")


# Initialize FastAPI application with lifespan
app = FastAPI(
    title="Payment Service",
    description="Payment processing microservice for FreshCart",
    version="1.0.0",
    lifespan=lifespan,
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    Returns 200 OK if service is running
    """
    return {
        "status": "healthy",
        "service": "payment-service",
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "Payment Service",
        "description": "Processes payments for orders",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
