import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Search from './Search';

// Mock the API module
jest.mock('../services/api');

// Mock theme
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

// Mock fetch for API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('Search Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/search/suggestions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            suggestions: ['climate change adaptation', 'greenhouse gas emissions'],
          }),
        });
      }
      
      if (url.includes('/search/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              chunk_id: 'chunk-1',
              document_id: 'doc-1',
              content: 'Climate change adaptation strategies are essential for corporate sustainability.',
              relevance_score: 0.95,
              document_filename: 'Climate_Adaptation_Guide.pdf',
              schema_elements: ['E1', 'Climate Change'],
            },
          ]),
        });
      }
      
      if (url.includes('/search/statistics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            total_documents: 50,
            total_chunks: 1250,
            chunks_with_embeddings: 1200,
            searchable_documents: true,
            vector_service_available: true,
          }),
        });
      }
      
      return Promise.reject(new Error('Unknown endpoint'));
    });
  });

  it('performs end-to-end search workflow', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Initial state
    expect(screen.getByText('Search Your Sustainability Documents')).toBeInTheDocument();

    // Type search query
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'climate adaptation');

    // Perform search
    await user.keyboard('{Enter}');

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Search Results (1)')).toBeInTheDocument();
      expect(screen.getByText('Climate_Adaptation_Guide.pdf')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
    });

    // Verify API call was made
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/search/'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
        body: expect.stringContaining('climate adaptation'),
      })
    );
  });

  it('handles search with filters applied', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters
    await user.click(screen.getByRole('button', { name: /filters/i }));

    // Apply document type filter
    const documentTypeSelect = screen.getByLabelText('Document Type');
    await user.click(documentTypeSelect);
    await user.click(screen.getByText('PDF'));

    // Apply schema type filter
    const schemaTypeSelect = screen.getByLabelText('Schema Type');
    await user.click(schemaTypeSelect);
    await user.click(screen.getByText('EU ESRS/CSRD'));

    // Perform search
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'sustainability reporting');
    await user.keyboard('{Enter}');

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Search Results (1)')).toBeInTheDocument();
    });

    // Verify API call includes filters
    const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1];
    const requestBody = JSON.parse(lastCall[1].body);
    
    expect(requestBody).toMatchObject({
      query: 'sustainability reporting',
      document_type: 'pdf',
      schema_type: 'EU_ESRS_CSRD',
    });
  });

  it('handles search suggestions workflow', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');

    // Type partial query to trigger suggestions
    await user.type(searchInput, 'cl');

    // Wait for suggestions to appear
    await waitFor(() => {
      expect(screen.getByText('climate change adaptation')).toBeInTheDocument();
    });

    // Click on suggestion
    await user.click(screen.getByText('climate change adaptation'));

    // Verify suggestion was selected and search triggered
    expect(searchInput).toHaveValue('climate change adaptation');
    
    await waitFor(() => {
      expect(screen.getByText('Search Results (1)')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    
    // Mock API error
    mockFetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it('handles empty search results', async () => {
    const user = userEvent.setup();
    
    // Mock empty results
    mockFetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      })
    );
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'nonexistent query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('No results found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search terms or filters')).toBeInTheDocument();
    });
  });

  it('displays search performance metrics', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'performance test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Search Results (1)')).toBeInTheDocument();
      // Should show search time
      expect(screen.getByText(/Found in \d+ms/)).toBeInTheDocument();
    });
  });

  it('handles relevance score filtering', async () => {
    const user = userEvent.setup();
    
    // Mock results with different relevance scores
    mockFetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          {
            chunk_id: 'chunk-1',
            document_id: 'doc-1',
            content: 'High relevance content',
            relevance_score: 0.95,
            document_filename: 'High_Relevance.pdf',
            schema_elements: ['E1'],
          },
          {
            chunk_id: 'chunk-2',
            document_id: 'doc-2',
            content: 'Low relevance content',
            relevance_score: 0.45,
            document_filename: 'Low_Relevance.pdf',
            schema_elements: ['E2'],
          },
        ]),
      })
    );
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters and set minimum relevance score
    await user.click(screen.getByRole('button', { name: /filters/i }));
    
    const slider = screen.getByRole('slider');
    await user.click(slider); // This should set it to around 0.5

    // Perform search
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'relevance test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Search Results (2)')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('45%')).toBeInTheDocument();
    });
  });

  it('handles schema element display and overflow', async () => {
    const user = userEvent.setup();
    
    // Mock result with many schema elements
    mockFetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          {
            chunk_id: 'chunk-1',
            document_id: 'doc-1',
            content: 'Content with many schema elements',
            relevance_score: 0.85,
            document_filename: 'Multi_Schema.pdf',
            schema_elements: ['E1', 'E2', 'E3', 'E4', 'E5', 'Climate', 'Biodiversity', 'Water'],
          },
        ]),
      })
    );
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'schema test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('E1')).toBeInTheDocument();
      expect(screen.getByText('E2')).toBeInTheDocument();
      expect(screen.getByText('E3')).toBeInTheDocument();
      expect(screen.getByText('+5 more')).toBeInTheDocument();
    });
  });

  it('handles content truncation and expansion', async () => {
    const user = userEvent.setup();
    
    const longContent = 'A'.repeat(400) + ' This is additional content that should be truncated in the initial display.';
    
    mockFetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          {
            chunk_id: 'chunk-1',
            document_id: 'doc-1',
            content: longContent,
            relevance_score: 0.85,
            document_filename: 'Long_Content.pdf',
            schema_elements: ['E1'],
          },
        ]),
      })
    );
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'long content');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/A{300}\.\.\./, { exact: false })).toBeInTheDocument();
      expect(screen.getByText('Show full content')).toBeInTheDocument();
    });
  });

  it('maintains search state during filter changes', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Perform initial search
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'initial query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Search Results (1)')).toBeInTheDocument();
    });

    // Open filters and change settings
    await user.click(screen.getByRole('button', { name: /filters/i }));
    
    const documentTypeSelect = screen.getByLabelText('Document Type');
    await user.click(documentTypeSelect);
    await user.click(screen.getByText('PDF'));

    // Search input should still contain the query
    expect(searchInput).toHaveValue('initial query');
  });

  it('handles concurrent search requests', async () => {
    const user = userEvent.setup();
    
    let resolveFirst: (value: any) => void;
    let resolveSecond: (value: any) => void;
    
    const firstPromise = new Promise(resolve => { resolveFirst = resolve; });
    const secondPromise = new Promise(resolve => { resolveSecond = resolve; });
    
    mockFetch
      .mockImplementationOnce(() => firstPromise)
      .mockImplementationOnce(() => secondPromise);
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');

    // Start first search
    await user.type(searchInput, 'first query');
    await user.keyboard('{Enter}');

    // Start second search before first completes
    await user.clear(searchInput);
    await user.type(searchInput, 'second query');
    await user.keyboard('{Enter}');

    // Resolve second search first
    resolveSecond!({
      ok: true,
      json: () => Promise.resolve([
        {
          chunk_id: 'chunk-2',
          document_id: 'doc-2',
          content: 'Second query result',
          relevance_score: 0.85,
          document_filename: 'Second.pdf',
          schema_elements: [],
        },
      ]),
    });

    await waitFor(() => {
      expect(screen.getByText('Second query result')).toBeInTheDocument();
    });

    // Resolve first search (should not override second results)
    resolveFirst!({
      ok: true,
      json: () => Promise.resolve([
        {
          chunk_id: 'chunk-1',
          document_id: 'doc-1',
          content: 'First query result',
          relevance_score: 0.95,
          document_filename: 'First.pdf',
          schema_elements: [],
        },
      ]),
    });

    // Should still show second results
    await waitFor(() => {
      expect(screen.getByText('Second query result')).toBeInTheDocument();
      expect(screen.queryByText('First query result')).not.toBeInTheDocument();
    });
  });
});