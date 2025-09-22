/**
 * CSRD RAG System Frontend - Main Application
 */

import { apiService } from './services/api';

class CSRDApp {
  private currentPage: string = 'dashboard';

  constructor() {
    this.init();
  }

  private async init() {
    console.log('🚀 Initializing CSRD RAG System Frontend...');
    
    // Set up navigation
    this.setupNavigation();
    
    // Load initial page
    await this.loadPage('dashboard');
    
    // Test backend connection
    await this.testBackendConnection();
  }

  private setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        const page = target.getAttribute('data-page');
        if (page) {
          this.loadPage(page);
        }
      });
    });
  }

  private async loadPage(pageName: string) {
    // Hide all pages
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));

    // Show selected page
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
      targetPage.classList.add('active');
    }

    // Update navigation
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => btn.classList.remove('active'));
    
    const activeBtn = document.querySelector(`[data-page="${pageName}"]`);
    if (activeBtn) {
      activeBtn.classList.add('active');
    }

    this.currentPage = pageName;

    // Load page-specific content
    switch (pageName) {
      case 'dashboard':
        await this.loadDashboard();
        break;
      case 'documents':
        await this.loadDocuments();
        break;
      case 'search':
        await this.loadSearch();
        break;
      case 'rag':
        await this.loadRAG();
        break;
      case 'reports':
        await this.loadReports();
        break;
      case 'schemas':
        await this.loadSchemas();
        break;
    }
  }

  private async testBackendConnection() {
    try {
      console.log('🔍 Testing backend connection...');
      
      const health = await apiService.healthCheck();
      console.log('✅ Backend health check:', health);
      
      // Test database
      try {
        const dbTest = await apiService.testDatabase();
        console.log('✅ Database connection:', dbTest);
      } catch (error) {
        console.warn('⚠️ Database test failed:', error);
      }
      
      // Test Redis
      try {
        const redisTest = await apiService.testRedis();
        console.log('✅ Redis connection:', redisTest);
      } catch (error) {
        console.warn('⚠️ Redis test failed:', error);
      }
      
      // Test OpenAI
      try {
        const openaiTest = await apiService.testOpenAI();
        console.log('✅ OpenAI API:', openaiTest);
      } catch (error) {
        console.warn('⚠️ OpenAI test failed:', error);
      }
      
      this.showNotification('✅ Backend connection successful!', 'success');
      
    } catch (error) {
      console.error('❌ Backend connection failed:', error);
      this.showNotification('❌ Backend connection failed!', 'error');
    }
  }

  private async loadDashboard() {
    console.log('📊 Loading dashboard...');
    
    try {
      const health = await apiService.healthCheck();
      
      // Update dashboard stats
      this.updateElement('doc-count', '0');
      this.updateElement('chunk-count', '0');
      this.updateElement('schema-count', '2');
      this.updateElement('report-count', '0');
      
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    }
  }

  private async loadDocuments() {
    console.log('📄 Loading documents...');
    // TODO: Implement document loading
  }

  private async loadSearch() {
    console.log('🔍 Loading search...');
    // TODO: Implement search functionality
  }

  private async loadRAG() {
    console.log('🤖 Loading RAG...');
    // TODO: Implement RAG functionality
  }

  private async loadReports() {
    console.log('📋 Loading reports...');
    // TODO: Implement reports functionality
  }

  private async loadSchemas() {
    console.log('📊 Loading schemas...');
    // TODO: Implement schemas functionality
  }

  private updateElement(id: string, content: string) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = content;
    }
  }

  private showNotification(message: string, type: 'success' | 'error' | 'info' = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '12px 20px',
      borderRadius: '4px',
      color: 'white',
      fontWeight: 'bold',
      zIndex: '1000',
      backgroundColor: type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'
    });
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new CSRDApp();
});

// Export for debugging
(window as any).CSRDApp = CSRDApp;