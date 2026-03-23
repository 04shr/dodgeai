"""
O2C Intelligence — FastAPI Entry Point
=======================================
Run:
    cd backend
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os, logging, time
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(name)s  %(message)s")
log = logging.getLogger("o2c")

from app.services.data_service import DataService
from app.routers import kpis, orders, issues, customers, ai

# ── Lifespan: warm data cache on startup ──────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Loading O2C datasets into memory…")
    DataService.load()
    log.info("Data ready ✓")
    yield
    log.info("Shutting down.")

app = FastAPI(
    title="O2C Intelligence API",
    version="1.0.0",
    description="AI-powered Order-to-Cash analytics for SAP data",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request timing middleware ─────────────────────────────
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - t0) * 1000)
    response.headers["X-Process-Time-Ms"] = str(ms)
    log.info(f"{request.method} {request.url.path}  {response.status_code}  {ms}ms")
    return response

# ── Global exception handler ─────────────────────────────
@app.exception_handler(Exception)
async def global_exc_handler(request: Request, exc: Exception):
    log.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": str(exc), "path": str(request.url.path)})

# ── Routers ───────────────────────────────────────────────
app.include_router(kpis.router,      prefix="/api/kpis",      tags=["KPIs"])
app.include_router(orders.router,    prefix="/api/orders",    tags=["Orders"])
app.include_router(issues.router,    prefix="/api/issues",    tags=["Issues"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(ai.router,        prefix="/api/ai",        tags=["AI"])

# ── Health + meta ──────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "data_loaded": DataService.is_loaded(),
        "orders": DataService.order_count(),
    }

@app.get("/", tags=["System"])
def root():
    return {"message": "O2C Intelligence API", "docs": "/docs", "health": "/health"}
