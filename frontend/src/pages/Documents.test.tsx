import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Documents from './Documents';
import { documentService } from '../services/documentService';

// Mock the document service
jest.mock('../services/documentService', () => ({
  documentService: {
    getDocuments: jest.fn(),
    uploadDocument: jest.fn(),
    deleteDocument: jest.fn(),
    syncRemoteDirectory: jest.fn(),
  },
}));

const mockDocumentService = documentService as jest.Mocked<typeof documentService>;

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

const mockDocuments = [
  {
    id: '1',
    filename: 'ESRS_Standards_2023.pdf',
    file_path: '/documents/ESRS_Standards_2023.pdf',
    file_size: 2500000,
    upload_date: '2023-12-01T10:00:00Z',
    document_type: 'pdf',
    schema_type: 'EU_ESRS_CSRD',
    processing_status: 'processed',
    metadata: { description: 'EU sustainability reporting standards' },
  },
  {
    id: '2',
    filename: 'UK_SRD_Guidelines.docx',
    file_path: '/documents/UK_SRD_Guidelines.docx',
    file_size: 1200000,
    upload_date: '2023-11-15T14:30:00Z',
    document_type: 'docx',
    schema_type: 'UK_SRD',
    processing_status: 'processing',
    metadata: { description: 'UK sustainability reporting directive' },
  },
];

