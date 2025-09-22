/**
 * API Service for CSRD RAG System Frontend
 */

const API_BASE_URL = 'http://localhost:61076';

export class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }

  // Test endpoints
  async testDatabase() {
    return this.request('/api/test-db');
  }

  async testRedis() {
    return this.request('/api/test-redis');
  }

  async testOpenAI() {
    return this.request('/api/test-openai');
  }

  // System info
  async getSystemInfo() {
    return this.request('/');
  }
}

export const apiService = new ApiService();