import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { axe, toHaveNoViolations } from 'jest-axe';
import Layout from './Layout';

expect.extend(toHaveNoViolations);

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

describe('Layout Accessibility Tests', () => {
  test('should not have any accessibility violations', async () => {
    const { container } = renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('has proper ARIA labels and roles', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Check for navigation role
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByLabelText('Main navigation')).toBeInTheDocument();
    
    // Check for main content area
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByLabelText('Main content')).toBeInTheDocument();
    
    // Check for menu button accessibility
    expect(screen.getByLabelText('open navigation menu')).toBeInTheDocument();
  });

  test('navigation items have proper accessibility attributes', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Check that navigation items have proper aria-labels
    expect(screen.getByLabelText('Navigate to Dashboard')).toBeInTheDocument();
    expect(screen.getByLabelText('Navigate to Documents')).toBeInTheDocument();
    expect(screen.getByLabelText('Navigate to Search')).toBeInTheDocument();
    expect(screen.getByLabelText('Navigate to RAG Query')).toBeInTheDocument();
    expect(screen.getByLabelText('Navigate to Reports')).toBeInTheDocument();
    expect(screen.getByLabelText('Navigate to Schemas')).toBeInTheDocument();
  });

  test('has proper heading hierarchy', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Check for proper heading structure
    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toHaveTextContent('Sustainability Reporting Documents Management');
  });

  test('keyboard navigation works properly', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // All interactive elements should be focusable
    const navigationItems = screen.getAllByRole('button');
    navigationItems.forEach(item => {
      expect(item).toHaveAttribute('tabindex', '0');
    });
  });
});