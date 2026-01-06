from fastapi import FastAPI, Response
from pydantic import BaseModel
from dotenv import load_dotenv
import time

from main import main as execute_sql_query

from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

load_dotenv()

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Prometheus metrics
# ---------------------------

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)

HTTP_REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["path"]
)

AGENT_FAILURES_TOTAL = Counter(
    "agent_failures_total",
    "Total failed agent executions"
)

# ---------------------------
# Middleware for metrics
# ---------------------------

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time

    HTTP_REQUESTS_TOTAL.labels(
        request.method,
        request.url.path,
        response.status_code
    ).inc()

    HTTP_REQUEST_LATENCY.labels(
        request.url.path
    ).observe(latency)

    return response


# Define what data we expect from user
class QueryRequest(BaseModel):
    query: str


# Root endpoint - just to check if server is running
@app.get("/")
def home():
    return {"message": "SQL Agent API is running!"}


# Main endpoint - execute natural language query
@app.post("/query")
def execute_query(request: QueryRequest):
    user_query = request.query

    result = execute_sql_query(user_query)

    # Track agent-level failures
    if not result.get("valid", False):
        AGENT_FAILURES_TOTAL.inc()

    return result


# ---------------------------
# Prometheus scrape endpoint
# ---------------------------

@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
