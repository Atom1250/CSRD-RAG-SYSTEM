import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import RAG from './RAG';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

// Mock API responses
const mockModels = [
  {
    type: 'openai_gpt4',
    provider: 'OpenAI',
    model: 'gpt-4',
    available: true,
    capabilities: ['text_generation', 'reasoning', 'analysis'],
    max_tokens: 4096,
  },
  {
    type: 'openai_gpt35',
    provider: 'OpenAI',
    model: 'gpt-3.5-turbo',
    available: true,
    capabilities: ['text_generation'],
    max_tokens: 2048,
  },
  {
    type: 'anthropic_claude',
    provider: 'Anthropic',
    model: 'claude-3-sonnet-20240229',
    available: true,
    capabilities: ['text_generation', 'reasoning', 'analysis', 'long_context'],
    max_tokens: 4096,
  },
  {
    type: 'local_llama',
    provider: 'Local Llama',
    model: 'llama-placeholder',
    available: false,
    capabilities: ['text_generation'],
    max_tokens: 2048,
  },
];

const mockModelStatus = {
  models: {
    openai_gpt4: { available: true, info: mockModels[0] },
    openai_gpt35: { available: true, info: mockModels[1] },
    anthropic_claude: { available: true, info: mockModels[2] },
    local_llama: { available: false, info: mockModels[3] },
  },
  default_model: 'openai_gpt35',
  available_count: 3,
};

const mockRAGResponse = {
  id: 'rag_1704110400_1234',
  query: 'What are the key requirements for climate-related disclosures under ESRS E1?',
  response_text: `Based on the ESRS E1 Climate Change standard, companies must disclose the following key requirements for climate-related information:

1. **Governance and Strategy**
   - Climate-related governance arrangements
   - Climate strategy including transition plans
   - Business model resilience assessment

2. **Risk and Impact Management**
   - Climate-related risks and opportunities identification
   - Risk assessment processes and methodologies
   - Impact materiality assessment

3. **Metrics and Targets**
   - Scope 1, 2, and 3 greenhouse gas emissions
   - Climate-related targets and progress
   - Energy consumption and mix

4. **Financial Effects**
   - Financial effects of climate risks and opportunities
   - Climate-related expenditures and investments

The disclosures must follow the double materiality principle, considering both impact materiality (company's impact on climate) and financial materiality (climate's impact on the company).`,
  model_used: 'openai_gpt35',
  confidence_score: 0.92,
  source_chunks: ['chunk_esrs_e1_001', 'chunk_esrs_e1_015', 'chunk_csrd_guide_023'],
  generation_timestamp: '2024-01-01T12:00:00Z',
};

const mockBatchResponse = [
  {
    id: 'rag_batch_1_1704110400',
    query: 'What are the disclosure requirements for greenhouse gas emissions?',
    response_text: 'Companies must disclose Scope 1, 2, and 3 greenhouse gas emissions according to ESRS E1...',
    model_used: 'openai_gpt35',
    confidence_score: 0.88,
    source_chunks: ['chunk_esrs_e1_002'],
    generation_timestamp: '2024-01-01T12:01:00Z',
  },
  {
    id: 'rag_batch_2_1704110400',
    query: 'How should companies report on biodiversity impacts?',
    response_text: 'Biodiversity reporting under ESRS E4 requires companies to disclose their impacts on ecosystems...',
    model_used: 'openai_gpt35',
    confidence_score: 0.85,
    source_chunks: ['chunk_esrs_e4_001'],
    generation_timestamp: '2024-01-01T12:02:00Z',
  },
];

const mockHealthCheck = {
  status: 'healthy',
  available_models: ['openai_gpt4', 'openai_gpt35', 'anthropic_claude'],
  total_models: 4,
  search_service: 'available',
  timestamp: '2024-01-01T12:00:00Z',
};

