from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class OrderItemRequest(BaseModel):
    product_id: str
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)

class OrderCreateRequest(BaseModel):
    customer_id: str
    items: List[OrderItemRequest] = Field(min_length=1)
    delivery_address: str
    delivery_slot: str

class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float

class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    items: List[OrderItemResponse]
    delivery_address: str
    delivery_slot: str
    total_price: float
    status: str
    created_at: datetime

