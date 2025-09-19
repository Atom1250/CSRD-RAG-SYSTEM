"""
Report Generation Service for creating structured sustainability reports
based on client requirements and RAG responses.
"""
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import re

from sqlalchemy.orm import Session

from ..models.database import ClientRequirements, Document, TextChunk
from ..models.schemas import (
    ClientRequirementsResponse, RAGResponseResponse, SchemaType
)
from .client_requirements_service import ClientRequirementsService
from .rag_service import RAGService, AIModelType

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """Report format enumeration"""
    STRUCTURED_TEXT = "structured_text"
    HTML = "html"
    MARKDOWN = "markdown"


class ReportTemplate(str, Enum):
    """Report template types"""
    EU_ESRS_STANDARD = "eu_esrs_standard"
    UK_SRD_STANDARD = "uk_srd_standard"
    CUSTOM_TEMPLATE = "custom_template"
    GAP_ANALYSIS = "gap_analysis"


@dataclass
class ReportSection:
    """Data class for report sections"""
    id: str
    title: str
    content: str
    subsections: List['ReportSection']
    metadata: Dict[str, Any]
    sources: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'subsections': [sub.to_dict() for sub in self.subsections],
            'metadata': self.metadata,
            'sources': self.sources
        }


@dataclass
class ReportContent:
    """Data class for complete report content"""
    title: str
    client_name: str
    generation_date: datetime
    template_type: ReportTemplate
    schema_type: SchemaType
    sections: List[ReportSection]
    executive_summary: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'client_name': self.client_name,
            'generation_date': self.generation_date.isoformat(),
            'template_type': self.template_type.value,
            'schema_type': self.schema_type.value,
            'sections': [section.to_dict() for section in self.sections],
            'executive_summary': self.executive_summary,
            'metadata': self.metadata
        }


