from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
import json

from app.models import OrderCreateRequest, OrderResponse
from app.database import (
    create_table,
    SessionLocal,
    save_order,
    get_order_by_id,
    get_all_orders
)
from app.rabbitmq import publish_order_created_event

app = FastAPI(title="FreshCart Order Service")

@app.on_event("startup")
def startup():
    create_table()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "Order Service is running"}


# Creates a new grocery order, validates input, calculates totals, stores the order and publishes an event
@app.post("/orders")
def create_order(order_request: OrderCreateRequest, db: Session = Depends(get_db)):
    try:
        order_items = []
        total_price = 0

        # Calculates the total price for each order
        for item in order_request.items:
            line_total = item.quantity * item.unit_price

            order_items.append({
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": line_total
            })

            # Add each line total to the final order total
            total_price += line_total

        # Creates the final order record that will be stored in the SQLite database
        order_data = {
            "order_id": str(uuid4()),
            "customer_id":order_request.customer_id,
            "items": order_items,
            "delivery_address": order_request.delivery_address,
            "delivery_slot": order_request.delivery_slot,
            "total_price": round(total_price, 2),
            "status": "CREATED",
            "created_at": datetime.utcnow()
        }

        saved_order = save_order(db, order_data)

        event_data = {
            "event_type": "OrderCreated",
            "order_id": order_data["order_id"],
            "customer_id": order_data["customer_id"],
            "items": order_data["items"],
            "total_price": order_data["total_price"],
            "delivery_address": order_data["delivery_address"],
            "delivery_slot": order_data["delivery_slot"],
            "created_at": order_data["created_at"]
        }

        # Publish an OrderCreated event so other services can react asynchronously
        publish_order_created_event(event_data)

        return {
            "order_id": saved_order.order_id,
            "status": saved_order.status,
            "total_price": saved_order.total_price,
            "status": "Order created successfully and awaiting payment"
        }
    
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Order could not be created: { str(error)}"
        )


@app.get("/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = get_order_by_id(db, order_id)

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "items": json.loads(order.items),
        "delivery_address": order.delivery_address,
        "delivery_slot": order.delivery_slot,
        "total_price": order.total_price,
        "status": order.status,
        "created_at": order.created_at
    }


@app.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = get_all_orders(db)

    return [
        {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "items": json.loads(order.items),
            "delivery_address": order.delivery_address,
            "delivery_slot": order.delivery_slot,
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at
        }
        for order in orders
    ]