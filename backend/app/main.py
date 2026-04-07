from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ingest, search, workflow, history, erp

from app.core.sql_db import init_db

app = FastAPI(title="Multi-Modal Vision-Language RAG API")

@app.on_event("startup")
def on_startup():
    init_db()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(workflow.router, prefix="/api/v1", tags=["Agent Workflow"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(erp.router, prefix="/api/v1", tags=["ERP Integration"])

@app.get("/")
async def root():


    return {"message": "Welcome to the Industrial Maintenance RAG System"}
