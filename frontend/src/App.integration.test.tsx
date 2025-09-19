import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import App from './App';

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement, initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </MemoryRouter>
  );
};

describe('App Integration Tests', () => {
  test('navigates between different pages correctly', async () => {
    renderWithProviders(<App />);
    
    // Start at dashboard
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    
    // Navigate to Documents
    const documentsLink = screen.getByLabelText('Navigate to Documents');
    fireEvent.click(documentsLink);
    
    // Should show documents page content
    await waitFor(() => {
      expect(screen.getByText('Documents')).toBeInTheDocument();
    });
    
    // Navigate to Search
    const searchLink = screen.getByLabelText('Navigate to Search');
    fireEvent.click(searchLink);
    
    await waitFor(() => {
      expect(screen.getByText('Search')).toBeInTheDocument();
    });
    
    // Navigate to RAG
    const ragLink = screen.getByLabelText('Navigate to RAG Query');
    fireEvent.click(ragLink);
    
    await waitFor(() => {
      expect(screen.getByText('RAG Query')).toBeInTheDocument();
    });
    
    // Navigate to Reports
    const reportsLink = screen.getByLabelText('Navigate to Reports');
    fireEvent.click(reportsLink);
    
    await waitFor(() => {
      expect(screen.getByText('Reports')).toBeInTheDocument();
    });
    
    // Navigate to Schemas
    const schemasLink = screen.getByLabelText('Navigate to Schemas');
    fireEvent.click(schemasLink);
    
    await waitFor(() => {
      expect(screen.getByText('Schemas')).toBeInTheDocument();
    });
  });

  test('handles direct navigation to different routes', () => {
    // Test direct navigation to documents page
    renderWithProviders(<App />, ['/documents']);
    expect(screen.getByText('Documents')).toBeInTheDocument();
    
    // Test direct navigation to search page
    renderWithProviders(<App />, ['/search']);
    expect(screen.getByText('Search')).toBeInTheDocument();
    
    // Test direct navigation to RAG page
    renderWithProviders(<App />, ['/rag']);
    expect(screen.getByText('RAG Query')).toBeInTheDocument();
    
    // Test direct navigation to reports page
    renderWithProviders(<App />, ['/reports']);
    expect(screen.getByText('Reports')).toBeInTheDocument();
    
    // Test direct navigation to schemas page
    renderWithProviders(<App />, ['/schemas']);
    expect(screen.getByText('Schemas')).toBeInTheDocument();
  });

  test('maintains layout consistency across all pages', () => {
    const pages = ['/', '/documents', '/search', '/rag', '/reports', '/schemas'];
    
    pages.forEach(page => {
      renderWithProviders(<App />, [page]);
      
      // Check that layout elements are present on all pages
      expect(screen.getByText('CSRD RAG System')).toBeInTheDocument();
      expect(screen.getByText('Sustainability Reporting Documents Management')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  test('selected navigation item is highlighted correctly', () => {
    renderWithProviders(<App />, ['/documents']);
    
    // The Documents navigation item should be selected
    const documentsButton = screen.getByLabelText('Navigate to Documents');
    expect(documentsButton.closest('div')).toHaveClass('Mui-selected');
  });

  test('application is fully accessible', async () => {
    renderWithProviders(<App />);
    
    // Check for essential accessibility features
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('banner')).toBeInTheDocument(); // AppBar
    
    // Check for proper heading structure
    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toBeInTheDocument();
  });

  test('responsive behavior works correctly', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query.includes('max-width'),
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });
    
    renderWithProviders(<App />);
    
    // Mobile menu button should be present
    const menuButton = screen.getByLabelText('open navigation menu');
    expect(menuButton).toBeInTheDocument();
  });
});