# Multi-Modal Vision-Language RAG for Industrial Maintenance

This project is a React + FastAPI system for diagnosing machine faults using AI.

## Project Structure

- `frontend/`: React + Vite + TailwindCSS application.
- `backend/`: FastAPI + LangGraph + Qdrant application.
- `data/`: Storage for manual PDFs.
- `docker-compose.yml`: Services configuration (Qdrant).

## Setup Instructions

### 🔐 Security Setup
1. Copy `.env.example` to `.env`
2. Replace placeholder keys with your actual API keys
3. NEVER commit `.env` to version control
4. Rotate keys immediately if accidentally exposed

### Backend
1. Navigate to `backend/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend
1. Navigate to `frontend/`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```

### Infrastructure
Start Qdrant vector database:
```bash
docker-compose up -d qdrant
```
