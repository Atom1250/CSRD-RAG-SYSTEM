import { searchService, SearchQuery, SearchResult } from './searchService';
import api from './api';

// Mock the API module
jest.mock('./api');
const mockApi = api as jest.Mocked<typeof api>;

describe('SearchService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('search', () => {
    const mockSearchResults: SearchResult[] = [
      {
        chunk_id: 'chunk-1',
        document_id: 'doc-1',
        content: 'Sample search result content',
        relevance_score: 0.95,
        document_filename: 'test.pdf',
        schema_elements: ['E1', 'Climate'],
      },
    ];

    it('performs basic search successfully', async () => {
      mockApi.post.mockResolvedValue({ data: mockSearchResults });

      const query: SearchQuery = {
        query: 'climate change',
        top_k: 10,
      };

      const result = await searchService.search(query);

      expect(mockApi.post).toHaveBeenCalledWith('/search/', query);
      expect(result).toEqual(mockSearchResults);
    });

    it('performs search with all filters', async () => {
      mockApi.post.mockResolvedValue({ data: mockSearchResults });

      const query: SearchQuery = {
        query: 'sustainability reporting',
        top_k: 20,
        min_relevance_score: 0.5,
        enable_reranking: true,
        document_type: 'pdf',
        schema_type: 'EU_ESRS_CSRD',
        processing_status: 'completed',
        filename_contains: 'ESRS',
      };

      const result = await searchService.search(query);

      expect(mockApi.post).toHaveBeenCalledWith('/search/', query);
      expect(result).toEqual(mockSearchResults);
    });

    it('handles search API errors', async () => {
      const errorMessage = 'Search service unavailable';
      mockApi.post.mockRejectedValue(new Error(errorMessage));

      const query: SearchQuery = {
        query: 'test query',
      };

      await expect(searchService.search(query)).rejects.toThrow(errorMessage);
    });
  });

  describe('getSuggestions', () => {
    const mockSuggestions = ['climate change adaptation', 'climate risk assessment'];

    it('gets search suggestions successfully', async () => {
      mockApi.get.mockResolvedValue({ data: { suggestions: mockSuggestions } });

      const result = await searchService.getSuggestions('climate');

      expect(mockApi.get).toHaveBeenCalledWith('/search/suggestions', {
        params: {
          partial_query: 'climate',
          max_suggestions: 5,
        },
      });
      expect(result).toEqual(mockSuggestions);
    });

    it('gets suggestions with custom max count', async () => {
      mockApi.get.mockResolvedValue({ data: { suggestions: mockSuggestions } });

      const result = await searchService.getSuggestions('sustain', 10);

      expect(mockApi.get).toHaveBeenCalledWith('/search/suggestions', {
        params: {
          partial_query: 'sustain',
          max_suggestions: 10,
        },
      });
      expect(result).toEqual(mockSuggestions);
    });

    it('handles suggestions API errors', async () => {
      mockApi.get.mockRejectedValue(new Error('Suggestions unavailable'));

      await expect(searchService.getSuggestions('test')).rejects.toThrow('Suggestions unavailable');
    });
  });

  describe('searchBySchema', () => {
    const mockSchemaResults: SearchResult[] = [
      {
        chunk_id: 'chunk-1',
        document_id: 'doc-1',
        content: 'Schema-specific content',
        relevance_score: 1.0,
        document_filename: 'schema.pdf',
        schema_elements: ['E1', 'E2'],
      },
    ];

    it('searches by schema elements successfully', async () => {
      mockApi.post.mockResolvedValue({ data: mockSchemaResults });

      const result = await searchService.searchBySchema(['E1', 'E2']);

      expect(mockApi.post).toHaveBeenCalledWith('/search/schema', {
        schema_elements: ['E1', 'E2'],
        schema_type: undefined,
        top_k: 10,
      });
      expect(result).toEqual(mockSchemaResults);
    });

    it('searches by schema with type filter', async () => {
      mockApi.post.mockResolvedValue({ data: mockSchemaResults });

      const result = await searchService.searchBySchema(['E1'], 'EU_ESRS_CSRD', 20);

      expect(mockApi.post).toHaveBeenCalledWith('/search/schema', {
        schema_elements: ['E1'],
        schema_type: 'EU_ESRS_CSRD',
        top_k: 20,
      });
      expect(result).toEqual(mockSchemaResults);
    });
  });

  describe('findSimilar', () => {
    const mockSimilarResults: SearchResult[] = [
      {
        chunk_id: 'chunk-2',
        document_id: 'doc-2',
        content: 'Similar content',
        relevance_score: 0.85,
        document_filename: 'similar.pdf',
        schema_elements: ['E1'],
      },
    ];

    it('finds similar chunks successfully', async () => {
      mockApi.post.mockResolvedValue({ data: mockSimilarResults });

      const result = await searchService.findSimilar('chunk-1');

      expect(mockApi.post).toHaveBeenCalledWith('/search/similar', {
        chunk_id: 'chunk-1',
        top_k: 10,
        exclude_same_document: true,
      });
      expect(result).toEqual(mockSimilarResults);
    });

    it('finds similar chunks with custom parameters', async () => {
      mockApi.post.mockResolvedValue({ data: mockSimilarResults });

      const result = await searchService.findSimilar('chunk-1', 20, false);

      expect(mockApi.post).toHaveBeenCalledWith('/search/similar', {
        chunk_id: 'chunk-1',
        top_k: 20,
        exclude_same_document: false,
      });
      expect(result).toEqual(mockSimilarResults);
    });
  });

  describe('getStatistics', () => {
    const mockStats = {
      total_documents: 100,
      total_chunks: 2500,
      chunks_with_embeddings: 2400,
      searchable_documents: true,
      vector_service_available: true,
    };

    it('gets search statistics successfully', async () => {
      mockApi.get.mockResolvedValue({ data: mockStats });

      const result = await searchService.getStatistics();

      expect(mockApi.get).toHaveBeenCalledWith('/search/statistics');
      expect(result).toEqual(mockStats);
    });
  });

  describe('getPerformanceMetrics', () => {
    const mockMetrics = {
      query: 'test query',
      total_time_ms: 150.5,
      embedding_time_ms: 45.2,
      vector_search_time_ms: 85.3,
      results_count: 10,
      avg_relevance_score: 0.75,
      top_relevance_score: 0.95,
    };

    it('gets performance metrics successfully', async () => {
      mockApi.get.mockResolvedValue({ data: mockMetrics });

      const result = await searchService.getPerformanceMetrics('test query');

      expect(mockApi.get).toHaveBeenCalledWith('/search/performance', {
        params: {
          query: 'test query',
          top_k: 10,
        },
      });
      expect(result).toEqual(mockMetrics);
    });

    it('gets performance metrics with custom top_k', async () => {
      mockApi.get.mockResolvedValue({ data: mockMetrics });

      const result = await searchService.getPerformanceMetrics('test query', 20);

      expect(mockApi.get).toHaveBeenCalledWith('/search/performance', {
        params: {
          query: 'test query',
          top_k: 20,
        },
      });
      expect(result).toEqual(mockMetrics);
    });
  });

  describe('generateEmbedding', () => {
    const mockEmbedding = [0.1, 0.2, 0.3, 0.4, 0.5];

    it('generates embedding successfully', async () => {
      mockApi.post.mockResolvedValue({ data: mockEmbedding });

      const result = await searchService.generateEmbedding('test query');

      expect(mockApi.post).toHaveBeenCalledWith('/search/embedding/generate', null, {
        params: { query: 'test query' },
      });
      expect(result).toEqual(mockEmbedding);
    });
  });

  describe('searchWithEmbedding', () => {
    const mockEmbeddingResults: SearchResult[] = [
      {
        chunk_id: 'chunk-1',
        document_id: 'doc-1',
        content: 'Embedding search result',
        relevance_score: 0.88,
        document_filename: 'embedding.pdf',
        schema_elements: ['E1'],
      },
    ];

    it('searches with custom embedding successfully', async () => {
      mockApi.post.mockResolvedValue({ data: mockEmbeddingResults });

      const embedding = [0.1, 0.2, 0.3];
      const result = await searchService.searchWithEmbedding(embedding);

      expect(mockApi.post).toHaveBeenCalledWith('/search/embedding', {
        query_embedding: embedding,
        top_k: 10,
        min_relevance_score: 0.0,
      });
      expect(result).toEqual(mockEmbeddingResults);
    });

    it('searches with custom embedding and parameters', async () => {
      mockApi.post.mockResolvedValue({ data: mockEmbeddingResults });

      const embedding = [0.1, 0.2, 0.3];
      const result = await searchService.searchWithEmbedding(embedding, 20, 0.5);

      expect(mockApi.post).toHaveBeenCalledWith('/search/embedding', {
        query_embedding: embedding,
        top_k: 20,
        min_relevance_score: 0.5,
      });
      expect(result).toEqual(mockEmbeddingResults);
    });
  });

  describe('healthCheck', () => {
    const mockHealthStatus = {
      status: 'healthy',
      vector_service_available: true,
      searchable_documents: true,
      total_documents: 100,
    };

    it('performs health check successfully', async () => {
      mockApi.get.mockResolvedValue({ data: mockHealthStatus });

      const result = await searchService.healthCheck();

      expect(mockApi.get).toHaveBeenCalledWith('/search/health');
      expect(result).toEqual(mockHealthStatus);
    });

    it('handles health check errors', async () => {
      mockApi.get.mockRejectedValue(new Error('Health check failed'));

      await expect(searchService.healthCheck()).rejects.toThrow('Health check failed');
    });
  });

  describe('error handling', () => {
    it('handles network errors consistently', async () => {
      const networkError = new Error('Network Error');
      mockApi.post.mockRejectedValue(networkError);

      await expect(searchService.search({ query: 'test' })).rejects.toThrow('Network Error');
      await expect(searchService.searchBySchema(['E1'])).rejects.toThrow('Network Error');
      await expect(searchService.findSimilar('chunk-1')).rejects.toThrow('Network Error');
    });

    it('handles API response errors', async () => {
      const apiError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };
      mockApi.post.mockRejectedValue(apiError);

      await expect(searchService.search({ query: 'test' })).rejects.toEqual(apiError);
    });

    it('handles malformed responses gracefully', async () => {
      mockApi.post.mockResolvedValue({ data: null });

      const result = await searchService.search({ query: 'test' });
      expect(result).toBeNull();
    });
  });

  describe('parameter validation', () => {
    it('handles empty query strings', async () => {
      mockApi.post.mockResolvedValue({ data: [] });

      const result = await searchService.search({ query: '' });

      expect(mockApi.post).toHaveBeenCalledWith('/search/', { query: '' });
      expect(result).toEqual([]);
    });

    it('handles undefined optional parameters', async () => {
      mockApi.post.mockResolvedValue({ data: [] });

      const query: SearchQuery = {
        query: 'test',
        top_k: undefined,
        min_relevance_score: undefined,
      };

      const result = await searchService.search(query);

      expect(mockApi.post).toHaveBeenCalledWith('/search/', query);
      expect(result).toEqual([]);
    });
  });
});