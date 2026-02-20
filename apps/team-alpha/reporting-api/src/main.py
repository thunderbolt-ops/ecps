import os
import json
import logging
from datetime import datetime
from typing import List, Dict

import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
import time

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
logger = StructuredLogger("reporting-api", APP_TEAM, APP_ENV)

app = FastAPI(
    title="Reporting API",
    description="Read-only reporting service for billing data on ECPS dev platform.",
    version="0.1.0",
)


REQUEST_COUNT = Counter(
    "reporting_api_requests_total",
    "Total HTTP requests to reporting-api",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "reporting_api_request_latency_seconds",
    "HTTP request latency for reporting-api",
    ["method", "path"],
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


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
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


@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


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
