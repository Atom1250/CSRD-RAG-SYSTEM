import api from './api';

export interface ClientRequirement {
  id: string;
  client_name: string;
  requirements_text: string;
  schema_type: 'eu_esrs_csrd' | 'uk_srd';
  upload_date: string;
  processed_requirements: ProcessedRequirement[];
  schema_mappings: SchemaMapping[];
}

export interface ProcessedRequirement {
  requirement_id: string;
  requirement_text: string;
  priority: 'high' | 'medium' | 'low';
  schema_elements: string[];
}

export interface SchemaMapping {
  requirement_id: string;
  schema_element_id: string;
  confidence_score: number;
  mapping_type: 'automatic' | 'manual';
}

export interface ReportTemplate {
  type: string;
  name: string;
  description: string;
  sections: ReportSection[];
}

export interface ReportSection {
  id: string;
  title: string;
  required: boolean;
  description: string;
  subsections: ReportSubsection[];
}

export interface ReportSubsection {
  id: string;
  title: string;
}

export interface ReportGenerationRequest {
  requirements_id: string;
  template_type: string;
  ai_model: string;
  report_format: string;
  include_pdf: boolean;
}

export interface ReportGenerationResponse {
  report_content: string;
  metadata: ReportMetadata;
  pdf_generated: boolean;
  pdf_size_bytes?: number;
  pdf_download_url?: string;
}

export interface ReportMetadata {
  client_name: string;
  generation_date: string;
  template_type: string;
  ai_model: string;
  total_sections: number;
  word_count: number;
  source_documents_count: number;
}

export interface ReportPreview {
  client_name: string;
  template_type: string;
  template_name: string;
  sections: ReportSection[];
  relevant_requirements: {
    id: string;
    text: string;
    priority: string;
  }[];
}

export interface ValidationResult {
  requirements_id: string;
  template_type: string;
  validation_status: 'excellent' | 'good' | 'fair' | 'poor';
  coverage_percentage: number;
  recommendations: string[];
  warnings: string[];
  gap_analysis: GapAnalysis;
}

export interface GapAnalysis {
  coverage_percentage: number;
  covered_requirements: number;
  total_requirements: number;
  gaps: {
    uncovered_requirements: ProcessedRequirement[];
    missing_schema_elements: string[];
  };
}

export interface AIModel {
  value: string;
  name: string;
  description: string;
  capabilities: string[];
}

export interface ReportFormat {
  value: string;
  name: string;
  description: string;
}

export interface ReportProgress {
  task_id: string;
  status: 'started' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  current_step: string;
  estimated_completion: string;
  message: string;
}

class ReportService {
  // Client Requirements Management
  async uploadClientRequirements(
    file: File,
    clientName: string,
    schemaType: 'eu_esrs_csrd' | 'uk_srd'
  ): Promise<ClientRequirement> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('client_name', clientName);
    formData.append('schema_type', schemaType);

    const response = await api.post('/client-requirements/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  async getClientRequirements(requirementsId: string): Promise<ClientRequirement> {
    const response = await api.get(`/client-requirements/${requirementsId}`);
    return response.data;
  }

  async listClientRequirements(clientName?: string): Promise<ClientRequirement[]> {
    const params = clientName ? { client_name: clientName } : {};
    const response = await api.get('/client-requirements', { params });
    return response.data;
  }

  async deleteClientRequirements(requirementsId: string): Promise<void> {
    await api.delete(`/client-requirements/${requirementsId}`);
  }

  // Gap Analysis
  async performGapAnalysis(requirementsId: string): Promise<GapAnalysis> {
    const response = await api.get(`/client-requirements/${requirementsId}/gap-analysis`);
    return response.data;
  }

  // Report Templates
  async getAvailableTemplates(): Promise<ReportTemplate[]> {
    const response = await api.get('/reports/templates');
    return response.data;
  }

  async getTemplateDetails(templateType: string): Promise<ReportTemplate> {
    const response = await api.get(`/reports/templates/${templateType}`);
    return response.data.config;
  }

  // AI Models and Formats
  async getAvailableAIModels(): Promise<AIModel[]> {
    const response = await api.get('/reports/ai-models');
    return response.data;
  }

  async getAvailableFormats(): Promise<ReportFormat[]> {
    const response = await api.get('/reports/formats');
    return response.data;
  }

  // Report Preview and Validation
  async previewReportStructure(
    requirementsId: string,
    templateType: string = 'eu_esrs_standard'
  ): Promise<ReportPreview> {
    const response = await api.get(`/reports/preview/${requirementsId}`, {
      params: { template_type: templateType },
    });
    return response.data;
  }

  async validateRequirementsForReport(
    requirementsId: string,
    templateType: string = 'eu_esrs_standard'
  ): Promise<ValidationResult> {
    const response = await api.post(`/reports/validate-requirements/${requirementsId}`, null, {
      params: { template_type: templateType },
    });
    return response.data;
  }

  // Report Generation
  async generateReport(request: ReportGenerationRequest): Promise<ReportGenerationResponse> {
    const response = await api.post('/reports/generate-complete', null, {
      params: {
        requirements_id: request.requirements_id,
        template_type: request.template_type,
        ai_model: request.ai_model,
        report_format: request.report_format,
        include_pdf: request.include_pdf,
      },
    });
    return response.data;
  }

  async generateReportAsync(request: ReportGenerationRequest): Promise<{ task_id: string }> {
    const response = await api.post('/reports/generate-async', null, {
      params: {
        requirements_id: request.requirements_id,
        template_type: request.template_type,
        ai_model: request.ai_model,
        report_format: request.report_format,
      },
    });
    return response.data;
  }

  // PDF Generation and Download
  async generatePDFReport(
    requirementsId: string,
    templateType: string = 'eu_esrs_standard',
    aiModel: string = 'openai_gpt35'
  ): Promise<Blob> {
    const response = await api.post('/reports/generate-pdf', null, {
      params: {
        requirements_id: requirementsId,
        template_type: templateType,
        ai_model: aiModel,
        download: true,
      },
      responseType: 'blob',
    });
    return response.data;
  }

  async downloadPDFReport(
    requirementsId: string,
    templateType: string = 'eu_esrs_standard',
    aiModel: string = 'openai_gpt35'
  ): Promise<Blob> {
    const response = await api.get(`/reports/download-pdf/${requirementsId}`, {
      params: {
        template_type: templateType,
        ai_model: aiModel,
      },
      responseType: 'blob',
    });
    return response.data;
  }

  // Utility Methods
  downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  validateFile(file: File): { valid: boolean; error?: string } {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'application/json'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Invalid file type. Please upload PDF, DOCX, TXT, or JSON files.',
      };
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File size too large. Maximum size is 10MB.',
      };
    }

    return { valid: true };
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  getValidationStatusColor(status: string): 'success' | 'warning' | 'error' | 'info' {
    switch (status) {
      case 'excellent':
        return 'success';
      case 'good':
        return 'info';
      case 'fair':
        return 'warning';
      case 'poor':
        return 'error';
      default:
        return 'info';
    }
  }

  getValidationStatusText(status: string): string {
    switch (status) {
      case 'excellent':
        return 'Excellent Coverage';
      case 'good':
        return 'Good Coverage';
      case 'fair':
        return 'Fair Coverage';
      case 'poor':
        return 'Poor Coverage';
      default:
        return 'Unknown Status';
    }
  }
}

export default new ReportService();