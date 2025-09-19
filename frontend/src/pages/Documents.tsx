import React, { useState, useEffect, useCallback } from 'react';
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  Alert,
  Snackbar,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Toolbar,
  InputAdornment,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Folder as FolderIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  GridView as GridViewIcon,
  ViewList as ListViewIcon,
  FilterList as FilterIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';
import { documentService, Document, DocumentUpload } from '../services/documentService';
import { useError } from '../contexts/ErrorContext';
import { useLoading } from '../contexts/LoadingContext';
import { validateFile, validatePath, validateSchemaType, formatFileSize } from '../utils/validation';
import LoadingButton from '../components/common/LoadingButton';
import ProgressIndicator from '../components/common/ProgressIndicator';
import ValidatedTextField from '../components/common/ValidatedTextField';
import ErrorBoundary from '../components/common/ErrorBoundary';
import { ApiError, getErrorMessage, isNetworkError, isValidationError } from '../services/api';

interface DocumentFilters {
  search: string;
  schemaType: string;
  status: string;
}

const Documents: React.FC = () => {
  // Dialog states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [remoteDialogOpen, setRemoteDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  
  // Document management states
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [schemaType, setSchemaType] = useState('');
  const [remotePath, setRemotePath] = useState('');
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);
  
  // UI states
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filters, setFilters] = useState<DocumentFilters>({
    search: '',
    schemaType: '',
    status: '',
  });
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [dragActive, setDragActive] = useState(false);
  
  // Enhanced error and loading handling
  const { showError, showSuccess, showWarning } = useError();
  const { showLoading, hideLoading, updateProgress } = useLoading();
  
  // Validation states
  const [fileValidation, setFileValidation] = useState({ isValid: true, errors: [] });
  const [pathValidation, setPathValidation] = useState({ isValid: true, errors: [] });
  const [schemaValidation, setSchemaValidation] = useState({ isValid: true, errors: [] });

  // Load documents on component mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    const loadingId = showLoading('Loading documents...');
    try {
      setLoading(true);
      const docs = await documentService.getDocuments();
      setDocuments(docs);
    } catch (error) {
      const apiError = error as ApiError;
      if (isNetworkError(apiError)) {
        showError('Unable to connect to server. Please check your connection and try again.');
      } else {
        showError(`Failed to load documents: ${getErrorMessage(apiError)}`);
      }
    } finally {
      setLoading(false);
      hideLoading(loadingId);
    }
  };

  // File selection handlers with validation
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const validation = validateFile(file);
      setFileValidation(validation);
      
      if (validation.isValid) {
        setSelectedFile(file);
        showSuccess(`File "${file.name}" selected successfully`);
      } else {
        setSelectedFile(null);
        showError(`File validation failed: ${validation.errors.join(', ')}`);
      }
    }
  };

  const handleFileDrop = useCallback((files: FileList) => {
    const file = files[0];
    if (file) {
      const validation = validateFile(file);
      setFileValidation(validation);
      
      if (validation.isValid) {
        setSelectedFile(file);
        setUploadDialogOpen(true);
        showSuccess(`File "${file.name}" ready for upload`);
      } else {
        setSelectedFile(null);
        showError(`File validation failed: ${validation.errors.join(', ')}`);
      }
    }
  }, [showError, showSuccess]);

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileDrop(files);
    }
  };

  // Document operations with enhanced error handling
  const handleUpload = async () => {
    // Validate inputs before upload
    const fileVal = selectedFile ? validateFile(selectedFile) : { isValid: false, errors: ['No file selected'] };
    const schemaVal = validateSchemaType(schemaType);
    
    if (!fileVal.isValid) {
      showError(`File validation failed: ${fileVal.errors.join(', ')}`);
      return;
    }
    
    if (!schemaVal.isValid) {
      showError(`Schema validation failed: ${schemaVal.errors.join(', ')}`);
      return;
    }

    if (selectedFile && schemaType) {
      const loadingId = showLoading('Uploading document...', undefined, 'progress');
      try {
        setUploading(true);
        
        // Simulate progress updates (in real implementation, this would come from the upload progress)
        updateProgress(loadingId, 25, 'Preparing file...');
        
        const uploadData: DocumentUpload = {
          file: selectedFile,
          schema_type: schemaType,
        };
        
        updateProgress(loadingId, 50, 'Uploading file...');
        await documentService.uploadDocument(uploadData);
        
        updateProgress(loadingId, 75, 'Processing document...');
        
        showSuccess(`Document "${selectedFile.name}" uploaded successfully`);
        setUploadDialogOpen(false);
        setSelectedFile(null);
        setSchemaType('');
        setFileValidation({ isValid: true, errors: [] });
        setSchemaValidation({ isValid: true, errors: [] });
        
        updateProgress(loadingId, 100, 'Complete!');
        setTimeout(() => hideLoading(loadingId), 500);
        
        loadDocuments(); // Refresh the list
      } catch (error) {
        const apiError = error as ApiError;
        hideLoading(loadingId);
        
        if (isValidationError(apiError)) {
          showError(`Upload validation failed: ${getErrorMessage(apiError)}`);
        } else if (isNetworkError(apiError)) {
          showError('Upload failed due to network issues. Please check your connection and try again.');
        } else {
          showError(`Upload failed: ${getErrorMessage(apiError)}`);
        }
      } finally {
        setUploading(false);
      }
    }
  };

  const handleRemoteDirectory = async () => {
    // Validate path before sync
    const pathVal = validatePath(remotePath);
    if (!pathVal.isValid) {
      showError(`Path validation failed: ${pathVal.errors.join(', ')}`);
      return;
    }

    if (remotePath) {
      const loadingId = showLoading('Syncing remote directory...', undefined, 'progress');
      try {
        setLoading(true);
        updateProgress(loadingId, 25, 'Connecting to remote directory...');
        
        await documentService.syncRemoteDirectory(remotePath);
        
        updateProgress(loadingId, 75, 'Processing documents...');
        showSuccess(`Remote directory "${remotePath}" synced successfully`);
        setRemoteDialogOpen(false);
        setRemotePath('');
        setPathValidation({ isValid: true, errors: [] });
        
        updateProgress(loadingId, 100, 'Sync complete!');
        setTimeout(() => hideLoading(loadingId), 500);
        
        loadDocuments(); // Refresh the list
      } catch (error) {
        const apiError = error as ApiError;
        hideLoading(loadingId);
        
        if (isNetworkError(apiError)) {
          showError('Failed to connect to remote directory. Please check the path and your network connection.');
        } else {
          showError(`Remote directory sync failed: ${getErrorMessage(apiError)}`);
        }
      } finally {
        setLoading(false);
      }
    }
  };

  const handleDeleteDocument = async () => {
    if (documentToDelete) {
      const loadingId = showLoading(`Deleting "${documentToDelete.filename}"...`);
      try {
        await documentService.deleteDocument(documentToDelete.id);
        showSuccess(`Document "${documentToDelete.filename}" deleted successfully`);
        setDeleteDialogOpen(false);
        setDocumentToDelete(null);
        loadDocuments(); // Refresh the list
      } catch (error) {
        const apiError = error as ApiError;
        if (isNetworkError(apiError)) {
          showError('Delete failed due to network issues. Please try again.');
        } else {
          showError(`Failed to delete document: ${getErrorMessage(apiError)}`);
        }
      } finally {
        hideLoading(loadingId);
      }
    }
  };

  const openDeleteDialog = (document: Document) => {
    setDocumentToDelete(document);
    setDeleteDialogOpen(true);
  };

  // Filtering and pagination
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(filters.search.toLowerCase()) ||
                         doc.metadata?.description?.toLowerCase().includes(filters.search.toLowerCase());
    const matchesSchema = !filters.schemaType || doc.schema_type === filters.schemaType;
    const matchesStatus = !filters.status || doc.processing_status === filters.status;
    
    return matchesSearch && matchesSchema && matchesStatus;
  });

  const paginatedDocuments = filteredDocuments.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      sx={{
        position: 'relative',
        minHeight: '100vh',
        ...(dragActive && {
          '&::after': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(25, 118, 210, 0.1)',
            border: '2px dashed #1976d2',
            borderRadius: 1,
            zIndex: 1000,
            pointerEvents: 'none',
          },
        }),
      }}
    >
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Document Repository
        </Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            Upload Document
          </Button>
          <Button
            variant="outlined"
            startIcon={<FolderIcon />}
            onClick={() => setRemoteDialogOpen(true)}
          >
            Remote Directory
          </Button>
        </Box>
      </Box>

      {/* Drag and Drop Overlay */}
      {dragActive && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 1001,
            pointerEvents: 'none',
          }}
        >
          <Paper
            sx={{
              p: 4,
              textAlign: 'center',
              backgroundColor: 'background.paper',
              borderRadius: 2,
            }}
          >
            <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Drop files here to upload
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Supported formats: PDF, DOCX, TXT
            </Typography>
          </Paper>
        </Box>
      )}

      {/* Filters and Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Toolbar sx={{ px: 0 }}>
          <TextField
            size="small"
            placeholder="Search documents..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ mr: 2, minWidth: 200 }}
          />
          
          <FormControl size="small" sx={{ mr: 2, minWidth: 150 }}>
            <InputLabel>Schema Type</InputLabel>
            <Select
              value={filters.schemaType}
              label="Schema Type"
              onChange={(e) => setFilters({ ...filters, schemaType: e.target.value })}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="EU_ESRS_CSRD">EU ESRS/CSRD</MenuItem>
              <MenuItem value="UK_SRD">UK SRD</MenuItem>
              <MenuItem value="OTHER">Other</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ mr: 2, minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={filters.status}
              label="Status"
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="processed">Processed</MenuItem>
              <MenuItem value="processing">Processing</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ flexGrow: 1 }} />

          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="grid">
              <GridViewIcon />
            </ToggleButton>
            <ToggleButton value="list">
              <ListViewIcon />
            </ToggleButton>
          </ToggleButtonGroup>
        </Toolbar>
      </Paper>

      {/* Loading State */}
      {loading && (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Documents Display */}
      {!loading && (
        <>
          {viewMode === 'grid' ? (
            <Grid container spacing={3}>
              {filteredDocuments.length === 0 ? (
                <Grid item xs={12}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center', py: 6 }}>
                      <Typography variant="h6" color="textSecondary" gutterBottom>
                        {documents.length === 0 ? 'No documents uploaded yet' : 'No documents match your filters'}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {documents.length === 0 
                          ? 'Upload your first CSRD, ESRS, or UK SRD document to get started'
                          : 'Try adjusting your search criteria'
                        }
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ) : (
                paginatedDocuments.map((doc) => (
                  <Grid item xs={12} md={6} lg={4} key={doc.id}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom noWrap title={doc.filename}>
                          {doc.filename}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Size: {formatFileSize(doc.file_size)}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Uploaded: {new Date(doc.upload_date).toLocaleDateString()}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Schema: {doc.schema_type.replace('_', ' ')}
                        </Typography>
                        <Box mt={1}>
                          <Chip
                            label={doc.processing_status}
                            color={getStatusColor(doc.processing_status)}
                            size="small"
                          />
                        </Box>
                        <Box mt={2} display="flex" justifyContent="flex-end">
                          <Tooltip title="View Details">
                            <IconButton size="small" color="primary">
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete Document">
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => openDeleteDialog(doc)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))
              )}
            </Grid>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Filename</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Upload Date</TableCell>
                    <TableCell>Schema Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredDocuments.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                        <Typography variant="body2" color="textSecondary">
                          {documents.length === 0 ? 'No documents uploaded yet' : 'No documents match your filters'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedDocuments.map((doc) => (
                      <TableRow key={doc.id} hover>
                        <TableCell>
                          <Typography variant="body2" noWrap title={doc.filename}>
                            {doc.filename}
                          </Typography>
                        </TableCell>
                        <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                        <TableCell>{new Date(doc.upload_date).toLocaleDateString()}</TableCell>
                        <TableCell>{doc.schema_type.replace('_', ' ')}</TableCell>
                        <TableCell>
                          <Chip
                            label={doc.processing_status}
                            color={getStatusColor(doc.processing_status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title="View Details">
                            <IconButton size="small" color="primary">
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete Document">
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => openDeleteDialog(doc)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
              {filteredDocuments.length > 0 && (
                <TablePagination
                  rowsPerPageOptions={[5, 10, 25]}
                  component="div"
                  count={filteredDocuments.length}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={handleChangePage}
                  onRowsPerPageChange={handleChangeRowsPerPage}
                />
              )}
            </TableContainer>
          )}
        </>
      )}

      {/* Upload Dialog */}
      <Dialog 
        open={uploadDialogOpen} 
        onClose={() => !uploading && setUploadDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <input
              accept=".pdf,.docx,.txt"
              style={{ display: 'none' }}
              id="file-upload"
              type="file"
              onChange={handleFileSelect}
              disabled={uploading}
            />
            <label htmlFor="file-upload">
              <Button 
                variant="outlined" 
                component="span" 
                fullWidth 
                sx={{ mb: 2, py: 2 }}
                disabled={uploading}
                startIcon={<UploadIcon />}
                color={!fileValidation.isValid ? 'error' : 'primary'}
              >
                {selectedFile ? selectedFile.name : 'Choose File or Drag & Drop'}
              </Button>
            </label>
            
            {/* File validation errors */}
            {!fileValidation.isValid && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  {fileValidation.errors.join(', ')}
                </Typography>
              </Alert>
            )}
            
            {selectedFile && fileValidation.isValid && (
              <Box sx={{ mb: 2, p: 2, bgcolor: 'success.light', borderRadius: 1, color: 'success.contrastText' }}>
                <Typography variant="body2">
                  File: {selectedFile.name}
                </Typography>
                <Typography variant="body2">
                  Size: {formatFileSize(selectedFile.size)}
                </Typography>
                <Typography variant="body2">
                  Type: {selectedFile.type}
                </Typography>
              </Box>
            )}
            
            <FormControl fullWidth disabled={uploading} error={!schemaValidation.isValid}>
              <InputLabel>Schema Type *</InputLabel>
              <Select
                value={schemaType}
                label="Schema Type *"
                onChange={(e) => {
                  const value = e.target.value;
                  setSchemaType(value);
                  const validation = validateSchemaType(value);
                  setSchemaValidation(validation);
                }}
              >
                <MenuItem value="EU_ESRS_CSRD">EU ESRS/CSRD</MenuItem>
                <MenuItem value="UK_SRD">UK SRD</MenuItem>
                <MenuItem value="OTHER">Other</MenuItem>
              </Select>
              {!schemaValidation.isValid && (
                <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                  {schemaValidation.errors.join(', ')}
                </Typography>
              )}
            </FormControl>

            {uploading && (
              <Box sx={{ mt: 2 }}>
                <ProgressIndicator
                  type="linear"
                  message="Uploading document..."
                  inline={true}
                  size="small"
                />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)} disabled={uploading}>
            Cancel
          </Button>
          <LoadingButton 
            onClick={handleUpload} 
            variant="contained" 
            disabled={!selectedFile || !schemaType || !fileValidation.isValid || !schemaValidation.isValid}
            loading={uploading}
            loadingText="Uploading..."
            startIcon={<UploadIcon />}
          >
            Upload
          </LoadingButton>
        </DialogActions>
      </Dialog>

      {/* Remote Directory Dialog */}
      <Dialog open={remoteDialogOpen} onClose={() => setRemoteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Remote Directory</DialogTitle>
        <DialogContent>
          <ValidatedTextField
            autoFocus
            margin="dense"
            label="Remote Directory Path"
            fullWidth
            variant="outlined"
            value={remotePath}
            onChange={(e) => setRemotePath(e.target.value)}
            placeholder="/path/to/remote/documents"
            sx={{ mt: 2 }}
            helperText="Enter the path to a directory containing documents to sync"
            validator={validatePath}
            validateOnChange={true}
            validateOnBlur={true}
            onValidationChange={(isValid, errors) => {
              setPathValidation({ isValid, errors });
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRemoteDialogOpen(false)}>Cancel</Button>
          <LoadingButton 
            onClick={handleRemoteDirectory} 
            variant="contained" 
            disabled={!remotePath || !pathValidation.isValid}
            loading={loading}
            loadingText="Syncing..."
            startIcon={<FolderIcon />}
          >
            Sync Directory
          </LoadingButton>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Document</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{documentToDelete?.filename}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleDeleteDocument} 
            variant="contained" 
            color="error"
            startIcon={<DeleteIcon />}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};

// Wrap component in ErrorBoundary for additional error protection
const DocumentsWithErrorBoundary: React.FC = () => (
  <ErrorBoundary>
    <Documents />
  </ErrorBoundary>
);

export default DocumentsWithErrorBoundary;