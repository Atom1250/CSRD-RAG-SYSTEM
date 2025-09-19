import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Alert, Snackbar, AlertColor } from '@mui/material';

interface ErrorMessage {
  id: string;
  message: string;
  severity: AlertColor;
  duration?: number;
}

interface ErrorContextType {
  showError: (message: string, severity?: AlertColor, duration?: number) => void;
  showSuccess: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
  clearErrors: () => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

interface ErrorProviderProps {
  children: ReactNode;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [errors, setErrors] = useState<ErrorMessage[]>([]);

  const showError = useCallback((message: string, severity: AlertColor = 'error', duration = 6000) => {
    const id = Date.now().toString();
    const newError: ErrorMessage = { id, message, severity, duration };
    
    setErrors(prev => [...prev, newError]);
    
    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        setErrors(prev => prev.filter(error => error.id !== id));
      }, duration);
    }
  }, []);

  const showSuccess = useCallback((message: string, duration = 4000) => {
    showError(message, 'success', duration);
  }, [showError]);

  const showWarning = useCallback((message: string, duration = 5000) => {
    showError(message, 'warning', duration);
  }, [showError]);

  const showInfo = useCallback((message: string, duration = 4000) => {
    showError(message, 'info', duration);
  }, [showError]);

  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  const handleClose = (id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  };

  const value: ErrorContextType = {
    showError,
    showSuccess,
    showWarning,
    showInfo,
    clearErrors,
  };

  return (
    <ErrorContext.Provider value={value}>
      {children}
      {errors.map((error) => (
        <Snackbar
          key={error.id}
          open={true}
          autoHideDuration={error.duration}
          onClose={() => handleClose(error.id)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{ 
            position: 'fixed',
            bottom: 16 + (errors.indexOf(error) * 70), // Stack multiple notifications
            right: 16,
            zIndex: 9999
          }}
        >
          <Alert 
            onClose={() => handleClose(error.id)} 
            severity={error.severity} 
            sx={{ width: '100%', minWidth: 300 }}
            variant="filled"
          >
            {error.message}
          </Alert>
        </Snackbar>
      ))}
    </ErrorContext.Provider>
  );
};