# CSRD RAG System User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Document Management](#document-management)
4. [Search and Discovery](#search-and-discovery)
5. [AI-Powered Question Answering](#ai-powered-question-answering)
6. [Report Generation](#report-generation)
7. [Schema Management](#schema-management)
8. [Remote Directory Synchronization](#remote-directory-synchronization)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Introduction

The CSRD RAG (Corporate Sustainability Reporting Directive - Retrieval-Augmented Generation) System is a comprehensive platform designed to help organizations manage, search, and generate insights from sustainability reporting documents. The system supports both EU European Sustainability Reporting Standards (ESRS/CSRD) and UK Sustainability Reporting Directive (SRD) frameworks.

### Key Features

- **Document Repository**: Centralized storage and management of regulatory documents
- **Intelligent Search**: Semantic search across document content using AI
- **Question Answering**: AI-powered responses based on document content
- **Report Generation**: Automated creation of compliance reports
- **Schema Support**: Built-in support for ESRS/CSRD and UK SRD frameworks
- **Remote Synchronization**: Automatic monitoring of remote document directories

### Who Should Use This Guide

This guide is intended for:
- Sustainability professionals and compliance officers
- ESG analysts and consultants
- Legal and regulatory teams
- IT administrators deploying the system

## Getting Started

### System Requirements

**Minimum Requirements:**
- 4 GB RAM
- 20 GB available disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for AI model access

**Recommended Requirements:**
- 8 GB RAM or more
- 50 GB available disk space
- High-speed internet connection

### Accessing the System

1. **Web Interface**: Navigate to your system URL (e.g., `http://localhost:8000`)
2. **API Access**: Use the REST API at `/api/` endpoints
3. **Documentation**: Interactive API docs available at `/docs`

### First-Time Setup

1. **Upload Initial Documents**: Start by uploading key regulatory documents
2. **Select Schema Type**: Choose between EU ESRS/CSRD or UK SRD
3. **Wait for Processing**: Allow time for document processing and indexing
4. **Test Search**: Perform a test search to verify functionality

## Document Management

### Supported File Formats

The system accepts the following document formats:
- **PDF**: Portable Document Format (recommended)
- **DOCX**: Microsoft Word documents
- **TXT**: Plain text files

### Uploading Documents

#### Via Web Interface

1. Navigate to the **Documents** section
2. Click **Upload Document** button
3. Select your file using the file picker or drag-and-drop
4. Choose the appropriate **Schema Type**:
   - **EU ESRS/CSRD**: For European sustainability reporting standards
   - **UK SRD**: For UK sustainability reporting directive
5. Add optional metadata (category, tags, description)
6. Click **Upload** to start processing

#### Via API

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@sustainability_report.pdf" \
  -F "schema_type=eu_esrs_csrd" \
  -F "metadata={\"category\": \"environmental\"}"
```

### Document Processing

After upload, documents go through several processing stages:

1. **Text Extraction**: Content is extracted from the file
2. **Chunking**: Text is split into manageable segments
3. **Embedding Generation**: AI creates vector representations
4. **Schema Classification**: Content is mapped to schema elements
5. **Indexing**: Document is added to the search index

**Processing Time**: Typically 1-5 minutes depending on document size.

### Managing Documents

#### Viewing Documents

- **Document List**: View all uploaded documents with metadata
- **Filter Options**: Filter by schema type, processing status, or date
- **Search Documents**: Find specific documents by name or content
- **Sort Options**: Sort by upload date, file size, or processing status

#### Document Details

Click on any document to view:
- File information (size, format, upload date)
- Processing status and completion time
- Schema elements identified in the document
- Number of text chunks created
- Associated metadata

#### Deleting Documents

⚠️ **Warning**: Deleting a document removes all associated data including embeddings and search indices.

1. Navigate to the document details page
2. Click **Delete Document**
3. Confirm the deletion in the dialog box

## Search and Discovery

### Semantic Search

The system provides intelligent search capabilities that understand the meaning of your queries, not just keyword matching.

#### Performing a Search

1. Navigate to the **Search** section
2. Enter your search query in natural language
3. Optionally filter by:
   - **Schema Type**: Limit to specific regulatory framework
   - **Document Type**: Filter by document categories
   - **Relevance Score**: Set minimum relevance threshold
4. Click **Search** to see results

#### Search Examples

**Good Search Queries:**
- "carbon emissions reporting requirements"
- "mandatory disclosures for Scope 3 emissions"
- "climate change risk assessment procedures"
- "social sustainability metrics and KPIs"

**Search Results Include:**
- Relevant text excerpts with highlighting
- Source document information
- Relevance scores (0-1, higher is more relevant)
- Schema elements associated with the content
- Page numbers (for PDF documents)

#### Advanced Search Tips

1. **Use Natural Language**: Write queries as you would ask a colleague
2. **Be Specific**: Include specific terms like "ESRS E1" or "Scope 3"
3. **Use Context**: Include context like "reporting requirements" or "disclosure obligations"
4. **Filter Results**: Use schema type filters to narrow results

### Search Result Interpretation

**Relevance Scores:**
- **0.9-1.0**: Highly relevant, directly addresses your query
- **0.7-0.9**: Very relevant, contains important related information
- **0.5-0.7**: Moderately relevant, may contain useful context
- **Below 0.5**: Low relevance, may not be directly useful

## AI-Powered Question Answering

### How It Works

The RAG (Retrieval-Augmented Generation) system:
1. Searches for relevant document content based on your question
2. Retrieves the most relevant text chunks
3. Uses AI models to generate comprehensive answers
4. Provides source citations for verification

### Asking Questions

#### Via Web Interface

1. Navigate to the **RAG** section
2. Select your preferred AI model:
   - **GPT-4**: Most capable, best for complex questions
   - **Claude-3**: Balanced performance and speed
   - **Local Models**: Privacy-focused, may have limitations
3. Type your question in natural language
4. Optionally adjust settings:
   - **Schema Type**: Focus on specific regulatory framework
   - **Temperature**: Control creativity (lower = more factual)
   - **Max Context**: Number of document chunks to consider
5. Click **Ask Question**

#### Question Examples

**Effective Questions:**
- "What are the mandatory disclosure requirements for Scope 3 emissions under ESRS E1?"
- "How should companies report on their climate transition plans according to CSRD?"
- "What social sustainability metrics must be disclosed under ESRS S1?"
- "What are the key differences between ESRS and UK SRD reporting requirements?"

**Less Effective Questions:**
- "Tell me about sustainability" (too broad)
- "What is ESRS?" (basic definition, not document-specific)
- "How to be sustainable?" (not regulatory-focused)

### Understanding Responses

Each AI response includes:

**Answer Content:**
- Comprehensive response based on document content
- Structured information with clear explanations
- Specific requirements and obligations
- Relevant examples where available

**Source Citations:**
- Document names and page numbers
- Relevance scores for each source
- Direct excerpts from source documents
- Links to view full document context

**Quality Indicators:**
- **Confidence Score**: AI's confidence in the answer (0-1)
- **Processing Time**: Time taken to generate response
- **Model Used**: Which AI model generated the response
- **Context Quality**: How well sources match the question

### Model Selection Guide

**GPT-4 (OpenAI)**
- **Best for**: Complex analysis, detailed explanations
- **Strengths**: Superior reasoning, comprehensive responses
- **Use when**: Accuracy is critical, complex regulatory questions

**Claude-3 (Anthropic)**
- **Best for**: Balanced performance, faster responses
- **Strengths**: Good accuracy, efficient processing
- **Use when**: Need quick responses, moderate complexity

**Local Models**
- **Best for**: Privacy-sensitive content, offline operation
- **Strengths**: Data privacy, no external API calls
- **Use when**: Confidential documents, air-gapped environments

## Report Generation

### Overview

The report generation feature creates comprehensive sustainability reports based on client-specific requirements and regulatory documents.

### Process Workflow

1. **Upload Client Requirements**: Provide client-specific reporting needs
2. **Requirements Analysis**: System maps requirements to schema elements
3. **Content Generation**: AI creates responses for each requirement
4. **Report Compilation**: Content is structured into a professional report
5. **PDF Generation**: Final report is created with proper formatting

### Uploading Client Requirements

#### Supported Formats

- **PDF Questionnaires**: Client sustainability questionnaires
- **Word Templates**: Reporting templates with specific questions
- **Structured Data**: JSON or CSV files with requirements
- **Text Files**: Plain text requirement lists

#### Upload Process

1. Navigate to the **Reports** section
2. Click **New Report** or **Upload Requirements**
3. Select your client requirements file
4. Provide client information:
   - **Client Name**: Organization name
   - **Schema Type**: Target regulatory framework
   - **Report Template**: Choose from available templates
5. Click **Upload and Process**

### Report Generation Options

**Template Types:**
- **Standard Report**: Comprehensive regulatory compliance report
- **Executive Summary**: High-level overview for leadership
- **Technical Report**: Detailed technical analysis
- **Gap Analysis**: Identifies missing compliance elements

**Customization Options:**
- **Include Citations**: Add source references throughout
- **Executive Summary**: Generate summary section
- **Appendices**: Include supporting documentation
- **Custom Branding**: Add organization logos and styling

### Monitoring Report Progress

Report generation can take 10-30 minutes depending on complexity:

1. **Queued**: Report is waiting to be processed
2. **Processing Requirements**: Analyzing client requirements
3. **Generating Content**: AI is creating report sections
4. **Compiling Report**: Structuring and formatting content
5. **Creating PDF**: Final document generation
6. **Completed**: Report is ready for download

### Report Quality and Review

**Quality Assurance:**
- All responses include source citations
- Content is cross-referenced with regulatory documents
- Consistency checks across report sections
- Professional formatting and structure

**Review Process:**
1. Download and review the generated report
2. Check source citations for accuracy
3. Verify content against client requirements
4. Make manual edits if necessary
5. Regenerate sections if needed

## Schema Management

### Understanding Schemas

Schemas define the structure and requirements of regulatory frameworks:

**EU ESRS/CSRD Schema:**
- Environmental Standards (E1-E5)
- Social Standards (S1-S4)
- Governance Standards (G1)
- Cross-cutting Standards

**UK SRD Schema:**
- Mandatory Disclosures
- Voluntary Disclosures
- Sector-specific Requirements

### Viewing Schema Information

1. Navigate to the **Schemas** section
2. Select a schema type to view:
   - **Element Hierarchy**: Organized structure of requirements
   - **Detailed Requirements**: Specific disclosure obligations
   - **Cross-references**: Relationships between elements
   - **Updates and Versions**: Schema version information

### Schema Classification

Documents are automatically classified against schema elements:

**Classification Process:**
1. Text analysis identifies relevant topics
2. Content is mapped to specific schema elements
3. Confidence scores are assigned to mappings
4. Manual review and adjustment options available

**Using Classifications:**
- Filter search results by schema elements
- Focus questions on specific regulatory areas
- Generate targeted reports for compliance areas
- Track coverage across regulatory requirements

## Remote Directory Synchronization

### Overview

The system can automatically monitor and synchronize documents from remote directories, enabling seamless integration with existing document management systems.

### Supported Sources

- **Network Drives**: SMB/CIFS shared folders
- **SharePoint**: Microsoft SharePoint document libraries
- **Cloud Storage**: AWS S3, Google Drive, Dropbox
- **FTP/SFTP**: File transfer protocol servers

### Setting Up Remote Directories

1. Navigate to **Settings** > **Remote Directories**
2. Click **Add Remote Directory**
3. Configure connection settings:
   - **Directory Name**: Descriptive name for the source
   - **Path/URL**: Location of the remote directory
   - **Authentication**: Credentials if required
   - **Schema Type**: Default schema for documents
   - **Sync Interval**: How often to check for updates
4. Test the connection
5. Save and enable synchronization

### Synchronization Process

**Automatic Sync:**
- Runs at configured intervals (hourly, daily, weekly)
- Detects new, modified, and deleted files
- Processes new documents automatically
- Updates existing documents if changed
- Removes documents that are deleted from source

**Manual Sync:**
- Trigger immediate synchronization
- Useful for testing or urgent updates
- Monitor sync progress and results
- Review any errors or conflicts

### Monitoring Sync Status

**Sync Dashboard:**
- View all configured remote directories
- Check last sync time and status
- Monitor document counts and changes
- Review sync logs and error messages

**Notifications:**
- Email alerts for sync failures
- Dashboard notifications for new documents
- Error reports for processing issues

## Best Practices

### Document Organization

**File Naming Conventions:**
- Use descriptive, consistent names
- Include version numbers when applicable
- Avoid special characters and spaces
- Example: `ESRS_E1_Climate_Change_v2.1.pdf`

**Metadata Usage:**
- Add relevant categories and tags
- Include document source and date
- Note regulatory framework and scope
- Use consistent terminology across documents

### Search Optimization

**Query Formulation:**
- Use specific regulatory terminology
- Include context and scope in queries
- Combine multiple concepts for precision
- Iterate and refine based on results

**Result Evaluation:**
- Review relevance scores carefully
- Check multiple sources for completeness
- Verify information against original documents
- Use citations to trace back to sources

### Question Asking

**Effective Questions:**
- Be specific about regulatory requirements
- Include relevant schema elements (e.g., "ESRS E1")
- Ask for specific types of information
- Frame questions in business context

**Model Selection:**
- Use GPT-4 for complex, critical questions
- Use Claude-3 for routine inquiries
- Consider local models for sensitive content
- Match model capabilities to question complexity

### Report Generation

**Requirements Preparation:**
- Provide clear, specific client requirements
- Use structured formats when possible
- Include context and background information
- Specify desired level of detail

**Quality Review:**
- Always review generated content
- Verify citations and sources
- Check for consistency across sections
- Ensure alignment with client needs

## Troubleshooting

### Common Issues

#### Document Upload Problems

**Issue**: Upload fails or times out
**Solutions:**
- Check file size (max 100MB)
- Verify file format (PDF, DOCX, TXT only)
- Ensure stable internet connection
- Try uploading smaller files first

**Issue**: Processing takes too long
**Solutions:**
- Large documents may take 10+ minutes
- Check processing status regularly
- Contact administrator if stuck for hours
- Consider splitting very large documents

#### Search Issues

**Issue**: No search results found
**Solutions:**
- Try broader, more general queries
- Check spelling and terminology
- Verify documents are fully processed
- Use different search terms or synonyms

**Issue**: Irrelevant search results
**Solutions:**
- Use more specific queries
- Add context and qualifiers
- Filter by schema type or document category
- Increase minimum relevance score

#### RAG/Question Answering Issues

**Issue**: AI gives generic or unhelpful answers
**Solutions:**
- Make questions more specific
- Include relevant schema elements
- Try different AI models
- Ensure relevant documents are uploaded

**Issue**: Slow response times
**Solutions:**
- Check internet connection
- Try different AI models
- Reduce context window size
- Contact administrator about system load

#### Report Generation Issues

**Issue**: Report generation fails
**Solutions:**
- Check client requirements file format
- Verify sufficient relevant documents exist
- Try simpler requirements first
- Contact support with error details

**Issue**: Poor report quality
**Solutions:**
- Improve client requirements specificity
- Upload more relevant regulatory documents
- Use higher-capability AI models
- Review and refine requirements

### Getting Help

**Self-Service Resources:**
- Interactive API documentation at `/docs`
- System health check at `/health`
- This user guide and FAQ section
- Error messages and suggested solutions

**Administrator Support:**
- Contact your system administrator
- Provide specific error messages
- Include steps to reproduce issues
- Share relevant document or query details

**Technical Support:**
- Check system logs for detailed errors
- Monitor system performance metrics
- Review configuration settings
- Consult deployment documentation

### Performance Optimization

**System Performance:**
- Monitor disk space usage
- Check database performance
- Review memory and CPU usage
- Optimize document storage

**User Experience:**
- Use appropriate file sizes
- Batch upload multiple documents
- Cache frequently used searches
- Optimize query formulation

### Data Management

**Backup and Recovery:**
- Regular database backups
- Document storage backups
- Configuration backup
- Test recovery procedures

**Data Retention:**
- Define document retention policies
- Archive old or unused documents
- Clean up temporary files
- Monitor storage usage

**Security Considerations:**
- Secure document access
- Monitor user activity
- Regular security updates
- Data encryption at rest and in transit

---

## Appendix

### Glossary

**CSRD**: Corporate Sustainability Reporting Directive - EU regulation requiring sustainability reporting

**ESRS**: European Sustainability Reporting Standards - Technical standards for CSRD compliance

**RAG**: Retrieval-Augmented Generation - AI technique combining search and text generation

**Schema**: Structured framework defining reporting requirements and elements

**Semantic Search**: Search that understands meaning and context, not just keywords

**Vector Embedding**: Mathematical representation of text content for similarity comparison

### Regulatory Framework References

**EU ESRS/CSRD:**
- Environmental Standards: E1 (Climate), E2 (Pollution), E3 (Water), E4 (Biodiversity), E5 (Circular Economy)
- Social Standards: S1 (Workforce), S2 (Workers in Value Chain), S3 (Affected Communities), S4 (Consumers)
- Governance Standards: G1 (Business Conduct)

**UK SRD:**
- Mandatory climate-related disclosures
- Governance and risk management
- Strategy and business model
- Metrics and targets

### Contact Information

For additional support or questions about this user guide:
- Technical Documentation: `/docs`
- System Health: `/health`
- Administrator Contact: [Your admin contact information]