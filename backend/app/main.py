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

app = FastAPI(title="Multi-Modal Vision-Language RAG API", lifespan=lifespan)

# Configure CORS (configurable via CORS_ORIGINS env var)
default_origins = "http://localhost,http://localhost:5173,http://localhost:3000"
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

