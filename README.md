<p align="center">
  <h1 align="center">🏭 IndustriFix AI</h1>
  <p align="center">
    <strong>Multi-Modal Vision-Language RAG System for Industrial Maintenance</strong>
  </p>
  <p align="center">
    An intelligent, AI-powered platform that diagnoses machine faults from images and technical manuals, generates step-by-step repair guides, performs safety analysis, calculates ROI, and integrates with ERP systems — all through an agentic AI pipeline.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/LangChain-Agent-FF6F00" alt="LangChain">
  <img src="https://img.shields.io/badge/LangGraph-Agent-FF6F00" alt="LangGraph">
  <img src="https://img.shields.io/badge/Qdrant-Vector_DB-DC382D" alt="Qdrant">
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Getting Started](#-getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Environment Variables](#2-environment-variables)
  - [3. Generate Security Keys](#3-generate-security-keys)
  - [4a. Local Development Setup](#4a-local-development-setup)
  - [4b. Docker Setup (Recommended)](#4b-docker-setup-recommended)
- [Initial Setup & First Login](#-initial-setup--first-login)
- [Usage Guide](#-usage-guide)
- [API Reference](#-api-reference)
- [Agent Workflow Pipeline](#-agent-workflow-pipeline)
- [Security Features](#-security-features)
- [Multi-Tenancy](#-multi-tenancy)
- [Configuration Reference](#-configuration-reference)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

**IndustriFix AI** is an end-to-end industrial maintenance assistant that combines:

- **Computer Vision** — Upload photos of faulty machine parts for visual diagnosis
- **RAG (Retrieval-Augmented Generation)** — Searches through ingested PDF maintenance manuals using hybrid vector search
- **Agentic AI Pipeline** — A LangGraph-powered multi-step agent that retrieves context, generates repair guides, checks safety, calculates ROI, and creates ERP tickets
- **Human-in-the-Loop** — Engineers can review and approve before ERP tickets are created
- **Multi-Tenant SaaS Architecture** — Each company gets isolated data, users, and documents

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🖼️ **Multi-Modal Analysis** | Upload machine images + text queries for AI-powered fault diagnosis |
| 📚 **PDF Manual Ingestion** | Automatically extract, chunk, embed, and index technical manuals |
| 🔍 **Hybrid Search (RRF)** | Reciprocal Rank Fusion combining image + text vector search |
| 🤖 **Agentic Repair Guides** | LangGraph pipeline: Retrieve → Generate → Safety → ROI → ERP |
| ✅ **Human-in-the-Loop** | Breakpoint before ERP ticket creation for engineer approval |
| 🔐 **Enterprise Auth** | JWT (RS256) with access/refresh tokens, RBAC, token blacklisting |
| 🏢 **Multi-Tenancy** | Company-scoped data isolation for users, documents, and search |
| 👑 **Role-Based Access** | Super Admin, Admin, Engineer, and Viewer roles |
| 📊 **ROI Dashboard** | Automated cost-savings calculation vs. traditional repair times |
| 🔗 **ERP Integration** | Mock SAP S/4HANA ticket creation (ready for real integration) |
| 📜 **Repair History** | Paginated audit trail of all past diagnoses |
| 🛡️ **Safety Warnings** | Dynamic hazard detection based on AI output |
| 🔄 **LLM Fallback** | Primary: Gemini 2.5 Flash → Fallback: Groq Llama 3.3 70B |
| ⚡ **Performance** | Embedding cache (LRU), search cache (TTL), batch upserts |

---

## 🏗️ Architecture

<p align="center">
  <img src="./docs/images/system_architecture.png" alt="IndustriFix AI - System Architecture" width="700">
</p>

> *System Architecture — Frontend (React + Vite) → Backend (FastAPI + LangGraph + RAG) → Data Stores (Qdrant + SQLite) + LLM Providers (Gemini + Groq)*

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | Async REST API framework |
| **LangGraph** | Agentic workflow orchestration with checkpointing |
| **LangChain** | LLM abstractions, structured output, prompt management |
| **Qdrant** | Vector database for semantic search |
| **OpenCLIP (ViT-B-32)** | Multi-modal embeddings (text + image in shared space) |
| **Google Gemini 2.5 Flash** | Primary LLM for multi-modal repair guide generation |
| **Groq (Llama 3.3 70B)** | Fallback text-only LLM |
| **SQLAlchemy + SQLite** | Relational data (users, companies, documents, history) |
| **PyMuPDF (fitz)** | PDF text extraction |
| **python-jose (RS256)** | JWT token creation and validation |
| **Fernet (AES)** | Symmetric encryption for sensitive PII at rest |
| **Passlib + bcrypt** | Password hashing |

### Frontend
| Technology | Purpose |
|---|---|
| **React 18** | UI framework |
| **TypeScript** | Type-safe development |
| **Vite** | Build tool & dev server |
| **TailwindCSS** | Utility-first styling |
| **Zustand** | Lightweight state management |
| **Axios** | HTTP client |
| **Lucide React** | Icon library |
| **jwt-decode** | Client-side JWT decoding |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker & Docker Compose** | Containerized deployment |
| **Nginx** | Production frontend serving with SPA routing |
| **Qdrant (Docker)** | Managed vector database service |

---

## 📁 Project Structure

```
Major-Project/
├── backend/
│   ├── app/
│   │   ├── agent/                  # LangGraph agentic pipeline
│   │   │   ├── graph.py            # StateGraph definition with conditional edges
│   │   │   ├── nodes.py            # Agent nodes: retrieve, generate, safety, roi, erp
│   │   │   └── state.py            # AgentState TypedDict schema
│   │   ├── api/                    # FastAPI route handlers
│   │   │   ├── auth.py             # Login, signup, refresh, logout endpoints
│   │   │   ├── admin.py            # Company admin: user & document management
│   │   │   ├── superadmin.py       # Platform-wide admin: cross-company visibility
│   │   │   ├── workflow.py         # /analyze (SSE) & /approve (HITL) endpoints
│   │   │   ├── ingest.py           # PDF upload and indexing endpoint
│   │   │   ├── search.py           # Text & image search endpoints
│   │   │   ├── history.py          # Paginated repair log retrieval
│   │   │   └── erp.py              # Mock SAP ERP ticket creation
│   │   ├── core/                   # Core infrastructure
│   │   │   ├── config.py           # Pydantic settings (env vars, model config)
│   │   │   ├── auth.py             # JWT creation/validation, RBAC dependency
│   │   │   ├── security.py         # Password hashing, Fernet encryption
│   │   │   ├── db.py               # Qdrant client initialization
│   │   │   └── sql_db.py           # SQLAlchemy engine & session factory
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py             # Company, User, Document, BlacklistedToken
│   │   │   └── history.py          # RepairLog model
│   │   ├── rag/                    # RAG pipeline components
│   │   │   ├── embeddings.py       # OpenCLIP embedding model (singleton)
│   │   │   ├── ingestion.py        # PDF → chunk → embed → Qdrant storage
│   │   │   └── retrieval.py        # Hybrid search with RRF fusion
│   │   └── main.py                 # FastAPI app factory with CORS & routers
│   ├── Dockerfile                  # Python 3.11 backend container
│   └── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginPage.tsx        # Authentication form
│   │   │   ├── UploadSection.tsx    # Image upload with notes
│   │   │   ├── AnalysisResult.tsx   # Repair guide display with SSE streaming
│   │   │   ├── HistoryView.tsx      # Past repair logs table
│   │   │   ├── AdminPanel.tsx       # User & document management (company admin)
│   │   │   └── SuperAdminPanel.tsx  # Cross-company platform management
│   │   ├── api/
│   │   │   └── client.ts           # Axios client with JWT interceptors
│   │   ├── store/
│   │   │   ├── authStore.ts        # Authentication state (Zustand)
│   │   │   └── appStore.ts         # Application state (Zustand)
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   ├── App.tsx                  # Main app with routing & role-based views
│   │   └── main.tsx                 # React entry point
│   ├── Dockerfile                   # Multi-stage: Node build → Nginx
│   ├── package.json                 # NPM dependencies
│   ├── vite.config.ts               # Vite configuration
│   ├── tailwind.config.js           # TailwindCSS configuration
│   └── tsconfig.json                # TypeScript configuration
│
├── data/                            # Storage for uploaded PDF manuals
├── scripts/                         # Utility scripts (model checks, library updates)
├── docker-compose.yml               # Qdrant + Backend + Frontend orchestration
├── gen_keys.py                      # RSA key pair & Fernet key generator
├── .env                             # Environment variables (DO NOT COMMIT)
├── .gitignore                       # Git ignore rules
└── pyproject.toml                   # Python project metadata
```

---

## 📋 Prerequisites

Ensure you have the following installed:

| Requirement | Version | Purpose |
|---|---|---|
| **Python** | ≥ 3.11 | Backend runtime |
| **Node.js** | ≥ 18 | Frontend build tools |
| **npm** | ≥ 9 | Frontend package manager |
| **Docker** & **Docker Compose** | Latest | For Qdrant vector DB (and optional full deployment) |
| **Git** | Latest | Version control |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/AYUSHDEVANI/Major-Project.git
cd Major-Project
```

### 2. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# ─── LLM API Keys ───────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# ─── Encryption Key (AES/Fernet for data-at-rest) ──────────
ENCRYPTION_KEY=your_fernet_key_here

# ─── JWT RSA Keys (RS256 Signing) ──────────────────────────
JWT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
<your RSA private key content>
-----END PRIVATE KEY-----"

JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
<your RSA public key content>
-----END PUBLIC KEY-----"
```

> **🔑 How to get keys:**
> - **Google API Key**: Get from [Google AI Studio](https://aistudio.google.com/apikey)
> - **Groq API Key**: Get from [Groq Console](https://console.groq.com/keys)
> - **Encryption & JWT Keys**: Generate using the provided script (see next step)

### 3. Generate Security Keys

Run the key generation script to create RSA key pairs and Fernet encryption keys:

```bash
pip install cryptography
python gen_keys.py
```

Copy the output into your `.env` file:
- **Fernet key** → `ENCRYPTION_KEY`
- **Private key** → `JWT_PRIVATE_KEY` (wrap in double quotes)
- **Public key** → `JWT_PUBLIC_KEY` (wrap in double quotes)

### 4a. Local Development Setup

#### Start Qdrant Vector Database

```bash
docker-compose up -d qdrant
```

Qdrant will be available at `http://localhost:6333`.

#### Backend Setup

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# OR
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run the dev server
uvicorn app.main:app --reload --app-dir .
```

The API will be available at `http://localhost:8000`.
Interactive API docs at `http://localhost:8000/docs`.

#### Frontend Setup

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### 4b. Docker Setup (Recommended)

Deploy all services with a single command:

```bash
docker-compose up --build
```

This starts:
| Service | URL | Description |
|---|---|---|
| **Frontend** | `http://localhost:5173` | React app served by Nginx |
| **Backend** | `http://localhost:8000` | FastAPI application |
| **Qdrant** | `http://localhost:6333` | Vector database dashboard |

To stop all services:
```bash
docker-compose down
```

To reset all data (including vector DB):
```bash
docker-compose down -v
```

---

## 🔑 Initial Setup & First Login

After starting the application for the first time, you need to create initial user accounts.

### Step 1: Create a Super Admin (Platform Owner)

```bash
curl -X POST http://localhost:8000/api/v1/setup-superadmin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@industrifix.com",
    "password": "SuperAdmin@123",
    "employee_id": "SA001"
  }'
```

### Step 2: Create a Company Admin

```bash
curl -X POST http://localhost:8000/api/v1/setup-admin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "Admin@1234",
    "employee_id": "EMP001",
    "company_name": "Acme Industries"
  }'
```

### Step 3: Log In via the Frontend

1. Open `http://localhost:5173` in your browser
2. Log in with the admin credentials created above
3. Use the **Admin Panel** to create engineer/viewer accounts for your team

### Step 4: Ingest a PDF Manual

After logging in as admin:
1. Use the Admin Panel or the API to upload a PDF maintenance manual
2. The system will automatically extract, chunk, embed, and index the content

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Authorization: Bearer <your_access_token>" \
  -F "file=@path/to/manual.pdf"
```

### Step 5: Analyze a Machine Issue

Log in as an engineer, then:
1. Navigate to the **Analyze** tab
2. Upload a photo of the machine part
3. Optionally add text notes describing the issue
4. Click **Analyze** to start the AI diagnosis pipeline
5. Review the repair guide, safety warnings, and ROI calculations
6. **Approve** or reject the ERP ticket creation

---

## 📖 Usage Guide

### For Engineers
- **Analyze**: Upload machine images with optional text descriptions to receive AI-generated repair guides
- **History**: Review past diagnoses and repair logs for your company
- **Approve ERP Tickets**: Review AI-generated analysis and approve SAP ticket creation

### For Company Admins
- **User Management**: Create, enable/disable, and delete users within your company
- **Document Management**: Upload PDF manuals, activate/deactivate documents from search
- **All Engineer Features**: Admins have full access to diagnostic tools

### For Super Admins
- **Platform Overview**: View all companies, users, and documents across the platform
- **Metrics Dashboard**: Track user counts, document counts, and chunk counts per company

---

## 📡 API Reference

All endpoints are prefixed with `/api/v1`. Interactive documentation available at `/docs`.

### Authentication
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/setup-superadmin` | Create platform super admin (one-time) | None |
| `POST` | `/setup-admin` | Create company + first admin | None |
| `POST` | `/login` | Exchange credentials for JWT tokens | None |
| `POST` | `/refresh` | Refresh access token via cookie | Cookie |
| `POST` | `/logout` | Revoke tokens and clear session | Bearer |

### Core Workflow
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/analyze` | Run full AI diagnosis pipeline (SSE stream) | Engineer+ |
| `POST` | `/approve/{thread_id}` | Approve & resume ERP ticket creation | Engineer+ |

### Search & Ingestion
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/ingest` | Upload and index a PDF manual | Admin |
| `POST` | `/search/text` | Search manuals by text query | Any user |
| `POST` | `/search/image` | Search manuals by image | Any user |

### Data & History
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/history` | Paginated repair log history | Any user |
| `POST` | `/erp/ticket` | Create mock ERP maintenance ticket | Engineer+ |

### Admin Endpoints
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/admin/users` | List users in admin's company | Admin |
| `POST` | `/admin/users` | Create user in admin's company | Admin |
| `DELETE` | `/admin/users/{id}` | Delete user from company | Admin |
| `PATCH` | `/admin/users/{id}/toggle` | Enable/disable user | Admin |
| `GET` | `/admin/documents` | List company documents | Admin |
| `PATCH` | `/admin/documents/{id}/toggle` | Activate/deactivate document | Admin |

### Super Admin Endpoints
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/superadmin/companies` | List all companies with metrics | Super Admin |
| `GET` | `/superadmin/users` | List all users globally | Super Admin |
| `GET` | `/superadmin/documents` | List all documents globally | Super Admin |

---

## 🤖 Agent Workflow Pipeline

The core AI analysis uses a **LangGraph StateGraph** with conditional routing and Human-in-the-Loop control:

<p align="center">
  <img src="./docs/images/agent_workflow.png" alt="LangGraph Agent Workflow Pipeline" width="600">
</p>

> *Agent Pipeline — START → Retrieve (RRF) → Generate (Gemini/Groq) → Safety → ROI → ERP (HITL Approval) → END*

**Key Features:**
- **Conditional Routing**: Automatically escalates to human if retrieval fails or analysis errors occur
- **Human-in-the-Loop**: Graph pauses before ERP node; engineer must call `/approve/{thread_id}` to continue
- **Memory Checkpointing**: `MemorySaver` enables session persistence across the pause
- **Streaming (SSE)**: Real-time step-by-step progress via Server-Sent Events

---

## 🔐 Security Features

| Feature | Implementation |
|---|---|
| **JWT Authentication** | RS256 asymmetric signing with access (15min) + refresh (7 days) tokens |
| **Token Blacklisting** | Revoked JTIs stored in SQL (upgradeable to Redis for production) |
| **Refresh Token** | Stored as `HttpOnly`, `Secure`, `SameSite=Lax` cookie |
| **Password Hashing** | bcrypt via Passlib (work factor 12) |
| **Password Complexity** | Min 8 chars, 1 uppercase, 1 number, 1 special character |
| **Data Encryption** | Fernet (AES-128-CBC) for employee IDs at rest |
| **RBAC** | Role-based middleware: superadmin > admin > engineer > viewer |
| **CORS** | Configurable via `CORS_ORIGINS` env var |
| **File Size Limits** | 10MB max image upload enforced server-side |
| **Input Validation** | Pydantic models with `EmailStr` validation |

---

## 🏢 Multi-Tenancy

IndustriFix supports full multi-tenant isolation:

- **Company-scoped users**: Admins can only manage users within their own company
- **Company-scoped documents**: Ingested PDFs are tagged with `company_id`
- **Company-scoped search**: Qdrant queries include `company_id` filter
- **Company-scoped history**: Repair logs are filtered by the user's company
- **Super Admin oversight**: Platform-wide visibility across all companies

---

## ⚙️ Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ | — | Google AI / Gemini API key |
| `GROQ_API_KEY` | ✅ | — | Groq API key for fallback LLM |
| `ENCRYPTION_KEY` | ✅ | — | Fernet key for data-at-rest encryption |
| `JWT_PRIVATE_KEY` | ✅ | — | RSA private key (PEM) for JWT signing |
| `JWT_PUBLIC_KEY` | ✅ | — | RSA public key (PEM) for JWT verification |
| `QDRANT_MODE` | ❌ | `local` | `local` (file-based) or `server` (remote) |
| `QDRANT_HOST` | ❌ | `localhost` | Qdrant server hostname |
| `QDRANT_PORT` | ❌ | `6333` | Qdrant server port |
| `CORS_ORIGINS` | ❌ | `localhost:5173` | Comma-separated allowed origins |

### Model Configuration (in `backend/app/core/config.py`)

| Setting | Default | Options |
|---|---|---|
| `OPENCLIP_MODEL_NAME` | `ViT-B-32` | `ViT-B-16`, `ViT-L-14`, `ViT-H-14` |
| `OPENCLIP_PRETRAINED` | `laion2b_s34b_b79k` | See [OpenCLIP docs](https://github.com/mlfoundations/open_clip) |
| `COLLECTION_NAME` | `manuals` | Qdrant collection name |

---

## ❓ Troubleshooting

### Common Issues

<details>
<summary><strong>❌ 404 error for Gemini model</strong></summary>

The Google Generative AI library may be outdated. Update it:

```bash
pip install --upgrade google-generativeai langchain-google-genai
```

Then restart the backend server. See `UPDATE_INSTRUCTIONS.md` for details.
</details>

<details>
<summary><strong>❌ "ENCRYPTION_KEY must be set" error</strong></summary>

Ensure your `.env` file is in the **project root** directory (not inside `backend/`). The `.env` file must contain a valid Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
</details>

<details>
<summary><strong>❌ "JWT_PRIVATE_KEY must be set" error</strong></summary>

Ensure your `.env` contains valid RSA keys wrapped in double quotes. Generate fresh keys with:

```bash
python gen_keys.py
```
</details>

<details>
<summary><strong>❌ Qdrant connection refused</strong></summary>

Make sure Docker is running and Qdrant is healthy:

```bash
docker-compose up -d qdrant
docker-compose ps  # Check health status
curl http://localhost:6333/readyz  # Should return {"title":"qdrant..."}
```
</details>

<details>
<summary><strong>❌ Frontend can't reach backend (CORS error)</strong></summary>

Set the `CORS_ORIGINS` environment variable to include your frontend URL:

```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```
</details>

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m "Add your feature"`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

### Development Tips

- Backend auto-reloads with `--reload` flag
- Frontend hot-reloads via Vite HMR
- API docs available at `http://localhost:8000/docs` (Swagger) and `/redoc` (ReDoc)
- Use `backend/requirements-dev.txt` for development dependencies

---

## 📄 License

This project is developed as a Major Project for academic purposes.

---

<p align="center">
  <strong>Built with ❤️ using FastAPI, LangChain, LangGraph, React, and Qdrant</strong>
</p>
