"""Delta Plax Education Suite - FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.response import fail, ok
from app.middleware.tenant import TenantMiddleware

settings = get_settings()

app = FastAPI(
    title="Delta Plax Education Suite API",
    version="0.1.0",
    description="Multi-tenant, offline-capable School Management ERP.",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS for the React frontend (cloud) and the LAN-served local frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant resolution runs on every request (section 8.2).
app.add_middleware(TenantMiddleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["platform"])
def health() -> dict:
    """Liveness probe used by the sync engine and orchestrators."""
    return ok({"status": "healthy", "environment": settings.environment})


# --- Consistent error envelope (section 16) ---------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=fail("Validation error", errors=[str(e) for e in exc.errors()]),
    )
