import os
from datetime import datetime
from typing import List

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Billing API",
    description="Internal billing service for team-alpha running on ECPS dev platform.",
    version="0.2.0",
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


@app.get("/health")
def health():
    return {"status": "ok", "service": "billing-api"}


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

    return UsageRecordOut(id=new_id, **record.dict())


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

    return InvoiceOut(id=new_id, **invoice.dict())

