import os
import time
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request

from datetime import datetime
from typing import List

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure structured logging
class StructuredLogger:
    """JSON structured logging with context."""
    def __init__(self, service_name, team, environment):
        self.service_name = service_name
        self.team = team
        self.environment = environment
        self.logger = logging.getLogger(service_name)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log(self, level, message, **context):
        log_context = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "team": self.team,
            "environment": self.environment,
            "level": level,
            "message": message,
        }
        log_context.update(context)
        self.logger.info(json.dumps(log_context))

APP_TEAM = os.getenv("APP_TEAM", "team-alpha")
APP_ENV = os.getenv("APP_ENV", "dev")
logger = StructuredLogger("billing-api", APP_TEAM, APP_ENV)

app = FastAPI(
    title="Billing API",
    description="Internal billing service for team-alpha running on ECPS dev platform.",
    version="0.2.0",
)


# --- Prometheus metrics ---

REQUEST_COUNT = Counter(
    "billing_api_requests_total",
    "Total HTTP requests to billing-api",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "billing_api_request_latency_seconds",
    "HTTP request latency for billing-api",
    ["method", "path"],
)

DB_ERRORS = Counter(
    "billing_api_db_errors_total",
    "Total database errors in billing-api",
)

# Cost attribution metrics
COST_RECORDED = Counter(
    "billing_api_cost_recorded_total",
    "Total cost recorded (USD)",
    ["team", "service"],
)

COST_PER_REQUEST = Histogram(
    "billing_api_cost_per_request_dollars",
    "Cost per request in dollars",
    ["endpoint"],
)

USAGE_UNITS_TOTAL = Counter(
    "billing_api_usage_units_total",
    "Total usage units recorded",
    ["team", "service"],
)


DB_HOST = os.getenv("DB_HOST", "postgres.platform-data.svc.cluster.local")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not all([DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError("DB_NAME, DB_USER, DB_PASSWORD must be set in environment")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


class UsageRecordIn(BaseModel):
    team: str
    service: str
    units: float
    timestamp: datetime
    cost: float


class UsageRecordOut(UsageRecordIn):
    id: int


class InvoiceIn(BaseModel):
    team: str
    period_start: datetime
    period_end: datetime
    total_cost: float
    status: str


class InvoiceOut(InvoiceIn):
    id: int


@app.on_event("startup")
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_records (
            id SERIAL PRIMARY KEY,
            team TEXT NOT NULL,
            service TEXT NOT NULL,
            units DOUBLE PRECISION NOT NULL,
            ts TIMESTAMPTZ NOT NULL,
            cost NUMERIC(12,2) NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            team TEXT NOT NULL,
            period_start TIMESTAMPTZ NOT NULL,
            period_end TIMESTAMPTZ NOT NULL,
            total_cost NUMERIC(12,2) NOT NULL,
            status TEXT NOT NULL
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        # Count 500s even if exception bubbles up
        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status="500",
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            path=request.url.path,
        ).observe(time.time() - start)
        raise

    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status=str(response.status_code),
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        path=request.url.path,
    ).observe(time.time() - start)
    return response



@app.get("/health")
def health():
    return {"status": "ok", "service": "billing-api"}


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)



@app.get("/api/v1/usage", response_model=List[UsageRecordOut])
def list_usage():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, team, service, units, ts, cost
        FROM usage_records
        ORDER BY id ASC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        UsageRecordOut(
            id=row[0],
            team=row[1],
            service=row[2],
            units=float(row[3]),
            timestamp=row[4],
            cost=float(row[5]),
        )
        for row in rows
    ]


@app.post("/api/v1/usage", response_model=UsageRecordOut)
def create_usage(record: UsageRecordIn):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO usage_records (team, service, units, ts, cost)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (record.team, record.service, record.units, record.timestamp, record.cost),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # Track cost metrics
        COST_RECORDED.labels(team=record.team, service=record.service).inc(record.cost)
        USAGE_UNITS_TOTAL.labels(team=record.team, service=record.service).inc(record.units)
        COST_PER_REQUEST.labels(endpoint="/api/v1/usage").observe(record.cost)
        
        logger.log("info", "Usage recorded", team=record.team, service=record.service, 
                   cost=record.cost, units=record.units, usage_id=new_id)
        
        return UsageRecordOut(id=new_id, **record.dict())
    except Exception as e:
        DB_ERRORS.inc()
        logger.log("error", "Failed to record usage", error=str(e), team=record.team)
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/api/v1/invoices", response_model=List[InvoiceOut])
def list_invoices():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, team, period_start, period_end, total_cost, status
        FROM invoices
        ORDER BY id ASC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        InvoiceOut(
            id=row[0],
            team=row[1],
            period_start=row[2],
            period_end=row[3],
            total_cost=float(row[4]),
            status=row[5],
        )
        for row in rows
    ]


@app.get("/api/v1/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, team, period_start, period_end, total_cost, status
        FROM invoices
        WHERE id = %s;
        """,
        (invoice_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return InvoiceOut(
        id=row[0],
        team=row[1],
        period_start=row[2],
        period_end=row[3],
        total_cost=float(row[4]),
        status=row[5],
    )


@app.post("/api/v1/invoices", response_model=InvoiceOut)
def create_invoice(invoice: InvoiceIn):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO invoices (team, period_start, period_end, total_cost, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                invoice.team,
                invoice.period_start,
                invoice.period_end,
                invoice.total_cost,
                invoice.status,
            ),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # Track invoice cost
        COST_RECORDED.labels(team=invoice.team, service="billing-api").inc(invoice.total_cost)
        logger.log("info", "Invoice created", team=invoice.team, total_cost=invoice.total_cost, 
                   period_start=invoice.period_start.isoformat(), 
                   period_end=invoice.period_end.isoformat(), invoice_id=new_id)
        
        return InvoiceOut(id=new_id, **invoice.dict())
    except Exception as e:
        DB_ERRORS.inc()
        logger.log("error", "Failed to create invoice", error=str(e), team=invoice.team)
        raise HTTPException(status_code=500, detail="Database error")

