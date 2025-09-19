import reportService from './reportService';
import api from './api';

// Mock the api module
jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('ReportService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('uploadClientRequirements', () => {
    it('should upload client requirements successfully', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockResponse = {
        data: {
          id: 'req-123',
          client_name: 'Test Client',
          requirements_text: 'test content',
          schema_type: 'eu_esrs_csrd',
          upload_date: '2023-12-01T00:00:00Z',
          processed_requirements: [],
          schema_mappings: [],
        },
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      const result = await reportService.uploadClientRequirements(
        mockFile,
        'Test Client',
        'eu_esrs_csrd'
      );

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/client-requirements/upload',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle upload errors', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      mockedApi.post.mockRejectedValue(new Error('Upload failed'));

      await expect(
        reportService.uploadClientRequirements(mockFile, 'Test Client', 'eu_esrs_csrd')
      ).rejects.toThrow('Upload failed');
    });
  });

  describe('validateRequirementsForReport', () => {
    it('should validate requirements successfully', async () => {
      const mockResponse = {
        data: {
          requirements_id: 'req-123',
          template_type: 'eu_esrs_standard',
          validation_status: 'good',
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
        },
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      const result = await reportService.validateRequirementsForReport(
        'req-123',
        'eu_esrs_standard'
      );

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/reports/validate-requirements/req-123',
        null,
        {
          params: { template_type: 'eu_esrs_standard' },
        }
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('generateReport', () => {
    it('should generate report successfully', async () => {
      const mockRequest = {
        requirements_id: 'req-123',
        template_type: 'eu_esrs_standard',
        ai_model: 'openai_gpt35',
        report_format: 'structured_text',
        include_pdf: true,
      };

      const mockResponse = {
        data: {
          report_content: 'Generated report content',
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
          pdf_download_url: '/reports/download-pdf/req-123',
        },
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      const result = await reportService.generateReport(mockRequest);

      expect(mockedApi.post).toHaveBeenCalledWith('/reports/generate-complete', null, {
        params: {
          requirements_id: 'req-123',
          template_type: 'eu_esrs_standard',
          ai_model: 'openai_gpt35',
          report_format: 'structured_text',
          include_pdf: true,
        },
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('downloadPDFReport', () => {
    it('should download PDF report successfully', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });
      mockedApi.get.mockResolvedValue({ data: mockBlob });

      const result = await reportService.downloadPDFReport(
        'req-123',
        'eu_esrs_standard',
        'openai_gpt35'
      );

      expect(mockedApi.get).toHaveBeenCalledWith('/reports/download-pdf/req-123', {
        params: {
          template_type: 'eu_esrs_standard',
          ai_model: 'openai_gpt35',
        },
        responseType: 'blob',
      });
      expect(result).toEqual(mockBlob);
    });
  });

  describe('validateFile', () => {
    it('should validate valid files', () => {
      const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const result = reportService.validateFile(validFile);
      expect(result.valid).toBe(true);
    });

    it('should reject invalid file types', () => {
      const invalidFile = new File(['content'], 'test.exe', { type: 'application/exe' });
      const result = reportService.validateFile(invalidFile);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file type');
    });

    it('should reject files that are too large', () => {
      const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.pdf', {
        type: 'application/pdf',
      });
      const result = reportService.validateFile(largeFile);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('File size too large');
    });
  });

  describe('formatFileSize', () => {
    it('should format file sizes correctly', () => {
      expect(reportService.formatFileSize(0)).toBe('0 Bytes');
      expect(reportService.formatFileSize(1024)).toBe('1 KB');
      expect(reportService.formatFileSize(1024 * 1024)).toBe('1 MB');
      expect(reportService.formatFileSize(1024 * 1024 * 1024)).toBe('1 GB');
    });
  });

  describe('getValidationStatusColor', () => {
    it('should return correct colors for validation statuses', () => {
      expect(reportService.getValidationStatusColor('excellent')).toBe('success');
      expect(reportService.getValidationStatusColor('good')).toBe('info');
      expect(reportService.getValidationStatusColor('fair')).toBe('warning');
      expect(reportService.getValidationStatusColor('poor')).toBe('error');
      expect(reportService.getValidationStatusColor('unknown')).toBe('info');
    });
  });

  describe('getValidationStatusText', () => {
    it('should return correct text for validation statuses', () => {
      expect(reportService.getValidationStatusText('excellent')).toBe('Excellent Coverage');
      expect(reportService.getValidationStatusText('good')).toBe('Good Coverage');
      expect(reportService.getValidationStatusText('fair')).toBe('Fair Coverage');
      expect(reportService.getValidationStatusText('poor')).toBe('Poor Coverage');
      expect(reportService.getValidationStatusText('unknown')).toBe('Unknown Status');
    });
  });

  describe('downloadBlob', () => {
    it('should trigger file download', () => {
      // Mock DOM methods
      const mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
      };
      const createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
      const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation();
      const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation();
      const createObjectURLSpy = jest.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:url');
      const revokeObjectURLSpy = jest.spyOn(window.URL, 'revokeObjectURL').mockImplementation();

      const blob = new Blob(['content'], { type: 'application/pdf' });
      reportService.downloadBlob(blob, 'test.pdf');

      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(mockLink.download).toBe('test.pdf');
      expect(mockLink.click).toHaveBeenCalled();
      expect(appendChildSpy).toHaveBeenCalledWith(mockLink);
      expect(removeChildSpy).toHaveBeenCalledWith(mockLink);
      expect(createObjectURLSpy).toHaveBeenCalledWith(blob);
      expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:url');

      // Restore mocks
      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
      createObjectURLSpy.mockRestore();
      revokeObjectURLSpy.mockRestore();
    });
  });
});