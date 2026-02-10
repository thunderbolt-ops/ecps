import os
import uuid
import json
import time
from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from redis import Redis
from minio import Minio

# --------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------

PG_HOST = os.getenv("PG_HOST", "postgres.platform-data.svc.cluster.local")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "billing")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "dev-postgres-password")

REDIS_HOST = os.getenv("REDIS_HOST", "redis.platform-data.svc.cluster.local")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio.platform-data.svc.cluster.local:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "jobs-results")

JOB_QUEUE_KEY = os.getenv("JOB_QUEUE_KEY", "jobs:queue")

# --------------------------------------------------------------------
# DB / Redis / MinIO clients
# --------------------------------------------------------------------


def get_pg_conn():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )
    conn.autocommit = True
    return conn


redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

# --------------------------------------------------------------------
# Ensure schema and bucket exist
# --------------------------------------------------------------------


def init_db():
    conn = get_pg_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              id UUID PRIMARY KEY,
              job_type TEXT NOT NULL,
              team TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL,
              updated_at TIMESTAMPTZ NOT NULL,
              parameters JSONB,
              result_location TEXT
            );
            """
        )


def init_bucket():
    found = minio_client.bucket_exists(MINIO_BUCKET)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET)


init_db()
init_bucket()

# --------------------------------------------------------------------
# FastAPI app + models
# --------------------------------------------------------------------

app = FastAPI(title="jobs-api", version="0.1.0")


class JobCreateRequest(BaseModel):
    job_type: str
    team: str
    # For now we only support "cost-report" jobs.
    from_ts: Optional[datetime] = None
    to_ts: Optional[datetime] = None


class JobResponse(BaseModel):
    id: str
    job_type: str
    team: str
    status: str
    created_at: datetime
    updated_at: datetime
    parameters: dict
    result_location: Optional[str] = None


# --------------------------------------------------------------------
# Prometheus metrics
# --------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "jobs_api_requests_total",
    "Total HTTP requests to jobs-api",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "jobs_api_request_latency_seconds",
    "HTTP request latency for jobs-api",
    ["method", "path"],
)

JOBS_ENQUEUED = Counter(
    "jobs_api_jobs_enqueued_total",
    "Jobs successfully enqueued",
    ["job_type", "team"],
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
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


@app.get("/health")
def health():
    return {"status": "ok", "service": "jobs-api"}


@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# --------------------------------------------------------------------
# Job endpoints
# --------------------------------------------------------------------


@app.post("/api/v1/jobs", response_model=JobResponse)
def create_job(req: JobCreateRequest):
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    params = {
        "from_ts": req.from_ts.isoformat() if req.from_ts else None,
        "to_ts": req.to_ts.isoformat() if req.to_ts else None,
    }

    conn = get_pg_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO jobs (id, job_type, team, status, created_at, updated_at, parameters)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (job_id, req.job_type, req.team, "queued", now, now, json.dumps(params)),
        )

    # Push onto Redis queue as a simple JSON payload
    payload = {
        "id": job_id,
        "job_type": req.job_type,
        "team": req.team,
        "parameters": params,
    }
    redis_client.rpush(JOB_QUEUE_KEY, json.dumps(payload))

    JOBS_ENQUEUED.labels(job_type=req.job_type, team=req.team).inc()

    return JobResponse(
        id=job_id,
        job_type=req.job_type,
        team=req.team,
        status="queued",
        created_at=now,
        updated_at=now,
        parameters=params,
        result_location=None,
    )


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    conn = get_pg_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, job_type, team, status, created_at, updated_at, parameters, result_location
            FROM jobs
            WHERE id = %s
            """,
            (job_id,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=str(row[0]),
        job_type=row[1],
        team=row[2],
        status=row[3],
        created_at=row[4],
        updated_at=row[5],
        parameters=row[6] or {},
        result_location=row[7],
    )

