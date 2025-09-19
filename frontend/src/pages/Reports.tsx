import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stepper,
  Step,
  StepLabel,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Alert,
  AlertTitle,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  CloudUpload as UploadIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import reportService, {
  ClientRequirement,
  ReportTemplate,
  AIModel,
  ReportFormat,
  ValidationResult,
  ReportPreview,
  ReportGenerationRequest,
} from '../services/reportService';

interface Report {
  id: string;
  clientName: string;
  reportType: string;
  status: 'Draft' | 'In Progress' | 'Completed';
  createdDate: string;
  lastModified: string;
}

const Reports: React.FC = () => {
  // Dialog and workflow state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  
  // Form data
  const [clientName, setClientName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [schemaType, setSchemaType] = useState<'eu_esrs_csrd' | 'uk_srd'>('eu_esrs_csrd');
  const [selectedTemplate, setSelectedTemplate] = useState('eu_esrs_standard');
  const [selectedAIModel, setSelectedAIModel] = useState('openai_gpt35');
  const [selectedFormat, setSelectedFormat] = useState('structured_text');
  
  // Data state
  const [clientRequirements, setClientRequirements] = useState<ClientRequirement[]>([]);
  const [currentRequirement, setCurrentRequirement] = useState<ClientRequirement | null>(null);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [aiModels, setAIModels] = useState<AIModel[]>([]);
  const [formats, setFormats] = useState<ReportFormat[]>([]);
  const [reportPreview, setReportPreview] = useState<ReportPreview | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const steps = [
    'Upload Client Requirements',
    'Review & Validate',
    'Configure Report',
    'Generate & Download'
  ];

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [requirementsData, templatesData, modelsData, formatsData] = await Promise.all([
        reportService.listClientRequirements(),
        reportService.getAvailableTemplates(),
        reportService.getAvailableAIModels(),
        reportService.getAvailableFormats(),
      ]);
      
      setClientRequirements(requirementsData);
      setTemplates(templatesData);
      setAIModels(modelsData);
      setFormats(formatsData);
    } catch (err) {
      setError('Failed to load initial data');
      console.error('Error loading initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Convert client requirements to reports for display
  const reports: Report[] = clientRequirements.map(req => ({
    id: req.id,
    clientName: req.client_name,
    reportType: req.schema_type === 'eu_esrs_csrd' ? 'EU ESRS/CSRD Report' : 'UK SRD Report',
    status: 'Draft', // All are drafts until generated
    createdDate: new Date(req.upload_date).toLocaleDateString(),
    lastModified: new Date(req.upload_date).toLocaleDateString(),
  }));

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const validation = reportService.validateFile(file);
      if (!validation.valid) {
        setFileError(validation.error || 'Invalid file');
        setSelectedFile(null);
      } else {
        setFileError(null);
        setSelectedFile(file);
      }
    }
  };

  const handleNext = async () => {
    try {
      setError(null);
      
      if (activeStep === 0) {
        // Upload client requirements
        await handleUploadRequirements();
      } else if (activeStep === 1) {
        // Validate requirements
        await handleValidateRequirements();
      } else if (activeStep === 2) {
        // Preview report structure
        await handlePreviewReport();
      }
      
      setActiveStep((prevStep) => prevStep + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleUploadRequirements = async () => {
    if (!selectedFile || !clientName.trim()) {
      throw new Error('Please provide client name and select a file');
    }

    setUploading(true);
    try {
      const result = await reportService.uploadClientRequirements(
        selectedFile,
        clientName.trim(),
        schemaType
      );
      setCurrentRequirement(result);
      setSuccess('Client requirements uploaded successfully');
    } finally {
      setUploading(false);
    }
  };

  const handleValidateRequirements = async () => {
    if (!currentRequirement) {
      throw new Error('No requirements to validate');
    }

    setLoading(true);
    try {
      const validation = await reportService.validateRequirementsForReport(
        currentRequirement.id,
        selectedTemplate
      );
      setValidationResult(validation);
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewReport = async () => {
    if (!currentRequirement) {
      throw new Error('No requirements for preview');
    }

    setLoading(true);
    try {
      const preview = await reportService.previewReportStructure(
        currentRequirement.id,
        selectedTemplate
      );
      setReportPreview(preview);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!currentRequirement) {
      setError('No requirements selected for report generation');
      return;
    }

    setGenerating(true);
    try {
      const request: ReportGenerationRequest = {
        requirements_id: currentRequirement.id,
        template_type: selectedTemplate,
        ai_model: selectedAIModel,
        report_format: selectedFormat,
        include_pdf: true,
      };

      const result = await reportService.generateReport(request);
      
      if (result.pdf_generated && result.pdf_download_url) {
        // Download PDF
        const pdfBlob = await reportService.downloadPDFReport(
          currentRequirement.id,
          selectedTemplate,
          selectedAIModel
        );
        
        const filename = `${currentRequirement.client_name}_sustainability_report_${new Date().toISOString().split('T')[0]}.pdf`;
        reportService.downloadBlob(pdfBlob, filename);
      }

      setSuccess('Report generated and downloaded successfully');
      handleCloseDialog();
      await loadInitialData(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleCloseDialog = () => {
    setCreateDialogOpen(false);
    setActiveStep(0);
    setClientName('');
    setSelectedFile(null);
    setCurrentRequirement(null);
    setReportPreview(null);
    setValidationResult(null);
    setFileError(null);
    setError(null);
  };

  const handleDeleteRequirement = async (requirementId: string) => {
    try {
      await reportService.deleteClientRequirements(requirementId);
      setSuccess('Requirements deleted successfully');
      await loadInitialData();
    } catch (err) {
      setError('Failed to delete requirements');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed':
        return 'success';
      case 'In Progress':
        return 'warning';
      case 'Draft':
        return 'default';
      default:
        return 'default';
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <TextField
              fullWidth
              label="Client Name"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              sx={{ mb: 2 }}
              required
            />
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Reporting Schema</InputLabel>
              <Select
                value={schemaType}
                onChange={(e) => setSchemaType(e.target.value as 'eu_esrs_csrd' | 'uk_srd')}
                label="Reporting Schema"
              >
                <MenuItem value="eu_esrs_csrd">EU ESRS/CSRD</MenuItem>
                <MenuItem value="uk_srd">UK SRD</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ mb: 2 }}>
              <input
                accept=".pdf,.docx,.txt,.json"
                style={{ display: 'none' }}
                id="requirements-upload"
                type="file"
                onChange={handleFileSelect}
              />
              <label htmlFor="requirements-upload">
                <Button
                  variant="outlined"
                  component="span"
                  fullWidth
                  startIcon={<UploadIcon />}
                  sx={{ mb: 1 }}
                >
                  {selectedFile ? selectedFile.name : 'Upload Client Requirements'}
                </Button>
              </label>
              {selectedFile && (
                <Typography variant="body2" color="textSecondary">
                  File size: {reportService.formatFileSize(selectedFile.size)}
                </Typography>
              )}
              {fileError && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  {fileError}
                </Alert>
              )}
            </Box>

            {uploading && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Uploading and processing requirements...
                </Typography>
              </Box>
            )}
          </Box>
        );

      case 1:
        return (
          <Box>
            {loading ? (
              <Box textAlign="center" sx={{ py: 4 }}>
                <CircularProgress />
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Validating requirements...
                </Typography>
              </Box>
            ) : validationResult ? (
              <Box>
                <Alert 
                  severity={reportService.getValidationStatusColor(validationResult.validation_status)}
                  sx={{ mb: 2 }}
                >
                  <AlertTitle>
                    {reportService.getValidationStatusText(validationResult.validation_status)}
                  </AlertTitle>
                  Coverage: {validationResult.coverage_percentage}%
                </Alert>

                {validationResult.warnings.length > 0 && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <AlertTitle>Warnings</AlertTitle>
                    <List dense>
                      {validationResult.warnings.map((warning, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={warning} />
                        </ListItem>
                      ))}
                    </List>
                  </Alert>
                )}

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Schema Mappings</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {currentRequirement?.schema_mappings.map((mapping, index) => (
                      <Box key={index} sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          Requirement → {mapping.schema_element_id}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Confidence: {(mapping.confidence_score * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    ))}
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Recommendations</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {validationResult.recommendations.map((rec, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={rec} />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </Box>
            ) : (
              <Typography>No validation data available</Typography>
            )}
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Configure Report Generation
            </Typography>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Report Template</InputLabel>
              <Select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                label="Report Template"
              >
                {templates.map((template) => (
                  <MenuItem key={template.type} value={template.type}>
                    {template.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>AI Model</InputLabel>
              <Select
                value={selectedAIModel}
                onChange={(e) => setSelectedAIModel(e.target.value)}
                label="AI Model"
              >
                {aiModels.map((model) => (
                  <MenuItem key={model.value} value={model.value}>
                    {model.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Output Format</InputLabel>
              <Select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
                label="Output Format"
              >
                {formats.map((format) => (
                  <MenuItem key={format.value} value={format.value}>
                    {format.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {loading ? (
              <Box textAlign="center" sx={{ py: 2 }}>
                <CircularProgress />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Loading report preview...
                </Typography>
              </Box>
            ) : reportPreview && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Report Preview</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="subtitle1" gutterBottom>
                    {reportPreview.template_name}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Client: {reportPreview.client_name}
                  </Typography>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Report Sections ({reportPreview.sections.length})
                  </Typography>
                  <List dense>
                    {reportPreview.sections.map((section) => (
                      <ListItem key={section.id}>
                        <ListItemText
                          primary={section.title}
                          secondary={`${section.subsections.length} subsections`}
                        />
                        {section.required && (
                          <Chip label="Required" size="small" color="primary" />
                        )}
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}
          </Box>
        );

      case 3:
        return (
          <Box textAlign="center">
            {generating ? (
              <Box>
                <CircularProgress size={60} sx={{ mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Generating Report...
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  AI is analyzing your requirements and generating responses based on regulatory documents.
                  This may take a few minutes.
                </Typography>
                <LinearProgress sx={{ mt: 2 }} />
              </Box>
            ) : (
              <Box>
                <CheckCircleIcon color="success" sx={{ fontSize: 60, mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Ready to Generate Report
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
                  Click the button below to generate and download your sustainability report.
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<DownloadIcon />}
                  onClick={handleGenerateReport}
                  disabled={generating}
                >
                  Generate & Download PDF Report
                </Button>
              </Box>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Report Generation
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          disabled={loading}
        >
          Create Report
        </Button>
      </Box>

      {loading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
        </Box>
      )}

      <Grid container spacing={3}>
        {reports.length === 0 ? (
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <Typography variant="h6" color="textSecondary" gutterBottom>
                  No reports created yet
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Create your first sustainability report by uploading client requirements
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ) : (
          reports.map((report) => (
            <Grid item xs={12} md={6} lg={4} key={report.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" gutterBottom>
                      {report.clientName}
                    </Typography>
                    <Chip 
                      label={report.status} 
                      color={getStatusColor(report.status) as any}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    {report.reportType}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Created: {report.createdDate}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Modified: {report.lastModified}
                  </Typography>
                  <Box mt={2} display="flex" justifyContent="flex-end">
                    <IconButton 
                      size="small" 
                      color="primary"
                      onClick={() => {
                        const requirement = clientRequirements.find(req => req.id === report.id);
                        if (requirement) {
                          setCurrentRequirement(requirement);
                          setClientName(requirement.client_name);
                          setSchemaType(requirement.schema_type);
                          setCreateDialogOpen(true);
                        }
                      }}
                    >
                      <ViewIcon />
                    </IconButton>
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={() => handleDeleteRequirement(report.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {/* Create Report Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="lg" 
        fullWidth
        disableEscapeKeyDown={generating}
      >
        <DialogTitle>
          {currentRequirement ? `Generate Report - ${currentRequirement.client_name}` : 'Create New Report'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
            
            {renderStepContent(activeStep)}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={handleCloseDialog}
            disabled={uploading || generating}
          >
            Cancel
          </Button>
          {activeStep > 0 && (
            <Button 
              onClick={handleBack}
              disabled={uploading || generating}
            >
              Back
            </Button>
          )}
          {activeStep < steps.length - 1 ? (
            <Button 
              onClick={handleNext} 
              variant="contained"
              disabled={
                uploading || 
                generating ||
                (activeStep === 0 && (!clientName.trim() || !selectedFile || !!fileError)) ||
                (activeStep === 1 && !validationResult) ||
                (activeStep === 2 && !reportPreview)
              }
            >
              {uploading || loading ? 'Processing...' : 'Next'}
            </Button>
          ) : null}
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbars */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Reports;