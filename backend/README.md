---
title: IndustriFix AI Backend
emoji: 🏭
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: Dockerfile
pinned: false
---

# 🏭 IndustriFix AI — Industrial Maintenance RAG Backend

Multi-modal Vision-Language RAG system for industrial equipment maintenance, powered by FastAPI + LangGraph + Qdrant.

## 🚀 Features

- 🔍 Multi-modal search (text + image queries)
- 📄 PDF manual ingestion with intelligent chunking
- 🤖 LangGraph-based reasoning agents
- 🔐 JWT authentication with role-based access
- 📊 Qdrant vector database with metadata filtering

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env  # Then fill in your keys

# Run locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API docs: http://localhost:8000/docs