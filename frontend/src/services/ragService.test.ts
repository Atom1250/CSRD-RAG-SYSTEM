import { ragService, RAGQuery, ConversationEntry } from './ragService';
import api from './api';

// Mock the api module
jest.mock('./api', () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

const mockApi = api as jest.Mocked<typeof api>;

describe('ragService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('submitQuery', () => {
    const mockQuery: RAGQuery = {
      question: 'What are CSRD requirements?',
      model_type: 'openai_gpt35',
      max_context_chunks: 10,
      min_relevance_score: 0.3,
      max_tokens: 1000,
      temperature: 0.1,
    };

    const mockResponse = {
      id: 'rag_123',
      query: 'What are CSRD requirements?',
      response_text: 'CSRD requires companies to report...',
      confidence_score: 0.85,
      model_used: 'openai_gpt35',
      source_chunks: ['chunk1', 'chunk2'],
      generation_timestamp: '2024-01-01T12:00:00Z',
    };

    it('submits query with correct parameters', async () => {
      mockApi.post.mockResolvedValue({ data: mockResponse });

      const result = await ragService.submitQuery(mockQuery);

      expect(mockApi.post).toHaveBeenCalledWith('/rag/query', mockQuery);
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors', async () => {
      const error = new Error('API Error');
      mockApi.post.mockRejectedValue(error);

      await expect(ragService.submitQuery(mockQuery)).rejects.toThrow('API Error');
    });

    it('submits query with minimal parameters', async () => {
      const minimalQuery: RAGQuery = {
        question: 'Simple question',
      };

      mockApi.post.mockResolvedValue({ data: mockResponse });

      await ragService.submitQuery(minimalQuery);

      expect(mockApi.post).toHaveBeenCalledWith('/rag/query', minimalQuery);
    });
  });

  describe('submitBatchQuery', () => {
    const mockBatchResponse = [
      {
        id: 'rag_batch_1',
        query: 'Question 1',
        response_text: 'Answer 1',
        confidence_score: 0.8,
        model_used: 'openai_gpt35',
        source_chunks: ['chunk1'],
        generation_timestamp: '2024-01-01T12:00:00Z',
      },
      {
        id: 'rag_batch_2',
        query: 'Question 2',
        response_text: 'Answer 2',
        confidence_score: 0.9,
        model_used: 'openai_gpt35',
        source_chunks: ['chunk2'],
        generation_timestamp: '2024-01-01T12:01:00Z',
      },
    ];

    it('submits batch query with correct parameters', async () => {
      const questions = ['Question 1', 'Question 2'];
      const modelType = 'openai_gpt4';

      mockApi.post.mockResolvedValue({ data: mockBatchResponse });

      const result = await ragService.submitBatchQuery(questions, modelType);

      expect(mockApi.post).toHaveBeenCalledWith('/rag/batch-query', {
        questions,
        model_type: modelType,
        max_concurrent: 3,
      });
      expect(result).toEqual(mockBatchResponse);
    });

    it('submits batch query without model type', async () => {
      const questions = ['Question 1', 'Question 2'];

      mockApi.post.mockResolvedValue({ data: mockBatchResponse });

      await ragService.submitBatchQuery(questions);

      expect(mockApi.post).toHaveBeenCalledWith('/rag/batch-query', {
        questions,
        model_type: undefined,
        max_concurrent: 3,
      });
    });
  });

  describe('getAvailableModels', () => {
    const mockModels = [
      {
        type: 'openai_gpt4',
        provider: 'OpenAI',
        model: 'gpt-4',
        available: true,
        capabilities: ['text_generation', 'reasoning'],
        max_tokens: 4096,
      },
      {
        type: 'anthropic_claude',
        provider: 'Anthropic',
        model: 'claude-3-sonnet',
        available: false,
        capabilities: ['text_generation'],
        max_tokens: 4096,
      },
    ];

    it('fetches available models', async () => {
      mockApi.get.mockResolvedValue({ data: mockModels });

      const result = await ragService.getAvailableModels();

      expect(mockApi.get).toHaveBeenCalledWith('/rag/models');
      expect(result).toEqual(mockModels);
    });

    it('handles API errors when fetching models', async () => {
      const error = new Error('Network Error');
      mockApi.get.mockRejectedValue(error);

      await expect(ragService.getAvailableModels()).rejects.toThrow('Network Error');
    });
  });

  describe('getModelStatus', () => {
    const mockStatus = {
      models: {
        openai_gpt4: { available: true, info: {} },
        anthropic_claude: { available: false, info: {} },
      },
      default_model: 'openai_gpt4',
      available_count: 1,
    };

    it('fetches model status', async () => {
      mockApi.get.mockResolvedValue({ data: mockStatus });

      const result = await ragService.getModelStatus();

      expect(mockApi.get).toHaveBeenCalledWith('/rag/models/status');
      expect(result).toEqual(mockStatus);
    });
  });

  describe('validateResponseQuality', () => {
    const mockValidation = {
      response_id: 'rag_123',
      quality_score: 0.85,
      metrics: {
        confidence_score: 0.8,
        has_sources: true,
        source_count: 3,
      },
    };

    it('validates response quality', async () => {
      mockApi.post.mockResolvedValue({ data: mockValidation });

      const result = await ragService.validateResponseQuality('rag_123', ['topic1', 'topic2']);

      expect(mockApi.post).toHaveBeenCalledWith('/rag/validate-quality', {
        response_id: 'rag_123',
        expected_topics: ['topic1', 'topic2'],
      });
      expect(result).toEqual(mockValidation);
    });

    it('validates response quality without expected topics', async () => {
      mockApi.post.mockResolvedValue({ data: mockValidation });

      await ragService.validateResponseQuality('rag_123');

      expect(mockApi.post).toHaveBeenCalledWith('/rag/validate-quality', {
        response_id: 'rag_123',
        expected_topics: undefined,
      });
    });
  });

  describe('healthCheck', () => {
    const mockHealth = {
      status: 'healthy',
      available_models: ['openai_gpt4', 'openai_gpt35'],
      total_models: 4,
    };

    it('performs health check', async () => {
      mockApi.get.mockResolvedValue({ data: mockHealth });

      const result = await ragService.healthCheck();

      expect(mockApi.get).toHaveBeenCalledWith('/rag/health');
      expect(result).toEqual(mockHealth);
    });
  });

  describe('example endpoints', () => {
    it('gets example sustainability question', async () => {
      const mockExample = {
        example_question: 'What are CSRD requirements?',
        response: {},
        note: 'Example',
      };

      mockApi.post.mockResolvedValue({ data: mockExample });

      const result = await ragService.getExampleSustainabilityQuestion();

      expect(mockApi.post).toHaveBeenCalledWith('/rag/examples/sustainability-question');
      expect(result).toEqual(mockExample);
    });

    it('gets example batch questions', async () => {
      const mockExample = {
        example_questions: ['Q1', 'Q2'],
        responses: [],
        note: 'Example',
      };

      mockApi.post.mockResolvedValue({ data: mockExample });

      const result = await ragService.getExampleBatchQuestions();

      expect(mockApi.post).toHaveBeenCalledWith('/rag/examples/batch-questions');
      expect(result).toEqual(mockExample);
    });
  });

  describe('conversation history management', () => {
    const mockEntry: ConversationEntry = {
      id: 'conv_123',
      query: 'Test question',
      response: {
        id: 'rag_123',
        query: 'Test question',
        response_text: 'Test answer',
        confidence_score: 0.8,
        model_used: 'openai_gpt35',
        source_chunks: ['chunk1'],
        generation_timestamp: '2024-01-01T12:00:00Z',
      },
      timestamp: '2024-01-01T12:00:00Z',
    };

    describe('saveConversationEntry', () => {
      it('saves new conversation entry', () => {
        ragService.saveConversationEntry(mockEntry);

        const history = ragService.getConversationHistory();
        expect(history).toHaveLength(1);
        expect(history[0]).toEqual(mockEntry);
      });

      it('prepends new entries to history', () => {
        const entry1 = { ...mockEntry, id: 'conv_1' };
        const entry2 = { ...mockEntry, id: 'conv_2' };

        ragService.saveConversationEntry(entry1);
        ragService.saveConversationEntry(entry2);

        const history = ragService.getConversationHistory();
        expect(history).toHaveLength(2);
        expect(history[0].id).toBe('conv_2');
        expect(history[1].id).toBe('conv_1');
      });

      it('limits history to 50 entries', () => {
        // Add 55 entries
        for (let i = 0; i < 55; i++) {
          ragService.saveConversationEntry({
            ...mockEntry,
            id: `conv_${i}`,
          });
        }

        const history = ragService.getConversationHistory();
        expect(history).toHaveLength(50);
        expect(history[0].id).toBe('conv_54'); // Most recent
        expect(history[49].id).toBe('conv_5'); // 50th from most recent
      });
    });

    describe('getConversationHistory', () => {
      it('returns empty array when no history exists', () => {
        const history = ragService.getConversationHistory();
        expect(history).toEqual([]);
      });

      it('returns stored history', () => {
        ragService.saveConversationEntry(mockEntry);
        const history = ragService.getConversationHistory();
        expect(history).toEqual([mockEntry]);
      });

      it('handles corrupted localStorage data', () => {
        localStorage.setItem('rag_conversation_history', 'invalid json');
        const history = ragService.getConversationHistory();
        expect(history).toEqual([]);
      });
    });

    describe('clearConversationHistory', () => {
      it('clears all conversation history', () => {
        ragService.saveConversationEntry(mockEntry);
        expect(ragService.getConversationHistory()).toHaveLength(1);

        ragService.clearConversationHistory();
        expect(ragService.getConversationHistory()).toHaveLength(0);
      });
    });

    describe('updateConversationFeedback', () => {
      it('updates feedback for existing entry', () => {
        ragService.saveConversationEntry(mockEntry);

        const feedback = { rating: 5, comment: 'Great response!' };
        ragService.updateConversationFeedback(mockEntry.id, feedback);

        const history = ragService.getConversationHistory();
        expect(history[0].feedback).toEqual(feedback);
      });

      it('does nothing for non-existent entry', () => {
        ragService.saveConversationEntry(mockEntry);

        const feedback = { rating: 5, comment: 'Great response!' };
        ragService.updateConversationFeedback('non_existent', feedback);

        const history = ragService.getConversationHistory();
        expect(history[0].feedback).toBeUndefined();
      });
    });

    describe('searchConversationHistory', () => {
      beforeEach(() => {
        const entries = [
          {
            ...mockEntry,
            id: 'conv_1',
            query: 'What are CSRD requirements?',
            response: { ...mockEntry.response, response_text: 'CSRD requires companies...' },
          },
          {
            ...mockEntry,
            id: 'conv_2',
            query: 'How to report biodiversity?',
            response: { ...mockEntry.response, response_text: 'Biodiversity reporting involves...' },
          },
          {
            ...mockEntry,
            id: 'conv_3',
            query: 'Climate change disclosures',
            response: { ...mockEntry.response, response_text: 'Climate disclosures under CSRD...' },
          },
        ];

        entries.forEach(entry => ragService.saveConversationEntry(entry));
      });

      it('searches by query text', () => {
        const results = ragService.searchConversationHistory('CSRD');
        expect(results).toHaveLength(2);
        expect(results[0].query).toContain('CSRD');
        expect(results[1].response.response_text).toContain('CSRD');
      });

      it('searches by response text', () => {
        const results = ragService.searchConversationHistory('biodiversity');
        expect(results).toHaveLength(1);
        expect(results[0].query).toContain('biodiversity');
      });

      it('performs case-insensitive search', () => {
        const results = ragService.searchConversationHistory('csrd');
        expect(results).toHaveLength(2);
      });

      it('returns empty array for no matches', () => {
        const results = ragService.searchConversationHistory('nonexistent');
        expect(results).toHaveLength(0);
      });

      it('returns all entries for empty search term', () => {
        const results = ragService.searchConversationHistory('');
        expect(results).toHaveLength(3);
      });
    });
  });

  describe('localStorage error handling', () => {
    it('handles localStorage quota exceeded', () => {
      // Mock localStorage to throw quota exceeded error
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = jest.fn(() => {
        throw new Error('QuotaExceededError');
      });

      // Should not throw error
      expect(() => {
        ragService.saveConversationEntry(mockEntry);
      }).not.toThrow();

      // Restore original method
      localStorage.setItem = originalSetItem;
    });

    it('handles localStorage access denied', () => {
      // Mock localStorage to throw access denied error
      const originalGetItem = localStorage.getItem;
      localStorage.getItem = jest.fn(() => {
        throw new Error('Access denied');
      });

      // Should return empty array instead of throwing
      const history = ragService.getConversationHistory();
      expect(history).toEqual([]);

      // Restore original method
      localStorage.getItem = originalGetItem;
    });
  });

  describe('edge cases and validation', () => {
    it('handles empty question in submitQuery', async () => {
      const emptyQuery: RAGQuery = { question: '' };
      mockApi.post.mockResolvedValue({ data: {} });

      await ragService.submitQuery(emptyQuery);

      expect(mockApi.post).toHaveBeenCalledWith('/rag/query', emptyQuery);
    });

    it('handles empty questions array in submitBatchQuery', async () => {
      mockApi.post.mockResolvedValue({ data: [] });

      const result = await ragService.submitBatchQuery([]);

      expect(mockApi.post).toHaveBeenCalledWith('/rag/batch-query', {
        questions: [],
        model_type: undefined,
        max_concurrent: 3,
      });
      expect(result).toEqual([]);
    });

    it('handles malformed API responses gracefully', async () => {
      mockApi.get.mockResolvedValue({ data: null });

      const result = await ragService.getAvailableModels();
      expect(result).toBeNull();
    });
  });
});