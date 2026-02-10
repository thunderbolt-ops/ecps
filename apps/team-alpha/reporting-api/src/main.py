import os
from datetime import datetime
from typing import List, Dict

import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Reporting API",
    description="Read-only reporting service for billing data on ECPS dev platform.",
    version="0.1.0",
)

# --- DB config from env ---

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


# --- Models ---

class TeamCost(BaseModel):
    team: str
    total_cost: float


class ServiceCost(BaseModel):
    service: str
    total_cost: float


class SummaryResponse(BaseModel):
    generated_at: datetime
    total_cost: float
    by_team: List[TeamCost]
    by_service: List[ServiceCost]


# --- Health endpoint ---

@app.get("/health")
def health():
    return {"status": "ok", "service": "reporting-api"}


# --- Reporting endpoints ---

@app.get("/api/v1/reports/summary", response_model=SummaryResponse)
def summary_report():
    conn = get_db_connection()
    cur = conn.cursor()

    # Total cost
    cur.execute("SELECT COALESCE(SUM(cost), 0) FROM usage_records;")
    total_cost = float(cur.fetchone()[0] or 0.0)

    # Cost by team
    cur.execute(
        """
        SELECT team, COALESCE(SUM(cost), 0)
        FROM usage_records
        GROUP BY team
        ORDER BY team;
        """
    )
    by_team_rows = cur.fetchall()

    # Cost by service
    cur.execute(
        """
        SELECT service, COALESCE(SUM(cost), 0)
        FROM usage_records
        GROUP BY service
        ORDER BY service;
        """
    )
    by_service_rows = cur.fetchall()

    cur.close()
    conn.close()

    return SummaryResponse(
        generated_at=datetime.utcnow(),
        total_cost=total_cost,
        by_team=[
            TeamCost(team=row[0], total_cost=float(row[1] or 0.0))
            for row in by_team_rows
        ],
        by_service=[
            ServiceCost(service=row[0], total_cost=float(row[1] or 0.0))
            for row in by_service_rows
        ],
    )
