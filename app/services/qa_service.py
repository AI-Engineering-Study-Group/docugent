"""
Main Q&A Service that orchestrates the entire multimodal Q&A pipeline.
Coordinates document processing, embeddings, retrieval, and answer generation.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

from app.config.logger import Logger
from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service, AnswerContext

logger = Logger.get_logger(__name__)

@dataclass
class QAResult:
    """Complete Q&A result with all metadata."""
    question: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    document_metadata: Dict[str, Any]
    processing_info: Dict[str, Any]
    model_used: str

class QAService:
    """Main service for handling Q&A operations."""
    
    def __init__(self):
        self.document_processor = document_processor
        self.embedding_service = embedding_service
        self.llm_service = llm_service
    
    def process_document_for_qa(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document for Q&A capabilities.
        This includes chunking, embedding generation, and storage.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Processing result with metadata
        """
        try:
            # Step 1: Process document into chunks
            logger.info(f"Processing document: {file_path}")
            doc_result = self.document_processor.process_document(file_path)
            
            if not doc_result["success"]:
                return doc_result
            
            file_hash = doc_result["file_hash"]
            metadata = doc_result["metadata"]
            
            # Step 2: Generate embeddings for chunks
            logger.info(f"Generating embeddings for document: {file_hash}")
            chunks_result = self.document_processor.get_document_chunks(file_hash)
            
            if not chunks_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to retrieve document chunks",
                    "message": "Document processing incomplete"
                }
            
            chunks = chunks_result["chunks"]
            embeddings = []
            
            # Generate embeddings for each chunk
            for chunk in chunks:
                chunk_id = chunk["chunk_id"]
                chunk_type = chunk["chunk_type"]
                
                try:
                    if chunk_type == "text":
                        # Generate text embedding
                        embedding_result = self.embedding_service.generate_text_embedding(
                            chunk["content"], chunk_id
                        )
                        embeddings.append(embedding_result)
                        
                    elif chunk_type == "image":
                        # Generate image embedding
                        image_file = chunk.get("image_file")
                        if image_file and Path(image_file).exists():
                            embedding_result = self.embedding_service.generate_image_embedding(
                                image_file, chunk_id
                            )
                            embeddings.append(embedding_result)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {chunk_id}: {e}")
                    continue
            
            # Step 3: Save embeddings
            if embeddings:
                success = self.embedding_service.save_embeddings(file_hash, embeddings)
                if not success:
                    logger.warning(f"Failed to save embeddings for document {file_hash}")
            
            # Step 4: Return comprehensive result
            return {
                "success": True,
                "message": f"Document processed for Q&A: {len(chunks)} chunks, {len(embeddings)} embeddings",
                "file_hash": file_hash,
                "metadata": metadata,
                "processing_summary": {
                    "total_chunks": len(chunks),
                    "text_chunks": len([c for c in chunks if c["chunk_type"] == "text"]),
                    "image_chunks": len([c for c in chunks if c["chunk_type"] == "image"]),
                    "embeddings_generated": len(embeddings),
                    "text_embeddings": len([e for e in embeddings if e.embedding_type == "text"]),
                    "image_embeddings": len([e for e in embeddings if e.embedding_type == "image"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing document for Q&A: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process document for Q&A"
            }
    
    def ask_question(self, question: str, file_hash: str = None) -> QAResult:
        """
        Ask a question and get a contextual answer.
        
        Args:
            question: The question to ask
            file_hash: Specific document to ask about (optional)
            
        Returns:
            QAResult with the answer and metadata
        """
        try:
            logger.info(f"Processing question: {question}")
            
            # Step 1: Generate query embedding
            query_embedding = self.embedding_service.generate_text_embedding(
                question, "query"
            ).embedding
            
            # Step 2: Search for relevant chunks
            logger.info("Searching for relevant chunks...")
            similar_chunks = self.embedding_service.search_similar_chunks(
                query_embedding, file_hash, top_k=5
            )
            
            if not similar_chunks:
                return QAResult(
                    question=question,
                    answer="I couldn't find any relevant information in the uploaded documents to answer your question. Please try rephrasing your question or upload documents that contain relevant information.",
                    confidence=0.0,
                    sources=[],
                    document_metadata={},
                    processing_info={"chunks_found": 0, "search_method": "embedding"},
                    model_used="no_results"
                )
            
            # Step 3: Get document chunks and metadata
            relevant_chunks = []
            document_metadata = {}
            
            for chunk_info in similar_chunks:
                chunk_file_hash = chunk_info["file_hash"]
                chunk_id = chunk_info["chunk_id"]
                
                # Get chunk details
                chunks_result = self.document_processor.get_document_chunks(chunk_file_hash)
                if chunks_result["success"]:
                    # Find the specific chunk
                    for chunk in chunks_result["chunks"]:
                        if chunk["chunk_id"] == chunk_id:
                            chunk["similarity"] = chunk_info["similarity"]
                            chunk["file_hash"] = chunk_file_hash
                            relevant_chunks.append(chunk)
                            break
                    
                    # Store document metadata
                    if not document_metadata:
                        document_metadata = chunks_result["metadata"]
            
            # Step 4: Create answer context
            context = AnswerContext(
                question=question,
                relevant_chunks=relevant_chunks,
                document_metadata=document_metadata,
                chunk_count=len(relevant_chunks),
                total_similarity=sum(chunk.get("similarity", 0) for chunk in relevant_chunks)
            )
            
            # Step 5: Generate answer
            logger.info("Generating answer...")
            generated_answer = self.llm_service.generate_answer(context)
            
            # Step 6: Format result
            processing_info = {
                "chunks_found": len(relevant_chunks),
                "search_method": "embedding_similarity",
                "total_similarity": context.total_similarity,
                "avg_similarity": context.total_similarity / len(relevant_chunks) if relevant_chunks else 0,
                "embedding_model": "simple_text_model",
                "llm_model": generated_answer.model_used
            }
            
            return QAResult(
                question=question,
                answer=generated_answer.answer,
                confidence=generated_answer.confidence,
                sources=generated_answer.sources,
                document_metadata=document_metadata,
                processing_info=processing_info,
                model_used=generated_answer.model_used
            )
            
        except Exception as e:
            logger.error(f"Error in Q&A process: {e}")
            return QAResult(
                question=question,
                answer=f"Sorry, I encountered an error while processing your question: {str(e)}. Please try again.",
                confidence=0.0,
                sources=[],
                document_metadata={},
                processing_info={"error": str(e)},
                model_used="error"
            )
    
    def get_document_status(self, file_hash: str) -> Dict[str, Any]:
        """
        Get the processing status of a document.
        
        Args:
            file_hash: Hash of the document
            
        Returns:
            Document status information
        """
        try:
            # Check if document is processed
            chunks_result = self.document_processor.get_document_chunks(file_hash)
            if not chunks_result["success"]:
                return {
                    "success": False,
                    "status": "not_processed",
                    "message": "Document has not been processed yet"
                }
            
            # Check if embeddings exist
            embeddings = self.embedding_service.load_embeddings(file_hash)
            
            metadata = chunks_result["metadata"]
            chunks = chunks_result["chunks"]
            
            status = {
                "success": True,
                "status": "ready_for_qa",
                "file_hash": file_hash,
                "metadata": metadata,
                "processing_info": {
                    "total_chunks": len(chunks),
                    "text_chunks": len([c for c in chunks if c["chunk_type"] == "text"]),
                    "image_chunks": len([c for c in chunks if c["chunk_type"] == "image"]),
                    "embeddings_available": len(embeddings),
                    "text_embeddings": len([e for e in embeddings if e.embedding_type == "text"]),
                    "image_embeddings": len([e for e in embeddings if e.embedding_type == "image"])
                }
            }
            
            if len(embeddings) == 0:
                status["status"] = "processed_no_embeddings"
                status["message"] = "Document processed but embeddings not generated"
            elif len(embeddings) < len(chunks):
                status["status"] = "partially_embedded"
                status["message"] = f"Document processed with {len(embeddings)}/{len(chunks)} embeddings"
            else:
                status["message"] = "Document ready for Q&A"
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting document status: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "message": "Failed to get document status"
            }
    
    def list_qa_documents(self) -> Dict[str, Any]:
        """
        List all documents available for Q&A.
        
        Returns:
            List of documents with their Q&A status
        """
        try:
            # Get all processed documents
            chunks_dir = Path("data/uploads/chunks")
            metadata_files = list(chunks_dir.glob("*_metadata.json"))
            
            documents = []
            for metadata_file in metadata_files:
                file_hash = metadata_file.stem.replace("_metadata", "")
                
                # Get document status
                status = self.get_document_status(file_hash)
                if status["success"]:
                    documents.append({
                        "file_hash": file_hash,
                        "status": status["status"],
                        "metadata": status["metadata"],
                        "processing_info": status["processing_info"]
                    })
            
            return {
                "success": True,
                "documents": documents,
                "total_count": len(documents),
                "ready_for_qa": len([d for d in documents if d["status"] == "ready_for_qa"])
            }
            
        except Exception as e:
            logger.error(f"Error listing Q&A documents: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list Q&A documents"
            }

# Initialize Q&A service
qa_service = QAService()
