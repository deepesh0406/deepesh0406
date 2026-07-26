from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import os
import uuid
from typing import List
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from services.document_processor import DocumentProcessor
from services.rag_service import RAGService
from services.visualization_service import VisualizationService
from models.schemas import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    AnalyticsRequest,
    VisualizationRequest,
)

load_dotenv()

# Container-safe paths
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global services
document_processor = None
rag_service = None
visualization_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global document_processor, rag_service, visualization_service

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment")

    document_processor = DocumentProcessor()
    rag_service = RAGService(gemini_model=os.getenv("GEMINI_MODEL"))
    visualization_service = VisualizationService(gemini_api_key=gemini_api_key)

    await rag_service.initialize()
    yield

    if rag_service:
        await rag_service.cleanup()


app = FastAPI(
    title="RAG System API",
    description="A comprehensive RAG system for document analysis and insights",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "RAG System API is running"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "document_processor": bool(document_processor),
            "rag_service": bool(rag_service),
            "visualization_service": bool(visualization_service),
        },
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    processed_files = []

    for file in files:
        if not file.filename:
            continue

        file_id = str(uuid.uuid4())
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()
        unique_filename = f"{file_id}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            processed_doc = await document_processor.process_document(file_path, file.filename)
            processed_doc["file_id"] = file_id

            # Normalize metadata for ChromaDB
            metadata = processed_doc.get("metadata", {})
            for k, v in list(metadata.items()):
                if isinstance(v, (list, dict)):
                    metadata[k] = str(v)
            processed_doc["metadata"] = metadata

            await rag_service.add_document(processed_doc)
            processed_files.append(processed_doc)

        except Exception as e:
            # best-effort cleanup
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")

    if not processed_files:
        raise HTTPException(status_code=400, detail="No files were successfully processed")

    return UploadResponse(
        success=True,
        message=f"Successfully processed {len(processed_files)} files",
        files=processed_files,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")

    try:
        relevant_docs = await rag_service.search_documents(request.query, max_results=request.max_results)

        response_text = await rag_service.generate_response(
            query=request.query,
            documents=relevant_docs,
            chat_history=request.chat_history,
        )

        visualization = None
        if request.include_visualization:
            viz_result = await visualization_service.generate_visualization(
                query=request.query,
                documents=relevant_docs,
                response=response_text,
            )
            if isinstance(viz_result, dict):
                visualization = viz_result

        return ChatResponse(
            response=response_text,
            sources=relevant_docs,
            visualization=visualization,
            timestamp=None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.post("/visualization")
async def generate_visualization(request: VisualizationRequest):
    try:
        relevant_docs = await rag_service.search_documents(request.query)
        if not relevant_docs:
            return {"error": "No relevant documents found for visualization"}

        chart_base64 = await visualization_service.generate_visualization(
            query=request.query,
            documents=relevant_docs,
            response="",
        )

        return chart_base64 if isinstance(chart_base64, dict) else {"result": chart_base64}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating visualization: {str(e)}")


@app.post("/analytics")
async def get_analytics(request: AnalyticsRequest):
    try:
        relevant_docs = await rag_service.search_documents(request.query)
        if not relevant_docs:
            return {"error": "No relevant documents found for analytics"}

        analytics = await visualization_service.generate_analytics(
            query=request.query,
            documents=relevant_docs,
            chart_types=request.chart_types,
        )
        return JSONResponse(content=analytics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")


@app.get("/documents")
async def list_documents():
    try:
        documents = await rag_service.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    try:
        success = await rag_service.delete_document(file_id)
        if success:
            return {"message": "Document deleted successfully"}
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

