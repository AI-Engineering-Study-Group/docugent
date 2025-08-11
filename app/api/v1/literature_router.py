"""
Literature Review API endpoints for PDF upload and Q&A functionality.
"""

import os
import tempfile
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from fastapi.responses import JSONResponse
import shutil

from app.config.logger import Logger
from app.agents.tools.literature_review_tools import literature_tools
from app.services.qa_service import qa_service

logger = Logger.get_logger(__name__)
router = APIRouter()

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for literature review analysis.
    
    Args:
        file: PDF file to upload
        
    Returns:
        Upload result with file metadata
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Create upload directory
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from PDF (legacy method)
        result = literature_tools.extract_text_from_pdf(str(file_path))
        
        # Process document for advanced Q&A capabilities
        qa_result = qa_service.process_document_for_qa(str(file_path))
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "PDF uploaded and processed successfully",
                    "data": result,
                    "qa_processing": qa_result
                }
            )
        else:
            # Clean up file if processing failed
            if file_path.exists():
                file_path.unlink()
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process PDF: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/list-pdfs")
async def list_pdfs():
    """
    List all uploaded PDFs with their metadata.
    
    Returns:
        List of uploaded PDFs
    """
    try:
        result = literature_tools.list_uploaded_pdfs()
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to list PDFs")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing PDFs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/search")
async def search_pdfs(
    query: str = Query(..., description="Search query"),
    file_hash: Optional[str] = Query(None, description="Specific PDF to search")
):
    """
    Search for content within uploaded PDFs.
    
    Args:
        query: Search query
        file_hash: Specific PDF to search (optional)
        
    Returns:
        Search results
    """
    try:
        result = literature_tools.search_pdf_content(query=query, file_hash=file_hash)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to search PDFs")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching PDFs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/summary/{file_hash}")
async def get_pdf_summary(file_hash: str):
    """
    Get summary of a specific PDF.
    
    Args:
        file_hash: Hash of the PDF file
        
    Returns:
        PDF summary
    """
    try:
        result = literature_tools.get_pdf_summary(file_hash=file_hash)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "Failed to get PDF summary")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/delete/{file_hash}")
async def delete_pdf(file_hash: str):
    """
    Delete an uploaded PDF and its associated data.
    
    Args:
        file_hash: Hash of the PDF file to delete
        
    Returns:
        Deletion result
    """
    try:
        # Check if PDF exists
        if file_hash not in literature_tools.metadata:
            raise HTTPException(
                status_code=404,
                detail="PDF not found"
            )
        
        # Remove files
        upload_dir = Path("data/uploads")
        
        # Remove text file
        text_file = upload_dir / f"{file_hash}.txt"
        if text_file.exists():
            text_file.unlink()
        
        # Remove PDF file
        pdf_filename = literature_tools.metadata[file_hash]["filename"]
        pdf_file = upload_dir / pdf_filename
        if pdf_file.exists():
            pdf_file.unlink()
        
        # Remove from metadata
        del literature_tools.metadata[file_hash]
        literature_tools._save_metadata()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"PDF {pdf_filename} deleted successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/ask-question")
async def ask_question(
    question: str = Form(..., description="Question about the uploaded PDFs"),
    file_hash: Optional[str] = Form(None, description="Specific PDF to ask about")
):
    """
    Ask a question about uploaded PDF content using advanced AI capabilities.
    
    Args:
        question: Question to ask
        file_hash: Specific PDF to ask about (optional)
        
    Returns:
        AI-generated answer with sources and metadata
    """
    try:
        # Use the advanced Q&A service
        qa_result = qa_service.ask_question(question, file_hash)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "question": qa_result.question,
                "answer": qa_result.answer,
                "confidence": qa_result.confidence,
                "sources": qa_result.sources,
                "document_metadata": qa_result.document_metadata,
                "processing_info": qa_result.processing_info,
                "model_used": qa_result.model_used,
                "file_hash": file_hash
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
