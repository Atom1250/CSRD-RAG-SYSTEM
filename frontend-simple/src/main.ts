import { documentAPI, searchAPI, ragAPI, schemaAPI, reportAPI, statsAPI } from './services/api.js';

class App {
  private currentPage = 'dashboard';

  constructor() {
    this.init();
  }

  private init() {
    this.setupNavigation();
    this.setupEventListeners();
    this.loadDashboard();
  }

  private setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const target = e.target as HTMLButtonElement;
        const page = target.dataset.page;
        if (page) {
          this.navigateTo(page);
        }
      });
    });
  }

  private navigateTo(page: string) {
    // Update active nav button
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

    // Update active page
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`${page}-page`)?.classList.add('active');

    this.currentPage = page;

    // Load page-specific data
    switch (page) {
      case 'dashboard':
        this.loadDashboard();
        break;
      case 'documents':
        this.loadDocuments();
        break;
      case 'schemas':
        this.loadSchemas();
        break;
      case 'reports':
        this.loadReports();
        break;
    }
  }

  private setupEventListeners() {
    // File upload
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input') as HTMLInputElement;
    const uploadBtn = document.getElementById('upload-btn');

    uploadArea?.addEventListener('click', () => fileInput?.click());
    uploadArea?.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });
    uploadArea?.addEventListener('dragleave', () => {
      uploadArea.classList.remove('dragover');
    });
    uploadArea?.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      const files = e.dataTransfer?.files;
      if (files) this.handleFileUpload(files);
    });

    fileInput?.addEventListener('change', (e) => {
      const files = (e.target as HTMLInputElement).files;
      if (files) this.handleFileUpload(files);
    });

    uploadBtn?.addEventListener('click', () => fileInput?.click());

    // Search
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input') as HTMLInputElement;
    
    searchBtn?.addEventListener('click', () => this.handleSearch());
    searchInput?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.handleSearch();
    });

    // RAG
    const askBtn = document.getElementById('ask-btn');
    const questionInput = document.getElementById('question-input') as HTMLTextAreaElement;
    
    askBtn?.addEventListener('click', () => this.handleRAGQuery());
    questionInput?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) this.handleRAGQuery();
    });

    // Reports
    const uploadRequirementsBtn = document.getElementById('upload-requirements-btn');
    const generateReportBtn = document.getElementById('generate-report-btn');
    
    uploadRequirementsBtn?.addEventListener('click', () => this.handleRequirementsUpload());
    generateReportBtn?.addEventListener('click', () => this.handleReportGeneration());
  }

  private async loadDashboard() {
    try {
      const stats = await statsAPI.getDashboardStats();
      
      document.getElementById('doc-count')!.textContent = stats.documents.toString();
      document.getElementById('chunk-count')!.textContent = stats.chunks.toString();
      document.getElementById('schema-count')!.textContent = stats.schemas.toString();
      document.getElementById('report-count')!.textContent = stats.reports.toString();
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
      // Set fallback values
      document.getElementById('doc-count')!.textContent = '0';
      document.getElementById('chunk-count')!.textContent = '0';
      document.getElementById('schema-count')!.textContent = '0';
      document.getElementById('report-count')!.textContent = '0';
    }
  }

  private async loadDocuments() {
    try {
      const documents = await documentAPI.getAll();
      const container = document.getElementById('documents-list')!;
      
      if (documents.length === 0) {
        container.innerHTML = '<p>No documents uploaded yet.</p>';
        return;
      }

      container.innerHTML = documents.map(doc => `
        <div class="result-item">
          <div class="result-title">${doc.filename}</div>
          <div class="result-content">
            Type: ${doc.document_type} | Size: ${this.formatFileSize(doc.file_size)} | 
            Status: ${doc.processing_status}
          </div>
          <div class="result-meta">
            Uploaded: ${new Date(doc.upload_date).toLocaleDateString()}
            <button class="btn btn-secondary" onclick="app.deleteDocument('${doc.id}')" style="margin-left: 1rem; padding: 0.25rem 0.5rem; font-size: 0.8rem;">Delete</button>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Failed to load documents:', error);
      document.getElementById('documents-list')!.innerHTML = '<p>Failed to load documents.</p>';
    }
  }

  private async loadSchemas() {
    try {
      const schemaTypes = await schemaAPI.getTypes();
      const container = document.getElementById('schemas-list')!;
      
      if (schemaTypes.length === 0) {
        container.innerHTML = '<p>No schema types available.</p>';
        return;
      }

      let html = '';
      for (const schemaType of schemaTypes) {
        try {
          const stats = await schemaAPI.getStats(schemaType);
          html += `
            <div class="result-item">
              <div class="result-title">${schemaType}</div>
              <div class="result-content">
                Elements: ${stats.total_elements} | Documents: ${stats.documents_using_schema}<br>
                Classification Rate: ${stats.classification_rate_percent}%
              </div>
              <div class="result-meta">
                Classified Chunks: ${stats.classified_chunks}/${stats.total_chunks}
              </div>
            </div>
          `;
        } catch (error) {
          html += `
            <div class="result-item">
              <div class="result-title">${schemaType}</div>
              <div class="result-content">Schema type available</div>
              <div class="result-meta">Statistics not available</div>
            </div>
          `;
        }
      }
      
      container.innerHTML = html;
    } catch (error) {
      console.error('Failed to load schemas:', error);
      document.getElementById('schemas-list')!.innerHTML = '<p>Failed to load schemas.</p>';
    }
  }

  private async loadReports() {
    try {
      const templates = await reportAPI.getTemplates();
      const container = document.getElementById('reports-list')!;
      
      if (templates.length === 0) {
        container.innerHTML = '<p>No report templates available.</p>';
        return;
      }

      container.innerHTML = templates.map(template => `
        <div class="result-item">
          <div class="result-title">${template.name || template.type}</div>
          <div class="result-content">
            Type: ${template.type}<br>
            ${template.description || 'Report template for sustainability reporting'}
          </div>
          <div class="result-meta">
            Template available for report generation
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Failed to load report templates:', error);
      document.getElementById('reports-list')!.innerHTML = '<p>Failed to load report templates.</p>';
    }
  }

  private async handleFileUpload(files: FileList) {
    try {
      await documentAPI.upload(files);
      alert('Files uploaded successfully!');
      if (this.currentPage === 'documents') {
        this.loadDocuments();
      }
      this.loadDashboard(); // Update stats
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    }
  }

  private async handleSearch() {
    const input = document.getElementById('search-input') as HTMLInputElement;
    const query = input.value.trim();
    
    if (!query) {
      alert('Please enter a search query.');
      return;
    }

    try {
      const results = await searchAPI.search(query);
      const container = document.getElementById('search-results')!;
      
      if (results.length === 0) {
        container.innerHTML = '<p>No results found.</p>';
        return;
      }

      container.innerHTML = results.map(result => `
        <div class="result-item">
          <div class="result-title">Score: ${result.relevance_score.toFixed(3)}</div>
          <div class="result-content">${result.content}</div>
          <div class="result-meta">
            Document: ${result.document_filename}
            ${result.schema_elements ? ` | Elements: ${result.schema_elements.join(', ')}` : ''}
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Search failed:', error);
      document.getElementById('search-results')!.innerHTML = '<p>Search failed. Please try again.</p>';
    }
  }

  private async handleRAGQuery() {
    const questionInput = document.getElementById('question-input') as HTMLTextAreaElement;
    const modelSelect = document.getElementById('model-select') as HTMLSelectElement;
    
    const question = questionInput.value.trim();
    const model = modelSelect.value;
    
    if (!question) {
      alert('Please enter a question.');
      return;
    }

    try {
      const response = await ragAPI.query(question, model);
      const container = document.getElementById('rag-response')!;
      
      container.innerHTML = `
        <div class="result-item">
          <div class="result-title">Response (${response.model_used})</div>
          <div class="result-content">${response.response_text}</div>
          <div class="result-meta">
            <strong>Query:</strong> ${response.query}<br>
            <strong>Confidence:</strong> ${response.confidence_score ? response.confidence_score.toFixed(3) : 'N/A'}<br>
            <strong>Generated:</strong> ${new Date(response.generation_timestamp).toLocaleString()}
            ${response.source_chunks ? `<br><strong>Sources:</strong> ${response.source_chunks.length} chunks` : ''}
          </div>
        </div>
      `;
    } catch (error) {
      console.error('RAG query failed:', error);
      document.getElementById('rag-response')!.innerHTML = '<p>Query failed. Please try again.</p>';
    }
  }

  private async handleRequirementsUpload() {
    const input = document.getElementById('requirements-input') as HTMLInputElement;
    const file = input.files?.[0];
    
    if (!file) {
      alert('Please select a requirements file.');
      return;
    }

    try {
      await reportAPI.uploadRequirements(file);
      alert('Requirements uploaded successfully!');
    } catch (error) {
      console.error('Requirements upload failed:', error);
      alert('Requirements upload failed. Please try again.');
    }
  }

  private async handleReportGeneration() {
    const templateSelect = document.getElementById('template-select') as HTMLSelectElement;
    const templateType = templateSelect.value;
    
    // For demo purposes, we'll use a placeholder requirements ID
    // In a real app, this would come from the uploaded requirements
    const requirementsId = 'demo-requirements-id';
    
    try {
      const result = await reportAPI.generate(requirementsId, templateType);
      alert('Report generated successfully!');
      console.log('Report result:', result);
    } catch (error) {
      console.error('Report generation failed:', error);
      alert('Report generation failed. Please upload client requirements first.');
    }
  }

  // Public methods for global access
  public async deleteDocument(id: string) {
    if (confirm('Are you sure you want to delete this document?')) {
      try {
        await documentAPI.delete(id);
        this.loadDocuments();
        this.loadDashboard();
      } catch (error) {
        console.error('Delete failed:', error);
        alert('Delete failed. Please try again.');
      }
    }
  }

  public async downloadReport(requirementsId: string) {
    try {
      const blob = await reportAPI.generatePDF(requirementsId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sustainability-report-${requirementsId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

// Initialize app
const app = new App();

// Make app globally accessible for onclick handlers
(window as any).app = app;