"""
Report Generation API endpoints
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
import asyncio

from ..models.database_config import get_db
from ..models.schemas import SchemaType
from ..services.report_service import (
    ReportService, ReportTemplate, ReportFormat, AIModelType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_available_templates(
    db: Session = Depends(get_db)
):
    """Get list of available report templates"""
    try:
        report_service = ReportService(db)
        templates = report_service.template_manager.get_available_templates()
        return templates
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_type}", response_model=Dict[str, Any])
async def get_template_details(
    template_type: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific template"""
    try:
        # Convert string to enum
        template_enum = None
        for template in ReportTemplate:
            if template.value == template_type:
                template_enum = template
                break
        
        if not template_enum:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_type}")
        
        report_service = ReportService(db)
        template_config = report_service.template_manager.get_template(template_enum)
        
        if not template_config:
            raise HTTPException(status_code=404, detail=f"Template configuration not found: {template_type}")
        
        return {
            "type": template_type,
            "config": template_config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=Dict[str, Any])
async def generate_report(
    requirements_id: str,
    template_type: str = Query(default="eu_esrs_standard", description="Report template type"),
    ai_model: str = Query(default="openai_gpt35", description="AI model to use"),
    report_format: str = Query(default="structured_text", description="Output format"),
    db: Session = Depends(get_db)
):
    """Generate a sustainability report based on client requirements"""
    try:
        # Convert string parameters to enums
        template_enum = None
        for template in ReportTemplate:
            if template.value == template_type:
                template_enum = template
                break
        
        if not template_enum:
            raise HTTPException(status_code=400, detail=f"Invalid template type: {template_type}")
        
        ai_model_enum = None
        for model in AIModelType:
            if model.value == ai_model:
                ai_model_enum = model
                break
        
        if not ai_model_enum:
            raise HTTPException(status_code=400, detail=f"Invalid AI model: {ai_model}")
        
        format_enum = None
        for fmt in ReportFormat:
            if fmt.value == report_format:
                format_enum = fmt
                break
        
        if not format_enum:
            raise HTTPException(status_code=400, detail=f"Invalid report format: {report_format}")
        
        # Generate report
        report_service = ReportService(db)
        report_content = await report_service.generate_report(
            requirements_id=requirements_id,
            template_type=template_enum,
            ai_model=ai_model_enum,
            report_format=format_enum
        )
        
        # Format the report
        formatted_report = report_service.format_report(report_content, format_enum)
        
        # Get metadata
        metadata = report_service.get_report_metadata(report_content)
        
        return {
            "report_content": formatted_report,
            "metadata": metadata,
            "raw_content": report_content.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-async", response_model=Dict[str, str])
async def generate_report_async(
    requirements_id: str,
    template_type: str = Query(default="eu_esrs_standard", description="Report template type"),
    ai_model: str = Query(default="openai_gpt35", description="AI model to use"),
    report_format: str = Query(default="structured_text", description="Output format"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Generate a sustainability report asynchronously"""
    try:
        # Convert string parameters to enums (same validation as sync version)
        template_enum = None
        for template in ReportTemplate:
            if template.value == template_type:
                template_enum = template
                break
        
        if not template_enum:
            raise HTTPException(status_code=400, detail=f"Invalid template type: {template_type}")
        
        ai_model_enum = None
        for model in AIModelType:
            if model.value == ai_model:
                ai_model_enum = model
                break
        
        if not ai_model_enum:
            raise HTTPException(status_code=400, detail=f"Invalid AI model: {ai_model}")
        
        format_enum = None
        for fmt in ReportFormat:
            if fmt.value == report_format:
                format_enum = fmt
                break
        
        if not format_enum:
            raise HTTPException(status_code=400, detail=f"Invalid report format: {report_format}")
        
        # Generate task ID
        import time
        task_id = f"report_{int(time.time())}_{hash(requirements_id) % 10000}"
        
        # Add background task
        background_tasks.add_task(
            _generate_report_background,
            task_id,
            requirements_id,
            template_enum,
            ai_model_enum,
            format_enum
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Report generation started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start async report generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_report_background(
    task_id: str,
    requirements_id: str,
    template_type: ReportTemplate,
    ai_model: AIModelType,
    report_format: ReportFormat
):
    """Background task for report generation"""
    try:
        logger.info(f"Starting background report generation for task {task_id}")
        
        # Note: In a production system, you would use a proper task queue like Celery
        # and store task status in a database or cache
        
        # For now, we'll just log the completion
        # In a real implementation, you would:
        # 1. Create a new database session
        # 2. Generate the report
        # 3. Store the result somewhere accessible
        # 4. Update task status
        
        logger.info(f"Background report generation completed for task {task_id}")
        
    except Exception as e:
        logger.error(f"Background report generation failed for task {task_id}: {str(e)}")


@router.get("/formats", response_model=List[Dict[str, str]])
async def get_available_formats():
    """Get list of available report formats"""
    try:
        formats = []
        for fmt in ReportFormat:
            formats.append({
                "value": fmt.value,
                "name": fmt.value.replace("_", " ").title(),
                "description": _get_format_description(fmt)
            })
        return formats
    except Exception as e:
        logger.error(f"Failed to get formats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_format_description(format_type: ReportFormat) -> str:
    """Get description for report format"""
    descriptions = {
        ReportFormat.STRUCTURED_TEXT: "Plain text with structured formatting",
        ReportFormat.MARKDOWN: "Markdown format suitable for documentation",
        ReportFormat.HTML: "HTML format for web display"
    }
    return descriptions.get(format_type, "Unknown format")


@router.get("/ai-models", response_model=List[Dict[str, Any]])
async def get_available_ai_models(
    db: Session = Depends(get_db)
):
    """Get list of available AI models for report generation"""
    try:
        report_service = ReportService(db)
        models = report_service.rag_service.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get AI models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{requirements_id}", response_model=Dict[str, Any])
async def preview_report_structure(
    requirements_id: str,
    template_type: str = Query(default="eu_esrs_standard", description="Report template type"),
    db: Session = Depends(get_db)
):
    """Preview report structure without generating full content"""
    try:
        # Convert template type
        template_enum = None
        for template in ReportTemplate:
            if template.value == template_type:
                template_enum = template
                break
        
        if not template_enum:
            raise HTTPException(status_code=400, detail=f"Invalid template type: {template_type}")
        
        report_service = ReportService(db)
        
        # Get client requirements
        client_requirements = report_service.client_requirements_service.get_client_requirements(requirements_id)
        if not client_requirements:
            raise HTTPException(status_code=404, detail=f"Client requirements not found: {requirements_id}")
        
        # Get template configuration
        template_config = report_service.template_manager.get_template(template_enum)
        if not template_config:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_type}")
        
        # Create preview structure
        preview = {
            "client_name": client_requirements.client_name,
            "template_type": template_type,
            "template_name": template_config.get("name", ""),
            "sections": []
        }
        
        # Add section previews
        for section_config in template_config.get("sections", []):
            section_preview = {
                "id": section_config.get("id", ""),
                "title": section_config.get("title", ""),
                "required": section_config.get("required", False),
                "description": section_config.get("description", ""),
                "subsections": []
            }
            
            # Add subsection previews
            for subsection_config in section_config.get("subsections", []):
                subsection_preview = {
                    "id": subsection_config.get("id", ""),
                    "title": subsection_config.get("title", "")
                }
                section_preview["subsections"].append(subsection_preview)
            
            preview["sections"].append(section_preview)
        
        # Find relevant requirements for preview
        relevant_requirements = []
        if client_requirements.processed_requirements:
            for req in client_requirements.processed_requirements[:5]:  # Show top 5
                relevant_requirements.append({
                    "id": req.get("requirement_id", ""),
                    "text": req.get("requirement_text", "")[:200] + "..." if len(req.get("requirement_text", "")) > 200 else req.get("requirement_text", ""),
                    "priority": req.get("priority", "medium")
                })
        
        preview["relevant_requirements"] = relevant_requirements
        
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview report structure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-requirements/{requirements_id}", response_model=Dict[str, Any])
async def validate_requirements_for_report(
    requirements_id: str,
    template_type: str = Query(default="eu_esrs_standard", description="Report template type"),
    db: Session = Depends(get_db)
):
    """Validate if client requirements are sufficient for report generation"""
    try:
        report_service = ReportService(db)
        
        # Get client requirements
        client_requirements = report_service.client_requirements_service.get_client_requirements(requirements_id)
        if not client_requirements:
            raise HTTPException(status_code=404, detail=f"Client requirements not found: {requirements_id}")
        
        # Perform gap analysis
        gap_analysis = report_service.client_requirements_service.perform_gap_analysis(requirements_id)
        
        # Determine validation status
        coverage_percentage = gap_analysis.get("coverage_percentage", 0)
        
        validation_result = {
            "requirements_id": requirements_id,
            "template_type": template_type,
            "validation_status": "unknown",
            "coverage_percentage": coverage_percentage,
            "recommendations": [],
            "warnings": [],
            "gap_analysis": gap_analysis
        }
        
        # Determine validation status
        if coverage_percentage >= 80:
            validation_result["validation_status"] = "excellent"
            validation_result["recommendations"].append("Requirements are well-covered. Report generation should produce comprehensive results.")
        elif coverage_percentage >= 60:
            validation_result["validation_status"] = "good"
            validation_result["recommendations"].append("Requirements have good coverage. Some sections may have limited content.")
        elif coverage_percentage >= 40:
            validation_result["validation_status"] = "fair"
            validation_result["warnings"].append("Limited coverage detected. Consider uploading additional regulatory documents.")
            validation_result["recommendations"].append("Report generation is possible but may have gaps in some sections.")
        else:
            validation_result["validation_status"] = "poor"
            validation_result["warnings"].append("Low coverage detected. Report quality may be significantly impacted.")
            validation_result["recommendations"].append("Upload additional regulatory documents before generating report.")
        
        # Add specific warnings
        uncovered_requirements = gap_analysis.get("gaps", {}).get("uncovered_requirements", [])
        if uncovered_requirements:
            high_priority_uncovered = [req for req in uncovered_requirements if req.get("priority") == "high"]
            if high_priority_uncovered:
                validation_result["warnings"].append(f"{len(high_priority_uncovered)} high-priority requirements have no coverage.")
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf_report(
    requirements_id: str,
    template_type: str = Query(default="eu_esrs_standard", description="Report template type"),
    ai_model: str = Query(default="openai_gpt35", description="AI model to use"),
    download: bool = Query(default=True, description="Return as downloadable file"),
    db: Session = Depends(get_db)
):
    """Generate a PDF report based on client requirements"""
    try:
        # Convert string parameters to enums
        template_enum = None
        for template in ReportTemplate:
            if template.value == template_type:
                template_enum = template
                break
        
        if not template_enum:
            raise HTTPException(status_code=400, detail=f"Invalid template type: {template_type}")
        
        ai_model_enum = None
        for model in AIModelType:
            if model.value == ai_model:
                ai_model_enum = model
                break
        
        if not ai_model_enum:
            raise HTTPException(status_code=400, detail=f"Invalid AI model: {ai_model}")
        
        # Generate report with PDF
        report_service = ReportService(db)
        report_content, pdf_bytes = await report_service.generate_complete_report_with_pdf(
            requirements_id=requirements_id,
            template_type=template_enum,
            ai_model=ai_model_enum,
            include_pdf=True
        )
        
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Validate PDF quality
        validation_results = report_service.validate_pdf_quality(pdf_bytes)
        
        if download:
            # Return PDF as downloadable file
            filename = f"sustainability_report_{report_content.client_name}_{report_content.generation_date.strftime('%Y%m%d')}.pdf"
            filename = filename.replace(" ", "_").replace("/", "_")
            
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(pdf_bytes))
                }
            )
        else:
            # Return PDF metadata and validation results
            return {
                "pdf_generated": True,
                "pdf_size_bytes": len(pdf_bytes),
                "validation_results": validation_results,
                "report_metadata": report_service.get_report_metadata(report_content),
                "message": "PDF generated successfully. Use download=true to get the file."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-complete")
async def generate_complete_report(
    requirements_id: str,
    template_type: str = Query(default="eu_esrs_standard", description="Report template type"),
    ai_model: str = Query(default="openai_gpt35", description="AI model to use"),
    report_format: str = Query(default="structured_text", description="Text output format"),
    include_pdf: bool = Query(default=True, description="Include PDF generation"),
    db: Session = Depends(get_db)
):
    """Generate complete report with both text and PDF formats"""
    try:
        # Convert string parameters to enums
        template_enum = None
        for template in ReportTemplate:
            if template.value == template_type:
                template_enum = template
                break
        
        if not template_enum:
            raise HTTPException(status_code=400, detail=f"Invalid template type: {template_type}")
        
        ai_model_enum = None
        for model in AIModelType:
            if model.value == ai_model:
                ai_model_enum = model
                break
        
        if not ai_model_enum:
            raise HTTPException(status_code=400, detail=f"Invalid AI model: {ai_model}")
        
        format_enum = None
        for fmt in ReportFormat:
            if fmt.value == report_format:
                format_enum = fmt
                break
        
        if not format_enum:
            raise HTTPException(status_code=400, detail=f"Invalid report format: {report_format}")
        
        # Generate complete report
        report_service = ReportService(db)
        report_content, pdf_bytes = await report_service.generate_complete_report_with_pdf(
            requirements_id=requirements_id,
            template_type=template_enum,
            ai_model=ai_model_enum,
            include_pdf=include_pdf
        )
        
        # Format the text report
        formatted_report = report_service.format_report(report_content, format_enum)
        
        # Get metadata
        metadata = report_service.get_report_metadata(report_content)
        
        # Prepare response
        response_data = {
            "report_content": formatted_report,
            "metadata": metadata,
            "raw_content": report_content.to_dict(),
            "pdf_generated": pdf_bytes is not None
        }
        
        # Add PDF information if generated
        if pdf_bytes:
            validation_results = report_service.validate_pdf_quality(pdf_bytes)
            response_data.update({
                "pdf_size_bytes": len(pdf_bytes),
                "pdf_validation": validation_results,
                "pdf_download_url": f"/reports/download-pdf/{requirements_id}?template_type={template_type}&ai_model={ai_model}"
            })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate complete report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-pdf/{requirements_id}")
async def download_pdf_report(
    requirements_id: str,
    template_type: str = Query(default="eu_esrs_standard", description="Report template type"),
    ai_model: str = Query(default="openai_gpt35", description="AI model to use"),
    db: Session = Depends(get_db)
):
    """Download a previously generated PDF report"""
    try:
        # Note: In a production system, you would cache generated PDFs
        # For now, we regenerate the PDF each time
        
        # Convert string parameters to enums
        template_enum = None
        for template in ReportTemplate:
            if template.value == template_type:
                template_enum = template
                break
        
        if not template_enum:
            raise HTTPException(status_code=400, detail=f"Invalid template type: {template_type}")
        
        ai_model_enum = None
        for model in AIModelType:
            if model.value == ai_model:
                ai_model_enum = model
                break
        
        if not ai_model_enum:
            raise HTTPException(status_code=400, detail=f"Invalid AI model: {ai_model}")
        
        # Generate report with PDF
        report_service = ReportService(db)
        report_content, pdf_bytes = await report_service.generate_complete_report_with_pdf(
            requirements_id=requirements_id,
            template_type=template_enum,
            ai_model=ai_model_enum,
            include_pdf=True
        )
        
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Create filename
        filename = f"sustainability_report_{report_content.client_name}_{report_content.generation_date.strftime('%Y%m%d')}.pdf"
        filename = filename.replace(" ", "_").replace("/", "_")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-pdf")
async def validate_pdf_quality(
    pdf_file: bytes,
    db: Session = Depends(get_db)
):
    """Validate PDF quality and formatting consistency"""
    try:
        report_service = ReportService(db)
        validation_results = report_service.validate_pdf_quality(pdf_file)
        
        return {
            "validation_results": validation_results,
            "recommendations": _get_pdf_quality_recommendations(validation_results)
        }
        
    except Exception as e:
        logger.error(f"Failed to validate PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_pdf_quality_recommendations(validation_results: Dict[str, Any]) -> List[str]:
    """Get recommendations based on PDF validation results"""
    recommendations = []
    
    quality_score = validation_results.get("quality_score", 0)
    issues = validation_results.get("issues", [])
    
    if quality_score < 0.5:
        recommendations.append("PDF quality is below acceptable standards. Consider regenerating the report.")
    
    if quality_score < 0.8:
        recommendations.append("PDF quality could be improved. Review content and formatting.")
    
    for issue in issues:
        if "size too small" in issue:
            recommendations.append("PDF appears to have insufficient content. Verify report generation completed successfully.")
        elif "size too large" in issue:
            recommendations.append("PDF file size is very large. Consider optimizing images or content.")
        elif "lacks expected content" in issue:
            recommendations.append("PDF may be missing expected sustainability report content.")
    
    if not recommendations:
        recommendations.append("PDF quality is acceptable for distribution.")
    
    return recommendations