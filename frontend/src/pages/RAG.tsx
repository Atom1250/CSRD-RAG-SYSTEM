import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Paper,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  IconButton,
  Tooltip,
  Alert,
  Slider,
  FormControlLabel,
  Switch,
  Divider,
  Rating,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Badge,
  Tabs,
  Tab,
  LinearProgress,
} from '@mui/material';
import {
  Psychology as RAGIcon,
  ExpandMore as ExpandMoreIcon,
  Source as SourceIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Clear as ClearIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Star as StarIcon,
  Close as CloseIcon,
  Send as SendIcon,
  AutoAwesome as AutoAwesomeIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

import { ragService, RAGResponse, AIModel, ConversationEntry, ModelStatus } from '../services/ragService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`rag-tabpanel-${index}`}
      aria-labelledby={`rag-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const RAG: React.FC = () => {
  // Core state
  const [query, setQuery] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<RAGResponse | null>(null);
  
  // Models and status
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [modelsLoading, setModelsLoading] = useState(true);
  
  // Conversation history
  const [conversationHistory, setConversationHistory] = useState<ConversationEntry[]>([]);
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
  const [historySearchTerm, setHistorySearchTerm] = useState('');
  
  // Advanced settings
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [maxContextChunks, setMaxContextChunks] = useState(10);
  const [minRelevanceScore, setMinRelevanceScore] = useState(0.3);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [temperature, setTemperature] = useState(0.1);
  const [autoRefine, setAutoRefine] = useState(false);
  
  // Feedback and rating
  const [feedbackDialog, setFeedbackDialog] = useState<{ open: boolean; entryId: string | null }>({
    open: false,
    entryId: null
  });
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  
  // UI state
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info'
  });
  const [activeTab, setActiveTab] = useState(0);
  
  const queryInputRef = useRef<HTMLInputElement>(null);

  // Load initial data
  useEffect(() => {
    loadModels();
    loadConversationHistory();
  }, []);

  // Set default model when models are loaded
  useEffect(() => {
    if (modelStatus && !selectedModel) {
      setSelectedModel(modelStatus.default_model);
    }
  }, [modelStatus, selectedModel]);

  const loadModels = async () => {
    try {
      setModelsLoading(true);
      const [models, status] = await Promise.all([
        ragService.getAvailableModels(),
        ragService.getModelStatus()
      ]);
      setAvailableModels(models);
      setModelStatus(status);
    } catch (error) {
      console.error('Failed to load models:', error);
      showSnackbar('Failed to load AI models', 'error');
    } finally {
      setModelsLoading(false);
    }
  };

  const loadConversationHistory = () => {
    const history = ragService.getConversationHistory();
    setConversationHistory(history);
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleSubmitQuery = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await ragService.submitQuery({
        question: query.trim(),
        model_type: selectedModel,
        max_context_chunks: maxContextChunks,
        min_relevance_score: minRelevanceScore,
        max_tokens: maxTokens,
        temperature: temperature
      });

      setCurrentResponse(response);
      
      // Save to conversation history
      const conversationEntry: ConversationEntry = {
        id: response.id,
        query: query.trim(),
        response,
        timestamp: new Date().toISOString()
      };
      
      ragService.saveConversationEntry(conversationEntry);
      loadConversationHistory();
      
      setQuery('');
      showSnackbar('Response generated successfully', 'success');
      
      // Auto-refine if enabled and confidence is low
      if (autoRefine && response.confidence_score < 0.6) {
        showSnackbar('Low confidence detected. Consider refining your question.', 'info');
      }
      
    } catch (error) {
      console.error('Failed to generate response:', error);
      showSnackbar('Failed to generate response. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmitQuery();
    }
  };

  const handleHistoryItemClick = (entry: ConversationEntry) => {
    setCurrentResponse(entry.response);
    setQuery(entry.query);
    setHistoryDrawerOpen(false);
  };

  const handleClearHistory = () => {
    ragService.clearConversationHistory();
    setConversationHistory([]);
    showSnackbar('Conversation history cleared', 'info');
  };

  const handleRefineQuery = (originalQuery: string) => {
    const refinedQuery = `Please provide more specific details about: ${originalQuery}`;
    setQuery(refinedQuery);
    queryInputRef.current?.focus();
  };

  const handleFeedbackSubmit = () => {
    if (feedbackDialog.entryId && feedbackRating !== null) {
      const feedback = {
        rating: feedbackRating,
        comment: feedbackComment.trim() || undefined
      };
      
      ragService.updateConversationFeedback(feedbackDialog.entryId, feedback);
      loadConversationHistory();
      
      setFeedbackDialog({ open: false, entryId: null });
      setFeedbackRating(null);
      setFeedbackComment('');
      showSnackbar('Feedback submitted successfully', 'success');
    }
  };

  const getModelIcon = (modelType: string) => {
    if (modelType.includes('gpt')) return <AutoAwesomeIcon />;
    if (modelType.includes('claude')) return <RAGIcon />;
    if (modelType.includes('llama')) return <SecurityIcon />;
    return <SpeedIcon />;
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const filteredHistory = historySearchTerm
    ? ragService.searchConversationHistory(historySearchTerm)
    : conversationHistory;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          RAG Question Answering
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Conversation History">
            <IconButton onClick={() => setHistoryDrawerOpen(true)}>
              <Badge badgeContent={conversationHistory.length} color="primary">
                <HistoryIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          <Tooltip title="Advanced Settings">
            <IconButton onClick={() => setSettingsOpen(true)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh Models">
            <IconButton onClick={loadModels} disabled={modelsLoading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Model Status Alert */}
      {modelStatus && modelStatus.available_count === 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          No AI models are currently available. Please check your configuration.
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 2 }}>
        <Tab label="Ask Question" />
        <Tab label="Current Response" disabled={!currentResponse} />
      </Tabs>

      <TabPanel value={activeTab} index={0}>
        {/* Query Input Section */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="flex-end">
              <Grid item xs={12} md={4}>
                <FormControl fullWidth disabled={modelsLoading}>
                  <InputLabel>AI Model</InputLabel>
                  <Select
                    value={selectedModel}
                    label="AI Model"
                    onChange={(e) => setSelectedModel(e.target.value)}
                  >
                    {availableModels.map((model) => (
                      <MenuItem key={model.type} value={model.type} disabled={!model.available}>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getModelIcon(model.type)}
                          <Box>
                            <Typography variant="body2">
                              {model.provider} {model.model}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {model.capabilities.join(', ')}
                            </Typography>
                          </Box>
                          {!model.available && (
                            <Chip label="Unavailable" size="small" color="error" />
                          )}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={8}>
                <Box display="flex" gap={1}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    variant="outlined"
                    placeholder="Ask a question about your sustainability documents... (e.g., 'What are the key requirements for climate-related disclosures under ESRS E1?')"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    inputRef={queryInputRef}
                    disabled={loading || !selectedModel}
                  />
                  <Button
                    variant="contained"
                    onClick={handleSubmitQuery}
                    disabled={loading || !query.trim() || !selectedModel}
                    sx={{ minWidth: 120, height: 'fit-content' }}
                    startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                  >
                    {loading ? 'Generating...' : 'Ask'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
            
            {loading && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
                  Retrieving context and generating response...
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Quick Examples */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Examples
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {[
                "What are the key requirements for climate-related disclosures under ESRS E1?",
                "How should companies report on biodiversity impacts?",
                "What are the governance requirements under CSRD?",
                "Explain the double materiality assessment process"
              ].map((example, index) => (
                <Chip
                  key={index}
                  label={example}
                  variant="outlined"
                  clickable
                  onClick={() => setQuery(example)}
                  sx={{ mb: 1 }}
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        {/* Current Response Display */}
        {currentResponse && (
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                <Typography variant="h6" sx={{ flex: 1 }}>
                  {currentResponse.query}
                </Typography>
                <Box display="flex" gap={1} alignItems="center">
                  <Chip 
                    label={`Confidence: ${(currentResponse.confidence_score * 100).toFixed(0)}%`} 
                    size="small" 
                    color={getConfidenceColor(currentResponse.confidence_score)}
                  />
                  <Chip 
                    label={currentResponse.model_used} 
                    size="small" 
                    variant="outlined" 
                  />
                  <Tooltip title="Rate this response">
                    <IconButton 
                      size="small"
                      onClick={() => setFeedbackDialog({ open: true, entryId: currentResponse.id })}
                    >
                      <StarIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Refine this query">
                    <IconButton 
                      size="small"
                      onClick={() => handleRefineQuery(currentResponse.query)}
                    >
                      <AutoAwesomeIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
              
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {currentResponse.response_text}
                </Typography>
              </Paper>
              
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <SourceIcon />
                    <Typography variant="subtitle2">
                      Sources ({currentResponse.source_chunks.length})
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {currentResponse.source_chunks.length > 0 ? (
                    currentResponse.source_chunks.map((chunkId, index) => (
                      <Box key={index} sx={{ mb: 2, p: 2, border: 1, borderColor: 'grey.300', borderRadius: 1 }}>
                        <Typography variant="subtitle2" color="primary">
                          Source Chunk {chunkId}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Referenced in response generation
                        </Typography>
                      </Box>
                    ))
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      No source chunks available for this response.
                    </Typography>
                  )}
                </AccordionDetails>
              </Accordion>
              
              <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
                Generated on {new Date(currentResponse.generation_timestamp).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        )}
      </TabPanel>

      {/* Conversation History Drawer */}
      <Drawer
        anchor="right"
        open={historyDrawerOpen}
        onClose={() => setHistoryDrawerOpen(false)}
        sx={{ '& .MuiDrawer-paper': { width: 400 } }}
      >
        <Box sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Conversation History</Typography>
            <Box>
              <IconButton onClick={handleClearHistory} size="small">
                <ClearIcon />
              </IconButton>
              <IconButton onClick={() => setHistoryDrawerOpen(false)} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
          
          <TextField
            fullWidth
            size="small"
            placeholder="Search conversations..."
            value={historySearchTerm}
            onChange={(e) => setHistorySearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            sx={{ mb: 2 }}
          />
          
          <List>
            {filteredHistory.map((entry) => (
              <ListItem key={entry.id} disablePadding>
                <ListItemButton onClick={() => handleHistoryItemClick(entry)}>
                  <ListItemText
                    primary={entry.query}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          {new Date(entry.timestamp).toLocaleString()}
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                          <Chip 
                            label={`${(entry.response.confidence_score * 100).toFixed(0)}%`}
                            size="small"
                            color={getConfidenceColor(entry.response.confidence_score)}
                          />
                          {entry.feedback && (
                            <Rating value={entry.feedback.rating} size="small" readOnly />
                          )}
                        </Box>
                      </Box>
                    }
                    primaryTypographyProps={{ 
                      noWrap: true,
                      sx: { fontSize: '0.875rem' }
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
            {filteredHistory.length === 0 && (
              <ListItem>
                <ListItemText 
                  primary="No conversations found"
                  secondary="Start asking questions to build your history"
                />
              </ListItem>
            )}
          </List>
        </Box>
      </Drawer>

      {/* Advanced Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Advanced Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Typography gutterBottom>Max Context Chunks: {maxContextChunks}</Typography>
            <Slider
              value={maxContextChunks}
              onChange={(_, value) => setMaxContextChunks(value as number)}
              min={1}
              max={20}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />
            
            <Typography gutterBottom>Min Relevance Score: {minRelevanceScore}</Typography>
            <Slider
              value={minRelevanceScore}
              onChange={(_, value) => setMinRelevanceScore(value as number)}
              min={0}
              max={1}
              step={0.1}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />
            
            <Typography gutterBottom>Max Tokens: {maxTokens}</Typography>
            <Slider
              value={maxTokens}
              onChange={(_, value) => setMaxTokens(value as number)}
              min={100}
              max={4000}
              step={100}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />
            
            <Typography gutterBottom>Temperature: {temperature}</Typography>
            <Slider
              value={temperature}
              onChange={(_, value) => setTemperature(value as number)}
              min={0}
              max={2}
              step={0.1}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefine}
                  onChange={(e) => setAutoRefine(e.target.checked)}
                />
              }
              label="Auto-suggest refinements for low confidence responses"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Feedback Dialog */}
      <Dialog open={feedbackDialog.open} onClose={() => setFeedbackDialog({ open: false, entryId: null })}>
        <DialogTitle>Rate Response</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Typography gutterBottom>How would you rate this response?</Typography>
            <Rating
              value={feedbackRating}
              onChange={(_, value) => setFeedbackRating(value)}
              size="large"
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              multiline
              rows={3}
              placeholder="Optional feedback comment..."
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackDialog({ open: false, entryId: null })}>
            Cancel
          </Button>
          <Button 
            onClick={handleFeedbackSubmit}
            disabled={feedbackRating === null}
            variant="contained"
          >
            Submit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Empty State */}
      {!currentResponse && activeTab === 1 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <RAGIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="textSecondary" gutterBottom>
              No response yet
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Ask a question to see AI-powered responses with source citations
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default RAG;