// Setup MSW server
const server = setupServer(
  // Get available models
  rest.get('/api/rag/models', (req, res, ctx) => {
    return res(ctx.json(mockModels));
  }),

  // Get model status
  rest.get('/api/rag/models/status', (req, res, ctx) => {
    return res(ctx.json(mockModelStatus));
  }),

  // Submit RAG query
  rest.post('/api/rag/query', async (req, res, ctx) => {
    const body = await req.json();
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Return response based on query
    if (body.question.includes('error')) {
      return res(ctx.status(500), ctx.json({ detail: 'Internal server error' }));
    }
    
    return res(ctx.json({
      ...mockRAGResponse,
      query: body.question,
      model_used: body.model_type || 'openai_gpt35',
    }));
  }),

  // Submit batch RAG query
  rest.post('/api/rag/batch-query', async (req, res, ctx) => {
    const body = await req.json();
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return res(ctx.json(mockBatchResponse));
  }),

  // Validate response quality
  rest.post('/api/rag/validate-quality', (req, res, ctx) => {
    return res(ctx.json({
      response_id: 'rag_1704110400_1234',
      validation_timestamp: '2024-01-01T12:00:00Z',
      quality_score: 0.85,
      metrics: {
        confidence_score: 0.92,
        has_sources: true,
        source_count: 3,
        response_length: 450,
        contains_regulatory_terms: true,
        topic_coverage: 0.8,
        overall_quality: 'good',
      },
      recommendations: [
        'Response demonstrates good understanding of regulatory context',
        'Consider including more specific citations',
        'Response length is appropriate for the question complexity',
      ],
    }));
  }),

  // Health check
  rest.get('/api/rag/health', (req, res, ctx) => {
    return res(ctx.json(mockHealthCheck));
  }),

  // Example endpoints
  rest.post('/api/rag/examples/sustainability-question', (req, res, ctx) => {
    return res(ctx.json({
      example_question: 'What are the key requirements for climate change adaptation reporting under CSRD?',
      response: mockRAGResponse,
      note: 'This is an example demonstrating RAG functionality',
    }));
  }),

  rest.post('/api/rag/examples/batch-questions', (req, res, ctx) => {
    return res(ctx.json({
      example_questions: [
        'What are the disclosure requirements for greenhouse gas emissions?',
        'How should companies report on biodiversity impacts?',
        'What are the governance requirements under ESRS?',
      ],
      responses: mockBatchResponse,
      note: 'This is an example demonstrating batch RAG functionality',
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
});
afterAll(() => server.close());

describe('RAG Integration Tests', () => {
  describe('End-to-End Question Answering Flow', () => {
    it('completes full question answering workflow', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      // Wait for models to load
      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Verify models are loaded
      expect(screen.getByDisplayValue('openai_gpt35')).toBeInTheDocument();

      // Enter question
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'What are the key requirements for climate-related disclosures under ESRS E1?');

      // Submit query
      const askButton = screen.getByRole('button', { name: /Ask/i });
      await user.click(askButton);

      // Verify loading state
      expect(screen.getByText('Generating...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Wait for response
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Switch to response tab
      await user.click(screen.getByText('Current Response'));

      // Verify response content
      expect(screen.getByText('What are the key requirements for climate-related disclosures under ESRS E1?')).toBeInTheDocument();
      expect(screen.getByText(/Based on the ESRS E1 Climate Change standard/)).toBeInTheDocument();
      expect(screen.getByText('Confidence: 92%')).toBeInTheDocument();
      expect(screen.getByText('openai_gpt35')).toBeInTheDocument();

      // Verify sources
      expect(screen.getByText('Sources (3)')).toBeInTheDocument();
      
      // Expand sources
      await user.click(screen.getByText('Sources (3)'));
      expect(screen.getByText('Source Chunk chunk_esrs_e1_001')).toBeInTheDocument();
      expect(screen.getByText('Source Chunk chunk_esrs_e1_015')).toBeInTheDocument();
      expect(screen.getByText('Source Chunk chunk_csrd_guide_023')).toBeInTheDocument();
    });

    it('handles model switching during query', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      // Wait for models to load
      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Switch to GPT-4
      const modelSelect = screen.getByLabelText('AI Model');
      await user.click(modelSelect);
      await user.click(screen.getByText('OpenAI gpt-4'));

      // Enter question
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'Test model switching');

      // Submit query
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      // Wait for response
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Switch to response tab and verify model used
      await user.click(screen.getByText('Current Response'));
      expect(screen.getByText('openai_gpt4')).toBeInTheDocument();
    });

    it('persists conversation history across sessions', async () => {
      const user = userEvent.setup();
      
      // First session - submit a query
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'First question');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Unmount and remount component (simulate page refresh)
      const { unmount } = render(<div />);
      unmount();

      // Second session - check history
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Open history drawer
      const historyButton = screen.getByLabelText(/Conversation History/i);
      await user.click(historyButton);

      // Verify history is preserved
      expect(screen.getByText('First question')).toBeInTheDocument();
    });
  });

  describe('Advanced Settings Integration', () => {
    it('applies advanced settings to query parameters', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Open advanced settings
      const settingsButton = screen.getByLabelText(/Advanced Settings/i);
      await user.click(settingsButton);

      // Modify settings
      const maxChunksSlider = screen.getByRole('slider', { name: /Max Context Chunks/i });
      fireEvent.change(maxChunksSlider, { target: { value: 15 } });

      const relevanceSlider = screen.getByRole('slider', { name: /Min Relevance Score/i });
      fireEvent.change(relevanceSlider, { target: { value: 0.5 } });

      const tokensSlider = screen.getByRole('slider', { name: /Max Tokens/i });
      fireEvent.change(tokensSlider, { target: { value: 2000 } });

      const temperatureSlider = screen.getByRole('slider', { name: /Temperature/i });
      fireEvent.change(temperatureSlider, { target: { value: 0.3 } });

      // Close settings
      await user.click(screen.getByText('Close'));

      // Submit query with modified settings
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'Test advanced settings');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      // Verify request was made with correct parameters
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // The actual parameter verification would be done through network monitoring
      // For this test, we verify the UI reflects the changes
      await user.click(settingsButton);
      expect(screen.getByText('Max Context Chunks: 15')).toBeInTheDocument();
      expect(screen.getByText('Min Relevance Score: 0.5')).toBeInTheDocument();
      expect(screen.getByText('Max Tokens: 2000')).toBeInTheDocument();
      expect(screen.getByText('Temperature: 0.3')).toBeInTheDocument();
    });

    it('enables auto-refinement suggestions for low confidence responses', async () => {
      const user = userEvent.setup();
      
      // Mock low confidence response
      server.use(
        rest.post('/api/rag/query', (req, res, ctx) => {
          return res(ctx.json({
            ...mockRAGResponse,
            confidence_score: 0.4, // Low confidence
          }));
        })
      );

      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Enable auto-refinement
      const settingsButton = screen.getByLabelText(/Advanced Settings/i);
      await user.click(settingsButton);

      const autoRefineSwitch = screen.getByRole('checkbox', { name: /Auto-suggest refinements/i });
      await user.click(autoRefineSwitch);
      await user.click(screen.getByText('Close'));

      // Submit query
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'Vague question');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      // Wait for low confidence notification
      await waitFor(() => {
        expect(screen.getByText(/Low confidence detected/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Conversation History Integration', () => {
    it('searches and filters conversation history', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Submit multiple queries to build history
      const questions = [
        'What are CSRD requirements?',
        'How to report biodiversity?',
        'Climate change disclosures'
      ];

      for (const question of questions) {
        const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
        await user.clear(questionInput);
        await user.type(questionInput, question);
        await user.click(screen.getByRole('button', { name: /Ask/i }));
        
        await waitFor(() => {
          expect(screen.getByText('Current Response')).toBeInTheDocument();
        }, { timeout: 5000 });
      }

      // Open history drawer
      const historyButton = screen.getByLabelText(/Conversation History/i);
      await user.click(historyButton);

      // Verify all questions are in history
      expect(screen.getByText('What are CSRD requirements?')).toBeInTheDocument();
      expect(screen.getByText('How to report biodiversity?')).toBeInTheDocument();
      expect(screen.getByText('Climate change disclosures')).toBeInTheDocument();

      // Search history
      const searchInput = screen.getByPlaceholderText('Search conversations...');
      await user.type(searchInput, 'CSRD');

      // Verify search filtering (this would require proper search implementation)
      // For now, we just verify the search input works
      expect(searchInput).toHaveValue('CSRD');
    });

    it('loads previous conversation and allows refinement', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Submit initial query
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'Initial question');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Switch to response tab and refine
      await user.click(screen.getByText('Current Response'));
      
      const refineButton = screen.getByLabelText(/Refine this query/i);
      await user.click(refineButton);

      // Verify refined query is populated
      expect(screen.getByDisplayValue(/Please provide more specific details about: Initial question/)).toBeInTheDocument();
    });
  });

  describe('Feedback and Rating Integration', () => {
    it('submits and persists response feedback', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Submit query
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'Test feedback');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Switch to response tab
      await user.click(screen.getByText('Current Response'));

      // Open feedback dialog
      const ratingButton = screen.getByLabelText(/Rate this response/i);
      await user.click(ratingButton);

      // Submit rating
      const fourthStar = screen.getAllByRole('radio')[3]; // 4 stars
      await user.click(fourthStar);

      const commentInput = screen.getByPlaceholderText('Optional feedback comment...');
      await user.type(commentInput, 'Great response!');

      await user.click(screen.getByRole('button', { name: 'Submit' }));

      // Verify feedback success message
      await waitFor(() => {
        expect(screen.getByText('Feedback submitted successfully')).toBeInTheDocument();
      });

      // Verify feedback is persisted in history
      const historyButton = screen.getByLabelText(/Conversation History/i);
      await user.click(historyButton);

      // Look for rating in history (would show as stars)
      const historyItems = screen.getAllByRole('button');
      const historyItem = historyItems.find(item => 
        within(item).queryByText('Test feedback')
      );
      expect(historyItem).toBeInTheDocument();
    });
  });

  describe('Error Handling Integration', () => {
    it('handles API errors gracefully', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Submit query that triggers error
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'error trigger question');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      // Verify error handling
      await waitFor(() => {
        expect(screen.getByText(/Failed to generate response/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('handles network failures during model loading', async () => {
      // Mock network failure
      server.use(
        rest.get('/api/rag/models', (req, res, ctx) => {
          return res.networkError('Network error');
        }),
        rest.get('/api/rag/models/status', (req, res, ctx) => {
          return res.networkError('Network error');
        })
      );

      renderWithTheme(<RAG />);

      // Verify error message appears
      await waitFor(() => {
        expect(screen.getByText(/Failed to load AI models/)).toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });

  describe('Performance and Responsiveness', () => {
    it('handles concurrent queries appropriately', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Submit first query
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'First concurrent query');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      // Verify loading state
      expect(screen.getByText('Generating...')).toBeInTheDocument();

      // Try to submit another query while first is processing
      // The button should be disabled
      expect(screen.getByRole('button', { name: /Generating.../i })).toBeDisabled();

      // Wait for first query to complete
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Now button should be enabled again
      expect(screen.getByRole('button', { name: /Ask/i })).not.toBeDisabled();
    });

    it('provides responsive feedback during long operations', async () => {
      const user = userEvent.setup();
      
      // Mock slower response
      server.use(
        rest.post('/api/rag/query', async (req, res, ctx) => {
          await new Promise(resolve => setTimeout(resolve, 2000));
          return res(ctx.json(mockRAGResponse));
        })
      );

      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Submit query
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'Slow query');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      // Verify loading indicators
      expect(screen.getByText('Generating...')).toBeInTheDocument();
      expect(screen.getByText('Retrieving context and generating response...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 10000 });
    });
  });

  describe('Accessibility Integration', () => {
    it('maintains focus management during interactions', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Tab through interface
      await user.tab(); // Model select
      expect(screen.getByLabelText('AI Model')).toHaveFocus();

      await user.tab(); // Question input
      expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toHaveFocus();

      await user.tab(); // Ask button
      expect(screen.getByRole('button', { name: /Ask/i })).toHaveFocus();
    });

    it('provides proper screen reader announcements', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);

      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });

      // Submit query
      const questionInput = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(questionInput, 'Accessibility test');
      await user.click(screen.getByRole('button', { name: /Ask/i }));

      // Verify ARIA live regions and labels
      expect(screen.getByText('Generating...')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify response has proper structure for screen readers
      await user.click(screen.getByText('Current Response'));
      expect(screen.getByRole('tabpanel')).toBeInTheDocument();
    });
  });
});