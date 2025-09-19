import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Backdrop, CircularProgress, Typography, Box, LinearProgress } from '@mui/material';

interface LoadingState {
  id: string;
  message: string;
  progress?: number;
  type: 'backdrop' | 'inline' | 'progress';
}

interface LoadingContextType {
  showLoading: (message: string, id?: string, type?: 'backdrop' | 'inline' | 'progress') => string;
  hideLoading: (id: string) => void;
  updateProgress: (id: string, progress: number, message?: string) => void;
  isLoading: (id?: string) => boolean;
  getLoadingState: (id: string) => LoadingState | undefined;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export const useLoading = () => {
  const context = useContext(LoadingContext);
  if (!context) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
};

interface LoadingProviderProps {
  children: ReactNode;
}

export const LoadingProvider: React.FC<LoadingProviderProps> = ({ children }) => {
  const [loadingStates, setLoadingStates] = useState<LoadingState[]>([]);

  const showLoading = useCallback((message: string, id?: string, type: 'backdrop' | 'inline' | 'progress' = 'backdrop') => {
    const loadingId = id || Date.now().toString();
    const newState: LoadingState = { id: loadingId, message, type };
    
    setLoadingStates(prev => {
      const filtered = prev.filter(state => state.id !== loadingId);
      return [...filtered, newState];
    });
    
    return loadingId;
  }, []);

  const hideLoading = useCallback((id: string) => {
    setLoadingStates(prev => prev.filter(state => state.id !== id));
  }, []);

  const updateProgress = useCallback((id: string, progress: number, message?: string) => {
    setLoadingStates(prev => prev.map(state => 
      state.id === id 
        ? { ...state, progress, ...(message && { message }) }
        : state
    ));
  }, []);

  const isLoading = useCallback((id?: string) => {
    if (id) {
      return loadingStates.some(state => state.id === id);
    }
    return loadingStates.length > 0;
  }, [loadingStates]);

  const getLoadingState = useCallback((id: string) => {
    return loadingStates.find(state => state.id === id);
  }, [loadingStates]);

  const backdropLoading = loadingStates.find(state => state.type === 'backdrop');

  const value: LoadingContextType = {
    showLoading,
    hideLoading,
    updateProgress,
    isLoading,
    getLoadingState,
  };

  return (
    <LoadingContext.Provider value={value}>
      {children}
      
      {/* Global backdrop loading */}
      <Backdrop
        sx={{ 
          color: '#fff', 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          flexDirection: 'column',
          gap: 2
        }}
        open={!!backdropLoading}
      >
        <CircularProgress color="inherit" size={60} />
        {backdropLoading && (
          <Box textAlign="center">
            <Typography variant="h6" gutterBottom>
              {backdropLoading.message}
            </Typography>
            {backdropLoading.progress !== undefined && (
              <Box sx={{ width: 300, mt: 2 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={backdropLoading.progress} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {Math.round(backdropLoading.progress)}%
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </Backdrop>
    </LoadingContext.Provider>
  );
};