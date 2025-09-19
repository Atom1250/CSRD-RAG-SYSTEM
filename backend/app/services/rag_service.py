"""
RAG (Retrieval-Augmented Generation) service for AI-powered question answering with caching
"""
import logging
import time
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod
from enum import Enum
import json
import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.schemas import SearchResult, RAGResponseCreate, RAGResponseResponse
from app.services.search_service import SearchService
from app.services.cache_service import cache_service
from app.services.performance_service import async_performance_timer
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIModelType(str, Enum):
    """Available AI model types"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35 = "openai_gpt35"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    LOCAL_LLAMA = "local_llama"


class AIModelProvider(ABC):
    """Abstract base class for AI model providers"""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: str, 
        max_tokens: int = 1000,
        temperature: float = 0.1
    ) -> Tuple[str, float]:
        """
        Generate response using the AI model
        
        Args:
            prompt: The user's question/prompt
            context: Retrieved context from documents
            max_tokens: Maximum tokens in response
            temperature: Model temperature for creativity
            
        Returns:
            Tuple of (response_text, confidence_score)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available and configured"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        pass


class OpenAIProvider(AIModelProvider):
    """OpenAI GPT model provider"""
    
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.api_key = settings.openai_api_key
        self.client = None
        
        if self.api_key:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI library not installed. Install with: pip install openai")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    
    async def generate_response(
        self, 
        prompt: str, 
        context: str, 
        max_tokens: int = 1000,
        temperature: float = 0.1
    ) -> Tuple[str, float]:
        """Generate response using OpenAI GPT"""
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            # Create the full prompt with context
            full_prompt = self._create_sustainability_prompt(prompt, context)
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in sustainability reporting and CSRD/ESRS compliance. Provide accurate, detailed answers based on the provided context."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9
            )
            
            response_text = response.choices[0].message.content
            
            # Calculate confidence based on response quality indicators
            confidence = self._calculate_confidence(response_text, context)
            
            return response_text, confidence
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return self.client is not None and self.api_key is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information"""
        return {
            "provider": "OpenAI",
            "model": self.model_name,
            "available": self.is_available(),
            "capabilities": ["text_generation", "reasoning", "analysis"],
            "max_tokens": 4096 if "gpt-4" in self.model_name else 2048
        }
    
    def _create_sustainability_prompt(self, question: str, context: str) -> str:
        """Create a specialized prompt for sustainability reporting"""
        return f"""
Based on the following regulatory documents and sustainability reporting context, please answer the question accurately and comprehensively.

CONTEXT FROM REGULATORY DOCUMENTS:
{context}

QUESTION:
{question}

INSTRUCTIONS:
1. Base your answer primarily on the provided context
2. If the context doesn't contain sufficient information, clearly state this
3. Include specific references to regulatory standards (CSRD, ESRS, UK SRD) when relevant
4. Provide practical guidance for compliance when applicable
5. Structure your response clearly with headings if appropriate
6. Cite specific sections or requirements from the context when possible

