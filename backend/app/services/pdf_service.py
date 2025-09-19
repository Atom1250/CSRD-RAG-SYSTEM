"""
PDF Generation Service for creating professional sustainability reports
using HTML to PDF conversion with WeasyPrint as fallback to ReportLab.
"""
import io
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import re
import html

logger = logging.getLogger(__name__)


@dataclass
class PDFStyle:
    """PDF styling configuration"""
    font_family: str = "Arial, sans-serif"
    title_size: str = "24px"
    heading1_size: str = "20px"
    heading2_size: str = "16px"
    heading3_size: str = "14px"
    body_size: str = "11px"
    caption_size: str = "9px"
    line_height: str = "1.4"
    margin: str = "2cm"
    primary_color: str = "#1f4e79"
    secondary_color: str = "#2e75b6"


@dataclass
class Citation:
    """Citation data structure"""
    id: str
    title: str
    source: str
    page: Optional[int] = None
    url: Optional[str] = None
    access_date: Optional[datetime] = None
    
    def format_citation(self) -> str:
        """Format citation in standard format"""
        citation_parts = [self.title]
        if self.source:
            citation_parts.append(self.source)
        if self.page:
            citation_parts.append(f"p. {self.page}")
        if self.url:
            citation_parts.append(f"Available at: {self.url}")
        if self.access_date:
            citation_parts.append(f"Accessed: {self.access_date.strftime('%Y-%m-%d')}")
        
        return ". ".join(citation_parts) + "."


