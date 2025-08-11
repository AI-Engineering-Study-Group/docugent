"""
Advanced Document Processor for multimodal Q&A system.
Handles text extraction, image extraction, chunking, and embeddings.
"""

import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF
import hashlib
import json
import base64
from PIL import Image
import io
import numpy as np
from dataclasses import dataclass
import re

from app.config.logger import Logger

logger = Logger.get_logger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of document content with metadata."""
    chunk_id: str
    page_number: int
    content: str
    chunk_type: str  # 'text' or 'image'
    image_data: Optional[bytes] = None
    image_format: Optional[str] = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0

@dataclass
class DocumentMetadata:
    """Document metadata and processing information."""
    file_hash: str
    filename: str
    page_count: int
    total_chunks: int
    text_chunks: int
    image_chunks: int
    upload_timestamp: str
    processing_status: str

class DocumentProcessor:
    """Advanced document processor with multimodal capabilities."""
    
    def __init__(self):
        self.upload_dir = Path("data/uploads")
        self.chunks_dir = self.upload_dir / "chunks"
        self.embeddings_dir = self.upload_dir / "embeddings"
        self.images_dir = self.upload_dir / "images"
        
        # Create directories
        for dir_path in [self.upload_dir, self.chunks_dir, self.embeddings_dir, self.images_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.chunk_size = 1000  # characters per chunk
        self.chunk_overlap = 200  # overlap between chunks
        
    def _generate_file_hash(self, file_path: str) -> str:
        """Generate hash for file identification."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]', '', text)
        return text.strip()
    
    def _create_chunks(self, text: str, page_number: int, chunk_type: str = 'text') -> List[DocumentChunk]:
        """Create overlapping chunks from text content."""
        chunks = []
        text = self._clean_text(text)
        
        if len(text) <= self.chunk_size:
            chunk = DocumentChunk(
                chunk_id=f"page_{page_number}_chunk_0",
                page_number=page_number,
                content=text,
                chunk_type=chunk_type,
                chunk_index=0,
                start_char=0,
                end_char=len(text)
            )
            chunks.append(chunk)
        else:
            start = 0
            chunk_index = 0
            
            while start < len(text):
                end = start + self.chunk_size
                
                # Try to break at sentence boundaries
                if end < len(text):
                    # Look for sentence endings
                    for i in range(end, max(start, end - 100), -1):
                        if text[i] in '.!?':
                            end = i + 1
                            break
                
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunk = DocumentChunk(
                        chunk_id=f"page_{page_number}_chunk_{chunk_index}",
                        page_number=page_number,
                        content=chunk_text,
                        chunk_type=chunk_type,
                        chunk_index=chunk_index,
                        start_char=start,
                        end_char=end
                    )
                    chunks.append(chunk)
                
                start = end - self.chunk_overlap
                chunk_index += 1
                
                if start >= len(text):
                    break
        
        return chunks
    
    def _extract_images_from_page(self, page, page_number: int) -> List[DocumentChunk]:
        """Extract images from a PDF page."""
        image_chunks = []
        
        try:
            # Get image list from page
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        
                        # Create image chunk
                        chunk = DocumentChunk(
                            chunk_id=f"page_{page_number}_image_{img_index}",
                            page_number=page_number,
                            content=f"Image {img_index + 1} from page {page_number}",
                            chunk_type='image',
                            image_data=img_data,
                            image_format='png',
                            chunk_index=img_index
                        )
                        image_chunks.append(chunk)
                    
                    pix = None  # Free memory
                    
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_number}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to extract images from page {page_number}: {e}")
        
        return image_chunks
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document and extract text chunks, images, and metadata.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with processing results
        """
        try:
            file_hash = self._generate_file_hash(file_path)
            
            # Check if already processed
            metadata_file = self.chunks_dir / f"{file_hash}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                return {
                    "success": True,
                    "message": "Document already processed",
                    "file_hash": file_hash,
                    "metadata": metadata
                }
            
            # Open PDF
            doc = fitz.open(file_path)
            page_count = len(doc)
            
            all_chunks = []
            text_chunks_count = 0
            image_chunks_count = 0
            
            # Process each page
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                # Extract text
                text_content = page.get_text()
                if text_content.strip():
                    text_chunks = self._create_chunks(text_content, page_num + 1, 'text')
                    all_chunks.extend(text_chunks)
                    text_chunks_count += len(text_chunks)
                
                # Extract images
                image_chunks = self._extract_images_from_page(page, page_num + 1)
                all_chunks.extend(image_chunks)
                image_chunks_count += len(image_chunks)
            
            doc.close()
            
            # Save chunks
            chunks_file = self.chunks_dir / f"{file_hash}_chunks.json"
            chunks_data = []
            
            for chunk in all_chunks:
                chunk_dict = {
                    "chunk_id": chunk.chunk_id,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "chunk_type": chunk.chunk_type,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char
                }
                
                # Save image data separately if present
                if chunk.image_data:
                    image_file = self.images_dir / f"{chunk.chunk_id}.png"
                    with open(image_file, 'wb') as f:
                        f.write(chunk.image_data)
                    chunk_dict["image_file"] = str(image_file)
                
                chunks_data.append(chunk_dict)
            
            with open(chunks_file, 'w') as f:
                json.dump(chunks_data, f, indent=2)
            
            # Create metadata
            metadata = DocumentMetadata(
                file_hash=file_hash,
                filename=Path(file_path).name,
                page_count=page_count,
                total_chunks=len(all_chunks),
                text_chunks=text_chunks_count,
                image_chunks=image_chunks_count,
                upload_timestamp=str(Path(file_path).stat().st_mtime),
                processing_status="completed"
            )
            
            # Save metadata
            metadata_dict = {
                "file_hash": metadata.file_hash,
                "filename": metadata.filename,
                "page_count": metadata.page_count,
                "total_chunks": metadata.total_chunks,
                "text_chunks": metadata.text_chunks,
                "image_chunks": metadata.image_chunks,
                "upload_timestamp": metadata.upload_timestamp,
                "processing_status": metadata.processing_status
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            
            return {
                "success": True,
                "message": f"Document processed successfully: {page_count} pages, {len(all_chunks)} chunks",
                "file_hash": file_hash,
                "metadata": metadata_dict,
                "chunks_summary": {
                    "total_chunks": len(all_chunks),
                    "text_chunks": text_chunks_count,
                    "image_chunks": image_chunks_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process document"
            }
    
    def get_document_chunks(self, file_hash: str) -> Dict[str, Any]:
        """
        Retrieve chunks for a specific document.
        
        Args:
            file_hash: Hash of the document
            
        Returns:
            Dictionary with document chunks
        """
        try:
            chunks_file = self.chunks_dir / f"{file_hash}_chunks.json"
            metadata_file = self.chunks_dir / f"{file_hash}_metadata.json"
            
            if not chunks_file.exists() or not metadata_file.exists():
                return {
                    "success": False,
                    "error": "Document not found or not processed",
                    "message": "Document has not been processed yet"
                }
            
            # Load chunks
            with open(chunks_file, 'r') as f:
                chunks_data = json.load(f)
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            return {
                "success": True,
                "file_hash": file_hash,
                "metadata": metadata,
                "chunks": chunks_data,
                "total_chunks": len(chunks_data)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve document chunks"
            }
    
    def search_chunks(self, query: str, file_hash: str = None, chunk_type: str = None) -> Dict[str, Any]:
        """
        Search for relevant chunks based on query.
        
        Args:
            query: Search query
            file_hash: Specific document to search (optional)
            chunk_type: Type of chunks to search ('text', 'image', or None for all)
            
        Returns:
            Dictionary with search results
        """
        try:
            results = []
            
            # Determine which files to search
            if file_hash:
                files_to_search = [file_hash]
            else:
                # Get all processed documents
                metadata_files = list(self.chunks_dir.glob("*_metadata.json"))
                files_to_search = [f.stem.replace("_metadata", "") for f in metadata_files]
            
            for f_hash in files_to_search:
                chunks_result = self.get_document_chunks(f_hash)
                if not chunks_result["success"]:
                    continue
                
                chunks = chunks_result["chunks"]
                metadata = chunks_result["metadata"]
                
                # Filter by chunk type if specified
                if chunk_type:
                    chunks = [c for c in chunks if c["chunk_type"] == chunk_type]
                
                # Simple text search (will be enhanced with vector search)
                query_lower = query.lower()
                matches = []
                
                for chunk in chunks:
                    if chunk["chunk_type"] == "text":
                        content_lower = chunk["content"].lower()
                        if query_lower in content_lower:
                            # Calculate relevance score (simple)
                            relevance_score = content_lower.count(query_lower) / len(content_lower)
                            
                            matches.append({
                                "chunk_id": chunk["chunk_id"],
                                "page_number": chunk["page_number"],
                                "content": chunk["content"],
                                "chunk_type": chunk["chunk_type"],
                                "relevance_score": relevance_score,
                                "start_char": chunk["start_char"],
                                "end_char": chunk["end_char"]
                            })
                
                # Sort by relevance score
                matches.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                if matches:
                    results.append({
                        "file_hash": f_hash,
                        "filename": metadata["filename"],
                        "matches": matches[:10],  # Limit results
                        "total_matches": len(matches)
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_documents": len(results),
                "total_matches": sum(len(r["matches"]) for r in results)
            }
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search chunks"
            }

# Initialize document processor
document_processor = DocumentProcessor()
