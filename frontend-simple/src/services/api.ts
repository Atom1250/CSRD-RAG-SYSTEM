import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor for loading states
api.interceptors.request.use((config) => {
  showLoading();
  return config;
});

// Response interceptor for loading states
api.interceptors.response.use(
  (response) => {
    hideLoading();
    return response;
  },
  (error) => {
    hideLoading();
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

function showLoading() {
  const loading = document.getElementById('loading');
  if (loading) loading.classList.remove('hidden');
}

function hideLoading() {
  const loading = document.getElementById('loading');
  if (loading) loading.classList.add('hidden');
}

export interface Document {
  id: string;
  filename: string;
  document_type: string;
  file_size: number;
  upload_date: string;
  processing_status: string;
  file_path: string;
  schema_type?: string;
  document_metadata?: any;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  content: string;
  relevance_score: number;
  document_filename: string;
  schema_elements?: string[];
}

export interface RAGResponse {
  id: string;
  query: string;
  response_text: string;
  model_used: string;
  confidence_score?: number;
  source_chunks?: string[];
  generation_timestamp: string;
}

export interface Schema {
  id: string;
  schema_type: string;
  element_code: string;
  element_name: string;
  description?: string;
  requirements?: string[];
  created_at: string;
  updated_at: string;
}

export interface Report {
  id: string;
  client_name: string;
  upload_date: string;
  requirements_text: string;
  schema_mappings?: any[];
  processed_requirements?: any[];
}

// API functions
export const documentAPI = {
  async getAll(): Promise<Document[]> {
    const response = await api.get('/documents/');
    return response.data;
  },

  async upload(files: FileList): Promise<Document[]> {
    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/documents/${id}`);
  }
};

export const searchAPI = {
  async search(query: string, limit: number = 10): Promise<SearchResult[]> {
    const response = await api.post('/search/', {
      query,
      limit
    });
    return response.data;
  }
};

export const ragAPI = {
  async query(question: string, model: string = 'openai'): Promise<RAGResponse> {
    const response = await api.post('/rag/query', {
      question,
      model
    });
    return response.data;
  }
};

export const schemaAPI = {
  async getTypes(): Promise<string[]> {
    const response = await api.get('/schemas/types');
    return response.data;
  },

  async getElements(schemaType: string): Promise<Schema[]> {
    const response = await api.get(`/schemas/elements/${schemaType}`);
    return response.data;
  },

  async getStats(schemaType: string): Promise<any> {
    const response = await api.get(`/schemas/stats/${schemaType}`);
    return response.data;
  }
};

export const reportAPI = {
  async getTemplates(): Promise<any[]> {
    const response = await api.get('/reports/templates');
    return response.data;
  },

  async uploadRequirements(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/client-requirements/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async generate(requirementsId: string, templateType: string = 'eu_esrs_standard'): Promise<any> {
    const response = await api.post(`/reports/generate?requirements_id=${requirementsId}&template_type=${templateType}`);
    return response.data;
  },

  async generatePDF(requirementsId: string, templateType: string = 'eu_esrs_standard'): Promise<Blob> {
    const response = await api.post(`/reports/generate-pdf?requirements_id=${requirementsId}&template_type=${templateType}`, {}, {
      responseType: 'blob'
    });
    return response.data;
  },

  async preview(requirementsId: string, templateType: string = 'eu_esrs_standard'): Promise<any> {
    const response = await api.get(`/reports/preview/${requirementsId}?template_type=${templateType}`);
    return response.data;
  }
};

export const statsAPI = {
  async getDashboardStats(): Promise<{
    documents: number;
    chunks: number;
    schemas: number;
    reports: number;
  }> {
    try {
      // Since there's no dedicated stats endpoint, we'll aggregate from other endpoints
      const [documents, schemaTypes, templates] = await Promise.all([
        documentAPI.getAll().catch(() => []),
        schemaAPI.getTypes().catch(() => []),
        reportAPI.getTemplates().catch(() => [])
      ]);
      
      return {
        documents: documents.length,
        chunks: documents.reduce((sum, doc) => sum + (doc.file_size > 0 ? 1 : 0), 0), // Rough estimate
        schemas: schemaTypes.length,
        reports: templates.length
      };
    } catch (error) {
      console.error('Failed to get dashboard stats:', error);
      return {
        documents: 0,
        chunks: 0,
        schemas: 0,
        reports: 0
      };
    }
  }
};

export default api;