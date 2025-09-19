import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Reports from './Reports';
import reportService from '../services/reportService';

// Mock the report service
jest.mock('../services/reportService');
const mockedReportService = reportService as jest.Mocked<typeof reportService>;

// Mock data
const mockClientRequirements = [
  {
    id: 'req-1',
    client_name: 'Test Client 1',
    requirements_text: 'Test requirements',
    schema_type: 'eu_esrs_csrd' as const,
    upload_date: '2023-12-01T00:00:00Z',
    processed_requirements: [],
    schema_mappings: [],
  },
  {
    id: 'req-2',
    client_name: 'Test Client 2',
    requirements_text: 'Test requirements 2',
    schema_type: 'uk_srd' as const,
    upload_date: '2023-12-02T00:00:00Z',
    processed_requirements: [],
    schema_mappings: [],
  },
];

const mockTemplates = [
  {
    type: 'eu_esrs_standard',
    name: 'EU ESRS Standard Report',
    description: 'Standard EU ESRS report template',
    sections: [],
  },
];

const mockAIModels = [
  {
    value: 'openai_gpt35',
    name: 'OpenAI GPT-3.5',
    description: 'OpenAI GPT-3.5 Turbo model',
    capabilities: ['text-generation'],
  },
];

const mockFormats = [
  {
    value: 'structured_text',
    name: 'Structured Text',
    description: 'Plain text with structured formatting',
  },
];

const mockValidationResult = {
  requirements_id: 'req-1',
  template_type: 'eu_esrs_standard',
  validation_status: 'good' as const,
  coverage_percentage: 75,
  recommendations: ['Good coverage detected'],
  warnings: [],
  gap_analysis: {
    coverage_percentage: 75,
    covered_requirements: 15,
    total_requirements: 20,
    gaps: {
      uncovered_requirements: [],
      missing_schema_elements: [],
    },
  },
};

const mockReportPreview = {
  client_name: 'Test Client 1',
  template_type: 'eu_esrs_standard',
  template_name: 'EU ESRS Standard Report',
  sections: [
    {
      id: 'section-1',
      title: 'Climate Change',
      required: true,
      description: 'Climate change disclosures',
      subsections: [],
    },
  ],
  relevant_requirements: [],
};

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

