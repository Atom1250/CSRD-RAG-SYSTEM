import api from './api';

export interface SearchResult {
  id: string;
  content: string;
  source: string;
  relevance_score: number;
  schema_elements: string[];
  document_id: string;
}

export interface SearchQuery {
  query: string;
  top_k?: number;
  min_relevance_score?: number;
  enable_reranking?: boolean;
  document_type?: string;
  schema_type?: string;
  processing_status?: string;
  filename_contains?: string;
}

export const searchService = {
  // Perform semantic search
  async search(searchQuery: SearchQuery): Promise<SearchResult[]> {
    const response = await api.post('/search/', searchQuery);
    return response.data;
  },

  // Get search suggestions
  async getSuggestions(partialQuery: string, maxSuggestions: number = 5): Promise<string[]> {
    const response = await api.get('/search/suggestions', {
      params: {
        partial_query: partialQuery,
        max_suggestions: maxSuggestions,
      },
    });
    return response.data.suggestions;
  },

  // Search by schema elements
  async searchBySchema(schemaElements: string[], schemaType?: string, topK: number = 10): Promise<SearchResult[]> {
    const response = await api.post('/search/schema', {
      schema_elements: schemaElements,
      schema_type: schemaType,
      top_k: topK,
    });
    return response.data;
  },

  // Find similar chunks
  async findSimilar(chunkId: string, topK: number = 10, excludeSameDocument: boolean = true): Promise<SearchResult[]> {
    const response = await api.post('/search/similar', {
      chunk_id: chunkId,
      top_k: topK,
      exclude_same_document: excludeSameDocument,
    });
    return response.data;
  },

  // Get search statistics
  async getStatistics(): Promise<any> {
    const response = await api.get('/search/statistics');
    return response.data;
  },

  // Get search performance metrics
  async getPerformanceMetrics(query: string, topK: number = 10): Promise<any> {
    const response = await api.get('/search/performance', {
      params: {
        query,
        top_k: topK,
      },
    });
    return response.data;
  },

  // Generate query embedding
  async generateEmbedding(query: string): Promise<number[]> {
    const response = await api.post('/search/embedding/generate', null, {
      params: { query },
    });
    return response.data;
  },

  // Search with custom embedding
  async searchWithEmbedding(queryEmbedding: number[], topK: number = 10, minRelevanceScore: number = 0.0): Promise<SearchResult[]> {
    const response = await api.post('/search/embedding', {
      query_embedding: queryEmbedding,
      top_k: topK,
      min_relevance_score: minRelevanceScore,
    });
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<any> {
    const response = await api.get('/search/health');
    return response.data;
  },
};