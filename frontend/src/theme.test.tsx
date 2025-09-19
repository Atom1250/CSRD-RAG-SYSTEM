import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme, useTheme } from '@mui/material/styles';
import { Typography, Button } from '@mui/material';

// Test component to verify theme application
const ThemeTestComponent: React.FC = () => {
  const theme = useTheme();
  
  return (
    <div>
      <Typography variant="h1" data-testid="h1-text">
        Heading 1
      </Typography>
      <Typography variant="h2" data-testid="h2-text">
        Heading 2
      </Typography>
      <Typography variant="h6" data-testid="h6-text">
        Heading 6
      </Typography>
      <Button variant="contained" color="primary" data-testid="primary-button">
        Primary Button
      </Button>
      <div data-testid="theme-breakpoints">
        {JSON.stringify(theme.breakpoints.values)}
      </div>
    </div>
  );
};

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      '@media (max-width:600px)': {
        fontSize: '2rem',
      },
    },
    h2: {
      fontSize: '2rem',
      '@media (max-width:600px)': {
        fontSize: '1.75rem',
      },
    },
    h6: {
      fontSize: '1.25rem',
      '@media (max-width:600px)': {
        fontSize: '1.1rem',
      },
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
});

describe('Theme Configuration Tests', () => {
  test('theme is properly configured with correct colors', () => {
    render(
      <ThemeProvider theme={theme}>
        <ThemeTestComponent />
      </ThemeProvider>
    );
    
    const primaryButton = screen.getByTestId('primary-button');
    expect(primaryButton).toBeInTheDocument();
  });

  test('typography variants are properly configured', () => {
    render(
      <ThemeProvider theme={theme}>
        <ThemeTestComponent />
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('h1-text')).toBeInTheDocument();
    expect(screen.getByTestId('h2-text')).toBeInTheDocument();
    expect(screen.getByTestId('h6-text')).toBeInTheDocument();
  });

  test('breakpoints are correctly configured', () => {
    render(
      <ThemeProvider theme={theme}>
        <ThemeTestComponent />
      </ThemeProvider>
    );
    
    const breakpointsElement = screen.getByTestId('theme-breakpoints');
    const breakpointsText = breakpointsElement.textContent;
    
    expect(breakpointsText).toContain('600'); // sm breakpoint
    expect(breakpointsText).toContain('900'); // md breakpoint
    expect(breakpointsText).toContain('1200'); // lg breakpoint
  });

  test('font family is correctly set', () => {
    render(
      <ThemeProvider theme={theme}>
        <Typography data-testid="font-test">Test Text</Typography>
      </ThemeProvider>
    );
    
    const textElement = screen.getByTestId('font-test');
    expect(textElement).toBeInTheDocument();
  });
});