class ReportTemplateManager:
    """Manages report templates for different reporting standards"""
    
    def __init__(self):
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[ReportTemplate, Dict[str, Any]]:
        """Load default report templates"""
        return {
            ReportTemplate.EU_ESRS_STANDARD: {
                "name": "EU ESRS/CSRD Standard Report",
                "description": "Standard report template for EU ESRS/CSRD compliance",
                "sections": [
                    {
                        "id": "executive_summary",
                        "title": "Executive Summary",
                        "required": True,
                        "description": "High-level overview of sustainability performance and compliance"
                    },
                    {
                        "id": "general_requirements",
                        "title": "General Requirements (ESRS 1 & 2)",
                        "required": True,
                        "description": "General principles and disclosure requirements"
                    },
                    {
                        "id": "environmental_standards",
                        "title": "Environmental Standards (E1-E5)",
                        "required": False,
                        "subsections": [
                            {"id": "e1_climate", "title": "E1 - Climate Change"},
                            {"id": "e2_pollution", "title": "E2 - Pollution"},
                            {"id": "e3_water", "title": "E3 - Water and Marine Resources"},
                            {"id": "e4_biodiversity", "title": "E4 - Biodiversity and Ecosystems"},
                            {"id": "e5_circular", "title": "E5 - Resource Use and Circular Economy"}
                        ]
                    },
                    {
                        "id": "social_standards",
                        "title": "Social Standards (S1-S4)",
                        "required": False,
                        "subsections": [
                            {"id": "s1_workforce", "title": "S1 - Own Workforce"},
                            {"id": "s2_workers", "title": "S2 - Workers in Value Chain"},
                            {"id": "s3_communities", "title": "S3 - Affected Communities"},
                            {"id": "s4_consumers", "title": "S4 - Consumers and End-users"}
                        ]
                    },
                    {
                        "id": "governance_standards",
                        "title": "Governance Standards (G1)",
                        "required": False,
                        "subsections": [
                            {"id": "g1_governance", "title": "G1 - Business Conduct"}
                        ]
                    },
                    {
                        "id": "conclusions",
                        "title": "Conclusions and Recommendations",
                        "required": True,
                        "description": "Summary of findings and next steps"
                    }
                ]
            },
            ReportTemplate.UK_SRD_STANDARD: {
                "name": "UK SRD Standard Report",
                "description": "Standard report template for UK Sustainability Reporting Directive compliance",
                "sections": [
                    {
                        "id": "executive_summary",
                        "title": "Executive Summary",
                        "required": True,
                        "description": "Overview of sustainability reporting compliance"
                    },
                    {
                        "id": "mandatory_disclosures",
                        "title": "Mandatory Disclosures",
                        "required": True,
                        "description": "Required sustainability disclosures under UK SRD"
                    },
                    {
                        "id": "voluntary_disclosures",
                        "title": "Voluntary Disclosures",
                        "required": False,
                        "description": "Additional voluntary sustainability information"
                    },
                    {
                        "id": "sector_specific",
                        "title": "Sector-Specific Requirements",
                        "required": False,
                        "description": "Industry-specific sustainability requirements"
                    },
                    {
                        "id": "compliance_assessment",
                        "title": "Compliance Assessment",
                        "required": True,
                        "description": "Assessment of compliance with UK SRD requirements"
                    }
                ]
            },
            ReportTemplate.GAP_ANALYSIS: {
                "name": "Gap Analysis Report",
                "description": "Template for gap analysis between requirements and available documentation",
                "sections": [
                    {
                        "id": "overview",
                        "title": "Gap Analysis Overview",
                        "required": True,
                        "description": "Summary of gap analysis methodology and scope"
                    },
                    {
                        "id": "coverage_analysis",
                        "title": "Coverage Analysis",
                        "required": True,
                        "description": "Analysis of requirement coverage by available documents"
                    },
                    {
                        "id": "identified_gaps",
                        "title": "Identified Gaps",
                        "required": True,
                        "description": "Detailed analysis of gaps and missing information"
                    },
                    {
                        "id": "recommendations",
                        "title": "Recommendations",
                        "required": True,
                        "description": "Recommendations for addressing identified gaps"
                    }
                ]
            }
        }
    
    def get_template(self, template_type: ReportTemplate) -> Dict[str, Any]:
        """Get template configuration by type"""
        return self.templates.get(template_type, {})
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates"""
        return [
            {
                "type": template_type.value,
                "name": template_config.get("name", ""),
                "description": template_config.get("description", "")
            }
            for template_type, template_config in self.templates.items()
        ]
    
    def add_custom_template(self, template_type: str, template_config: Dict[str, Any]) -> bool:
        """Add a custom template"""
        try:
            custom_template = ReportTemplate.CUSTOM_TEMPLATE
            self.templates[custom_template] = template_config
            return True
        except Exception as e:
            logger.error(f"Failed to add custom template: {str(e)}")
            return False


class ReportService:
    """Service for generating structured sustainability reports"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.client_requirements_service = ClientRequirementsService(db_session)
        self.rag_service = RAGService(db_session)
        self.template_manager = ReportTemplateManager()
    
    async def generate_report(
        self,
        requirements_id: str,
        template_type: ReportTemplate = ReportTemplate.EU_ESRS_STANDARD,
        ai_model: AIModelType = AIModelType.OPENAI_GPT35,
        report_format: ReportFormat = ReportFormat.STRUCTURED_TEXT
    ) -> ReportContent:
        """
        Generate a complete sustainability report based on client requirements
        
        Args:
            requirements_id: ID of the client requirements
            template_type: Type of report template to use
            ai_model: AI model for generating content
            report_format: Output format for the report
            
        Returns:
            ReportContent: Complete structured report
        """
        logger.info(f"Generating report for requirements {requirements_id} using template {template_type.value}")
        
        # Get client requirements
        client_requirements = self.client_requirements_service.get_client_requirements(requirements_id)
        if not client_requirements:
            raise ValueError(f"Client requirements not found: {requirements_id}")
        
        # Get template configuration
        template_config = self.template_manager.get_template(template_type)
        if not template_config:
            raise ValueError(f"Template not found: {template_type.value}")
        
        # Determine schema type from requirements or use default
        schema_type = self._determine_schema_type(client_requirements, template_type)
        
        # Generate report sections
        sections = await self._generate_report_sections(
            client_requirements, template_config, ai_model
        )
        
        # Generate executive summary
        executive_summary = await self._generate_executive_summary(
            client_requirements, sections, ai_model
        )
        
        # Create report content
        report_content = ReportContent(
            title=f"{template_config.get('name', 'Sustainability Report')} - {client_requirements.client_name}",
            client_name=client_requirements.client_name,
            generation_date=datetime.utcnow(),
            template_type=template_type,
            schema_type=schema_type,
            sections=sections,
            executive_summary=executive_summary,
            metadata={
                "requirements_id": requirements_id,
                "ai_model_used": ai_model.value,
                "report_format": report_format.value,
                "generation_timestamp": datetime.utcnow().isoformat(),
                "template_version": "1.0"
            }
        )
        
        logger.info(f"Report generated successfully with {len(sections)} sections")
        return report_content
    
    def _determine_schema_type(
        self, 
        client_requirements: ClientRequirementsResponse, 
        template_type: ReportTemplate
    ) -> SchemaType:
        """Determine the appropriate schema type for the report"""
        # Default based on template type first
        if template_type == ReportTemplate.UK_SRD_STANDARD:
            return SchemaType.UK_SRD
        
        # Check if requirements have schema mappings
        if client_requirements.schema_mappings:
            # Analyze schema mappings to determine predominant schema type
            eu_count = sum(1 for mapping in client_requirements.schema_mappings 
                          if mapping.schema_element_id.startswith('EU_'))
            uk_count = sum(1 for mapping in client_requirements.schema_mappings 
                          if mapping.schema_element_id.startswith('UK_'))
            
            if uk_count > eu_count and template_type == ReportTemplate.UK_SRD_STANDARD:
                return SchemaType.UK_SRD
            elif eu_count > 0:
                return SchemaType.EU_ESRS_CSRD
        
        # Default to EU ESRS for other templates
        return SchemaType.EU_ESRS_CSRD
    
    async def _generate_report_sections(
        self,
        client_requirements: ClientRequirementsResponse,
        template_config: Dict[str, Any],
        ai_model: AIModelType
    ) -> List[ReportSection]:
        """Generate all report sections based on template and requirements"""
        sections = []
        
        template_sections = template_config.get("sections", [])
        
        for section_config in template_sections:
            section = await self._generate_single_section(
                section_config, client_requirements, ai_model
            )
            if section:
                sections.append(section)
        
        return sections
    
    async def _generate_single_section(
        self,
        section_config: Dict[str, Any],
        client_requirements: ClientRequirementsResponse,
        ai_model: AIModelType
    ) -> Optional[ReportSection]:
        """Generate a single report section"""
        try:
            section_id = section_config.get("id", "")
            section_title = section_config.get("title", "")
            
            logger.info(f"Generating section: {section_title}")
            
            # Generate content for this section
            content, sources = await self._generate_section_content(
                section_config, client_requirements, ai_model
            )
            
            # Generate subsections if defined
            subsections = []
            if "subsections" in section_config:
                for subsection_config in section_config["subsections"]:
                    subsection = await self._generate_single_section(
                        subsection_config, client_requirements, ai_model
                    )
                    if subsection:
                        subsections.append(subsection)
            
            return ReportSection(
                id=section_id,
                title=section_title,
                content=content,
                subsections=subsections,
                metadata={
                    "required": section_config.get("required", False),
                    "description": section_config.get("description", ""),
                    "generation_timestamp": datetime.utcnow().isoformat()
                },
                sources=sources
            )
            
        except Exception as e:
            logger.error(f"Failed to generate section {section_config.get('title', 'Unknown')}: {str(e)}")
            return None
    
    async def _generate_section_content(
        self,
        section_config: Dict[str, Any],
        client_requirements: ClientRequirementsResponse,
        ai_model: AIModelType
    ) -> Tuple[str, List[str]]:
        """Generate content for a specific section using RAG"""
        section_id = section_config.get("id", "")
        section_title = section_config.get("title", "")
        
        # Find relevant requirements for this section
        relevant_requirements = self._find_relevant_requirements(
            section_id, client_requirements
        )
        
        if not relevant_requirements:
            return f"No specific requirements found for {section_title}.", []
        
        # Generate questions for RAG based on requirements
        questions = self._generate_section_questions(section_config, relevant_requirements)
        
        # Get RAG responses for all questions
        all_sources = []
        content_parts = []
        
        for question in questions:
            try:
                rag_response = await self.rag_service.generate_rag_response(
                    question=question,
                    model_type=ai_model,
                    max_context_chunks=5,
                    min_relevance_score=0.3
                )
                
                if rag_response.response_text and rag_response.confidence_score > 0.2:
                    content_parts.append(rag_response.response_text)
                    all_sources.extend(rag_response.source_chunks or [])
                
            except Exception as e:
                logger.warning(f"Failed to generate RAG response for question '{question}': {str(e)}")
        
        # Combine and structure content
        if content_parts:
            combined_content = self._structure_section_content(
                section_title, content_parts, relevant_requirements
            )
        else:
            combined_content = f"Unable to generate specific content for {section_title} based on available documents."
        
        return combined_content, list(set(all_sources))
    
    def _find_relevant_requirements(
        self,
        section_id: str,
        client_requirements: ClientRequirementsResponse
    ) -> List[Dict[str, Any]]:
        """Find requirements relevant to a specific section"""
        if not client_requirements.processed_requirements:
            return []
        
        relevant_requirements = []
        
        # Define section keywords for matching
        section_keywords = {
            "executive_summary": ["summary", "overview", "executive"],
            "general_requirements": ["general", "principle", "disclosure"],
            "environmental_standards": ["environmental", "climate", "pollution", "water", "biodiversity", "circular"],
            "e1_climate": ["climate", "carbon", "emission", "greenhouse"],
            "e2_pollution": ["pollution", "air", "waste", "chemical"],
            "e3_water": ["water", "marine", "ocean", "aquatic"],
            "e4_biodiversity": ["biodiversity", "ecosystem", "species", "habitat"],
            "e5_circular": ["circular", "resource", "material", "waste"],
            "social_standards": ["social", "workforce", "worker", "community", "consumer"],
            "s1_workforce": ["workforce", "employee", "staff", "worker"],
            "s2_workers": ["supply chain", "value chain", "contractor"],
            "s3_communities": ["community", "local", "stakeholder"],
            "s4_consumers": ["consumer", "customer", "end-user"],
            "governance_standards": ["governance", "business conduct", "ethics"],
            "g1_governance": ["governance", "conduct", "ethics", "compliance"],
            "mandatory_disclosures": ["mandatory", "required", "disclosure"],
            "voluntary_disclosures": ["voluntary", "additional", "optional"],
            "sector_specific": ["sector", "industry", "specific"],
            "compliance_assessment": ["compliance", "assessment", "evaluation"],
            "conclusions": ["conclusion", "recommendation", "next step"]
        }
        
        keywords = section_keywords.get(section_id, [section_id])
        
        for req in client_requirements.processed_requirements:
            # Handle both dict and Pydantic model formats
            if isinstance(req, dict):
                req_text = req.get("requirement_text", "").lower()
            else:
                req_text = getattr(req, "requirement_text", "").lower()
            
            # Check if any keywords match the requirement text
            if any(keyword in req_text for keyword in keywords):
                relevant_requirements.append(req)
        
        # If no specific matches, include high-priority requirements
        if not relevant_requirements:
            high_priority_reqs = []
            for req in client_requirements.processed_requirements:
                # Handle both dict and Pydantic model formats
                if isinstance(req, dict):
                    priority = req.get("priority", "medium")
                else:
                    priority = getattr(req, "priority", "medium")
                
                if priority == "high":
                    high_priority_reqs.append(req)
            
            relevant_requirements.extend(high_priority_reqs[:3])  # Limit to top 3
        
        return relevant_requirements
    
    def _generate_section_questions(
        self,
        section_config: Dict[str, Any],
        relevant_requirements: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate questions for RAG based on section and requirements"""
        section_title = section_config.get("title", "")
        section_description = section_config.get("description", "")
        
        questions = []
        
        # Generate general section question
        if section_description:
            questions.append(f"What are the key requirements and guidelines for {section_title}? {section_description}")
        else:
            questions.append(f"What are the key requirements and guidelines for {section_title}?")
        
        # Generate specific questions from requirements
        for req in relevant_requirements[:3]:  # Limit to top 3 requirements
            # Handle both dict and Pydantic model formats
            if isinstance(req, dict):
                req_text = req.get("requirement_text", "")
            else:
                req_text = getattr(req, "requirement_text", "")
            
            if req_text:
                questions.append(f"How should an organization address the following requirement: {req_text}")
        
        return questions
    
    def _structure_section_content(
        self,
        section_title: str,
        content_parts: List[str],
        relevant_requirements: List[Dict[str, Any]]
    ) -> str:
        """Structure and format section content"""
        structured_content = []
        
        # Add section introduction
        structured_content.append(f"## {section_title}\n")
        
        # Add requirements overview if available
        if relevant_requirements:
            structured_content.append("### Relevant Requirements\n")
            for i, req in enumerate(relevant_requirements[:3], 1):
                # Handle both dict and Pydantic model formats
                if isinstance(req, dict):
                    req_text = req.get("requirement_text", "")
                    priority = req.get("priority", "medium")
                else:
                    req_text = getattr(req, "requirement_text", "")
                    priority = getattr(req, "priority", "medium")
                
                structured_content.append(f"{i}. **{priority.title()} Priority**: {req_text}\n")
            structured_content.append("")
        
        # Add generated content
        structured_content.append("### Analysis and Guidance\n")
        
        for i, content in enumerate(content_parts, 1):
            if len(content_parts) > 1:
                structured_content.append(f"#### Aspect {i}\n")
            structured_content.append(content)
            structured_content.append("")
        
        return "\n".join(structured_content)
    
    async def _generate_executive_summary(
        self,
        client_requirements: ClientRequirementsResponse,
        sections: List[ReportSection],
        ai_model: AIModelType
    ) -> str:
        """Generate executive summary based on report sections"""
        try:
            # Create summary prompt based on sections
            section_summaries = []
            for section in sections:
                if section.content and len(section.content) > 100:
                    # Extract first paragraph or first 200 characters
                    summary = section.content.split('\n')[0][:200] + "..."
                    section_summaries.append(f"- {section.title}: {summary}")
            
            summary_prompt = f"""
            Based on the following sustainability report sections for {client_requirements.client_name}, 
            create a comprehensive executive summary that highlights key findings, compliance status, 
            and main recommendations:
            
            {chr(10).join(section_summaries)}
            
            The executive summary should be concise (2-3 paragraphs) and provide stakeholders with 
            a clear understanding of the organization's sustainability reporting status and key areas of focus.
            """
            
            rag_response = await self.rag_service.generate_rag_response(
                question=summary_prompt,
                model_type=ai_model,
                max_context_chunks=3,
                min_relevance_score=0.2
            )
            
            if rag_response.response_text and rag_response.confidence_score > 0.3:
                return rag_response.response_text
            else:
                return self._generate_default_executive_summary(client_requirements, sections)
                
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {str(e)}")
            return self._generate_default_executive_summary(client_requirements, sections)
    
    def _generate_default_executive_summary(
        self,
        client_requirements: ClientRequirementsResponse,
        sections: List[ReportSection]
    ) -> str:
        """Generate a default executive summary when AI generation fails"""
        return f"""
        ## Executive Summary
        
        This sustainability report for {client_requirements.client_name} provides a comprehensive analysis 
        of regulatory compliance requirements and available documentation. The report covers {len(sections)} 
        key areas of sustainability reporting based on the client's specific requirements.
        
        The analysis includes evaluation of current documentation against regulatory standards, 
        identification of compliance gaps, and recommendations for addressing any deficiencies. 
        This report serves as a foundation for developing a comprehensive sustainability reporting strategy.
        
        Key areas covered in this report include regulatory compliance assessment, documentation analysis, 
        and strategic recommendations for enhancing sustainability reporting capabilities.
        """
    
    def format_report(self, report_content: ReportContent, format_type: ReportFormat) -> str:
        """Format report content according to specified format"""
        if format_type == ReportFormat.MARKDOWN:
            return self._format_as_markdown(report_content)
        elif format_type == ReportFormat.HTML:
            return self._format_as_html(report_content)
        else:  # STRUCTURED_TEXT
            return self._format_as_structured_text(report_content)
    
    def _format_as_markdown(self, report_content: ReportContent) -> str:
        """Format report as Markdown"""
        lines = []
        
        # Title and metadata
        lines.append(f"# {report_content.title}")
        lines.append(f"**Client:** {report_content.client_name}")
        lines.append(f"**Generated:** {report_content.generation_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Template:** {report_content.template_type.value}")
        lines.append(f"**Schema:** {report_content.schema_type.value}")
        lines.append("")
        
        # Executive summary
        lines.append(report_content.executive_summary)
        lines.append("")
        
        # Sections
        for section in report_content.sections:
            lines.append(self._format_section_markdown(section, level=2))
        
        return "\n".join(lines)
    
    def _format_section_markdown(self, section: ReportSection, level: int = 2) -> str:
        """Format a single section as Markdown"""
        lines = []
        
        # Section title
        lines.append(f"{'#' * level} {section.title}")
        lines.append("")
        
        # Section content
        if section.content:
            lines.append(section.content)
            lines.append("")
        
        # Subsections
        for subsection in section.subsections:
            lines.append(self._format_section_markdown(subsection, level + 1))
        
        # Sources
        if section.sources:
            lines.append("**Sources:**")
            for source in section.sources:
                lines.append(f"- {source}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_as_html(self, report_content: ReportContent) -> str:
        """Format report as HTML"""
        html_parts = []
        
        # HTML header
        html_parts.append("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .metadata {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; }}
                .section {{ margin-bottom: 30px; }}
                .sources {{ font-size: 0.9em; color: #6c757d; }}
            </style>
        </head>
        <body>
        """.format(title=report_content.title))
        
        # Title and metadata
        html_parts.append(f"<h1>{report_content.title}</h1>")
        html_parts.append('<div class="metadata">')
        html_parts.append(f"<strong>Client:</strong> {report_content.client_name}<br>")
        html_parts.append(f"<strong>Generated:</strong> {report_content.generation_date.strftime('%Y-%m-%d %H:%M:%S')}<br>")
        html_parts.append(f"<strong>Template:</strong> {report_content.template_type.value}<br>")
        html_parts.append(f"<strong>Schema:</strong> {report_content.schema_type.value}")
        html_parts.append('</div>')
        
        # Executive summary
        html_parts.append('<div class="section">')
        html_parts.append(self._markdown_to_html(report_content.executive_summary))
        html_parts.append('</div>')
        
        # Sections
        for section in report_content.sections:
            html_parts.append(self._format_section_html(section))
        
        # HTML footer
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)
    
    def _format_section_html(self, section: ReportSection, level: int = 2) -> str:
        """Format a single section as HTML"""
        html_parts = []
        
        html_parts.append('<div class="section">')
        html_parts.append(f"<h{level}>{section.title}</h{level}>")
        
        if section.content:
            html_parts.append(self._markdown_to_html(section.content))
        
        # Subsections
        for subsection in section.subsections:
            html_parts.append(self._format_section_html(subsection, level + 1))
        
        # Sources
        if section.sources:
            html_parts.append('<div class="sources">')
            html_parts.append('<strong>Sources:</strong>')
            html_parts.append('<ul>')
            for source in section.sources:
                html_parts.append(f"<li>{source}</li>")
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return "\n".join(html_parts)
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Simple Markdown to HTML conversion"""
        # This is a basic implementation - in production, use a proper Markdown library
        html = markdown_text
        
        # Convert headers
        html = re.sub(r'^### (.*)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Convert bold text
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert paragraphs
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        for para in paragraphs:
            if para.strip() and not para.strip().startswith('<'):
                html_paragraphs.append(f"<p>{para.strip()}</p>")
            else:
                html_paragraphs.append(para)
        
        return '\n'.join(html_paragraphs)
    
    def _format_as_structured_text(self, report_content: ReportContent) -> str:
        """Format report as structured text"""
        lines = []
        
        # Title and metadata
        lines.append("=" * 80)
        lines.append(f"SUSTAINABILITY REPORT: {report_content.title}")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Client: {report_content.client_name}")
        lines.append(f"Generated: {report_content.generation_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Template: {report_content.template_type.value}")
        lines.append(f"Schema: {report_content.schema_type.value}")
        lines.append("")
        lines.append("-" * 80)
        
        # Executive summary
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(report_content.executive_summary)
        lines.append("")
        
        # Sections
        for i, section in enumerate(report_content.sections, 1):
            lines.append(f"{i}. {section.title.upper()}")
            lines.append("-" * 80)
            lines.append(section.content)
            
            # Subsections
            for j, subsection in enumerate(section.subsections, 1):
                lines.append(f"  {i}.{j} {subsection.title}")
                lines.append("  " + "-" * 40)
                lines.append("  " + subsection.content.replace("\n", "\n  "))
            
            # Sources
            if section.sources:
                lines.append("")
                lines.append("Sources:")
                for source in section.sources:
                    lines.append(f"  - {source}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def save_report(self, report_content: ReportContent, file_path: str, format_type: ReportFormat) -> bool:
        """Save report to file"""
        try:
            formatted_content = self.format_report(report_content, format_type)
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            logger.info(f"Report saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save report to {file_path}: {str(e)}")
            return False
    
    def get_report_metadata(self, report_content: ReportContent) -> Dict[str, Any]:
        """Get report metadata and statistics"""
        total_sections = len(report_content.sections)
        total_subsections = sum(len(section.subsections) for section in report_content.sections)
        total_sources = sum(len(section.sources) for section in report_content.sections)
        for section in report_content.sections:
            total_sources += sum(len(subsection.sources) for subsection in section.subsections)
        
        # Calculate content statistics
        total_content_length = len(report_content.executive_summary)
        for section in report_content.sections:
            total_content_length += len(section.content)
            for subsection in section.subsections:
                total_content_length += len(subsection.content)
        
        return {
            "title": report_content.title,
            "client_name": report_content.client_name,
            "generation_date": report_content.generation_date.isoformat(),
            "template_type": report_content.template_type.value,
            "schema_type": report_content.schema_type.value,
            "statistics": {
                "total_sections": total_sections,
                "total_subsections": total_subsections,
                "total_sources": total_sources,
                "total_content_length": total_content_length,
                "estimated_reading_time_minutes": max(1, total_content_length // 1000)
            },
            "metadata": report_content.metadata
        }
    
    def generate_pdf_report(
        self, 
        report_content: ReportContent, 
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF version of the report
        
        Args:
            report_content: The report content to convert to PDF
            output_path: Optional file path to save PDF
            
        Returns:
            bytes: PDF content as bytes
        """
        logger.info(f"Generating PDF for report: {report_content.title}")
        
        try:
            # Import PDF service here to avoid circular imports
            from .pdf_service import PDFService
            
            pdf_service = PDFService()
            
            # Convert ReportContent to dictionary format
            report_dict = self._convert_report_content_to_dict(report_content)
            
            pdf_bytes = pdf_service.generate_pdf(report_dict, output_path)
            
            # Validate PDF quality
            validation_results = pdf_service.validate_pdf_quality(pdf_bytes)
            
            if validation_results["quality_score"] < 0.5:
                logger.warning(f"PDF quality score is low: {validation_results['quality_score']}")
                logger.warning(f"Issues found: {validation_results['issues']}")
            
            logger.info(f"PDF generated successfully ({len(pdf_bytes)} bytes, quality: {validation_results['quality_score']:.2f})")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}")
            raise
    
    def _convert_report_content_to_dict(self, report_content: ReportContent) -> Dict[str, Any]:
        """Convert ReportContent object to dictionary for PDF service"""
        return {
            "title": report_content.title,
            "client_name": report_content.client_name,
            "generation_date": report_content.generation_date.isoformat() if hasattr(report_content.generation_date, 'isoformat') else str(report_content.generation_date),
            "template_type": report_content.template_type.value if hasattr(report_content.template_type, 'value') else str(report_content.template_type),
            "schema_type": report_content.schema_type.value if hasattr(report_content.schema_type, 'value') else str(report_content.schema_type),
            "executive_summary": report_content.executive_summary,
            "sections": [self._convert_section_to_dict(section) for section in report_content.sections],
            "metadata": report_content.metadata
        }
    
    def _convert_section_to_dict(self, section: ReportSection) -> Dict[str, Any]:
        """Convert ReportSection object to dictionary"""
        return {
            "id": section.id,
            "title": section.title,
            "content": section.content,
            "subsections": [self._convert_section_to_dict(subsection) for subsection in section.subsections],
            "metadata": section.metadata,
            "sources": section.sources
        }
    
    async def generate_complete_report_with_pdf(
        self,
        requirements_id: str,
        template_type: ReportTemplate = ReportTemplate.EU_ESRS_STANDARD,
        ai_model: AIModelType = AIModelType.OPENAI_GPT35,
        include_pdf: bool = True,
        pdf_output_path: Optional[str] = None
    ) -> Tuple[ReportContent, Optional[bytes]]:
        """
        Generate complete report with optional PDF output
        
        Args:
            requirements_id: ID of the client requirements
            template_type: Type of report template to use
            ai_model: AI model for generating content
            include_pdf: Whether to generate PDF version
            pdf_output_path: Optional file path to save PDF
            
        Returns:
            Tuple of (ReportContent, PDF bytes or None)
        """
        logger.info(f"Generating complete report with PDF for requirements {requirements_id}")
        
        # Generate report content
        report_content = await self.generate_report(
            requirements_id=requirements_id,
            template_type=template_type,
            ai_model=ai_model
        )
        
        # Generate PDF if requested
        pdf_bytes = None
        if include_pdf:
            pdf_bytes = self.generate_pdf_report(report_content, pdf_output_path)
        
        return report_content, pdf_bytes
    
    def validate_pdf_quality(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Validate PDF quality and formatting
        
        Args:
            pdf_bytes: PDF content as bytes
            
        Returns:
            Dict with validation results
        """
        from .pdf_service import PDFService
        pdf_service = PDFService()
        return pdf_service.validate_pdf_quality(pdf_bytes)