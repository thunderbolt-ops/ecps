from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import List

app = FastAPI(
    title="Billing API",
    description="Internal billing service for team-alpha running on ECPS dev platform.",
    version="0.1.0",
)


class UsageRecord(BaseModel):
    id: int
    team: str
    service: str
    units: float
    timestamp: datetime
    cost: float


class Invoice(BaseModel):
    id: int
    team: str
    period_start: datetime
    period_end: datetime
    total_cost: float
    status: str


FAKE_USAGE: List[UsageRecord] = [
    UsageRecord(
        id=1,
        team="team-alpha",
        service="api-calls",
        units=150,
        timestamp=datetime.utcnow(),
        cost=15.0,
    ),
    UsageRecord(
        id=2,
        team="team-beta",
        service="jobs",
        units=3,
        timestamp=datetime.utcnow(),
        cost=45.0,
    ),
]

FAKE_INVOICES: List[Invoice] = [
    Invoice(
        id=1,
        team="team-alpha",
        period_start=datetime(2024, 2, 1),
        period_end=datetime(2024, 2, 29),
        total_cost=1200.0,
        status="generated",
    )
]


@app.get("/health")
def health():
    return {"status": "ok", "service": "billing-api"}


@app.get("/api/v1/usage", response_model=List[UsageRecord])
def list_usage():
    return FAKE_USAGE


@app.post("/api/v1/usage", response_model=UsageRecord)
def create_usage(record: UsageRecord):
    FAKE_USAGE.append(record)
    return record


@app.get("/api/v1/invoices", response_model=List[Invoice])
def list_invoices():
    return FAKE_INVOICES


@app.get("/api/v1/invoices/{invoice_id}", response_model=Invoice)
def get_invoice(invoice_id: int):
    for inv in FAKE_INVOICES:
        if inv.id == invoice_id:
            return inv
    # simple 404 for now
    raise ValueError(f"Invoice {invoice_id} not found")