describe('Reports Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default mocks
    mockedReportService.listClientRequirements.mockResolvedValue(mockClientRequirements);
    mockedReportService.getAvailableTemplates.mockResolvedValue(mockTemplates);
    mockedReportService.getAvailableAIModels.mockResolvedValue(mockAIModels);
    mockedReportService.getAvailableFormats.mockResolvedValue(mockFormats);
    mockedReportService.validateFile.mockReturnValue({ valid: true });
    mockedReportService.formatFileSize.mockReturnValue('1 KB');
    mockedReportService.getValidationStatusColor.mockReturnValue('info');
    mockedReportService.getValidationStatusText.mockReturnValue('Good Coverage');
  });

  it('renders the reports page correctly', async () => {
    renderWithTheme(<Reports />);
    
    expect(screen.getByText('Report Generation')).toBeInTheDocument();
    expect(screen.getByText('Create Report')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      expect(screen.getByText('Test Client 2')).toBeInTheDocument();
    });
  });

  it('opens create report dialog when create button is clicked', async () => {
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    expect(screen.getByText('Create New Report')).toBeInTheDocument();
    expect(screen.getByText('Upload Client Requirements')).toBeInTheDocument();
  });

  it('handles file upload in step 1', async () => {
    const user = userEvent.setup();
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    // Fill in client name
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'New Test Client');
    
    // Mock file upload
    const file = new File(['test content'], 'requirements.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    
    await user.upload(fileInput, file);
    
    expect(mockedReportService.validateFile).toHaveBeenCalledWith(file);
  });

  it('validates requirements in step 2', async () => {
    const user = userEvent.setup();
    
    // Mock successful upload
    mockedReportService.uploadClientRequirements.mockResolvedValue(mockClientRequirements[0]);
    mockedReportService.validateRequirementsForReport.mockResolvedValue(mockValidationResult);
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    // Fill in step 1
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'New Test Client');
    
    const file = new File(['test content'], 'requirements.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    await user.upload(fileInput, file);
    
    // Click Next to go to step 2
    fireEvent.click(screen.getByText('Next'));
    
    await waitFor(() => {
      expect(mockedReportService.uploadClientRequirements).toHaveBeenCalled();
      expect(mockedReportService.validateRequirementsForReport).toHaveBeenCalled();
    });
  });

  it('configures report settings in step 3', async () => {
    const user = userEvent.setup();
    
    // Mock successful previous steps
    mockedReportService.uploadClientRequirements.mockResolvedValue(mockClientRequirements[0]);
    mockedReportService.validateRequirementsForReport.mockResolvedValue(mockValidationResult);
    mockedReportService.previewReportStructure.mockResolvedValue(mockReportPreview);
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    // Fill in step 1
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'New Test Client');
    
    const file = new File(['test content'], 'requirements.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    await user.upload(fileInput, file);
    
    // Go to step 2
    fireEvent.click(screen.getByText('Next'));
    
    await waitFor(() => {
      expect(screen.getByText('Good Coverage')).toBeInTheDocument();
    });
    
    // Go to step 3
    fireEvent.click(screen.getByText('Next'));
    
    await waitFor(() => {
      expect(screen.getByText('Configure Report Generation')).toBeInTheDocument();
      expect(screen.getByLabelText('Report Template')).toBeInTheDocument();
      expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
    });
  });

  it('generates report in step 4', async () => {
    const user = userEvent.setup();
    
    // Mock successful previous steps
    mockedReportService.uploadClientRequirements.mockResolvedValue(mockClientRequirements[0]);
    mockedReportService.validateRequirementsForReport.mockResolvedValue(mockValidationResult);
    mockedReportService.previewReportStructure.mockResolvedValue(mockReportPreview);
    mockedReportService.generateReport.mockResolvedValue({
      report_content: 'Generated content',
      metadata: {
        client_name: 'Test Client',
        generation_date: '2023-12-01T00:00:00Z',
        template_type: 'eu_esrs_standard',
        ai_model: 'openai_gpt35',
        total_sections: 5,
        word_count: 1000,
        source_documents_count: 3,
      },
      pdf_generated: true,
      pdf_size_bytes: 50000,
      pdf_download_url: '/download/test.pdf',
    });
    mockedReportService.downloadPDFReport.mockResolvedValue(new Blob(['PDF content']));
    mockedReportService.downloadBlob.mockImplementation(() => {});
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    // Navigate through all steps
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'New Test Client');
    
    const file = new File(['test content'], 'requirements.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    await user.upload(fileInput, file);
    
    fireEvent.click(screen.getByText('Next')); // Step 2
    
    await waitFor(() => {
      expect(screen.getByText('Good Coverage')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Next')); // Step 3
    
    await waitFor(() => {
      expect(screen.getByText('Configure Report Generation')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Next')); // Step 4
    
    await waitFor(() => {
      expect(screen.getByText('Ready to Generate Report')).toBeInTheDocument();
    });
    
    // Generate report
    fireEvent.click(screen.getByText('Generate & Download PDF Report'));
    
    await waitFor(() => {
      expect(mockedReportService.generateReport).toHaveBeenCalled();
      expect(mockedReportService.downloadPDFReport).toHaveBeenCalled();
      expect(mockedReportService.downloadBlob).toHaveBeenCalled();
    });
  });

  it('handles file validation errors', async () => {
    const user = userEvent.setup();
    
    // Mock file validation error
    mockedReportService.validateFile.mockReturnValue({
      valid: false,
      error: 'Invalid file type',
    });
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    const file = new File(['test content'], 'requirements.exe', { type: 'application/exe' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    
    await user.upload(fileInput, file);
    
    expect(screen.getByText('Invalid file type')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    mockedReportService.listClientRequirements.mockRejectedValue(new Error('API Error'));
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Report Generation')).toBeInTheDocument();
    });
    
    // The component should still render even with API errors
    expect(screen.getByText('Create Report')).toBeInTheDocument();
  });

  it('deletes client requirements', async () => {
    mockedReportService.deleteClientRequirements.mockResolvedValue();
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    // Find and click delete button for first client
    const deleteButtons = screen.getAllByTestId('DeleteIcon');
    fireEvent.click(deleteButtons[0]);
    
    await waitFor(() => {
      expect(mockedReportService.deleteClientRequirements).toHaveBeenCalledWith('req-1');
    });
  });

  it('opens existing requirement for editing', async () => {
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    });
    
    // Find and click view button for first client
    const viewButtons = screen.getAllByTestId('VisibilityIcon');
    fireEvent.click(viewButtons[0]);
    
    expect(screen.getByText('Generate Report - Test Client 1')).toBeInTheDocument();
  });
});