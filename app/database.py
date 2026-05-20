from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

# SQLite database used for local storage
DATABASE_URL = "sqlite:///./orders.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    
    order_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, nullable=False)
    items = Column(Text, nullable=False)
    delivery_address = Column(String, nullable=False)
    delivery_slot = Column(String, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create the database tables automatically on startup
def create_table():
    Base.metadata.create_all(bind=engine)

def save_order(db, order_data):
    order = Order(
        order_id = order_data["order_id"],
        customer_id = order_data["customer_id"],
        items = json.dumps(order_data["items"]),  # Store item list as a JSON text inside SQLite
        delivery_address = order_data["delivery_address"],
        delivery_slot = order_data["delivery_slot"],
        total_price = order_data["total_price"],
        status = order_data["status"],
        created_at = order_data["created_at"]
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order

def get_order_by_id(db, order_id):
    return db.query(Order).filter(Order.order_id == order_id).first()

def get_all_orders(db):
    return db.query(Order).all()