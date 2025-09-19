import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import RAG from './RAG';
import { ragService } from '../services/ragService';

// Mock the ragService
jest.mock('../services/ragService', () => ({
  ragService: {
    getAvailableModels: jest.fn(),
    getModelStatus: jest.fn(),
    submitQuery: jest.fn(),
    submitBatchQuery: jest.fn(),
    validateResponseQuality: jest.fn(),
    healthCheck: jest.fn(),
    getConversationHistory: jest.fn(),
    saveConversationEntry: jest.fn(),
    clearConversationHistory: jest.fn(),
    updateConversationFeedback: jest.fn(),
    searchConversationHistory: jest.fn(),
  },
}));

const mockRagService = ragService as jest.Mocked<typeof ragService>;

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('RAG Component', () => {
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
      model: 'claude-3-sonnet',
      available: false,
      capabilities: ['text_generation', 'reasoning'],
      max_tokens: 4096,
    },
  ];

  const mockModelStatus = {
    models: {
      openai_gpt4: { available: true, info: mockModels[0] },
      openai_gpt35: { available: true, info: mockModels[1] },
      anthropic_claude: { available: false, info: mockModels[2] },
    },
    default_model: 'openai_gpt35',
    available_count: 2,
  };

  const mockResponse = {
    id: 'test-response-1',
    query: 'What are CSRD requirements?',
    response_text: 'CSRD requires companies to report on sustainability matters...',
    confidence_score: 0.85,
    model_used: 'openai_gpt35',
    source_chunks: ['chunk-1', 'chunk-2'],
    generation_timestamp: '2024-01-01T12:00:00Z',
  };

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Setup default mock implementations
    mockRagService.getAvailableModels.mockResolvedValue(mockModels);
    mockRagService.getModelStatus.mockResolvedValue(mockModelStatus);
    mockRagService.getConversationHistory.mockReturnValue([]);
    mockRagService.searchConversationHistory.mockReturnValue([]);
    
    // Clear localStorage
    localStorage.clear();
  });

  describe('Initial Rendering', () => {
    it('renders the main components', async () => {
      renderWithTheme(<RAG />);
      
      expect(screen.getByText('RAG Question Answering')).toBeInTheDocument();
      expect(screen.getByText('Ask Question')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      
      // Wait for models to load
      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });
    });

    it('loads available models on mount', async () => {
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(mockRagService.getAvailableModels).toHaveBeenCalled();
        expect(mockRagService.getModelStatus).toHaveBeenCalled();
      });
    });

    it('displays model selection dropdown with available models', async () => {
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        const modelSelect = screen.getByLabelText('AI Model');
        expect(modelSelect).toBeInTheDocument();
      });
      
      // Click to open dropdown
      const modelSelect = screen.getByLabelText('AI Model');
      fireEvent.mouseDown(modelSelect);
      
      await waitFor(() => {
        expect(screen.getByText('OpenAI gpt-4')).toBeInTheDocument();
        expect(screen.getByText('OpenAI gpt-3.5-turbo')).toBeInTheDocument();
        expect(screen.getByText('Anthropic claude-3-sonnet')).toBeInTheDocument();
      });
    });

    it('shows warning when no models are available', async () => {
      mockRagService.getModelStatus.mockResolvedValue({
        ...mockModelStatus,
        available_count: 0,
      });
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByText(/No AI models are currently available/)).toBeInTheDocument();
      });
    });
  });

  describe('Question Input Interface', () => {
    it('allows typing in the question input field', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      
      expect(input).toHaveValue('What are CSRD requirements?');
    });

    it('enables ask button when query is entered and model is selected', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      const askButton = screen.getByRole('button', { name: /Ask/i });
      
      // Initially disabled
      expect(askButton).toBeDisabled();
      
      // Type question
      await user.type(input, 'What are CSRD requirements?');
      
      // Should be enabled after model loads and question is entered
      await waitFor(() => {
        expect(askButton).not.toBeDisabled();
      });
    });

    it('submits query on Enter key press', async () => {
      const user = userEvent.setup();
      mockRagService.submitQuery.mockResolvedValue(mockResponse);
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockRagService.submitQuery).toHaveBeenCalledWith({
          question: 'What are CSRD requirements?',
          model_type: 'openai_gpt35',
          max_context_chunks: 10,
          min_relevance_score: 0.3,
          max_tokens: 1000,
          temperature: 0.1,
        });
      });
    });

    it('does not submit on Shift+Enter', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.keyboard('{Shift>}{Enter}{/Shift}');
      
      expect(mockRagService.submitQuery).not.toHaveBeenCalled();
    });
  });

  describe('Model Selection', () => {
    it('allows selecting different AI models', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });
      
      // Open dropdown
      const modelSelect = screen.getByLabelText('AI Model');
      await user.click(modelSelect);
      
      // Select GPT-4
      await user.click(screen.getByText('OpenAI gpt-4'));
      
      // Verify selection
      expect(screen.getByDisplayValue('openai_gpt4')).toBeInTheDocument();
    });

    it('shows model capabilities and availability', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });
      
      // Open dropdown
      const modelSelect = screen.getByLabelText('AI Model');
      await user.click(modelSelect);
      
      // Check for capabilities
      expect(screen.getByText('text_generation, reasoning')).toBeInTheDocument();
      expect(screen.getByText('Unavailable')).toBeInTheDocument();
    });

    it('disables unavailable models', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });
      
      // Open dropdown
      const modelSelect = screen.getByLabelText('AI Model');
      await user.click(modelSelect);
      
      // Claude should be disabled
      const claudeOption = screen.getByText('Anthropic claude-3-sonnet').closest('li');
      expect(claudeOption).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('Response Display', () => {
    it('displays response with confidence score and source citations', async () => {
      const user = userEvent.setup();
      mockRagService.submitQuery.mockResolvedValue(mockResponse);
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Submit query
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.click(screen.getByRole('button', { name: /Ask/i }));
      
      // Wait for response
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      });
      
      // Switch to response tab
      await user.click(screen.getByText('Current Response'));
      
      // Check response content
      expect(screen.getByText('What are CSRD requirements?')).toBeInTheDocument();
      expect(screen.getByText(/CSRD requires companies to report/)).toBeInTheDocument();
      expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
      expect(screen.getByText('openai_gpt35')).toBeInTheDocument();
    });

    it('shows source chunks in accordion', async () => {
      const user = userEvent.setup();
      mockRagService.submitQuery.mockResolvedValue(mockResponse);
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Submit query and switch to response tab
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.click(screen.getByRole('button', { name: /Ask/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Current Response'));
      
      // Check sources accordion
      expect(screen.getByText('Sources (2)')).toBeInTheDocument();
      
      // Expand sources
      await user.click(screen.getByText('Sources (2)'));
      expect(screen.getByText('Source Chunk chunk-1')).toBeInTheDocument();
      expect(screen.getByText('Source Chunk chunk-2')).toBeInTheDocument();
    });

    it('displays loading state during query processing', async () => {
      const user = userEvent.setup();
      // Mock a delayed response
      mockRagService.submitQuery.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(mockResponse), 1000))
      );
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Submit query
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.click(screen.getByRole('button', { name: /Ask/i }));
      
      // Check loading state
      expect(screen.getByText('Generating...')).toBeInTheDocument();
      expect(screen.getByText('Retrieving context and generating response...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Conversation History', () => {
    const mockHistory = [
      {
        id: 'conv-1',
        query: 'What are CSRD requirements?',
        response: mockResponse,
        timestamp: '2024-01-01T12:00:00Z',
      },
      {
        id: 'conv-2',
        query: 'How to report biodiversity?',
        response: { ...mockResponse, id: 'resp-2', query: 'How to report biodiversity?' },
        timestamp: '2024-01-01T11:00:00Z',
      },
    ];

    it('opens conversation history drawer', async () => {
      const user = userEvent.setup();
      mockRagService.getConversationHistory.mockReturnValue(mockHistory);
      
      renderWithTheme(<RAG />);
      
      // Click history button
      const historyButton = screen.getByLabelText(/Conversation History/i);
      await user.click(historyButton);
      
      // Check drawer content
      expect(screen.getByText('Conversation History')).toBeInTheDocument();
      expect(screen.getByText('What are CSRD requirements?')).toBeInTheDocument();
      expect(screen.getByText('How to report biodiversity?')).toBeInTheDocument();
    });

    it('searches conversation history', async () => {
      const user = userEvent.setup();
      mockRagService.getConversationHistory.mockReturnValue(mockHistory);
      mockRagService.searchConversationHistory.mockReturnValue([mockHistory[0]]);
      
      renderWithTheme(<RAG />);
      
      // Open history drawer
      const historyButton = screen.getByLabelText(/Conversation History/i);
      await user.click(historyButton);
      
      // Search
      const searchInput = screen.getByPlaceholderText('Search conversations...');
      await user.type(searchInput, 'CSRD');
      
      expect(mockRagService.searchConversationHistory).toHaveBeenCalledWith('CSRD');
    });

    it('clears conversation history', async () => {
      const user = userEvent.setup();
      mockRagService.getConversationHistory.mockReturnValue(mockHistory);
      
      renderWithTheme(<RAG />);
      
      // Open history drawer
      const historyButton = screen.getByLabelText(/Conversation History/i);
      await user.click(historyButton);
      
      // Clear history
      const clearButton = screen.getByLabelText(/Clear/i);
      await user.click(clearButton);
      
      expect(mockRagService.clearConversationHistory).toHaveBeenCalled();
    });

    it('loads previous conversation when clicked', async () => {
      const user = userEvent.setup();
      mockRagService.getConversationHistory.mockReturnValue(mockHistory);
      
      renderWithTheme(<RAG />);
      
      // Open history drawer
      const historyButton = screen.getByLabelText(/Conversation History/i);
      await user.click(historyButton);
      
      // Click on first conversation
      await user.click(screen.getByText('What are CSRD requirements?'));
      
      // Check that query is loaded
      expect(screen.getByDisplayValue('What are CSRD requirements?')).toBeInTheDocument();
    });
  });

  describe('Advanced Settings', () => {
    it('opens advanced settings dialog', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      // Click settings button
      const settingsButton = screen.getByLabelText(/Advanced Settings/i);
      await user.click(settingsButton);
      
      // Check dialog content
      expect(screen.getByText('Advanced Settings')).toBeInTheDocument();
      expect(screen.getByText(/Max Context Chunks/)).toBeInTheDocument();
      expect(screen.getByText(/Min Relevance Score/)).toBeInTheDocument();
      expect(screen.getByText(/Max Tokens/)).toBeInTheDocument();
      expect(screen.getByText(/Temperature/)).toBeInTheDocument();
    });

    it('adjusts advanced parameters', async () => {
      const user = userEvent.setup();
      mockRagService.submitQuery.mockResolvedValue(mockResponse);
      
      renderWithTheme(<RAG />);
      
      // Open settings
      const settingsButton = screen.getByLabelText(/Advanced Settings/i);
      await user.click(settingsButton);
      
      // Adjust max context chunks slider
      const maxChunksSlider = screen.getByLabelText(/Max Context Chunks/i);
      fireEvent.change(maxChunksSlider, { target: { value: 15 } });
      
      // Close settings
      await user.click(screen.getByText('Close'));
      
      // Submit query to test new settings
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'Test query');
      await user.click(screen.getByRole('button', { name: /Ask/i }));
      
      await waitFor(() => {
        expect(mockRagService.submitQuery).toHaveBeenCalledWith(
          expect.objectContaining({
            max_context_chunks: 15,
          })
        );
      });
    });
  });

  describe('Feedback and Rating', () => {
    it('opens feedback dialog when rating button is clicked', async () => {
      const user = userEvent.setup();
      mockRagService.submitQuery.mockResolvedValue(mockResponse);
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Submit query and switch to response tab
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.click(screen.getByRole('button', { name: /Ask/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Current Response'));
      
      // Click rating button
      const ratingButton = screen.getByLabelText(/Rate this response/i);
      await user.click(ratingButton);
      
      // Check dialog
      expect(screen.getByText('Rate Response')).toBeInTheDocument();
      expect(screen.getByText('How would you rate this response?')).toBeInTheDocument();
    });

    it('submits feedback with rating and comment', async () => {
      const user = userEvent.setup();
      mockRagService.submitQuery.mockResolvedValue(mockResponse);
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Submit query and open feedback
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.click(screen.getByRole('button', { name: /Ask/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Current Response')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Current Response'));
      
      const ratingButton = screen.getByLabelText(/Rate this response/i);
      await user.click(ratingButton);
      
      // Rate 4 stars
      const fourthStar = screen.getAllByRole('radio')[3]; // 4th star (0-indexed)
      await user.click(fourthStar);
      
      // Add comment
      const commentInput = screen.getByPlaceholderText('Optional feedback comment...');
      await user.type(commentInput, 'Good response but could be more detailed');
      
      // Submit
      await user.click(screen.getByRole('button', { name: 'Submit' }));
      
      expect(mockRagService.updateConversationFeedback).toHaveBeenCalledWith(
        mockResponse.id,
        {
          rating: 4,
          comment: 'Good response but could be more detailed',
        }
      );
    });
  });

  describe('Quick Examples', () => {
    it('displays quick example questions', () => {
      renderWithTheme(<RAG />);
      
      expect(screen.getByText('Quick Examples')).toBeInTheDocument();
      expect(screen.getByText(/What are the key requirements for climate-related disclosures/)).toBeInTheDocument();
      expect(screen.getByText(/How should companies report on biodiversity impacts/)).toBeInTheDocument();
    });

    it('populates query field when example is clicked', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Click example
      await user.click(screen.getByText(/What are the key requirements for climate-related disclosures/));
      
      // Check input field
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      expect(input).toHaveValue('What are the key requirements for climate-related disclosures under ESRS E1?');
    });
  });

  describe('Error Handling', () => {
    it('displays error message when query fails', async () => {
      const user = userEvent.setup();
      mockRagService.submitQuery.mockRejectedValue(new Error('API Error'));
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Submit query
      const input = screen.getByPlaceholderText(/Ask a question about your sustainability documents/);
      await user.type(input, 'What are CSRD requirements?');
      await user.click(screen.getByRole('button', { name: /Ask/i }));
      
      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/Failed to generate response/)).toBeInTheDocument();
      });
    });

    it('displays error message when models fail to load', async () => {
      mockRagService.getAvailableModels.mockRejectedValue(new Error('Network Error'));
      mockRagService.getModelStatus.mockRejectedValue(new Error('Network Error'));
      
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to load AI models/)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
      });
      
      expect(screen.getByRole('button', { name: /Ask/i })).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      renderWithTheme(<RAG />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toBeInTheDocument();
      });
      
      // Tab through elements
      await user.tab();
      expect(screen.getByLabelText('AI Model')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByPlaceholderText(/Ask a question about your sustainability documents/)).toHaveFocus();
    });
  });
});