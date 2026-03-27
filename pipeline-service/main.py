from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import uvicorn

from database import engine, get_db, Base
from models.customer import Customer
from services.ingestion import run_ingestion

# NOTE: Table creation is handled by dlt during ingestion.
# Do NOT call Base.metadata.create_all() here — it conflicts with dlt's staging schema.

app = FastAPI(title="Pipeline Service", version="1.0.0")


# --- Pydantic schema for API responses ---
class CustomerSchema(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    account_balance: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # allows reading from SQLAlchemy model


# GET /api/health - Health check
@app.get("/api/health")
def health():
    return {"status": "ok"}


# POST /api/ingest - Trigger the data pipeline
@app.post("/api/ingest")
def ingest():
    """
    Runs the dlt pipeline: fetches all customers from Flask mock server
    and upserts them into PostgreSQL. Pagination is handled automatically.
    """
    try:
        records_processed = run_ingestion()
        return {
            "status": "success",
            "records_processed": records_processed
        }
    except Exception as e:
        print(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/customers - Return paginated customers from DB
@app.get("/api/customers", response_model=List[CustomerSchema])
def get_customers(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    """Return customers from the database with pagination."""
    offset = (page - 1) * limit
    customers = db.query(Customer).offset(offset).limit(limit).all()
    return customers


# GET /api/customers/{id} - Return a single customer from DB
@app.get("/api/customers/{customer_id}", response_model=CustomerSchema)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Return a single customer by customer_id, or 404 if not found."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
