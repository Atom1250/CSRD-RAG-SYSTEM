import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Documents from '../Documents';
import { ErrorProvider } from '../../contexts/ErrorContext';
import { LoadingProvider } from '../../contexts/LoadingContext';
import * as documentService from '../../services/documentService';
import { ApiError } from '../../services/api';

// Mock the document service
jest.mock('../../services/documentService');
const mockDocumentService = documentService as jest.Mocked<typeof documentService>;

// Mock file for testing
const createMockFile = (name: string, size: number, type: string) => {
  const file = new File(['content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <ErrorProvider>
          <LoadingProvider>
            {component}
          </LoadingProvider>
        </ErrorProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Documents - Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDocumentService.getDocuments.mockResolvedValue([]);
  });

  describe('File Upload Error Handling', () => {
    it('should show error for invalid file type', async () => {
      renderWithProviders(<Documents />);
      
      // Open upload dialog
      fireEvent.click(screen.getByText('Upload Document'));
      
      // Create invalid file
      const invalidFile = createMockFile('test.exe', 1024 * 1024, 'application/x-executable');
      
      // Simulate file selection
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [invalidFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/File type.*not supported/)).toBeInTheDocument();
      });
    });

    it('should show error for file too large', async () => {
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Upload Document'));
      
      // Create oversized file (100MB)
      const largeFile = createMockFile('large.pdf', 100 * 1024 * 1024, 'application/pdf');
      
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [largeFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      await waitFor(() => {
        expect(screen.getByText(/exceeds maximum allowed size/)).toBeInTheDocument();
      });
    });

    it('should show error for file too small', async () => {
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Upload Document'));
      
      // Create tiny file (100 bytes)
      const tinyFile = createMockFile('tiny.pdf', 100, 'application/pdf');
      
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [tinyFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      await waitFor(() => {
        expect(screen.getByText(/below minimum required size/)).toBeInTheDocument();
      });
    });

    it('should handle upload API errors', async () => {
      const apiError: ApiError = {
        type: 'ValidationError',
        status_code: 422,
        message: 'Document processing failed',
        timestamp: Date.now()
      };
      
      mockDocumentService.uploadDocument.mockRejectedValue(apiError);
      
      renderWithProviders(<Documents />);
      
      // Open upload dialog and select valid file
      fireEvent.click(screen.getByText('Upload Document'));
      
      const validFile = createMockFile('test.pdf', 1024 * 1024, 'application/pdf');
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [validFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      // Select schema type
      const schemaSelect = screen.getByLabelText('Schema Type *');
      fireEvent.mouseDown(schemaSelect);
      fireEvent.click(screen.getByText('EU ESRS/CSRD'));
      
      // Attempt upload
      fireEvent.click(screen.getByText('Upload'));
      
      // Should show error notification
      await waitFor(() => {
        expect(screen.getByText(/Upload validation failed/)).toBeInTheDocument();
      });
    });

    it('should handle network errors during upload', async () => {
      const networkError: ApiError = {
        type: 'NetworkError',
        status_code: 0,
        message: 'Network error',
        timestamp: Date.now()
      };
      
      mockDocumentService.uploadDocument.mockRejectedValue(networkError);
      
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Upload Document'));
      
      const validFile = createMockFile('test.pdf', 1024 * 1024, 'application/pdf');
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [validFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      const schemaSelect = screen.getByLabelText('Schema Type *');
      fireEvent.mouseDown(schemaSelect);
      fireEvent.click(screen.getByText('EU ESRS/CSRD'));
      
      fireEvent.click(screen.getByText('Upload'));
      
      await waitFor(() => {
        expect(screen.getByText(/network issues/)).toBeInTheDocument();
      });
    });
  });

  describe('Remote Directory Error Handling', () => {
    it('should validate remote directory path', async () => {
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Remote Directory'));
      
      // Enter invalid path with security issue
      const pathInput = screen.getByLabelText('Remote Directory Path');
      fireEvent.change(pathInput, { target: { value: '../../../etc/passwd' } });
      fireEvent.blur(pathInput);
      
      await waitFor(() => {
        expect(screen.getByText(/security reasons/)).toBeInTheDocument();
      });
    });

    it('should handle remote directory sync errors', async () => {
      const apiError: ApiError = {
        type: 'RemoteDirectoryError',
        status_code: 502,
        message: 'Remote directory not accessible',
        timestamp: Date.now()
      };
      
      mockDocumentService.syncRemoteDirectory.mockRejectedValue(apiError);
      
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Remote Directory'));
      
      const pathInput = screen.getByLabelText('Remote Directory Path');
      fireEvent.change(pathInput, { target: { value: '/valid/path' } });
      
      fireEvent.click(screen.getByText('Sync Directory'));
      
      await waitFor(() => {
        expect(screen.getByText(/Remote directory sync failed/)).toBeInTheDocument();
      });
    });
  });

  describe('Document Loading Error Handling', () => {
    it('should handle document loading errors', async () => {
      const apiError: ApiError = {
        type: 'HTTPError',
        status_code: 500,
        message: 'Internal server error',
        timestamp: Date.now()
      };
      
      mockDocumentService.getDocuments.mockRejectedValue(apiError);
      
      renderWithProviders(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to load documents/)).toBeInTheDocument();
      });
    });

    it('should handle network errors when loading documents', async () => {
      const networkError: ApiError = {
        type: 'NetworkError',
        status_code: 0,
        message: 'Network error',
        timestamp: Date.now()
      };
      
      mockDocumentService.getDocuments.mockRejectedValue(networkError);
      
      renderWithProviders(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText(/Unable to connect to server/)).toBeInTheDocument();
      });
    });
  });

  describe('Document Deletion Error Handling', () => {
    it('should handle document deletion errors', async () => {
      const mockDocument = {
        id: '1',
        filename: 'test.pdf',
        file_size: 1024 * 1024,
        upload_date: new Date().toISOString(),
        schema_type: 'EU_ESRS_CSRD',
        processing_status: 'processed',
        metadata: {}
      };
      
      mockDocumentService.getDocuments.mockResolvedValue([mockDocument]);
      
      const apiError: ApiError = {
        type: 'HTTPError',
        status_code: 404,
        message: 'Document not found',
        timestamp: Date.now()
      };
      
      mockDocumentService.deleteDocument.mockRejectedValue(apiError);
      
      renderWithProviders(<Documents />);
      
      // Wait for documents to load
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });
      
      // Click delete button
      const deleteButton = screen.getByLabelText('Delete Document');
      fireEvent.click(deleteButton);
      
      // Confirm deletion
      fireEvent.click(screen.getByText('Delete'));
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to delete document/)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading indicator during document upload', async () => {
      // Mock a delayed upload
      mockDocumentService.uploadDocument.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 1000))
      );
      
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Upload Document'));
      
      const validFile = createMockFile('test.pdf', 1024 * 1024, 'application/pdf');
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [validFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      const schemaSelect = screen.getByLabelText('Schema Type *');
      fireEvent.mouseDown(schemaSelect);
      fireEvent.click(screen.getByText('EU ESRS/CSRD'));
      
      fireEvent.click(screen.getByText('Upload'));
      
      // Should show loading state
      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });

    it('should show loading indicator during remote directory sync', async () => {
      mockDocumentService.syncRemoteDirectory.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 1000))
      );
      
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Remote Directory'));
      
      const pathInput = screen.getByLabelText('Remote Directory Path');
      fireEvent.change(pathInput, { target: { value: '/valid/path' } });
      
      fireEvent.click(screen.getByText('Sync Directory'));
      
      expect(screen.getByText('Syncing...')).toBeInTheDocument();
    });
  });

  describe('Input Validation Feedback', () => {
    it('should provide real-time validation feedback for file selection', async () => {
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Upload Document'));
      
      // Select invalid file
      const invalidFile = createMockFile('test.exe', 1024 * 1024, 'application/x-executable');
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [invalidFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      // Upload button should be disabled
      await waitFor(() => {
        const uploadButton = screen.getByRole('button', { name: /upload/i });
        expect(uploadButton).toBeDisabled();
      });
    });

    it('should provide real-time validation feedback for path input', async () => {
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Remote Directory'));
      
      const pathInput = screen.getByLabelText('Remote Directory Path');
      
      // Enter invalid path
      fireEvent.change(pathInput, { target: { value: '../invalid' } });
      fireEvent.blur(pathInput);
      
      await waitFor(() => {
        // Sync button should be disabled
        const syncButton = screen.getByRole('button', { name: /sync directory/i });
        expect(syncButton).toBeDisabled();
      });
    });
  });

  describe('Success Feedback', () => {
    it('should show success message after successful upload', async () => {
      mockDocumentService.uploadDocument.mockResolvedValue({
        id: '1',
        filename: 'test.pdf',
        file_size: 1024 * 1024,
        upload_date: new Date().toISOString(),
        schema_type: 'EU_ESRS_CSRD',
        processing_status: 'processing',
        metadata: {}
      });
      
      renderWithProviders(<Documents />);
      
      fireEvent.click(screen.getByText('Upload Document'));
      
      const validFile = createMockFile('test.pdf', 1024 * 1024, 'application/pdf');
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      Object.defineProperty(fileInput, 'files', {
        value: [validFile],
        writable: false,
      });
      fireEvent.change(fileInput);
      
      const schemaSelect = screen.getByLabelText('Schema Type *');
      fireEvent.mouseDown(schemaSelect);
      fireEvent.click(screen.getByText('EU ESRS/CSRD'));
      
      fireEvent.click(screen.getByText('Upload'));
      
      await waitFor(() => {
        expect(screen.getByText(/uploaded successfully/)).toBeInTheDocument();
      });
    });
  });
});