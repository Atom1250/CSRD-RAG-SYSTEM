import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ErrorProvider, useError } from '../ErrorContext';

// Test component that uses the error context
const TestComponent: React.FC = () => {
  const { showError, showSuccess, showWarning, showInfo, clearErrors } = useError();

  return (
    <div>
      <button onClick={() => showError('Test error message')}>Show Error</button>
      <button onClick={() => showSuccess('Test success message')}>Show Success</button>
      <button onClick={() => showWarning('Test warning message')}>Show Warning</button>
      <button onClick={() => showInfo('Test info message')}>Show Info</button>
      <button onClick={clearErrors}>Clear Errors</button>
    </div>
  );
};

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <ErrorProvider>
      {component}
    </ErrorProvider>
  );
};

describe('ErrorContext', () => {
  beforeEach(() => {
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should show error messages', async () => {
    renderWithProvider(<TestComponent />);
    
    fireEvent.click(screen.getByText('Show Error'));
    
    await waitFor(() => {
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });
  });

  it('should show success messages', async () => {
    renderWithProvider(<TestComponent />);
    
    fireEvent.click(screen.getByText('Show Success'));
    
    await waitFor(() => {
      expect(screen.getByText('Test success message')).toBeInTheDocument();
    });
  });

  it('should show warning messages', async () => {
    renderWithProvider(<TestComponent />);
    
    fireEvent.click(screen.getByText('Show Warning'));
    
    await waitFor(() => {
      expect(screen.getByText('Test warning message')).toBeInTheDocument();
    });
  });

  it('should show info messages', async () => {
    renderWithProvider(<TestComponent />);
    
    fireEvent.click(screen.getByText('Show Info'));
    
    await waitFor(() => {
      expect(screen.getByText('Test info message')).toBeInTheDocument();
    });
  });

  it('should auto-remove messages after duration', async () => {
    renderWithProvider(<TestComponent />);
    
    fireEvent.click(screen.getByText('Show Error'));
    
    await waitFor(() => {
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    // Fast-forward time
    jest.advanceTimersByTime(6000);

    await waitFor(() => {
      expect(screen.queryByText('Test error message')).not.toBeInTheDocument();
    });
  });

  it('should clear all errors when clearErrors is called', async () => {
    renderWithProvider(<TestComponent />);
    
    fireEvent.click(screen.getByText('Show Error'));
    fireEvent.click(screen.getByText('Show Warning'));
    
    await waitFor(() => {
      expect(screen.getByText('Test error message')).toBeInTheDocument();
      expect(screen.getByText('Test warning message')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Clear Errors'));

    await waitFor(() => {
      expect(screen.queryByText('Test error message')).not.toBeInTheDocument();
      expect(screen.queryByText('Test warning message')).not.toBeInTheDocument();
    });
  });

  it('should stack multiple notifications', async () => {
    renderWithProvider(<TestComponent />);
    
    fireEvent.click(screen.getByText('Show Error'));
    fireEvent.click(screen.getByText('Show Success'));
    fireEvent.click(screen.getByText('Show Warning'));
    
    await waitFor(() => {
      expect(screen.getByText('Test error message')).toBeInTheDocument();
      expect(screen.getByText('Test success message')).toBeInTheDocument();
      expect(screen.getByText('Test warning message')).toBeInTheDocument();
    });
  });

  it('should throw error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useError must be used within an ErrorProvider');
    
    consoleSpy.mockRestore();
  });
});