import api from './api';

export interface RAGQuery {
  question: string;
  model_type?: string;
  max_context_chunks?: number;
  min_relevance_score?: number;
  max_tokens?: number;
  temperature?: number;
}

export interface RAGResponse {
  id: string;
  query: string;
  response_text: string;
  confidence_score: number;
  model_used: string;
  source_chunks: string[];
  generation_timestamp: string;
}

export interface SourceChunk {
  id: string;
  document_filename: string;
  content: string;
  relevance_score: number;
  schema_elements?: string[];
}

export interface AIModel {
  type: string;
  provider: string;
  model: string;
  available: boolean;
  capabilities: string[];
  max_tokens: number;
}

export interface ConversationEntry {
  id: string;
  query: string;
  response: RAGResponse;
  timestamp: string;
  feedback?: {
    rating: number;
    comment?: string;
  };
}

export interface ModelStatus {
  models: Record<string, {
    available: boolean;
    info: AIModel;
  }>;
  default_model: string;
  available_count: number;
}

export const ragService = {
  // Submit RAG query
  async submitQuery(ragQuery: RAGQuery): Promise<RAGResponse> {
    const response = await api.post('/rag/query', ragQuery);
    return response.data;
  },

  // Submit batch RAG queries
  async submitBatchQuery(questions: string[], model_type?: string): Promise<RAGResponse[]> {
    const response = await api.post('/rag/batch-query', {
      questions,
      model_type,
      max_concurrent: 3
    });
    return response.data;
  },

  // Get available AI models
  async getAvailableModels(): Promise<AIModel[]> {
    const response = await api.get('/rag/models');
    return response.data;
  },

  // Get model status
  async getModelStatus(): Promise<ModelStatus> {
    const response = await api.get('/rag/models/status');
    return response.data;
  },

  // Validate response quality
  async validateResponseQuality(responseId: string, expectedTopics?: string[]): Promise<any> {
    const response = await api.post('/rag/validate-quality', {
      response_id: responseId,
      expected_topics: expectedTopics
    });
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<any> {
    const response = await api.get('/rag/health');
    return response.data;
  },

  // Example queries for testing
  async getExampleSustainabilityQuestion(): Promise<any> {
    const response = await api.post('/rag/examples/sustainability-question');
    return response.data;
  },

  async getExampleBatchQuestions(): Promise<any> {
    const response = await api.post('/rag/examples/batch-questions');
    return response.data;
  },

  // Local storage helpers for conversation history
  saveConversationEntry(entry: ConversationEntry): void {
    const history = this.getConversationHistory();
    history.unshift(entry);
    // Keep only last 50 entries
    const trimmedHistory = history.slice(0, 50);
    localStorage.setItem('rag_conversation_history', JSON.stringify(trimmedHistory));
  },

  getConversationHistory(): ConversationEntry[] {
    const stored = localStorage.getItem('rag_conversation_history');
    return stored ? JSON.parse(stored) : [];
  },

  clearConversationHistory(): void {
    localStorage.removeItem('rag_conversation_history');
  },

  updateConversationFeedback(entryId: string, feedback: { rating: number; comment?: string }): void {
    const history = this.getConversationHistory();
    const entryIndex = history.findIndex(entry => entry.id === entryId);
    if (entryIndex !== -1) {
      history[entryIndex].feedback = feedback;
      localStorage.setItem('rag_conversation_history', JSON.stringify(history));
    }
  },

  // Search conversation history
  searchConversationHistory(searchTerm: string): ConversationEntry[] {
    const history = this.getConversationHistory();
    const lowerSearchTerm = searchTerm.toLowerCase();
    return history.filter(entry => 
      entry.query.toLowerCase().includes(lowerSearchTerm) ||
      entry.response.response_text.toLowerCase().includes(lowerSearchTerm)
    );
  }
};