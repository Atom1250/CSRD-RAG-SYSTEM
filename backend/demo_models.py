#!/usr/bin/env python3
"""
Demo script to showcase the database models and functionality
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import (
    DatabaseManager, get_db_session,
    Document, TextChunk, SchemaElement, ClientRequirements, RAGResponse,
    DocumentType, SchemaType, ProcessingStatus,
    DocumentCreate, TextChunkCreate, SchemaElementCreate,
    ClientRequirementsCreate, RAGResponseCreate
)


def demo_database_operations():
    """Demonstrate database operations with all models"""
    print("🚀 CSRD RAG System - Database Models Demo")
    print("=" * 50)
    
    # Initialize database
    print("\n1. Initializing database...")
    DatabaseManager.init_db()
    print("✅ Database initialized successfully")
    
    # Check connection
    print("\n2. Checking database connection...")
    if DatabaseManager.check_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return
    
    with get_db_session() as db:
        print("\n3. Creating sample data...")
        
        # Create a document
        document = Document(
            filename="ESRS_E1_Climate_Change.pdf",
            file_path="/data/documents/ESRS_E1_Climate_Change.pdf",
            file_size=2048576,  # 2MB
            document_type=DocumentType.PDF,
            schema_type=SchemaType.EU_ESRS_CSRD,
            processing_status=ProcessingStatus.COMPLETED,
            document_metadata={
                "author": "EFRAG",
                "version": "1.0",
                "language": "en",
                "pages": 45
            }
        )
        db.add(document)
        db.flush()  # Get the ID
        print(f"✅ Created document: {document.filename} (ID: {document.id})")
        
        # Create schema elements
        climate_element = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change-related disclosures including GHG emissions, climate risks, and transition plans",
            requirements=[
                "Disclose Scope 1, 2, and 3 GHG emissions",
                "Report climate-related risks and opportunities",
                "Describe climate transition plan"
            ]
        )
        db.add(climate_element)
        db.flush()
        print(f"✅ Created schema element: {climate_element.element_name} ({climate_element.element_code})")
        
        # Create sub-element
        ghg_element = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1-1",
            element_name="GHG Emissions",
            description="Greenhouse gas emissions disclosure requirements",
            parent_element_id=climate_element.id,
            requirements=[
                "Report absolute GHG emissions in tonnes CO2 equivalent",
                "Provide intensity ratios",
                "Disclose methodology and assumptions"
            ]
        )
        db.add(ghg_element)
        db.flush()
        print(f"✅ Created sub-element: {ghg_element.element_name} ({ghg_element.element_code})")
        
        # Create text chunks
        chunks_data = [
            {
                "content": "Companies shall disclose their gross Scope 1, Scope 2, and Scope 3 GHG emissions in tonnes of CO2 equivalent. The disclosure shall include the methodologies and emission factors used.",
                "index": 0,
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "elements": [climate_element.id, ghg_element.id]
            },
            {
                "content": "Climate-related risks shall be categorized as physical risks (acute and chronic) or transition risks (policy, legal, technology, market, reputation).",
                "index": 1,
                "embedding": [0.2, 0.3, 0.4, 0.5, 0.6],
                "elements": [climate_element.id]
            },
            {
                "content": "The undertaking shall disclose its climate transition plan, including targets, actions, and resources allocated to achieve climate neutrality.",
                "index": 2,
                "embedding": [0.3, 0.4, 0.5, 0.6, 0.7],
                "elements": [climate_element.id]
            }
        ]
        
        for chunk_data in chunks_data:
            chunk = TextChunk(
                document_id=document.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["index"],
                embedding_vector=chunk_data["embedding"],
                schema_elements=chunk_data["elements"]
            )
            db.add(chunk)
        
        db.flush()
        print(f"✅ Created {len(chunks_data)} text chunks")
        
        # Create client requirements
        client_requirements = ClientRequirements(
            client_name="Green Tech Corp",
            requirements_text="We need to prepare our first CSRD report focusing on climate change disclosures. Please provide guidance on GHG emissions reporting and climate risk assessment.",
            schema_mappings=[
                {
                    "requirement_id": "req_001",
                    "schema_element_id": climate_element.id,
                    "confidence_score": 0.95
                },
                {
                    "requirement_id": "req_002", 
                    "schema_element_id": ghg_element.id,
                    "confidence_score": 0.88
                }
            ],
            processed_requirements=[
                {
                    "requirement_id": "req_001",
                    "requirement_text": "Climate change disclosures",
                    "mapped_elements": [climate_element.id],
                    "priority": "high"
                },
                {
                    "requirement_id": "req_002",
                    "requirement_text": "GHG emissions reporting",
                    "mapped_elements": [ghg_element.id],
                    "priority": "high"
                }
            ]
        )
        db.add(client_requirements)
        db.flush()
        print(f"✅ Created client requirements for: {client_requirements.client_name}")
        
        # Create RAG response
        rag_response = RAGResponse(
            query="What are the requirements for GHG emissions reporting under ESRS E1?",
            response_text="Under ESRS E1 Climate Change, companies must disclose their gross Scope 1, Scope 2, and Scope 3 GHG emissions in tonnes of CO2 equivalent. The disclosure must include the methodologies and emission factors used. Companies should also provide intensity ratios and disclose their methodology and assumptions for calculating emissions.",
            confidence_score=0.92,
            source_chunks=[chunk.id for chunk in db.query(TextChunk).filter_by(document_id=document.id).all()],
            model_used="gpt-4"
        )
        db.add(rag_response)
        db.flush()
        print(f"✅ Created RAG response (confidence: {rag_response.confidence_score})")
    
    print("\n4. Querying and displaying data...")
    
    with get_db_session() as db:
        # Query documents
        documents = db.query(Document).all()
        print(f"\n📄 Documents ({len(documents)}):")
        for doc in documents:
            print(f"  • {doc.filename} ({doc.document_type.value}) - {doc.processing_status.value}")
            print(f"    Size: {doc.file_size:,} bytes, Chunks: {len(doc.text_chunks)}")
        
        # Query schema elements
        schema_elements = db.query(SchemaElement).all()
        print(f"\n🏗️  Schema Elements ({len(schema_elements)}):")
        for element in schema_elements:
            parent_info = f" (parent: {element.parent.element_code})" if element.parent else ""
            print(f"  • {element.element_code}: {element.element_name}{parent_info}")
            print(f"    Requirements: {len(element.requirements or [])}")
        
        # Query text chunks
        chunks = db.query(TextChunk).all()
        print(f"\n📝 Text Chunks ({len(chunks)}):")
        for chunk in chunks:
            preview = chunk.content[:80] + "..." if len(chunk.content) > 80 else chunk.content
            print(f"  • Chunk {chunk.chunk_index}: {preview}")
            print(f"    Schema elements: {len(chunk.schema_elements or [])}")
        
        # Query client requirements
        requirements = db.query(ClientRequirements).all()
        print(f"\n👥 Client Requirements ({len(requirements)}):")
        for req in requirements:
            print(f"  • {req.client_name}")
            print(f"    Mappings: {len(req.schema_mappings or [])}")
            print(f"    Processed: {len(req.processed_requirements or [])}")
        
        # Query RAG responses
        responses = db.query(RAGResponse).all()
        print(f"\n🤖 RAG Responses ({len(responses)}):")
        for response in responses:
            query_preview = response.query[:60] + "..." if len(response.query) > 60 else response.query
            print(f"  • Query: {query_preview}")
            print(f"    Model: {response.model_used}, Confidence: {response.confidence_score}")
            print(f"    Sources: {len(response.source_chunks or [])} chunks")
    
    print("\n5. Testing Pydantic schemas...")
    
    # Test document creation schema
    doc_create = DocumentCreate(
        filename="test_schema.pdf",
        document_type="pdf",
        file_size=1024,
        file_path="/test/path.pdf",
        schema_type="EU_ESRS_CSRD",
        document_metadata={"test": True}
    )
    print(f"✅ DocumentCreate schema validation passed: {doc_create.filename}")
    
    # Test text chunk creation schema
    chunk_create = TextChunkCreate(
        document_id="test-doc-id",
        content="Test content for validation",
        chunk_index=0,
        embedding_vector=[0.1, 0.2, 0.3],
        schema_elements=["E1", "E2"]
    )
    print(f"✅ TextChunkCreate schema validation passed: chunk {chunk_create.chunk_index}")
    
    # Test schema element creation
    element_create = SchemaElementCreate(
        schema_type="EU_ESRS_CSRD",
        element_code="e2",  # Should be converted to uppercase
        element_name="Water and Marine Resources",
        description="Water-related disclosures",
        requirements=["Water consumption", "Water pollution"]
    )
    print(f"✅ SchemaElementCreate schema validation passed: {element_create.element_code}")
    
    print("\n🎉 Demo completed successfully!")
    print("All database models, schemas, and operations are working correctly.")


if __name__ == "__main__":
    try:
        demo_database_operations()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)