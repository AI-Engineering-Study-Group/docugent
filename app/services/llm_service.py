"""
LLM Service for generating contextual answers based on document chunks.
Handles answer generation using various LLM models.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
import google.generativeai as genai

from app.config.logger import Logger

logger = Logger.get_logger(__name__)

@dataclass
class AnswerContext:
    """Context information for answer generation."""
    question: str
    relevant_chunks: List[Dict[str, Any]]
    document_metadata: Dict[str, Any]
    chunk_count: int
    total_similarity: float

@dataclass
class GeneratedAnswer:
    """Generated answer with metadata."""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    reasoning: str
    model_used: str

class LLMService:
    """Service for generating contextual answers using LLM models."""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        self.use_gemini = True if self.gemini_api_key else False
        
        if self.use_gemini:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("LLM service initialized with Google Gemini API")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini: {e}")
                self.use_gemini = False
        else:
            logger.warning("No GEMINI_API_KEY found, using fallback answer generation")
            logger.info("To use Gemini API, set GEMINI_API_KEY environment variable")
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            if not self.model:
                return ""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return ""
    
    def _create_context_prompt(self, context: AnswerContext) -> str:
        """
        Create a prompt for the LLM based on the context.
        
        Args:
            context: Answer context with question and relevant chunks
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = f"""You are a helpful AI assistant that answers questions based on provided document content. 
Please answer the following question using only the information provided in the document chunks below.

Question: {context.question}

Document Information:
- Document: {context.document_metadata.get('filename', 'Unknown')}
- Total pages: {context.document_metadata.get('page_count', 0)}
- Relevant chunks found: {context.chunk_count}

Relevant Document Content:
"""
        
        # Add relevant chunks with page numbers
        for i, chunk in enumerate(context.relevant_chunks, 1):
            chunk_content = chunk.get('content', '')
            page_number = chunk.get('page_number', 'Unknown')
            similarity = chunk.get('similarity', 0.0)
            
            prompt += f"""
Chunk {i} (Page {page_number}, Relevance: {similarity:.2f}):
{chunk_content}
"""
        
        prompt += f"""

Instructions:
1. Answer the question based ONLY on the provided document content
2. If the information is not available in the provided chunks, say so
3. Include page numbers when referencing specific information
4. Be concise but comprehensive
5. If there are images mentioned, describe what they likely contain based on the text context

Answer:"""
        
        return prompt
    
    def _generate_fallback_answer(self, context: AnswerContext) -> GeneratedAnswer:
        """
        Generate a fallback answer when LLM is not available.
        
        Args:
            context: Answer context
            
        Returns:
            Generated answer
        """
        question = context.question.lower()
        chunks = context.relevant_chunks
        
        if not chunks:
            return GeneratedAnswer(
                answer="I don't have enough information from the document to answer this question. Please try rephrasing your question or upload a document that contains relevant information.",
                confidence=0.0,
                sources=[],
                reasoning="No relevant chunks found in the document.",
                model_used="fallback_model"
            )
        
        # Simple keyword-based answer generation
        answer_parts = []
        sources = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            page_number = chunk.get('page_number', 'Unknown')
            similarity = chunk.get('similarity', 0.0)
            
            # Check if chunk contains relevant information
            if any(keyword in content.lower() for keyword in question.split()):
                # Extract relevant sentences
                sentences = content.split('.')
                relevant_sentences = []
                
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in question.split()):
                        relevant_sentences.append(sentence.strip())
                
                if relevant_sentences:
                    answer_parts.append(f"On page {page_number}: {' '.join(relevant_sentences)}.")
                    sources.append({
                        'page_number': page_number,
                        'content': content[:200] + "..." if len(content) > 200 else content,
                        'similarity': similarity
                    })
        
        if answer_parts:
            answer = " ".join(answer_parts)
            confidence = min(0.8, sum(chunk.get('similarity', 0) for chunk in chunks) / len(chunks))
        else:
            answer = f"Based on the document content, I found some relevant information but it may not directly answer your question. The document contains {len(chunks)} relevant sections across {len(set(chunk.get('page_number', 0) for chunk in chunks))} pages."
            confidence = 0.3
            sources = [{
                'page_number': chunk.get('page_number', 'Unknown'),
                'content': chunk.get('content', '')[:100] + "...",
                'similarity': chunk.get('similarity', 0)
            } for chunk in chunks[:3]]
        
        return GeneratedAnswer(
            answer=answer,
            confidence=confidence,
            sources=sources,
            reasoning="Generated using keyword matching and content analysis.",
            model_used="fallback_model"
        )
    
    def generate_answer(self, context: AnswerContext) -> GeneratedAnswer:
        """
        Generate a contextual answer using the LLM.
        
        Args:
            context: Answer context with question and relevant chunks
            
        Returns:
            Generated answer with metadata
        """
        try:
            if self.use_gemini:
                # Use Google Gemini API
                prompt = self._create_context_prompt(context)
                answer = self._call_gemini_api(prompt)
                
                if answer and len(answer) > 10:
                    confidence = 0.9  # High confidence for Gemini-generated answers
                else:
                    logger.warning("Generated answer too short, using fallback")
                    return self._generate_fallback_answer(context)
            else:
                # Use fallback method
                return self._generate_fallback_answer(context)
            
            # Create sources list
            sources = []
            for chunk in context.relevant_chunks:
                sources.append({
                    'page_number': chunk.get('page_number', 'Unknown'),
                    'content': chunk.get('content', '')[:200] + "..." if len(chunk.get('content', '')) > 200 else chunk.get('content', ''),
                    'similarity': chunk.get('similarity', 0.0)
                })
            
            return GeneratedAnswer(
                answer=answer,
                confidence=confidence,
                sources=sources,
                reasoning="Generated using Google Gemini API based on relevant document chunks.",
                model_used="gemini-pro"
            )
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            # Return fallback answer
            return self._generate_fallback_answer(context)
    
    def format_answer_for_display(self, answer: GeneratedAnswer) -> Dict[str, Any]:
        """
        Format the generated answer for frontend display.
        
        Args:
            answer: Generated answer
            
        Returns:
            Formatted answer for display
        """
        return {
            "answer": answer.answer,
            "confidence": answer.confidence,
            "sources": answer.sources,
            "reasoning": answer.reasoning,
            "model_used": answer.model_used,
            "source_count": len(answer.sources),
            "has_sources": len(answer.sources) > 0
        }

# Initialize LLM service
llm_service = LLMService()