describe('Documents Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDocumentService.getDocuments.mockResolvedValue([]);
  });

  describe('Basic Rendering', () => {
    test('renders documents page title', async () => {
      renderWithTheme(<Documents />);
      expect(screen.getByText('Document Repository')).toBeInTheDocument();
    });

    test('renders upload and remote directory buttons', async () => {
      renderWithTheme(<Documents />);
      expect(screen.getByText('Upload Document')).toBeInTheDocument();
      expect(screen.getByText('Remote Directory')).toBeInTheDocument();
    });

    test('shows loading state initially', async () => {
      renderWithTheme(<Documents />);
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('shows empty state when no documents', async () => {
      renderWithTheme(<Documents />);
      await waitFor(() => {
        expect(screen.getByText('No documents uploaded yet')).toBeInTheDocument();
      });
    });

    test('has proper accessibility attributes', async () => {
      renderWithTheme(<Documents />);
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Document Repository');
    });
  });

  describe('Document Display', () => {
    beforeEach(() => {
      mockDocumentService.getDocuments.mockResolvedValue(mockDocuments);
    });

    test('displays documents in grid view by default', async () => {
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
        expect(screen.getByText('UK_SRD_Guidelines.docx')).toBeInTheDocument();
      });

      expect(screen.getByText('2.4 MB')).toBeInTheDocument();
      expect(screen.getByText('1.1 MB')).toBeInTheDocument();
    });

    test('switches between grid and list view', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
      });

      // Switch to list view
      const listViewButton = screen.getByRole('button', { name: /list view/i });
      await user.click(listViewButton);

      // Check if table headers are present (list view)
      expect(screen.getByText('Filename')).toBeInTheDocument();
      expect(screen.getByText('Size')).toBeInTheDocument();
      expect(screen.getByText('Upload Date')).toBeInTheDocument();
    });

    test('displays document status chips with correct colors', async () => {
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        const processedChip = screen.getByText('processed');
        const processingChip = screen.getByText('processing');
        
        expect(processedChip).toBeInTheDocument();
        expect(processingChip).toBeInTheDocument();
      });
    });
  });

  describe('Upload Dialog', () => {
    test('opens upload dialog when upload button clicked', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      const uploadButton = screen.getByText('Upload Document');
      await user.click(uploadButton);
      
      expect(screen.getByText('Choose File or Drag & Drop')).toBeInTheDocument();
      expect(screen.getByText('Schema Type')).toBeInTheDocument();
    });

    test('upload dialog has schema selection options', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      const uploadButton = screen.getByText('Upload Document');
      await user.click(uploadButton);
      
      const schemaSelect = screen.getByLabelText('Schema Type');
      await user.click(schemaSelect);
      
      expect(screen.getByText('EU ESRS/CSRD')).toBeInTheDocument();
      expect(screen.getByText('UK SRD')).toBeInTheDocument();
      expect(screen.getByText('Other')).toBeInTheDocument();
    });

    test('upload button is disabled without file and schema', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      const uploadButton = screen.getByText('Upload Document');
      await user.click(uploadButton);
      
      const submitButton = screen.getByRole('button', { name: /^upload$/i });
      expect(submitButton).toBeDisabled();
    });

    test('handles file upload successfully', async () => {
      const user = userEvent.setup();
      mockDocumentService.uploadDocument.mockResolvedValue(mockDocuments[0]);
      
      renderWithTheme(<Documents />);
      
      const uploadButton = screen.getByText('Upload Document');
      await user.click(uploadButton);
      
      // Create a mock file
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = screen.getByLabelText(/choose file/i);
      
      await user.upload(fileInput, file);
      
      // Select schema type
      const schemaSelect = screen.getByLabelText('Schema Type');
      await user.click(schemaSelect);
      await user.click(screen.getByText('EU ESRS/CSRD'));
      
      // Submit upload
      const submitButton = screen.getByRole('button', { name: /^upload$/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(mockDocumentService.uploadDocument).toHaveBeenCalledWith({
          file,
          schema_type: 'EU_ESRS_CSRD',
        });
      });
    });
  });

  describe('Remote Directory Dialog', () => {
    test('opens remote directory dialog when button clicked', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      const remoteButton = screen.getByText('Remote Directory');
      await user.click(remoteButton);
      
      expect(screen.getByText('Configure Remote Directory')).toBeInTheDocument();
      expect(screen.getByLabelText('Remote Directory Path')).toBeInTheDocument();
    });

    test('handles remote directory sync', async () => {
      const user = userEvent.setup();
      mockDocumentService.syncRemoteDirectory.mockResolvedValue(mockDocuments);
      
      renderWithTheme(<Documents />);
      
      const remoteButton = screen.getByText('Remote Directory');
      await user.click(remoteButton);
      
      const pathInput = screen.getByLabelText('Remote Directory Path');
      await user.type(pathInput, '/path/to/documents');
      
      const syncButton = screen.getByRole('button', { name: /sync directory/i });
      await user.click(syncButton);
      
      await waitFor(() => {
        expect(mockDocumentService.syncRemoteDirectory).toHaveBeenCalledWith('/path/to/documents');
      });
    });
  });

  describe('Document Management', () => {
    beforeEach(() => {
      mockDocumentService.getDocuments.mockResolvedValue(mockDocuments);
    });

    test('opens delete confirmation dialog', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
      });
      
      const deleteButtons = screen.getAllByLabelText(/delete document/i);
      await user.click(deleteButtons[0]);
      
      expect(screen.getByText('Delete Document')).toBeInTheDocument();
      expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument();
    });

    test('handles document deletion', async () => {
      const user = userEvent.setup();
      mockDocumentService.deleteDocument.mockResolvedValue();
      
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
      });
      
      const deleteButtons = screen.getAllByLabelText(/delete document/i);
      await user.click(deleteButtons[0]);
      
      const confirmButton = screen.getByRole('button', { name: /^delete$/i });
      await user.click(confirmButton);
      
      await waitFor(() => {
        expect(mockDocumentService.deleteDocument).toHaveBeenCalledWith('1');
      });
    });
  });

  describe('Filtering and Search', () => {
    beforeEach(() => {
      mockDocumentService.getDocuments.mockResolvedValue(mockDocuments);
    });

    test('filters documents by search term', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
        expect(screen.getByText('UK_SRD_Guidelines.docx')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search documents...');
      await user.type(searchInput, 'ESRS');
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
        expect(screen.queryByText('UK_SRD_Guidelines.docx')).not.toBeInTheDocument();
      });
    });

    test('filters documents by schema type', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
        expect(screen.getByText('UK_SRD_Guidelines.docx')).toBeInTheDocument();
      });
      
      const schemaFilter = screen.getByDisplayValue('');
      await user.click(schemaFilter);
      await user.click(screen.getByText('UK SRD'));
      
      await waitFor(() => {
        expect(screen.queryByText('ESRS_Standards_2023.pdf')).not.toBeInTheDocument();
        expect(screen.getByText('UK_SRD_Guidelines.docx')).toBeInTheDocument();
      });
    });

    test('filters documents by status', async () => {
      const user = userEvent.setup();
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
        expect(screen.getByText('UK_SRD_Guidelines.docx')).toBeInTheDocument();
      });
      
      const statusFilters = screen.getAllByDisplayValue('');
      const statusFilter = statusFilters.find(filter => 
        filter.closest('[aria-labelledby]')?.getAttribute('aria-labelledby')?.includes('Status')
      );
      
      if (statusFilter) {
        await user.click(statusFilter);
        await user.click(screen.getByText('Processed'));
        
        await waitFor(() => {
          expect(screen.getByText('ESRS_Standards_2023.pdf')).toBeInTheDocument();
          expect(screen.queryByText('UK_SRD_Guidelines.docx')).not.toBeInTheDocument();
        });
      }
    });
  });

  describe('Drag and Drop', () => {
    test('shows drag overlay when files are dragged over', async () => {
      renderWithTheme(<Documents />);
      
      const dropZone = screen.getByText('Document Repository').closest('div');
      
      if (dropZone) {
        fireEvent.dragEnter(dropZone);
        
        await waitFor(() => {
          expect(screen.getByText('Drop files here to upload')).toBeInTheDocument();
        });
      }
    });

    test('handles file drop', async () => {
      renderWithTheme(<Documents />);
      
      const dropZone = screen.getByText('Document Repository').closest('div');
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      
      if (dropZone) {
        fireEvent.dragEnter(dropZone);
        fireEvent.drop(dropZone, {
          dataTransfer: {
            files: [file],
          },
        });
        
        await waitFor(() => {
          expect(screen.getByText('Choose File or Drag & Drop')).toBeInTheDocument();
        });
      }
    });
  });

  describe('Error Handling', () => {
    test('shows error message when document loading fails', async () => {
      mockDocumentService.getDocuments.mockRejectedValue(new Error('Network error'));
      
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load documents')).toBeInTheDocument();
      });
    });

    test('shows error message when upload fails', async () => {
      const user = userEvent.setup();
      mockDocumentService.uploadDocument.mockRejectedValue(new Error('Upload failed'));
      
      renderWithTheme(<Documents />);
      
      const uploadButton = screen.getByText('Upload Document');
      await user.click(uploadButton);
      
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, file);
      
      const schemaSelect = screen.getByLabelText('Schema Type');
      await user.click(schemaSelect);
      await user.click(screen.getByText('EU ESRS/CSRD'));
      
      const submitButton = screen.getByRole('button', { name: /^upload$/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to upload document')).toBeInTheDocument();
      });
    });
  });

  describe('Pagination', () => {
    test('shows pagination controls in list view', async () => {
      const user = userEvent.setup();
      const manyDocuments = Array.from({ length: 15 }, (_, i) => ({
        ...mockDocuments[0],
        id: `doc-${i}`,
        filename: `document-${i}.pdf`,
      }));
      
      mockDocumentService.getDocuments.mockResolvedValue(manyDocuments);
      renderWithTheme(<Documents />);
      
      await waitFor(() => {
        expect(screen.getByText('document-0.pdf')).toBeInTheDocument();
      });
      
      // Switch to list view
      const listViewButton = screen.getByRole('button', { name: /list view/i });
      await user.click(listViewButton);
      
      await waitFor(() => {
        expect(screen.getByText('1–10 of 15')).toBeInTheDocument();
      });
    });
  });
});