import os
import json
import time
from datetime import datetime

import psycopg2
from psycopg2 import errors
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from redis import Redis
from minio import Minio

# --------------------------------------------------------------------
# Env
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
# Clients
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
# Metrics
# --------------------------------------------------------------------

JOBS_PROCESSED = Counter(
    "jobs_worker_jobs_processed_total",
    "Jobs processed successfully",
    ["job_type", "team"],
)

JOBS_FAILED = Counter(
    "jobs_worker_jobs_failed_total",
    "Jobs that failed processing",
    ["job_type", "team"],
)

JOB_DURATION = Histogram(
    "jobs_worker_job_duration_seconds",
    "Job processing duration",
    ["job_type"],
)

QUEUE_DEPTH = Gauge(
    "jobs_worker_queue_depth",
    "Number of jobs currently in the queue",
)

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------


def process_cost_report_job(conn, job):
    """
    Example "processing": aggregate total cost for the given team
    from usage_records and write result as JSON to MinIO.

    If the usage_records table does not exist (lab out-of-sync), we treat
    the total_cost as 0 instead of failing the job.
    """
    job_id = job["id"]
    team = job["team"]

    # 1) Aggregate cost from usage_records, but be tolerant if table is missing
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(cost), 0)
                FROM usage_records
                WHERE team = %s
                """,
                (team,),
            )
            total_cost = cur.fetchone()[0]
    except errors.UndefinedTable:
        # Table does not exist in this DB; log and assume 0 cost.
        print("[WARN] usage_records table not found; treating total_cost as 0")
        total_cost = 0

    result = {
        "job_id": job_id,
        "job_type": job["job_type"],
        "team": team,
        "generated_at": datetime.utcnow().isoformat(),
        "total_cost": float(total_cost),
    }

    # 2) Ensure bucket exists before writing
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)

    # 3) Write result JSON to MinIO
    object_name = f"{job_id}.json"
    data_bytes = json.dumps(result).encode("utf-8")
    minio_client.put_object(
        MINIO_BUCKET,
        object_name,
        data=data_bytes,
        length=len(data_bytes),
        content_type="application/json",
    )

    result_location = f"s3://{MINIO_BUCKET}/{object_name}"

    # 4) Update job row with completed status + result_location
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE jobs
            SET status = %s,
                updated_at = %s,
                result_location = %s
            WHERE id = %s
            """,
            ("completed", datetime.utcnow(), result_location, job_id),
        )




def process_job_loop():
    conn = get_pg_conn()
    print("jobs-worker started, polling Redis queue...")

    while True:
        QUEUE_DEPTH.set(redis_client.llen(JOB_QUEUE_KEY))
        item = redis_client.brpop(JOB_QUEUE_KEY, timeout=5)
        if not item:
            continue

        _, payload = item
        job = json.loads(payload)

        job_type = job.get("job_type", "unknown")
        team = job.get("team", "unknown")

        start = time.time()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    ("running", datetime.utcnow(), job["id"]),
                )

            if job_type == "cost-report":
                process_cost_report_job(conn, job)
            else:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE jobs
                        SET status = %s,
                            updated_at = %s
                        WHERE id = %s
                        """,
                        ("failed", datetime.utcnow(), job["id"]),
                    )
                raise ValueError(f"Unsupported job_type: {job_type}")

            duration = time.time() - start
            JOB_DURATION.labels(job_type=job_type).observe(duration)
            JOBS_PROCESSED.labels(job_type=job_type, team=team).inc()

        except Exception as exc:
            print(f"Error processing job {job.get('id')}: {exc}")
            JOBS_FAILED.labels(job_type=job_type, team=team).inc()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    ("failed", datetime.utcnow(), job["id"]),
                )



if __name__ == "__main__":
    # Expose metrics on :8001/metrics
    start_http_server(8001)
    process_job_loop()