class PDFService:
    """Service for generating professional PDF reports using HTML conversion"""
    
    def __init__(self):
        self.style = PDFStyle()
        self.citations: List[Citation] = []
        self.citation_counter = 0
        
        # Try to import PDF libraries
        self.weasyprint_available = self._check_weasyprint()
        self.reportlab_available = self._check_reportlab()
        
        if not self.weasyprint_available and not self.reportlab_available:
            logger.warning("No PDF generation libraries available. PDF generation will be limited.")
    
    def _check_weasyprint(self) -> bool:
        """Check if WeasyPrint is available"""
        try:
            import weasyprint
            return True
        except ImportError:
            return False
    
    def _check_reportlab(self) -> bool:
        """Check if ReportLab is available"""
        try:
            import reportlab
            return True
        except ImportError:
            return False
    
    def generate_pdf(self, report_content: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
        """
        Generate a professional PDF report from report content
        
        Args:
            report_content: Dictionary containing report data
            output_path: Optional file path to save PDF
            
        Returns:
            bytes: PDF content as bytes
        """
        logger.info(f"Generating PDF for report: {report_content.get('title', 'Unknown')}")
        
        # Reset citations for this report
        self.citations = []
        self.citation_counter = 0
        
        # Generate HTML content
        html_content = self._generate_html_report(report_content)
        
        # Convert HTML to PDF
        if self.weasyprint_available:
            pdf_bytes = self._generate_pdf_with_weasyprint(html_content)
        elif self.reportlab_available:
            pdf_bytes = self._generate_pdf_with_reportlab(html_content, report_content)
        else:
            # Fallback: create a simple text-based PDF
            pdf_bytes = self._generate_simple_pdf(report_content)
        
        # Save to file if path provided
        if output_path and pdf_bytes:
            try:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                logger.info(f"PDF saved to: {output_path}")
            except Exception as e:
                logger.error(f"Failed to save PDF to {output_path}: {str(e)}")
        
        logger.info(f"PDF generated successfully ({len(pdf_bytes) if pdf_bytes else 0} bytes)")
        return pdf_bytes or b""
    
    def _generate_html_report(self, report_content: Dict[str, Any]) -> str:
        """Generate HTML content for the report"""
        html_parts = []
        
        # HTML header with CSS
        html_parts.append(self._get_html_header())
        
        # Title page
        html_parts.append(self._create_html_title_page(report_content))
        
        # Table of contents
        html_parts.append(self._create_html_toc(report_content))
        
        # Executive summary
        if report_content.get('executive_summary'):
            html_parts.append(self._create_html_executive_summary(report_content['executive_summary']))
        
        # Report sections
        sections = report_content.get('sections', [])
        for section in sections:
            html_parts.append(self._create_html_section(section, level=1))
        
        # Bibliography
        if self.citations:
            html_parts.append(self._create_html_bibliography())
        
        # HTML footer
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)
    
    def _get_html_header(self) -> str:
        """Generate HTML header with CSS styling"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sustainability Report</title>
    <style>
        @page {{
            size: A4;
            margin: {self.style.margin};
            @top-center {{
                content: "Sustainability Report";
                font-size: 10px;
                color: #666;
            }}
            @bottom-center {{
                content: "Page " counter(page);
                font-size: 10px;
                color: #666;
            }}
        }}
        
        body {{
            font-family: {self.style.font_family};
            font-size: {self.style.body_size};
            line-height: {self.style.line_height};
            color: #333;
            margin: 0;
            padding: 0;
        }}
        
        .title-page {{
            text-align: center;
            padding: 3cm 0;
            page-break-after: always;
        }}
        
        .main-title {{
            font-size: {self.style.title_size};
            font-weight: bold;
            color: {self.style.primary_color};
            margin-bottom: 1cm;
            line-height: 1.2;
        }}
        
        .client-info {{
            font-size: {self.style.heading2_size};
            margin-bottom: 2cm;
        }}
        
        .metadata {{
            font-size: {self.style.body_size};
            text-align: left;
            display: inline-block;
            margin-bottom: 2cm;
        }}
        
        .disclaimer {{
            font-size: {self.style.caption_size};
            color: #666;
            font-style: italic;
            margin-top: 2cm;
        }}
        
        h1 {{
            font-size: {self.style.heading1_size};
            color: {self.style.primary_color};
            font-weight: bold;
            margin-top: 2em;
            margin-bottom: 1em;
            page-break-after: avoid;
        }}
        
        h2 {{
            font-size: {self.style.heading2_size};
            color: {self.style.secondary_color};
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            page-break-after: avoid;
        }}
        
        h3 {{
            font-size: {self.style.heading3_size};
            color: {self.style.secondary_color};
            font-weight: bold;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
            page-break-after: avoid;
        }}
        
        p {{
            margin-bottom: 1em;
            text-align: justify;
        }}
        
        ul, ol {{
            margin-bottom: 1em;
            padding-left: 2em;
        }}
        
        li {{
            margin-bottom: 0.5em;
        }}
        
        .toc {{
            page-break-after: always;
        }}
        
        .toc-title {{
            font-size: {self.style.heading1_size};
            color: {self.style.primary_color};
            font-weight: bold;
            margin-bottom: 1em;
        }}
        
        .toc-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5em;
            border-bottom: 1px dotted #ccc;
            padding-bottom: 0.2em;
        }}
        
        .toc-item.level-2 {{
            margin-left: 1em;
            font-size: 0.9em;
        }}
        
        .section {{
            page-break-inside: avoid;
            margin-bottom: 2em;
        }}
        
        .section.level-1 {{
            page-break-before: always;
        }}
        
        .citation {{
            font-size: {self.style.caption_size};
            color: #666;
            font-style: italic;
            margin-top: 0.5em;
        }}
        
        .bibliography {{
            page-break-before: always;
        }}
        
        .bibliography-item {{
            margin-bottom: 1em;
            text-indent: -2em;
            padding-left: 2em;
        }}
        
        .executive-summary {{
            page-break-after: always;
            background-color: #f8f9fa;
            padding: 1em;
            border-left: 4px solid {self.style.primary_color};
        }}
        
        strong {{
            font-weight: bold;
        }}
        
        em {{
            font-style: italic;
        }}
        
        .highlight {{
            background-color: #fff3cd;
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
"""
    
    def _create_html_title_page(self, report_content: Dict[str, Any]) -> str:
        """Create HTML title page"""
        title = html.escape(report_content.get('title', 'Sustainability Report'))
        client_name = html.escape(report_content.get('client_name', 'Unknown Client'))
        
        # Parse generation date
        generation_date = report_content.get('generation_date')
        if isinstance(generation_date, str):
            try:
                generation_date = datetime.fromisoformat(generation_date.replace('Z', '+00:00'))
            except:
                generation_date = datetime.now()
        elif not isinstance(generation_date, datetime):
            generation_date = datetime.now()
        
        template_type = report_content.get('template_type', 'standard').replace('_', ' ').title()
        schema_type = report_content.get('schema_type', 'unknown').replace('_', ' ').upper()
        
        return f"""
<div class="title-page">
    <div class="main-title">{title}</div>
    <div class="client-info"><strong>Prepared for:</strong> {client_name}</div>
    
    <div class="metadata">
        <p><strong>Report Type:</strong> {template_type}</p>
        <p><strong>Schema Standard:</strong> {schema_type}</p>
        <p><strong>Generation Date:</strong> {generation_date.strftime('%B %d, %Y')}</p>
    </div>
    
    <div class="disclaimer">
        <strong>Disclaimer:</strong> This report has been generated using artificial intelligence 
        and automated analysis of regulatory documents. While every effort has been made 
        to ensure accuracy, this report should be reviewed by qualified professionals 
        before use for compliance purposes.
    </div>
</div>
"""
    
    def _create_html_toc(self, report_content: Dict[str, Any]) -> str:
        """Create HTML table of contents"""
        toc_items = []
        
        if report_content.get('executive_summary'):
            toc_items.append('<div class="toc-item"><span>Executive Summary</span><span>3</span></div>')
        
        sections = report_content.get('sections', [])
        page_num = 4
        
        for section in sections:
            section_title = html.escape(section.get('title', 'Untitled Section'))
            toc_items.append(f'<div class="toc-item"><span>{section_title}</span><span>{page_num}</span></div>')
            page_num += 1
            
            # Add subsections
            for subsection in section.get('subsections', []):
                subsection_title = html.escape(subsection.get('title', 'Untitled Subsection'))
                toc_items.append(f'<div class="toc-item level-2"><span>{subsection_title}</span><span>{page_num}</span></div>')
        
        if self.citations:
            toc_items.append(f'<div class="toc-item"><span>Bibliography</span><span>{page_num + 1}</span></div>')
        
        return f"""
<div class="toc">
    <div class="toc-title">Table of Contents</div>
    {''.join(toc_items)}
</div>
"""
    
    def _create_html_executive_summary(self, executive_summary: str) -> str:
        """Create HTML executive summary"""
        formatted_summary = self._process_markdown_to_html(executive_summary)
        
        return f"""
<div class="executive-summary">
    <h1>Executive Summary</h1>
    {formatted_summary}
</div>
"""
    
    def _create_html_section(self, section: Dict[str, Any], level: int = 1) -> str:
        """Create HTML section content"""
        section_id = section.get('id', 'section')
        section_title = html.escape(section.get('title', 'Untitled Section'))
        section_content = section.get('content', '')
        
        # Process content
        formatted_content = self._process_markdown_to_html(section_content)
        
        # Process sources and create citations
        sources = section.get('sources', [])
        citation_html = ""
        if sources:
            citations = self._process_section_sources(sources)
            if citations:
                citation_html = '<div class="citation">' + '<br>'.join(citations) + '</div>'
        
        # Create subsections
        subsections_html = ""
        for subsection in section.get('subsections', []):
            subsections_html += self._create_html_section(subsection, level + 1)
        
        # Determine heading level
        heading_tag = f"h{min(level, 3)}"
        section_class = f"section level-{level}"
        
        return f"""
<div class="{section_class}">
    <{heading_tag}>{section_title}</{heading_tag}>
    {formatted_content}
    {citation_html}
    {subsections_html}
</div>
"""
    
    def _create_html_bibliography(self) -> str:
        """Create HTML bibliography"""
        bibliography_items = []
        
        for i, citation in enumerate(self.citations, 1):
            citation_text = f"[{i}] {citation.format_citation()}"
            bibliography_items.append(f'<div class="bibliography-item">{html.escape(citation_text)}</div>')
        
        return f"""
<div class="bibliography">
    <h1>Bibliography</h1>
    {''.join(bibliography_items)}
</div>
"""
    
    def _process_markdown_to_html(self, text: str) -> str:
        """Convert markdown-like text to HTML"""
        if not text:
            return ""
        
        # Escape HTML first
        text = html.escape(text)
        
        # Convert markdown headers (process in order from most specific to least)
        text = re.sub(r'^\s*### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # Convert markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Convert lists (handle both bullet and numbered)
        text = re.sub(r'^\s*- (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\. (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        
        # Wrap consecutive list items in ul tags
        text = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul>\1</ul>', text, flags=re.DOTALL)
        
        # Convert paragraphs - split by double newlines and wrap non-HTML content
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Don't wrap if it's already HTML (starts with < or contains HTML tags)
                if not (para.startswith('<') or '</' in para):
                    # Handle single line breaks within paragraphs
                    para = para.replace('\n', '<br>')
                    para = f'<p>{para}</p>'
                formatted_paragraphs.append(para)
        
        return '\n'.join(formatted_paragraphs)
    
    def _process_section_sources(self, sources: List[str]) -> List[str]:
        """Process section sources and create citations"""
        citations = []
        
        for source in sources:
            # Create citation object
            self.citation_counter += 1
            citation = Citation(
                id=f"ref_{self.citation_counter}",
                title=f"Source Document {self.citation_counter}",
                source=source,
                access_date=datetime.now()
            )
            
            self.citations.append(citation)
            
            # Format inline citation
            inline_citation = f"[{self.citation_counter}] {html.escape(source)}"
            citations.append(inline_citation)
        
        return citations
    
    def _generate_pdf_with_weasyprint(self, html_content: str) -> bytes:
        """Generate PDF using WeasyPrint"""
        try:
            import weasyprint
            
            # Create PDF from HTML
            pdf_document = weasyprint.HTML(string=html_content)
            pdf_bytes = pdf_document.write_pdf()
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"WeasyPrint PDF generation failed: {str(e)}")
            return b""
    
    def _generate_pdf_with_reportlab(self, html_content: str, report_content: Dict[str, Any]) -> bytes:
        """Generate PDF using ReportLab (simplified version)"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title = report_content.get('title', 'Sustainability Report')
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 20))
            
            # Add basic content (simplified)
            if report_content.get('executive_summary'):
                story.append(Paragraph("Executive Summary", styles['Heading1']))
                story.append(Paragraph(report_content['executive_summary'], styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Add sections
            for section in report_content.get('sections', []):
                story.append(Paragraph(section.get('title', 'Section'), styles['Heading1']))
                if section.get('content'):
                    story.append(Paragraph(section['content'], styles['Normal']))
                story.append(Spacer(1, 20))
            
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"ReportLab PDF generation failed: {str(e)}")
            return b""
    
    def _generate_simple_pdf(self, report_content: Dict[str, Any]) -> bytes:
        """Generate a simple text-based PDF when no libraries are available"""
        # Create a minimal PDF structure
        title = report_content.get('title', 'Sustainability Report')
        client_name = report_content.get('client_name', 'Unknown Client')
        
        # This is a very basic PDF structure - in production you'd want proper PDF generation
        pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
50 750 Td
({title}) Tj
0 -20 Td
(Client: {client_name}) Tj
0 -20 Td
(Generated: {datetime.now().strftime('%Y-%m-%d')}) Tj
0 -40 Td
(This is a simplified PDF. Please install WeasyPrint or ReportLab for full functionality.) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000110 00000 n 
0000000251 00000 n 
0000000504 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
581
%%EOF"""
        
        return pdf_content.encode('utf-8')
    
    def validate_pdf_quality(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Validate PDF quality and formatting consistency
        
        Args:
            pdf_bytes: PDF content as bytes
            
        Returns:
            Dict with validation results
        """
        validation_results = {
            "file_size_bytes": len(pdf_bytes),
            "is_valid_pdf": False,
            "has_content": False,
            "estimated_pages": 0,
            "quality_score": 0.0,
            "issues": []
        }
        
        try:
            # Basic PDF validation
            if pdf_bytes.startswith(b'%PDF-'):
                validation_results["is_valid_pdf"] = True
            else:
                validation_results["issues"].append("Invalid PDF format")
                return validation_results
            
            # Check file size (reasonable range)
            file_size_kb = len(pdf_bytes) / 1024
            if file_size_kb < 1:
                validation_results["issues"].append("PDF file size too small (< 1KB)")
            elif file_size_kb > 50000:  # 50MB
                validation_results["issues"].append("PDF file size too large (> 50MB)")
            
            # Estimate page count based on file size (rough heuristic)
            validation_results["estimated_pages"] = max(1, int(file_size_kb / 50))
            
            # Check for content indicators
            pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
            if any(keyword in pdf_text for keyword in ['Sustainability', 'Report', 'ESRS', 'CSRD']):
                validation_results["has_content"] = True
            else:
                validation_results["issues"].append("PDF appears to lack expected content")
            
            # Calculate quality score
            quality_factors = []
            
            # File size factor (optimal range 10KB - 10MB)
            if 10 <= file_size_kb <= 10000:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.5)
            
            # Content factor
            quality_factors.append(1.0 if validation_results["has_content"] else 0.0)
            
            # Format factor
            quality_factors.append(1.0 if validation_results["is_valid_pdf"] else 0.0)
            
            validation_results["quality_score"] = sum(quality_factors) / len(quality_factors)
            
            logger.info(f"PDF validation completed: {validation_results['quality_score']:.2f} quality score")
            
        except Exception as e:
            logger.error(f"PDF validation failed: {str(e)}")
            validation_results["issues"].append(f"Validation error: {str(e)}")
        
        return validation_results


# Utility functions for PDF generation
def create_pdf_from_report(report_content: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
    """
    Convenience function to create PDF from report content
    
    Args:
        report_content: Dictionary containing report data
        output_path: Optional file path to save PDF
        
    Returns:
        bytes: PDF content as bytes
    """
    pdf_service = PDFService()
    return pdf_service.generate_pdf(report_content, output_path)


def validate_pdf_output(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Convenience function to validate PDF output
    
    Args:
        pdf_bytes: PDF content as bytes
        
    Returns:
        Dict with validation results
    """
    pdf_service = PDFService()
    return pdf_service.validate_pdf_quality(pdf_bytes)