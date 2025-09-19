import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Reports from './Reports';
import api from '../services/api';

// Mock the API
jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

describe('Reports Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    mockedApi.get.mockImplementation((url) => {
      if (url === '/client-requirements') {
        return Promise.resolve({
          data: [
            {
              id: 'req-1',
              client_name: 'Integration Test Client',
              requirements_text: 'Test requirements for integration',
              schema_type: 'eu_esrs_csrd',
              upload_date: '2023-12-01T00:00:00Z',
              processed_requirements: [
                {
                  requirement_id: 'req-1-1',
                  requirement_text: 'Climate change disclosure requirement',
                  priority: 'high',
                  schema_elements: ['ESRS-E1'],
                },
              ],
              schema_mappings: [
                {
                  requirement_id: 'req-1-1',
                  schema_element_id: 'ESRS-E1',
                  confidence_score: 0.85,
                  mapping_type: 'automatic',
                },
              ],
            },
          ],
        });
      }
      
      if (url === '/reports/templates') {
        return Promise.resolve({
          data: [
            {
              type: 'eu_esrs_standard',
              name: 'EU ESRS Standard Report',
              description: 'Standard EU ESRS compliance report',
              sections: [
                {
                  id: 'climate',
                  title: 'Climate Change Disclosures',
                  required: true,
                  description: 'ESRS E1 Climate Change requirements',
                  subsections: [
                    { id: 'climate-1', title: 'Transition Plan' },
                    { id: 'climate-2', title: 'Physical Risks' },
                  ],
                },
              ],
            },
          ],
        });
      }
      
      if (url === '/reports/ai-models') {
        return Promise.resolve({
          data: [
            {
              value: 'openai_gpt35',
              name: 'OpenAI GPT-3.5 Turbo',
              description: 'Fast and efficient model for report generation',
              capabilities: ['text-generation', 'analysis'],
            },
            {
              value: 'openai_gpt4',
              name: 'OpenAI GPT-4',
              description: 'Advanced model with superior accuracy',
              capabilities: ['text-generation', 'analysis', 'reasoning'],
            },
          ],
        });
      }
      
      if (url === '/reports/formats') {
        return Promise.resolve({
          data: [
            {
              value: 'structured_text',
              name: 'Structured Text',
              description: 'Plain text with structured formatting',
            },
            {
              value: 'markdown',
              name: 'Markdown',
              description: 'Markdown format suitable for documentation',
            },
          ],
        });
      }
      
      if (url.startsWith('/reports/preview/')) {
        return Promise.resolve({
          data: {
            client_name: 'Integration Test Client',
            template_type: 'eu_esrs_standard',
            template_name: 'EU ESRS Standard Report',
            sections: [
              {
                id: 'climate',
                title: 'Climate Change Disclosures',
                required: true,
                description: 'ESRS E1 Climate Change requirements',
                subsections: [
                  { id: 'climate-1', title: 'Transition Plan' },
                  { id: 'climate-2', title: 'Physical Risks' },
                ],
              },
            ],
            relevant_requirements: [
              {
                id: 'req-1-1',
                text: 'Climate change disclosure requirement',
                priority: 'high',
              },
            ],
          },
        });
      }
      
      if (url.startsWith('/reports/download-pdf/')) {
        const pdfContent = new Blob(['Mock PDF content'], { type: 'application/pdf' });
        return Promise.resolve({ data: pdfContent });
      }
      
      return Promise.reject(new Error(`Unhandled GET request: ${url}`));
    });
    
    mockedApi.post.mockImplementation((url, data, config) => {
      if (url === '/client-requirements/upload') {
        return Promise.resolve({
          data: {
            id: 'req-new',
            client_name: 'New Integration Client',
            requirements_text: 'Uploaded requirements content',
            schema_type: 'eu_esrs_csrd',
            upload_date: new Date().toISOString(),
            processed_requirements: [],
            schema_mappings: [],
          },
        });
      }
      
      if (url.startsWith('/reports/validate-requirements/')) {
        return Promise.resolve({
          data: {
            requirements_id: 'req-new',
            template_type: 'eu_esrs_standard',
            validation_status: 'excellent',
            coverage_percentage: 92,
            recommendations: [
              'Excellent coverage detected. Report generation should produce comprehensive results.',
            ],
            warnings: [],
            gap_analysis: {
              coverage_percentage: 92,
              covered_requirements: 23,
              total_requirements: 25,
              gaps: {
                uncovered_requirements: [],
                missing_schema_elements: [],
              },
            },
          },
        });
      }
      
      if (url === '/reports/generate-complete') {
        return Promise.resolve({
          data: {
            report_content: 'Generated sustainability report content with comprehensive analysis...',
            metadata: {
              client_name: 'New Integration Client',
              generation_date: new Date().toISOString(),
              template_type: 'eu_esrs_standard',
              ai_model: 'openai_gpt35',
              total_sections: 5,
              word_count: 2500,
              source_documents_count: 8,
            },
            pdf_generated: true,
            pdf_size_bytes: 125000,
            pdf_download_url: '/reports/download-pdf/req-new',
          },
        });
      }
      
      return Promise.reject(new Error(`Unhandled POST request: ${url}`));
    });
  });

  it('completes full report generation workflow', async () => {
    const user = userEvent.setup();
    
    renderWithTheme(<Reports />);
    
    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByText('Integration Test Client')).toBeInTheDocument();
    });
    
    // Start creating a new report
    fireEvent.click(screen.getByText('Create Report'));
    
    expect(screen.getByText('Create New Report')).toBeInTheDocument();
    expect(screen.getByText('Upload Client Requirements')).toBeInTheDocument();
    
    // Step 1: Upload client requirements
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'New Integration Client');
    
    // Select schema type
    const schemaSelect = screen.getByLabelText('Reporting Schema');
    fireEvent.mouseDown(schemaSelect);
    fireEvent.click(screen.getByText('EU ESRS/CSRD'));
    
    // Upload file
    const file = new File(['Integration test requirements content'], 'requirements.txt', {
      type: 'text/plain',
    });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    await user.upload(fileInput, file);
    
    // Proceed to step 2
    fireEvent.click(screen.getByText('Next'));
    
    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText('Excellent Coverage')).toBeInTheDocument();
      expect(screen.getByText('Coverage: 92%')).toBeInTheDocument();
    });
    
    // Verify validation results
    expect(screen.getByText('Schema Mappings')).toBeInTheDocument();
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
    
    // Proceed to step 3
    fireEvent.click(screen.getByText('Next'));
    
    // Wait for configuration step
    await waitFor(() => {
      expect(screen.getByText('Configure Report Generation')).toBeInTheDocument();
    });
    
    // Verify configuration options are available
    expect(screen.getByLabelText('Report Template')).toBeInTheDocument();
    expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
    expect(screen.getByLabelText('Output Format')).toBeInTheDocument();
    
    // Change AI model to GPT-4
    const aiModelSelect = screen.getByLabelText('AI Model');
    fireEvent.mouseDown(aiModelSelect);
    fireEvent.click(screen.getByText('OpenAI GPT-4'));
    
    // Proceed to step 4
    fireEvent.click(screen.getByText('Next'));
    
    // Wait for final step
    await waitFor(() => {
      expect(screen.getByText('Ready to Generate Report')).toBeInTheDocument();
    });
    
    // Generate and download report
    fireEvent.click(screen.getByText('Generate & Download PDF Report'));
    
    // Wait for generation to complete
    await waitFor(() => {
      expect(mockedApi.post).toHaveBeenCalledWith('/reports/generate-complete', null, {
        params: {
          requirements_id: 'req-new',
          template_type: 'eu_esrs_standard',
          ai_model: 'openai_gpt4',
          report_format: 'structured_text',
          include_pdf: true,
        },
      });
    });
    
    // Verify PDF download was triggered
    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledWith('/reports/download-pdf/req-new', {
        params: {
          template_type: 'eu_esrs_standard',
          ai_model: 'openai_gpt4',
        },
        responseType: 'blob',
      });
    });
  }, 15000);

  it('handles validation warnings appropriately', async () => {
    const user = userEvent.setup();
    
    // Mock validation with warnings
    mockedApi.post.mockImplementation((url) => {
      if (url.startsWith('/reports/validate-requirements/')) {
        return Promise.resolve({
          data: {
            requirements_id: 'req-new',
            template_type: 'eu_esrs_standard',
            validation_status: 'fair',
            coverage_percentage: 65,
            recommendations: [
              'Report generation is possible but may have gaps in some sections.',
            ],
            warnings: [
              'Limited coverage detected. Consider uploading additional regulatory documents.',
              '3 high-priority requirements have no coverage.',
            ],
            gap_analysis: {
              coverage_percentage: 65,
              covered_requirements: 13,
              total_requirements: 20,
              gaps: {
                uncovered_requirements: [
                  {
                    requirement_id: 'req-gap-1',
                    requirement_text: 'Biodiversity impact assessment',
                    priority: 'high',
                    schema_elements: [],
                  },
                ],
                missing_schema_elements: ['ESRS-E4'],
              },
            },
          },
        });
      }
      return Promise.reject(new Error(`Unhandled POST request: ${url}`));
    });
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Integration Test Client')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    // Complete step 1
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'Warning Test Client');
    
    const file = new File(['Test content'], 'requirements.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    await user.upload(fileInput, file);
    
    fireEvent.click(screen.getByText('Next'));
    
    // Wait for validation with warnings
    await waitFor(() => {
      expect(screen.getByText('Fair Coverage')).toBeInTheDocument();
      expect(screen.getByText('Coverage: 65%')).toBeInTheDocument();
    });
    
    // Verify warnings are displayed
    expect(screen.getByText('Warnings')).toBeInTheDocument();
    expect(screen.getByText('Limited coverage detected. Consider uploading additional regulatory documents.')).toBeInTheDocument();
    expect(screen.getByText('3 high-priority requirements have no coverage.')).toBeInTheDocument();
    
    // Should still be able to proceed
    expect(screen.getByText('Next')).toBeEnabled();
  });

  it('handles API errors gracefully during workflow', async () => {
    const user = userEvent.setup();
    
    // Mock upload failure
    mockedApi.post.mockImplementation((url) => {
      if (url === '/client-requirements/upload') {
        return Promise.reject(new Error('Upload failed: Server error'));
      }
      return Promise.reject(new Error(`Unhandled POST request: ${url}`));
    });
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Integration Test Client')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    // Complete step 1
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'Error Test Client');
    
    const file = new File(['Test content'], 'requirements.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    await user.upload(fileInput, file);
    
    fireEvent.click(screen.getByText('Next'));
    
    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText('Upload failed: Server error')).toBeInTheDocument();
    });
    
    // Should not proceed to next step
    expect(screen.queryByText('Review & Validate')).not.toBeInTheDocument();
  });

  it('allows navigation back and forth between steps', async () => {
    const user = userEvent.setup();
    
    renderWithTheme(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Integration Test Client')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Create Report'));
    
    // Complete step 1
    const clientNameInput = screen.getByLabelText('Client Name');
    await user.type(clientNameInput, 'Navigation Test Client');
    
    const file = new File(['Test content'], 'requirements.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/upload client requirements/i);
    await user.upload(fileInput, file);
    
    fireEvent.click(screen.getByText('Next'));
    
    // Wait for step 2
    await waitFor(() => {
      expect(screen.getByText('Excellent Coverage')).toBeInTheDocument();
    });
    
    // Go to step 3
    fireEvent.click(screen.getByText('Next'));
    
    await waitFor(() => {
      expect(screen.getByText('Configure Report Generation')).toBeInTheDocument();
    });
    
    // Go back to step 2
    fireEvent.click(screen.getByText('Back'));
    
    expect(screen.getByText('Excellent Coverage')).toBeInTheDocument();
    
    // Go back to step 1
    fireEvent.click(screen.getByText('Back'));
    
    expect(screen.getByDisplayValue('Navigation Test Client')).toBeInTheDocument();
    expect(screen.getByText('Upload Client Requirements')).toBeInTheDocument();
  });
});