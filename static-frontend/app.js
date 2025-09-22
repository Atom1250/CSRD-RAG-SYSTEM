/**
 * CSRD RAG System - Static Frontend Application
 * Pure JavaScript implementation to avoid npm/build issues
 */

class CSRDApp {
    constructor() {
        this.backendPort = null;
        this.backendUrl = null;
        this.currentPage = 'dashboard';
        this.init();
    }

    async init() {
        console.log('🚀 Initializing CSRD RAG System...');
        
        // Setup navigation
        this.setupNavigation();
        
        // Load dashboard first
        this.loadPage('dashboard');
        
        // Auto-detect backend with delay (same as working simple page)
        console.log('⏳ Starting backend detection in 1 second...');
        setTimeout(async () => {
            try {
                await this.detectBackend();
            } catch (error) {
                console.error('❌ Backend detection failed:', error);
                this.showStatus('error', `Detection error: ${error.message}`);
            }
        }, 1000);
    }

    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        navButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const page = e.target.getAttribute('data-page');
                if (page) {
                    this.loadPage(page);
                }
            });
        });
    }

    loadPage(pageName) {
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
        console.log(`📄 Loaded page: ${pageName}`);
    }

    async detectBackend() {
        console.log('🔍 Auto-detecting backend...');
        
        // Update UI to show detection in progress
        const backendPortEl = document.getElementById('backend-port');
        const connectionStatus = document.getElementById('connection-status');
        
        if (backendPortEl) {
            backendPortEl.textContent = 'Detecting...';
        }
        if (connectionStatus) {
            connectionStatus.textContent = 'Detecting backend...';
            connectionStatus.className = 'connection-status disconnected';
        }
        
        // Use the same ports as the working simple page
        const portsToTry = [62871, 61076, 61038, 60145, 8000, 8002, 8080];
        
        for (let i = 0; i < portsToTry.length; i++) {
            const port = portsToTry[i];
            
            try {
                console.log(`🔍 Testing port ${port} (${i + 1}/${portsToTry.length})`);
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => {
                    console.log(`⏰ Timeout for port ${port}`);
                    controller.abort();
                }, 4000);
                
                const response = await fetch(`http://localhost:${port}/health`, {
                    method: 'GET',
                    mode: 'cors',
                    signal: controller.signal,
                    headers: {
                        'Accept': 'application/json',
                    }
                });
                
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    const data = await response.json();
                    this.backendPort = port;
                    this.backendUrl = `http://localhost:${port}`;
                    
                    if (backendPortEl) {
                        backendPortEl.textContent = port;
                        backendPortEl.style.color = '#27ae60';
                    }
                    this.updateConnectionStatus(true);
                    
                    console.log(`✅ Backend detected on port ${port}`, data);
                    
                    // Test all connections
                    await this.testAllConnections();
                    return; // Success, exit the loop
                } else {
                    console.log(`❌ Port ${port}: HTTP ${response.status}`);
                }
            } catch (error) {
                console.log(`❌ Port ${port}: ${error.message}`);
                if (error.name === 'AbortError') {
                    console.log(`⏰ Port ${port} timed out`);
                }
            }
        }
        
        // If no backend found
        console.error('❌ No backend found on any port');
        this.updateConnectionStatus(false);
        
        if (backendPortEl) {
            backendPortEl.textContent = 'Not found';
            backendPortEl.style.color = '#e74c3c';
        }
        
        this.showStatus('error', 'Backend not detected. Please ensure the backend is running.');
        
        // Show manual detection button
        const dashboardSection = document.querySelector('#dashboard-page .section');
        if (dashboardSection) {
            // Remove existing retry button if any
            const existingButton = dashboardSection.querySelector('.retry-button');
            if (existingButton) {
                existingButton.remove();
            }
            
            const manualDetect = document.createElement('button');
            manualDetect.className = 'btn btn-primary retry-button';
            manualDetect.textContent = 'Retry Detection';
            manualDetect.onclick = () => this.detectBackend();
            
            dashboardSection.appendChild(manualDetect);
        }
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (connected) {
            statusEl.textContent = `Connected (Port ${this.backendPort})`;
            statusEl.className = 'connection-status connected';
        } else {
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'connection-status disconnected';
        }
    }

    async apiRequest(endpoint, options = {}) {
        if (!this.backendUrl) {
            throw new Error('Backend not detected');
        }

        const url = `${this.backendUrl}${endpoint}`;
        const config = {
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        console.log(`🌐 API Request: ${options.method || 'GET'} ${url}`);
        
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    async testAllConnections() {
        console.log('🧪 Testing all connections...');
        
        try {
            // Test backend health
            const health = await this.apiRequest('/health');
            document.getElementById('backend-status').textContent = '✅ Online';
            document.getElementById('backend-status').style.color = '#27ae60';
            
            // Test database
            try {
                const dbTest = await this.apiRequest('/api/test-db');
                document.getElementById('db-status').textContent = '✅ Connected';
                document.getElementById('db-status').style.color = '#27ae60';
            } catch (error) {
                document.getElementById('db-status').textContent = '❌ Error';
                document.getElementById('db-status').style.color = '#e74c3c';
            }
            
            // Test Redis
            try {
                const redisTest = await this.apiRequest('/api/test-redis');
                document.getElementById('redis-status').textContent = '✅ Connected';
                document.getElementById('redis-status').style.color = '#27ae60';
            } catch (error) {
                document.getElementById('redis-status').textContent = '❌ Error';
                document.getElementById('redis-status').style.color = '#e74c3c';
            }
            
            // Test OpenAI
            try {
                const openaiTest = await this.apiRequest('/api/test-openai');
                if (openaiTest.api_key_valid) {
                    document.getElementById('openai-status').textContent = '✅ Connected';
                    document.getElementById('openai-status').style.color = '#27ae60';
                } else {
                    document.getElementById('openai-status').textContent = '⚠️ Invalid Key';
                    document.getElementById('openai-status').style.color = '#f39c12';
                }
            } catch (error) {
                document.getElementById('openai-status').textContent = '❌ Error';
                document.getElementById('openai-status').style.color = '#e74c3c';
            }
            
        } catch (error) {
            document.getElementById('backend-status').textContent = '❌ Offline';
            document.getElementById('backend-status').style.color = '#e74c3c';
            console.error('Connection test failed:', error);
        }
    }

    async testDatabase() {
        this.showLoading('test-results');
        try {
            const result = await this.apiRequest('/api/test-db');
            this.showResults('test-results', 'success', 'Database Test', result);
        } catch (error) {
            this.showResults('test-results', 'error', 'Database Test Failed', { error: error.message });
        }
    }

    async testRedis() {
        this.showLoading('test-results');
        try {
            const result = await this.apiRequest('/api/test-redis');
            this.showResults('test-results', 'success', 'Redis Test', result);
        } catch (error) {
            this.showResults('test-results', 'error', 'Redis Test Failed', { error: error.message });
        }
    }

    async testOpenAI() {
        this.showLoading('test-results');
        try {
            const result = await this.apiRequest('/api/test-openai');
            this.showResults('test-results', result.api_key_valid ? 'success' : 'error', 'OpenAI Test', result);
        } catch (error) {
            this.showResults('test-results', 'error', 'OpenAI Test Failed', { error: error.message });
        }
    }

    async uploadDocuments() {
        const fileInput = document.getElementById('file-input');
        if (!fileInput.files.length) {
            this.showStatus('error', 'Please select files to upload');
            return;
        }

        this.showLoading('upload-results');
        try {
            const result = await this.apiRequest('/api/documents/upload', {
                method: 'POST'
            });
            this.showResults('upload-results', 'info', 'Upload Status', result);
        } catch (error) {
            this.showResults('upload-results', 'error', 'Upload Failed', { error: error.message });
        }
    }

    async searchDocuments() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) {
            this.showStatus('error', 'Please enter a search query');
            return;
        }

        this.showLoading('search-results');
        try {
            const result = await this.apiRequest('/api/search', {
                method: 'POST',
                body: JSON.stringify({ query })
            });
            this.showResults('search-results', 'info', 'Search Results', result);
        } catch (error) {
            this.showResults('search-results', 'error', 'Search Failed', { error: error.message });
        }
    }

    async askQuestion() {
        const question = document.getElementById('question-input').value.trim();
        const model = document.getElementById('model-select').value;
        
        if (!question) {
            this.showStatus('error', 'Please enter a question');
            return;
        }

        this.showLoading('rag-results');
        try {
            const result = await this.apiRequest('/api/rag/query', {
                method: 'POST',
                body: JSON.stringify({ question, model })
            });
            this.showResults('rag-results', 'info', 'RAG Response', result);
        } catch (error) {
            this.showResults('rag-results', 'error', 'RAG Query Failed', { error: error.message });
        }
    }

    async generateReport() {
        const template = document.getElementById('template-select').value;
        
        this.showLoading('report-results');
        try {
            const result = await this.apiRequest('/api/reports/generate', {
                method: 'POST',
                body: JSON.stringify({ template })
            });
            this.showResults('report-results', 'success', 'Report Generated', result);
        } catch (error) {
            this.showResults('report-results', 'error', 'Report Generation Failed', { error: error.message });
        }
    }

    showLoading(elementId) {
        const element = document.getElementById(elementId);
        element.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        `;
    }

    showResults(elementId, type, title, data) {
        const element = document.getElementById(elementId);
        element.innerHTML = `
            <div class="status ${type}">
                <h4>${title}</h4>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        `;
    }

    showStatus(type, message) {
        // Create temporary status message
        const statusDiv = document.createElement('div');
        statusDiv.className = `status ${type}`;
        statusDiv.textContent = message;
        
        document.body.appendChild(statusDiv);
        
        setTimeout(() => {
            if (statusDiv.parentNode) {
                statusDiv.parentNode.removeChild(statusDiv);
            }
        }, 3000);
    }
}

// Global functions for HTML onclick handlers
window.detectBackend = () => app.detectBackend();
window.testAllConnections = () => app.testAllConnections();
window.testDatabase = () => app.testDatabase();
window.testRedis = () => app.testRedis();
window.testOpenAI = () => app.testOpenAI();
window.uploadDocuments = () => app.uploadDocuments();
window.searchDocuments = () => app.searchDocuments();
window.askQuestion = () => app.askQuestion();
window.generateReport = () => app.generateReport();

// Initialize the application
let app;

console.log('📱 CSRD RAG System Frontend Script Loaded');
console.log('📊 Document ready state:', document.readyState);

// Use the same initialization pattern as the working simple page
window.addEventListener('load', () => {
    console.log('📄 Page fully loaded, starting app...');
    app = new CSRDApp();
});

console.log('📱 CSRD RAG System Frontend Setup Complete');