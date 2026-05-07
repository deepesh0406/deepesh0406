# RAG System - Document Intelligence

A **Retrieval-Augmented Generation (RAG)** system for document analysis and insights. This system allows users to upload documents, query them using natural language, and generate visualizations and analytics.

---

## 🚀 Features

- **Document Upload & Processing**
  - Supports PDF, Word, Excel, CSV, Text, JSON, and PowerPoint files.
  - Automatic document chunking and metadata extraction.

- **RAG Chat Interface**
  - Ask questions about your uploaded documents.
  - Generates context-aware responses using relevant document chunks.
  - Option to include visualizations for queries.

- **Visualization & Analytics**
  - Generate charts, graphs, and insights based on uploaded documents.
  - Supports bar, line, scatter, histogram, pie, heatmap, and box charts.
  - Advanced analytics including trends, correlation, and distribution.

- **Document Management**
  - View uploaded documents with metadata.
  - Delete individual or all documents from the system.

- **Technology Stack**
  - **Backend**: FastAPI, ChromaDB, Python 3.11
  - **Frontend**: Streamlit
  - **Containerization**: Docker, Docker Compose

---
## 📁 Project Structure
<img width="674" height="510" alt="image" src="https://github.com/user-attachments/assets/2dda04fc-b6fd-4b40-85e1-70b5f5254c68" />


## 🚀 Local Development (Docker Compose)

This project is designed to run with **Docker Compose**.

### Prerequisites
- Docker Desktop installed and running
- A `GEMINI_API_KEY`

### Setup
1. Copy/create a `.env` file in the repository root:
   ```env
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```

2. Build and run:
   ```bash
   docker compose -f rag/docker-compose.yml up --build
   ```

### Endpoints
- Backend API: http://localhost:8002
  - `GET /health`
  - `POST /upload`
  - `POST /chat`
  - `POST /analytics`
  - `GET /documents`
- Frontend (Streamlit): http://localhost:8800

### Notes
- Uploaded files are stored in the container at: **`/app/uploads`**.
- ChromaDB is exposed internally to the backend via:
  - `CHROMA_HOST=vectordb`
  - `CHROMA_PORT=8000`


