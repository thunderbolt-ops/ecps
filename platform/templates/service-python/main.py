"""
Python FastAPI microservice template for ECPS.
This is scaffolded by: ecpsctl service create --name <service> --language python
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request

# Configure structured logging
class StructuredLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log(self, level: str, message: str, **context):
        log_context = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": level,
            "message": message,
        }
        log_context.update(context)
        self.logger.info(json.dumps(log_context))

SERVICE_NAME = os.getenv("SERVICE_NAME", "REPLACING_SERVICE_NAME")
SERVICE_VERSION = "0.1.0"
logger = StructuredLogger(SERVICE_NAME)

# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_NAME,
    description=f"{SERVICE_NAME} microservice running on ECPS platform",
    version=SERVICE_VERSION,
)

# ========================================================================
# Prometheus metrics
# ========================================================================

REQUEST_COUNT = Counter(
    f"{SERVICE_NAME.replace('-', '_')}_requests_total",
    f"Total HTTP requests to {SERVICE_NAME}",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    f"{SERVICE_NAME.replace('-', '_')}_request_latency_seconds",
    f"HTTP request latency for {SERVICE_NAME}",
    ["method", "path"],
)

# ========================================================================
# Middleware
# ========================================================================

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

# ========================================================================
# Endpoints
# ========================================================================

@app.get("/health")
def health():
    """Health check endpoint for K8s liveness/readiness probes."""
    return {"status": "ok", "service": SERVICE_NAME, "version": SERVICE_VERSION}

@app.get("/ready")
def readiness():
    """Readiness check: service is ready to accept traffic."""
    # Add checks here: DB connectivity, Redis, etc.
    return {"ready": True, "service": SERVICE_NAME}

@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    data = generate_latest()
    return Response(content=data, media_type="text/plain")

@app.get("/api/v1/version")
def get_version():
    """Return service version and metadata."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }

# TODO: Add your business logic endpoints below
# Example:
# @app.get("/api/v1/items")
# def list_items():
#     logger.log("info", "Listing items")
#     return {"items": []}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
