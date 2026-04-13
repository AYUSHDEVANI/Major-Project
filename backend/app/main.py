import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ingest, search, workflow, history, erp, auth, admin, superadmin, chat

from app.core.sql_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(
    title="Multi-Modal Vision-Language RAG API",
    description="Industrial Maintenance RAG System with Multi-Modal Search",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",           # ← Explicitly enable Swagger UI
    redoc_url="/redoc",         # ← Enable alternate docs (optional)
    openapi_url="/openapi.json" # ← Enable OpenAPI schema
)

# Configure CORS (configurable via CORS_ORIGINS env var)
default_origins = "http://localhost,http://localhost:5173,http://localhost:3000,https://huggingface.co"
origins = os.getenv("CORS_ORIGINS", default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(workflow.router, prefix="/api/v1", tags=["Agent Workflow"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(erp.router, prefix="/api/v1", tags=["ERP Integration"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin Panel"])
app.include_router(superadmin.router, prefix="/api/v1", tags=["Super Admin"])
app.include_router(chat.router, prefix="/api/v1", tags=["Support Chat"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Industrial Maintenance RAG System"}


@app.get("/debug/routes")
async def list_routes():
    """List all registered routes for debugging"""
    return {
        "registered_routes": [
            {"path": route.path, "methods": route.methods, "name": route.name}
            for route in app.routes
            if hasattr(route, "path") and not route.path.startswith("/debug")
        ]
    }

@app.get("/debug/info")
async def debug_info():
    """Return app configuration for debugging"""
    return {
        "title": app.title,
        "docs_url": app.docs_url,
        "redoc_url": app.redoc_url,
        "openapi_url": app.openapi_url,
        "cors_origins": [m.middleware.cls.__name__ for m in app.user_middleware if "CORSMiddleware" in str(m.middleware.cls)],
    }
