import api from './api';

export interface Document {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  upload_date: string;
  document_type: string;
  schema_type: string;
  processing_status: string;
  metadata: Record<string, any>;
}

export interface DocumentUpload {
  file: File;
  schema_type: string;
}

export const documentService = {
  // Get all documents
  async getDocuments(): Promise<Document[]> {
    const response = await api.get('/documents');
    return response.data;
  },

  // Upload a document
  async uploadDocument(data: DocumentUpload): Promise<Document> {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('schema_type', data.schema_type);

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Delete a document
  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`);
  },

  // Sync remote directory
  async syncRemoteDirectory(directoryPath: string): Promise<Document[]> {
    const response = await api.post('/documents/sync-remote', {
      directory_path: directoryPath,
    });
    return response.data;
  },

  // Get document processing status
  async getProcessingStatus(documentId: string): Promise<{ status: string; progress: number }> {
    const response = await api.get(`/documents/${documentId}/status`);
    return response.data;
  },
};