"""
Literature Review Tools for Docugent.
Handles PDF upload, text extraction, and Q&A functionality for research papers.
"""

import os
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import PyPDF2
import fitz  # PyMuPDF
from google.adk.tools import FunctionTool
import hashlib
import json

from app.config.settings import settings
from app.config.logger import Logger

logger = Logger.get_logger(__name__)

class LiteratureReviewTools:
    """Tools for literature review and PDF analysis."""
    
    def __init__(self):
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.metadata_file = self.upload_dir / "pdf_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load existing PDF metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save PDF metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _generate_file_hash(self, file_path: str) -> str:
        """Generate hash for file identification."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def extract_text_from_pdf(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Extract text content from uploaded PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Generate file hash for identification
            file_hash = self._generate_file_hash(file_path)
            
            # Check if already processed
            if file_hash in self.metadata:
                return {
                    "success": True,
                    "message": "PDF already processed",
                    "file_hash": file_hash,
                    "metadata": self.metadata[file_hash]
                }
            
            # Extract text using PyMuPDF (more reliable)
            doc = fitz.open(file_path)
            text_content = ""
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text_content += page.get_text()
            
            doc.close()
            
            # Extract basic metadata
            pdf_info = {
                "file_hash": file_hash,
                "page_count": page_count,
                "text_length": len(text_content),
                "filename": Path(file_path).name,
                "upload_timestamp": str(Path(file_path).stat().st_mtime)
            }
            
            # Save extracted text
            text_file = self.upload_dir / f"{file_hash}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Save metadata
            self.metadata[file_hash] = pdf_info
            self._save_metadata()
            
            return {
                "success": True,
                "message": f"Successfully extracted text from {page_count} pages",
                "file_hash": file_hash,
                "metadata": pdf_info,
                "preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to extract text from PDF"
            }
    
    def search_pdf_content(self, query: str, file_hash: str = None, **kwargs) -> Dict[str, Any]:
        """
        Search for specific content within uploaded PDFs.
        
        Args:
            query: Search query
            file_hash: Specific PDF to search (optional)
            
        Returns:
            Dictionary with search results
        """
        try:
            results = []
            
            # Determine which files to search
            files_to_search = [file_hash] if file_hash else list(self.metadata.keys())
            
            for f_hash in files_to_search:
                if f_hash not in self.metadata:
                    continue
                
                text_file = self.upload_dir / f"{f_hash}.txt"
                if not text_file.exists():
                    continue
                
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple text search (can be enhanced with more sophisticated search)
                lines = content.split('\n')
                matches = []
                
                for i, line in enumerate(lines):
                    if query.lower() in line.lower():
                        matches.append({
                            "line_number": i + 1,
                            "content": line.strip(),
                            "context": lines[max(0, i-2):min(len(lines), i+3)]
                        })
                
                if matches:
                    results.append({
                        "file_hash": f_hash,
                        "filename": self.metadata[f_hash]["filename"],
                        "matches": matches[:10]  # Limit results
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_matches": sum(len(r["matches"]) for r in results)
            }
            
        except Exception as e:
            logger.error(f"Error searching PDF content: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search PDF content"
            }
    
    def get_pdf_summary(self, file_hash: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a summary of the PDF content.
        
        Args:
            file_hash: Hash of the PDF file
            
        Returns:
            Dictionary with PDF summary
        """
        try:
            if file_hash not in self.metadata:
                return {
                    "success": False,
                    "error": "PDF not found",
                    "message": "Specified PDF has not been uploaded"
                }
            
            text_file = self.upload_dir / f"{file_hash}.txt"
            if not text_file.exists():
                return {
                    "success": False,
                    "error": "Text content not found",
                    "message": "PDF text content is missing"
                }
            
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic summary (can be enhanced with AI)
            words = content.split()
            sentences = content.split('.')
            
            summary = {
                "filename": self.metadata[file_hash]["filename"],
                "page_count": self.metadata[file_hash]["page_count"],
                "word_count": len(words),
                "sentence_count": len(sentences),
                "estimated_reading_time": len(words) // 200,  # ~200 words per minute
                "first_paragraph": content[:500] + "..." if len(content) > 500 else content
            }
            
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error generating PDF summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate PDF summary"
            }
    
    def list_uploaded_pdfs(self, **kwargs) -> Dict[str, Any]:
        """
        List all uploaded PDFs with their metadata.
        
        Returns:
            Dictionary with list of uploaded PDFs
        """
        try:
            pdfs = []
            for file_hash, metadata in self.metadata.items():
                pdfs.append({
                    "file_hash": file_hash,
                    "filename": metadata["filename"],
                    "page_count": metadata["page_count"],
                    "upload_timestamp": metadata["upload_timestamp"],
                    "text_length": metadata["text_length"]
                })
            
            return {
                "success": True,
                "pdfs": pdfs,
                "total_count": len(pdfs)
            }
            
        except Exception as e:
            logger.error(f"Error listing PDFs: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list uploaded PDFs"
            }

# Initialize tools
literature_tools = LiteratureReviewTools()

def get_literature_review_tools() -> List[FunctionTool]:
    """Get literature review tools for the AI agent."""
    return [
        FunctionTool(
            name="extract_text_from_pdf",
            description="Extract text content from uploaded PDF files for analysis",
            func=literature_tools.extract_text_from_pdf
        ),
        FunctionTool(
            name="search_pdf_content",
            description="Search for specific content within uploaded PDFs",
            func=literature_tools.search_pdf_content
        ),
        FunctionTool(
            name="get_pdf_summary",
            description="Generate a summary of uploaded PDF content",
            func=literature_tools.get_pdf_summary
        ),
        FunctionTool(
            name="list_uploaded_pdfs",
            description="List all uploaded PDFs with their metadata",
            func=literature_tools.list_uploaded_pdfs
        )
    ]