ANSWER:
"""
    
    def _calculate_confidence(self, response: str, context: str) -> float:
        """Calculate confidence score based on response quality"""
        try:
            confidence = 0.5  # Base confidence
            
            # Check if response acknowledges context
            if "based on" in response.lower() or "according to" in response.lower():
                confidence += 0.2
            
            # Check for specific regulatory references
            regulatory_terms = ["csrd", "esrs", "srd", "regulation", "directive", "standard"]
            if any(term in response.lower() for term in regulatory_terms):
                confidence += 0.15
            
            # Check response length (not too short, not too long)
            if 100 <= len(response) <= 2000:
                confidence += 0.1
            
            # Check for structured response
            if any(marker in response for marker in ["1.", "2.", "•", "-", "##"]):
                confidence += 0.05
            
            return min(1.0, confidence)
            
        except Exception:
            return 0.5


class AnthropicProvider(AIModelProvider):
    """Anthropic Claude model provider"""
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        self.model_name = model_name
        self.api_key = settings.anthropic_api_key
        self.client = None
        
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("Anthropic library not installed. Install with: pip install anthropic")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {str(e)}")
    
    async def generate_response(
        self, 
        prompt: str, 
        context: str, 
        max_tokens: int = 1000,
        temperature: float = 0.1
    ) -> Tuple[str, float]:
        """Generate response using Anthropic Claude"""
        try:
            if not self.client:
                raise ValueError("Anthropic client not initialized")
            
            # Create the full prompt with context
            full_prompt = self._create_sustainability_prompt(prompt, context)
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            
            # Calculate confidence based on response quality indicators
            confidence = self._calculate_confidence(response_text, context)
            
            return response_text, confidence
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """Check if Anthropic is available"""
        return self.client is not None and self.api_key is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model information"""
        return {
            "provider": "Anthropic",
            "model": self.model_name,
            "available": self.is_available(),
            "capabilities": ["text_generation", "reasoning", "analysis", "long_context"],
            "max_tokens": 4096
        }
    
    def _create_sustainability_prompt(self, question: str, context: str) -> str:
        """Create a specialized prompt for sustainability reporting"""
        return f"""
You are an expert in sustainability reporting, CSRD compliance, and ESRS standards. Please answer the following question based on the provided regulatory context.

<context>
{context}
</context>

<question>
{question}
</question>

Please provide a comprehensive answer that:
1. Is based primarily on the provided context
2. References specific regulatory requirements when applicable
3. Provides practical compliance guidance
4. Clearly indicates if information is insufficient in the context
5. Uses proper sustainability reporting terminology

Answer:
"""
    
    def _calculate_confidence(self, response: str, context: str) -> float:
        """Calculate confidence score based on response quality"""
        try:
            confidence = 0.5  # Base confidence
            
            # Check if response acknowledges context
            if "based on" in response.lower() or "according to" in response.lower():
                confidence += 0.2
            
            # Check for specific regulatory references
            regulatory_terms = ["csrd", "esrs", "srd", "regulation", "directive", "standard"]
            if any(term in response.lower() for term in regulatory_terms):
                confidence += 0.15
            
            # Check response length (not too short, not too long)
            if 100 <= len(response) <= 2000:
                confidence += 0.1
            
            # Check for structured response
            if any(marker in response for marker in ["1.", "2.", "•", "-"]):
                confidence += 0.05
            
            return min(1.0, confidence)
            
        except Exception:
            return 0.5


class LocalLlamaProvider(AIModelProvider):
    """Local Llama model provider (placeholder for future implementation)"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        # Note: This is a placeholder - actual implementation would load a local model
        logger.info("Local Llama provider initialized (placeholder implementation)")
    
    async def generate_response(
        self, 
        prompt: str, 
        context: str, 
        max_tokens: int = 1000,
        temperature: float = 0.1
    ) -> Tuple[str, float]:
        """Generate response using local Llama model"""
        # Placeholder implementation
        response = f"This is a placeholder response from local Llama model for the question: {prompt[:100]}..."
        confidence = 0.3  # Lower confidence for placeholder
        return response, confidence
    
    def is_available(self) -> bool:
        """Check if local model is available"""
        return False  # Placeholder - not actually available
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get local model information"""
        return {
            "provider": "Local Llama",
            "model": "llama-placeholder",
            "available": self.is_available(),
            "capabilities": ["text_generation"],
            "max_tokens": 2048
        }


