import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Dashboard from './Dashboard';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Dashboard Component', () => {
  test('renders dashboard title', () => {
    renderWithTheme(<Dashboard />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  test('renders statistics cards', () => {
    renderWithTheme(<Dashboard />);
    expect(screen.getByText('Total Documents')).toBeInTheDocument();
    expect(screen.getByText('Search Queries')).toBeInTheDocument();
    expect(screen.getByText('RAG Responses')).toBeInTheDocument();
    expect(screen.getByText('Generated Reports')).toBeInTheDocument();
  });

  test('renders recent activity section', () => {
    renderWithTheme(<Dashboard />);
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('System initialized')).toBeInTheDocument();
  });

  test('renders quick actions section', () => {
    renderWithTheme(<Dashboard />);
    expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    expect(screen.getByText(/Upload your first document/)).toBeInTheDocument();
  });

  test('has proper accessibility structure', () => {
    renderWithTheme(<Dashboard />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Dashboard');
  });
});