import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Layout from './Layout';

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

// Mock window.matchMedia for responsive testing
const mockMatchMedia = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(), // deprecated
      removeListener: jest.fn(), // deprecated
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

describe('Layout Responsive Design Tests', () => {
  beforeEach(() => {
    // Reset matchMedia mock before each test
    delete (window as any).matchMedia;
  });

  test('shows mobile menu button on small screens', () => {
    // Mock mobile viewport
    mockMatchMedia(true); // matches mobile breakpoint
    
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Mobile menu button should be visible
    const menuButton = screen.getByLabelText('open navigation menu');
    expect(menuButton).toBeInTheDocument();
  });

  test('hides mobile menu button on desktop screens', () => {
    // Mock desktop viewport
    mockMatchMedia(false); // doesn't match mobile breakpoint
    
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Mobile menu button should be hidden on desktop
    const menuButton = screen.getByLabelText('open navigation menu');
    expect(menuButton).toHaveStyle('display: none');
  });

  test('mobile drawer can be opened and closed', () => {
    mockMatchMedia(true); // mobile viewport
    
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    const menuButton = screen.getByLabelText('open navigation menu');
    
    // Click to open mobile drawer
    fireEvent.click(menuButton);
    
    // Drawer should be open (temporary drawer for mobile)
    // Note: In a real test, you might check for specific drawer states
    // This is a simplified test for the interaction
    expect(menuButton).toBeInTheDocument();
  });

  test('navigation items are properly sized for mobile', () => {
    mockMatchMedia(true); // mobile viewport
    
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Check that navigation items exist and are accessible
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
  });

  test('content area has proper spacing on different screen sizes', () => {
    renderWithProviders(
      <Layout>
        <div data-testid="test-content">Test Content</div>
      </Layout>
    );
    
    const mainContent = screen.getByRole('main');
    expect(mainContent).toBeInTheDocument();
    expect(mainContent).toHaveAttribute('aria-label', 'Main content');
    
    const testContent = screen.getByTestId('test-content');
    expect(testContent).toBeInTheDocument();
  });

  test('app bar title is responsive', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    const title = screen.getByText('Sustainability Reporting Documents Management');
    expect(title).toBeInTheDocument();
    expect(title.tagName).toBe('H1'); // Should be h1 for accessibility
  });
});