class RAGService:
    """Service for Retrieval-Augmented Generation operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.search_service = SearchService(db)
        self.model_providers = self._initialize_model_providers()
        self.default_model = AIModelType.OPENAI_GPT35
        
    def _initialize_model_providers(self) -> Dict[AIModelType, AIModelProvider]:
        """Initialize all available model providers"""
        providers = {}
        
        # Initialize OpenAI providers
        try:
            providers[AIModelType.OPENAI_GPT4] = OpenAIProvider("gpt-4")
            providers[AIModelType.OPENAI_GPT35] = OpenAIProvider("gpt-3.5-turbo")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI providers: {str(e)}")
        
        # Initialize Anthropic provider
        try:
            providers[AIModelType.ANTHROPIC_CLAUDE] = AnthropicProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic provider: {str(e)}")
        
        # Initialize local Llama provider
        try:
            providers[AIModelType.LOCAL_LLAMA] = LocalLlamaProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Local Llama provider: {str(e)}")
        
        logger.info(f"Initialized {len(providers)} model providers")
        return providers
    
    @async_performance_timer("rag_response_generation")
    async def generate_rag_response(
        self,
        question: str,
        model_type: Optional[AIModelType] = None,
        max_context_chunks: int = 10,
        min_relevance_score: float = 0.3,
        max_tokens: int = 1000,
        temperature: float = 0.1
    ) -> RAGResponseResponse:
        """
        Generate a RAG response for a given question with caching
        
        Args:
            question: The user's question
            model_type: AI model to use (defaults to configured default)
            max_context_chunks: Maximum number of context chunks to retrieve
            min_relevance_score: Minimum relevance score for context chunks
            max_tokens: Maximum tokens in response
            temperature: Model temperature for creativity
            
        Returns:
            RAGResponseResponse: Complete RAG response with metadata
        """
        start_time = time.time()
        
        try:
            # Use default model if none specified
            if model_type is None:
                model_type = self.default_model
            
            # Create cache key from question and parameters
            cache_params = {
                "model_type": model_type.value,
                "max_context_chunks": max_context_chunks,
                "min_relevance_score": min_relevance_score,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Check cache first
            context_hash = hashlib.md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()
            cached_response = cache_service.get_cached_rag_response(question, model_type.value, context_hash)
            if cached_response:
                logger.info(f"Retrieved cached RAG response for question: '{question[:50]}...'")
                return RAGResponseResponse(**cached_response)
            
            # Get the model provider
            provider = self.model_providers.get(model_type)
            if not provider or not provider.is_available():
                # Fallback to first available model
                available_providers = [
                    (mt, p) for mt, p in self.model_providers.items() 
                    if p.is_available()
                ]
                if not available_providers:
                    raise ValueError("No AI models are available")
                
                model_type, provider = available_providers[0]
                logger.info(f"Falling back to {model_type.value} model")
            
            # Step 1: Retrieve relevant context using search service
            logger.info(f"Retrieving context for question: '{question[:100]}...'")
            search_results = await self.search_service.search_documents(
                query=question,
                top_k=max_context_chunks,
                min_relevance_score=min_relevance_score
            )
            
            if not search_results:
                return self._create_no_context_response(question, model_type.value)
            
            # Step 2: Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Step 3: Generate response using selected AI model
            logger.info(f"Generating response using {model_type.value}")
            response_text, confidence_score = await provider.generate_response(
                prompt=question,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Step 4: Create response with source citations
            source_chunks = [result.chunk_id for result in search_results]
            
            generation_time = time.time() - start_time
            logger.info(f"RAG response generated in {generation_time:.2f}s with confidence {confidence_score:.2f}")
            
            response = RAGResponseResponse(
                id=f"rag_{int(time.time())}_{hash(question) % 10000}",
                query=question,
                response_text=response_text,
                model_used=model_type.value,
                confidence_score=confidence_score,
                source_chunks=source_chunks,
                generation_timestamp=datetime.utcnow()
            )
            
            # Cache the response
            cache_service.cache_rag_response(question, model_type.value, context_hash, response.dict())
            
            return response
            
        except Exception as e:
            logger.error(f"RAG response generation failed: {str(e)}")
            return self._create_error_response(question, str(e))
    
    def _prepare_context(self, search_results: List[SearchResult]) -> str:
        """Prepare context string from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            # Add document source information
            source_info = f"[Source {i}: {result.document_filename}]"
            
            # Add schema elements if available
            schema_info = ""
            if result.schema_elements:
                schema_info = f" (Schema: {', '.join(result.schema_elements)})"
            
            # Add relevance score
            relevance_info = f" [Relevance: {result.relevance_score:.2f}]"
            
            # Combine all information
            context_part = f"{source_info}{schema_info}{relevance_info}\n{result.content}\n"
            context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)
    
    def _create_no_context_response(self, question: str, model_used: str) -> RAGResponseResponse:
        """Create response when no relevant context is found"""
        return RAGResponseResponse(
            id=f"rag_no_context_{int(time.time())}",
            query=question,
            response_text="I couldn't find relevant information in the document repository to answer your question. Please try rephrasing your question or ensure that relevant documents have been uploaded and processed.",
            model_used=model_used,
            confidence_score=0.0,
            source_chunks=[],
            generation_timestamp=datetime.utcnow()
        )
    
    def _create_error_response(self, question: str, error_message: str) -> RAGResponseResponse:
        """Create response when an error occurs"""
        return RAGResponseResponse(
            id=f"rag_error_{int(time.time())}",
            query=question,
            response_text=f"An error occurred while processing your question: {error_message}",
            model_used="error",
            confidence_score=0.0,
            source_chunks=[],
            generation_timestamp=datetime.utcnow()
        )
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available AI models with their information"""
        models = []
        
        for model_type, provider in self.model_providers.items():
            model_info = provider.get_model_info()
            model_info["type"] = model_type.value
            models.append(model_info)
        
        return models
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all model providers"""
        status = {}
        
        for model_type, provider in self.model_providers.items():
            status[model_type.value] = {
                "available": provider.is_available(),
                "info": provider.get_model_info()
            }
        
        return status
    
    async def validate_response_quality(
        self,
        response: RAGResponseResponse,
        expected_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate the quality of a RAG response
        
        Args:
            response: The RAG response to validate
            expected_topics: Optional list of topics that should be covered
            
        Returns:
            Dict containing quality metrics
        """
        try:
            quality_metrics = {
                "confidence_score": response.confidence_score,
                "has_sources": len(response.source_chunks) > 0,
                "source_count": len(response.source_chunks),
                "response_length": len(response.response_text),
                "contains_regulatory_terms": False,
                "topic_coverage": 0.0,
                "overall_quality": "unknown"
            }
            
            # Check for regulatory terms
            regulatory_terms = ["csrd", "esrs", "srd", "sustainability", "reporting", "compliance"]
            response_lower = response.response_text.lower()
            quality_metrics["contains_regulatory_terms"] = any(
                term in response_lower for term in regulatory_terms
            )
            
            # Check topic coverage if expected topics provided
            if expected_topics:
                covered_topics = sum(
                    1 for topic in expected_topics 
                    if topic.lower() in response_lower
                )
                quality_metrics["topic_coverage"] = covered_topics / len(expected_topics)
            
            # Calculate overall quality score
            quality_score = 0.0
            
            # Confidence score weight (40%)
            quality_score += response.confidence_score * 0.4
            
            # Source availability weight (20%)
            if quality_metrics["has_sources"]:
                quality_score += 0.2
            
            # Response length weight (20%)
            if 50 <= quality_metrics["response_length"] <= 2000:
                quality_score += 0.2
            
            # Regulatory terms weight (10%)
            if quality_metrics["contains_regulatory_terms"]:
                quality_score += 0.1
            
            # Topic coverage weight (10%)
            quality_score += quality_metrics["topic_coverage"] * 0.1
            
            # Determine overall quality rating
            if quality_score >= 0.8:
                quality_metrics["overall_quality"] = "excellent"
            elif quality_score >= 0.6:
                quality_metrics["overall_quality"] = "good"
            elif quality_score >= 0.4:
                quality_metrics["overall_quality"] = "fair"
            else:
                quality_metrics["overall_quality"] = "poor"
            
            quality_metrics["quality_score"] = round(quality_score, 2)
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Failed to validate response quality: {str(e)}")
            return {"error": str(e)}
    
    async def batch_generate_responses(
        self,
        questions: List[str],
        model_type: Optional[AIModelType] = None,
        max_concurrent: int = 3
    ) -> List[RAGResponseResponse]:
        """
        Generate RAG responses for multiple questions concurrently
        
        Args:
            questions: List of questions to process
            model_type: AI model to use for all questions
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List of RAG responses
        """
        try:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def generate_single_response(question: str) -> RAGResponseResponse:
                async with semaphore:
                    return await self.generate_rag_response(question, model_type)
            
            # Generate all responses concurrently
            tasks = [generate_single_response(q) for q in questions]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            final_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    error_response = self._create_error_response(
                        questions[i], 
                        str(response)
                    )
                    final_responses.append(error_response)
                else:
                    final_responses.append(response)
            
            return final_responses
            
        except Exception as e:
            logger.error(f"Batch response generation failed: {str(e)}")
            return [self._create_error_response(q, str(e)) for q in questions]


# Global RAG service factory
def get_rag_service(db: Session) -> RAGService:
    """Factory function to create RAGService instance"""
    return RAGService(db)