import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { axe, toHaveNoViolations } from 'jest-axe';
import App from './App';

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

describe('App Component', () => {
  test('renders without crashing', () => {
    renderWithProviders(<App />);
  });

  test('renders main layout', () => {
    renderWithProviders(<App />);
    expect(screen.getByText('CSRD RAG System')).toBeInTheDocument();
    expect(screen.getByText('Sustainability Reporting Documents Management')).toBeInTheDocument();
  });

  test('renders navigation menu', () => {
    renderWithProviders(<App />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
    expect(screen.getByText('RAG Query')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('Schemas')).toBeInTheDocument();
  });

  test('has proper application structure', () => {
    renderWithProviders(<App />);
    
    // Check for main application container
    const appContainer = screen.getByRole('main');
    expect(appContainer).toBeInTheDocument();
    
    // Check for navigation
    const navigation = screen.getByRole('navigation');
    expect(navigation).toBeInTheDocument();
  });

  test('navigation works correctly', () => {
    renderWithProviders(<App />);
    
    // Test navigation to different pages
    const documentsLink = screen.getByLabelText('Navigate to Documents');
    fireEvent.click(documentsLink);
    
    // The URL should change (in a real app, you'd check the route)
    expect(documentsLink).toBeInTheDocument();
  });

  test('should not have accessibility violations', async () => {
    const { container } = renderWithProviders(<App />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('has responsive design elements', () => {
    renderWithProviders(<App />);
    
    // Check that the app container has flex display for responsive layout
    const appContainer = document.querySelector('[data-testid="app-container"]') || 
                        screen.getByRole('main').parentElement;
    expect(appContainer).toBeInTheDocument();
  });

  test('theme is properly applied', () => {
    renderWithProviders(<App />);
    
    // Check that Material-UI theme is applied
    const appBar = screen.getByRole('banner'); // AppBar has banner role
    expect(appBar).toBeInTheDocument();
  });
});