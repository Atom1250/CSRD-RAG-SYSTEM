import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Documents from './Documents';
import { documentService } from '../services/documentService';

// Mock the document service
jest.mock('../services/documentService');
const mockDocumentService = documentService as jest.Mocked<typeof documentService>;

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Documents Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDocumentService.getDocuments.mockResolvedValue([]);
  });

  describe('Complete Document Management Workflow', () => {
    test('complete upload workflow with drag and drop', async () => {
      const user = userEvent.setup();
      
      // Mock successful upload
      const mockDocument = {
        id: '1',
        filename: 'test-document.pdf',
        file_path: '/documents/test-document.pdf',
        file_size: 1024000,
        upload_date: '2023-12-01T10:00:00Z',
        document_type: 'pdf',
        schema_type: 'EU_ESRS_CSRD',
        processing_status: 'processed',
        metadata: {},
      };
      
      mockDocumentService.uploadDocument.mockResolvedValue(mockDocument);
      mockDocumentService.getDocuments
        .mockResolvedValueOnce([]) // Initial empty state
        .mockResolvedValueOnce([mockDocument]); // After upload
      
      renderWithTheme(<Documents />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('No documents uploaded yet')).toBeInTheDocument();
      });
      
      // Test drag and drop functionality
      const dropZone = screen.getByText('Document Repository').closest('div');
      const file = new File(['test content'], 'test-document.pdf', { type: 'application/pdf' });
      
      // Simulate drag enter
      if (dropZone) {
        fireEvent.dragEnter(dropZone);
        await waitFor(() => {
          expect(screen.getByText('Drop files here to upload')).toBeInTheDocument();
        });
        
        // Simulate file drop
        fireEvent.drop(dropZone, {
          dataTransfer: { files: [file] },
        });
        
        // Upload dialog should open with file pre-selected
        await waitFor(() => {
          expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
        });
        
        // Select schema type
        const schemaSelect = screen.getByLabelText('Schema Type');
        await user.click(schemaSelect);
        await user.click(screen.getByText('EU ESRS/CSRD'));
        
        // Submit upload
        const uploadButton = screen.getByRole('button', { name: /^upload$/i });
        await user.click(uploadButton);
        
        // Verify upload was called
        await waitFor(() => {
          expect(mockDocumentService.uploadDocument).toHaveBeenCalledWith({
            file,
            schema_type: 'EU_ESRS_CSRD',
          });
        });
        
        // Verify success message
        expect(screen.getByText('Document uploaded successfully')).toBeInTheDocument();
      }
    });

    test('complete document management with filtering and deletion', async () => {
      const user = userEvent.setup();
      
      const mockDocuments = [
        {
          id: '1',
          filename: 'ESRS_Standards.pdf',
          file_path: '/documents/ESRS_Standards.pdf',
          file_size: 2500000,
          upload_date: '2023-12-01T10:00:00Z',
          document_type: 'pdf',
          schema_type: 'EU_ESRS_CSRD',
          processing_status: 'processed',
          metadata: { description: 'EU sustainability standards' },
        },
        {
          id: '2',
          filename: 'UK_Guidelines.docx',
          file_path: '/documents/UK_Guidelines.docx',
          file_size: 1200000,
          upload_date: '2023-11-15T14:30:00Z',
          document_type: 'docx',
          schema_type: 'UK_SRD',
          processing_status: 'processing',
          metadata: { description: 'UK reporting guidelines' },
        },
      ];
      
      mockDocumentService.getDocuments.mockResolvedValue(mockDocuments);
      mockDocumentService.deleteDocument.mockResolvedValue();
      
      renderWithTheme(<Documents />);
      
      // Wait for documents to load
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards.pdf')).toBeInTheDocument();
        expect(screen.getByText('UK_Guidelines.docx')).toBeInTheDocument();
      });
      
      // Test search filtering
      const searchInput = screen.getByPlaceholderText('Search documents...');
      await user.type(searchInput, 'ESRS');
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards.pdf')).toBeInTheDocument();
        expect(screen.queryByText('UK_Guidelines.docx')).not.toBeInTheDocument();
      });
      
      // Clear search
      await user.clear(searchInput);
      
      // Test schema type filtering
      const schemaFilter = screen.getByDisplayValue('');
      await user.click(schemaFilter);
      await user.click(screen.getByText('UK SRD'));
      
      await waitFor(() => {
        expect(screen.queryByText('ESRS_Standards.pdf')).not.toBeInTheDocument();
        expect(screen.getByText('UK_Guidelines.docx')).toBeInTheDocument();
      });
      
      // Reset filters
      await user.click(schemaFilter);
      await user.click(screen.getByText('All'));
      
      // Test view mode switching
      const listViewButton = screen.getByRole('button', { name: /list view/i });
      await user.click(listViewButton);
      
      // Verify table view
      expect(screen.getByText('Filename')).toBeInTheDocument();
      expect(screen.getByText('Size')).toBeInTheDocument();
      
      // Test document deletion
      const deleteButtons = screen.getAllByLabelText(/delete document/i);
      await user.click(deleteButtons[0]);
      
      // Confirm deletion
      expect(screen.getByText('Delete Document')).toBeInTheDocument();
      const confirmButton = screen.getByRole('button', { name: /^delete$/i });
      await user.click(confirmButton);
      
      await waitFor(() => {
        expect(mockDocumentService.deleteDocument).toHaveBeenCalledWith('1');
      });
    });

    test('remote directory sync workflow', async () => {
      const user = userEvent.setup();
      
      const syncedDocuments = [
        {
          id: '3',
          filename: 'remote-doc.pdf',
          file_path: '/remote/remote-doc.pdf',
          file_size: 800000,
          upload_date: '2023-12-02T09:00:00Z',
          document_type: 'pdf',
          schema_type: 'OTHER',
          processing_status: 'processed',
          metadata: {},
        },
      ];
      
      mockDocumentService.getDocuments
        .mockResolvedValueOnce([]) // Initial state
        .mockResolvedValueOnce(syncedDocuments); // After sync
      mockDocumentService.syncRemoteDirectory.mockResolvedValue(syncedDocuments);
      
      renderWithTheme(<Documents />);
      
      // Open remote directory dialog
      const remoteButton = screen.getByText('Remote Directory');
      await user.click(remoteButton);
      
      // Enter directory path
      const pathInput = screen.getByLabelText('Remote Directory Path');
      await user.type(pathInput, '/path/to/remote/documents');
      
      // Sync directory
      const syncButton = screen.getByRole('button', { name: /sync directory/i });
      await user.click(syncButton);
      
      await waitFor(() => {
        expect(mockDocumentService.syncRemoteDirectory).toHaveBeenCalledWith('/path/to/remote/documents');
      });
      
      // Verify success message
      expect(screen.getByText('Remote directory synced successfully')).toBeInTheDocument();
    });
  });

  describe('Error Handling Integration', () => {
    test('handles network errors gracefully', async () => {
      mockDocumentService.getDocuments.mockRejectedValue(new Error('Network error'));
      
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load documents')).toBeInTheDocument();
      });
    });

    test('handles upload errors with user feedback', async () => {
      const user = userEvent.setup();
      mockDocumentService.uploadDocument.mockRejectedValue(new Error('Upload failed'));
      
      renderWithTheme(<Documents />);
      
      // Open upload dialog
      const uploadButton = screen.getByText('Upload Document');
      await user.click(uploadButton);
      
      // Select file and schema
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, file);
      
      const schemaSelect = screen.getByLabelText('Schema Type');
      await user.click(schemaSelect);
      await user.click(screen.getByText('EU ESRS/CSRD'));
      
      // Attempt upload
      const submitButton = screen.getByRole('button', { name: /^upload$/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to upload document')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility Integration', () => {
    test('maintains accessibility standards throughout workflow', async () => {
      const user = userEvent.setup();
      
      renderWithTheme(<Documents />);
      
      // Check main heading
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Document Repository');
      
      // Check button accessibility
      const uploadButton = screen.getByRole('button', { name: /upload document/i });
      expect(uploadButton).toBeInTheDocument();
      
      // Open dialog and check accessibility
      await user.click(uploadButton);
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      
      // Check form labels
      expect(screen.getByLabelText('Schema Type')).toBeInTheDocument();
      
      // Check button states
      const submitButton = screen.getByRole('button', { name: /^upload$/i });
      expect(submitButton).toBeDisabled(); // Should be disabled without file
    });
  });
});