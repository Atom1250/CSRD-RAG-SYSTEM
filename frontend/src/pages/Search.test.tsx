import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Search from './Search';
import { searchService } from '../services/searchService';

// Mock the search service
jest.mock('../services/searchService');
const mockSearchService = searchService as jest.Mocked<typeof searchService>;

// Mock theme
const theme = createTheme();

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

// Mock search results
const mockSearchResults = [
  {
    chunk_id: 'chunk-1',
    document_id: 'doc-1',
    content: 'This is a sample search result about climate change adaptation strategies and their implementation in corporate sustainability reporting.',
    relevance_score: 0.95,
    document_filename: 'ESRS_Climate_Standards.pdf',
    schema_elements: ['E1', 'Climate Change', 'Adaptation'],
  },
  {
    chunk_id: 'chunk-2',
    document_id: 'doc-2',
    content: 'Environmental disclosure requirements under the Corporate Sustainability Reporting Directive (CSRD) mandate comprehensive reporting.',
    relevance_score: 0.87,
    document_filename: 'CSRD_Guidelines_2024.pdf',
    schema_elements: ['Environmental', 'Disclosure'],
  },
];

const mockSuggestions = [
  'climate change adaptation',
  'climate risk assessment',
  'climate governance',
];

describe('Search Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchService.search.mockResolvedValue(mockSearchResults);
    mockSearchService.getSuggestions.mockResolvedValue(mockSuggestions);
  });

  it('renders search interface correctly', () => {
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    expect(screen.getByText('Document Search')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search through your sustainability documents...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /filters/i })).toBeInTheDocument();
  });

  it('displays initial state with sample suggestions', () => {
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    expect(screen.getByText('Search Your Sustainability Documents')).toBeInTheDocument();
    expect(screen.getByText('climate change adaptation')).toBeInTheDocument();
    expect(screen.getByText('greenhouse gas emissions')).toBeInTheDocument();
  });

  it('performs search when search button is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    const searchButton = screen.getByRole('button', { name: /search/i });

    await user.type(searchInput, 'climate change');
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockSearchService.search).toHaveBeenCalledWith({
        query: 'climate change',
        top_k: 20,
        min_relevance_score: 0.0,
        enable_reranking: true,
        document_type: undefined,
        schema_type: undefined,
        processing_status: undefined,
        filename_contains: undefined,
      });
    });
  });

  it('performs search when Enter key is pressed', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');

    await user.type(searchInput, 'sustainability reporting');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'sustainability reporting',
        })
      );
    });
  });

  it('displays search results correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'climate');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Search Results (2)')).toBeInTheDocument();
      expect(screen.getByText('ESRS_Climate_Standards.pdf')).toBeInTheDocument();
      expect(screen.getByText('CSRD_Guidelines_2024.pdf')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('87%')).toBeInTheDocument();
    });
  });

  it('shows and hides search suggestions', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');

    // Type to trigger suggestions
    await user.type(searchInput, 'cl');

    await waitFor(() => {
      expect(mockSearchService.getSuggestions).toHaveBeenCalledWith('cl');
    });

    // Check if suggestions appear
    await waitFor(() => {
      expect(screen.getByText('climate change adaptation')).toBeInTheDocument();
    });

    // Clear input to hide suggestions
    await user.clear(searchInput);
    
    await waitFor(() => {
      expect(screen.queryByText('climate change adaptation')).not.toBeInTheDocument();
    });
  });

  it('handles suggestion clicks', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');

    await user.type(searchInput, 'cl');

    await waitFor(() => {
      expect(screen.getByText('climate change adaptation')).toBeInTheDocument();
    });

    await user.click(screen.getByText('climate change adaptation'));

    expect(searchInput).toHaveValue('climate change adaptation');
    
    // Should trigger search automatically
    await waitFor(() => {
      expect(mockSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'climate change adaptation',
        })
      );
    });
  });

  it('opens and closes filter panel', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const filtersButton = screen.getByRole('button', { name: /filters/i });

    // Open filters
    await user.click(filtersButton);
    expect(screen.getByText('Advanced Search Filters')).toBeInTheDocument();

    // Close filters
    await user.click(filtersButton);
    await waitFor(() => {
      expect(screen.queryByText('Document Type')).not.toBeVisible();
    });
  });

  it('applies document type filter', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters
    await user.click(screen.getByRole('button', { name: /filters/i }));

    // Select document type
    const documentTypeSelect = screen.getByLabelText('Document Type');
    await user.click(documentTypeSelect);
    await user.click(screen.getByText('PDF'));

    // Perform search
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          document_type: 'pdf',
        })
      );
    });
  });

  it('applies schema type filter', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters
    await user.click(screen.getByRole('button', { name: /filters/i }));

    // Select schema type
    const schemaTypeSelect = screen.getByLabelText('Schema Type');
    await user.click(schemaTypeSelect);
    await user.click(screen.getByText('EU ESRS/CSRD'));

    // Perform search
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          schema_type: 'EU_ESRS_CSRD',
        })
      );
    });
  });

  it('applies relevance score filter', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters
    await user.click(screen.getByRole('button', { name: /filters/i }));

    // Adjust relevance score slider
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: 0.5 } });

    // Perform search
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          min_relevance_score: 0.5,
        })
      );
    });
  });

  it('toggles advanced ranking', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters
    await user.click(screen.getByRole('button', { name: /filters/i }));

    // Toggle advanced ranking
    const rankingSwitch = screen.getByRole('checkbox', { name: /enable advanced ranking/i });
    await user.click(rankingSwitch);

    // Perform search
    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          enable_reranking: false,
        })
      );
    });
  });

  it('clears all filters', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters
    await user.click(screen.getByRole('button', { name: /filters/i }));

    // Apply some filters
    const documentTypeSelect = screen.getByLabelText('Document Type');
    await user.click(documentTypeSelect);
    await user.click(screen.getByText('PDF'));

    const filenameInput = screen.getByLabelText('Filename Contains');
    await user.type(filenameInput, 'test');

    // Clear filters
    const clearButton = screen.getByRole('button', { name: /clear all filters/i });
    await user.click(clearButton);

    // Check that filters are cleared
    expect(screen.getByDisplayValue('')).toBeInTheDocument(); // Document type should be empty
    expect(filenameInput).toHaveValue('');
  });

  it('displays no results message', async () => {
    const user = userEvent.setup();
    mockSearchService.search.mockResolvedValue([]);
    
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

  it('displays error message on search failure', async () => {
    const user = userEvent.setup();
    mockSearchService.search.mockRejectedValue(new Error('Search service unavailable'));
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Search service unavailable')).toBeInTheDocument();
    });
  });

  it('shows loading state during search', async () => {
    const user = userEvent.setup();
    
    // Mock a delayed response
    mockSearchService.search.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockSearchResults), 100))
    );
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    const searchButton = screen.getByRole('button', { name: /search/i });

    await user.type(searchInput, 'test query');
    await user.click(searchButton);

    // Check loading state
    expect(screen.getByText('Searching...')).toBeInTheDocument();
    expect(searchButton).toBeDisabled();

    // Wait for search to complete
    await waitFor(() => {
      expect(screen.getByText('Search Results (2)')).toBeInTheDocument();
    });
  });

  it('formats content correctly with truncation', async () => {
    const user = userEvent.setup();
    const longContentResult = {
      ...mockSearchResults[0],
      content: 'A'.repeat(400) + ' This content should be truncated because it exceeds the maximum display length.',
    };
    
    mockSearchService.search.mockResolvedValue([longContentResult]);
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/A{300}\.\.\./, { exact: false })).toBeInTheDocument();
      expect(screen.getByText('Show full content')).toBeInTheDocument();
    });
  });

  it('displays schema elements with overflow handling', async () => {
    const user = userEvent.setup();
    const manyElementsResult = {
      ...mockSearchResults[0],
      schema_elements: ['E1', 'E2', 'E3', 'E4', 'E5', 'Climate', 'Adaptation', 'Mitigation'],
    };
    
    mockSearchService.search.mockResolvedValue([manyElementsResult]);
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');
    await user.type(searchInput, 'test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('E1')).toBeInTheDocument();
      expect(screen.getByText('E2')).toBeInTheDocument();
      expect(screen.getByText('E3')).toBeInTheDocument();
      expect(screen.getByText('+5 more')).toBeInTheDocument();
    });
  });

  it('shows filter count in filters button', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    // Open filters
    await user.click(screen.getByRole('button', { name: /filters/i }));

    // Apply filters
    const documentTypeSelect = screen.getByLabelText('Document Type');
    await user.click(documentTypeSelect);
    await user.click(screen.getByText('PDF'));

    const filenameInput = screen.getByLabelText('Filename Contains');
    await user.type(filenameInput, 'test');

    // Check filter count
    expect(screen.getByText(/filters \(2\)/i)).toBeInTheDocument();
  });

  it('handles escape key to close suggestions', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Search />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search through your sustainability documents...');

    // Type to show suggestions
    await user.type(searchInput, 'cl');

    await waitFor(() => {
      expect(screen.getByText('climate change adaptation')).toBeInTheDocument();
    });

    // Press escape to close suggestions
    await user.keyboard('{Escape}');

    await waitFor(() => {
      expect(screen.queryByText('climate change adaptation')).not.toBeInTheDocument();
    });
  });
});