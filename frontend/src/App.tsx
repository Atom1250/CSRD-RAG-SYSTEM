import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Search from './pages/Search';
import RAG from './pages/RAG';
import Reports from './pages/Reports';
import Schemas from './pages/Schemas';
import { ErrorProvider } from './contexts/ErrorContext';
import { LoadingProvider } from './contexts/LoadingContext';
import ErrorBoundary from './components/common/ErrorBoundary';

function App() {
  return (
    <ErrorProvider>
      <LoadingProvider>
        <ErrorBoundary>
          <Box sx={{ display: 'flex', height: '100vh' }}>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/search" element={<Search />} />
                <Route path="/rag" element={<RAG />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/schemas" element={<Schemas />} />
              </Routes>
            </Layout>
          </Box>
        </ErrorBoundary>
      </LoadingProvider>
    </ErrorProvider>
  );
}

export default App;