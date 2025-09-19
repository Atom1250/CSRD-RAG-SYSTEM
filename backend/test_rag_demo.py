#!/usr/bin/env python3
"""
Demo script to test RAG service functionality
"""
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService, AIModelType
from app.models.schemas import SearchResult
from app.services.search_service import SearchService


async def demo_rag_service():
    """Demonstrate RAG service functionality"""
    print("🤖 RAG Service Demo")
    print("=" * 50)
    
    # Mock database session
    mock_db = Mock()
    
    # Create mock search service with sample data
    mock_search_service = Mock(spec=SearchService)
    
    def mock_search_documents(query, **kwargs):
        """Mock search function that returns relevant results based on query"""
        if "csrd" in query.lower():
            return [
                SearchResult(
                    chunk_id="csrd_chunk_1",
                    document_id="csrd_doc_1",
                    content="The Corporate Sustainability Reporting Directive (CSRD) requires large companies to report on sustainability matters. Companies must disclose information about their environmental, social and governance impacts according to European Sustainability Reporting Standards (ESRS).",
                    relevance_score=0.92,
                    document_filename="csrd_directive_2022.pdf",
                    schema_elements=["CSRD-1", "CSRD-2"]
                ),
                SearchResult(
                    chunk_id="csrd_chunk_2",
                    document_id="csrd_doc_1",
                    content="CSRD applies to companies with more than 500 employees or €40 million in net turnover. The directive aims to increase transparency and accountability in corporate sustainability reporting.",
                    relevance_score=0.88,
                    document_filename="csrd_directive_2022.pdf",
                    schema_elements=["CSRD-3"]
                )
            ]
        elif "esrs" in query.lower():
            return [
                SearchResult(
                    chunk_id="esrs_chunk_1",
                    document_id="esrs_doc_1",
                    content="European Sustainability Reporting Standards (ESRS) provide detailed requirements for sustainability reporting under CSRD. ESRS covers environmental standards (E1-E5), social standards (S1-S4), and governance standards (G1).",
                    relevance_score=0.90,
                    document_filename="esrs_standards_2023.pdf",
                    schema_elements=["ESRS-E1", "ESRS-S1", "ESRS-G1"]
                )
            ]
        else:
            return []
    
    mock_search_service.search_documents = AsyncMock(side_effect=mock_search_documents)
    
    # Create RAG service
    rag_service = RAGService(mock_db)
    rag_service.search_service = mock_search_service
    
    # Mock AI provider for demonstration
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    
    async def mock_generate_response(prompt, context, **kwargs):
        """Mock AI response generation"""
        if "CSRD" in context:
            response = f"""Based on the regulatory documents provided, I can answer your question about CSRD:

The Corporate Sustainability Reporting Directive (CSRD) is a comprehensive EU regulation that requires large companies to report on sustainability matters. Here are the key points:

**Scope and Application:**
- Applies to companies with more than 500 employees or €40 million in net turnover
- Requires disclosure of environmental, social, and governance (ESG) impacts

**Reporting Standards:**
- Companies must follow the European Sustainability Reporting Standards (ESRS)
- ESRS covers environmental standards (E1-E5), social standards (S1-S4), and governance standards (G1)

**Objectives:**
- Increase transparency in corporate sustainability reporting
- Enhance accountability for sustainability impacts
- Standardize sustainability reporting across the EU

This information is based on the CSRD directive documentation and ESRS standards provided in the context."""
            return response, 0.88
        elif "ESRS" in context:
            response = f"""Based on the regulatory documentation, here's what you need to know about ESRS:

The European Sustainability Reporting Standards (ESRS) are comprehensive standards that provide detailed requirements for sustainability reporting under the Corporate Sustainability Reporting Directive (CSRD).

**Structure:**
- Environmental Standards (E1-E5): Cover climate change, pollution, water, biodiversity, and circular economy
- Social Standards (S1-S4): Address workforce, value chain workers, affected communities, and consumers  
- Governance Standards (G1): Focus on business conduct and governance practices

**Purpose:**
- Ensure consistent and comparable sustainability reporting across EU companies
- Provide detailed guidance for CSRD compliance
- Establish standardized metrics and disclosure requirements

This information is derived from the ESRS standards documentation provided in the context."""
            return response, 0.85
        else:
            return "I don't have sufficient information to answer this question based on the available documents.", 0.3
    
    mock_provider.generate_response = mock_generate_response
    rag_service.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
    
    # Test questions
    test_questions = [
        "What is CSRD and what are its key requirements?",
        "What are the ESRS standards and how are they structured?",
        "How do CSRD and ESRS work together?"
    ]
    
    print("Testing RAG Service with sample questions:\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"📝 Question {i}: {question}")
        print("-" * 60)
        
        try:
            # Generate RAG response
            response = await rag_service.generate_rag_response(
                question=question,
                model_type=AIModelType.OPENAI_GPT35,
                max_context_chunks=5,
                min_relevance_score=0.3
            )
            
            print(f"🎯 Model Used: {response.model_used}")
            print(f"📊 Confidence Score: {response.confidence_score:.2f}")
            print(f"📚 Source Chunks: {len(response.source_chunks)}")
            print(f"💬 Response:\n{response.response_text}")
            
            if response.source_chunks:
                print(f"\n📖 Sources: {', '.join(response.source_chunks)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 80 + "\n")
    
    # Test model availability
    print("🔧 Available Models:")
    try:
        models = rag_service.get_available_models()
        for model in models:
            status = "✅ Available" if model.get("available", False) else "❌ Unavailable"
            provider = model.get("provider", "Unknown")
            model_name = model.get("model", "Unknown")
            print(f"  - {provider} {model_name}: {status}")
    except Exception as e:
        print(f"  - Mock OpenAI GPT-3.5: ✅ Available (Demo Mode)")
        print(f"  - Note: Full model info unavailable in demo mode")
    
    print("\n🎉 RAG Service Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_rag_service())