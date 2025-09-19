import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  FormControlLabel,
  Switch,
  Alert,
  Link,
  Grid,
  Paper,
  Tooltip,
  IconButton,
} from '@mui/material';
import { 
  Search as SearchIcon, 
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Info as InfoIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { searchService, SearchResult, SearchQuery } from '../services/searchService';

// Enum definitions matching backend
enum DocumentType {
  PDF = 'pdf',
  DOCX = 'docx',
  TXT = 'txt',
}

enum SchemaType {
  EU_ESRS_CSRD = 'EU_ESRS_CSRD',
  UK_SRD = 'UK_SRD',
}

enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

interface SearchFilters {
  documentType?: DocumentType;
  schemaType?: SchemaType;
  processingStatus?: ProcessingStatus;
  filenameContains?: string;
  minRelevanceScore: number;
  enableReranking: boolean;
}

const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTime, setSearchTime] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  
  // Search filters state
  const [filters, setFilters] = useState<SearchFilters>({
    minRelevanceScore: 0.0,
    enableReranking: true,
  });

  // Search suggestions
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Load search suggestions when query changes
  useEffect(() => {
    const loadSuggestions = async () => {
      if (query.length >= 2) {
        try {
          const suggestionResults = await searchService.getSuggestions(query);
          setSuggestions(suggestionResults);
          setShowSuggestions(true);
        } catch (err) {
          // Silently fail for suggestions
          setSuggestions([]);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    };

    const timeoutId = setTimeout(loadSuggestions, 300); // Debounce
    return () => clearTimeout(timeoutId);
  }, [query]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setShowSuggestions(false);
    const startTime = Date.now();
    
    try {
      const searchQuery: SearchQuery = {
        query: query.trim(),
        top_k: 20,
        min_relevance_score: filters.minRelevanceScore,
        enable_reranking: filters.enableReranking,
        document_type: filters.documentType,
        schema_type: filters.schemaType,
        processing_status: filters.processingStatus,
        filename_contains: filters.filenameContains,
      };

      const searchResults = await searchService.search(searchQuery);
      setResults(searchResults);
      setSearchTime(Date.now() - startTime);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed. Please try again.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    } else if (event.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    // Auto-search when suggestion is selected
    setTimeout(() => handleSearch(), 100);
  };

  const clearFilters = () => {
    setFilters({
      minRelevanceScore: 0.0,
      enableReranking: true,
    });
  };

  const hasActiveFilters = () => {
    return filters.documentType || 
           filters.schemaType || 
           filters.processingStatus || 
           filters.filenameContains || 
           filters.minRelevanceScore > 0;
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'default';
  };

  const formatContent = (content: string, maxLength: number = 300) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Document Search
      </Typography>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box position="relative">
            <Box display="flex" gap={2} mb={2}>
              <Box flex={1} position="relative">
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Search through your sustainability documents..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                />
                
                {/* Search Suggestions */}
                {showSuggestions && suggestions.length > 0 && (
                  <Paper
                    sx={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      zIndex: 1000,
                      maxHeight: 200,
                      overflow: 'auto',
                      mt: 1,
                    }}
                  >
                    <List dense>
                      {suggestions.map((suggestion, index) => (
                        <ListItem
                          key={index}
                          button
                          onClick={() => handleSuggestionClick(suggestion)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <ListItemText primary={suggestion} />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}
              </Box>
              
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => setShowFilters(!showFilters)}
                color={hasActiveFilters() ? 'primary' : 'inherit'}
              >
                Filters {hasActiveFilters() && `(${Object.values(filters).filter(v => v && v !== 0 && v !== true).length})`}
              </Button>
              
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                onClick={handleSearch}
                disabled={loading || !query.trim()}
                sx={{ minWidth: 120 }}
              >
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </Box>

            {/* Advanced Filters */}
            <Accordion expanded={showFilters} onChange={() => setShowFilters(!showFilters)}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Advanced Search Filters</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Document Type</InputLabel>
                      <Select
                        value={filters.documentType || ''}
                        onChange={(e) => setFilters({...filters, documentType: e.target.value as DocumentType || undefined})}
                      >
                        <MenuItem value="">All Types</MenuItem>
                        <MenuItem value={DocumentType.PDF}>PDF</MenuItem>
                        <MenuItem value={DocumentType.DOCX}>DOCX</MenuItem>
                        <MenuItem value={DocumentType.TXT}>TXT</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Schema Type</InputLabel>
                      <Select
                        value={filters.schemaType || ''}
                        onChange={(e) => setFilters({...filters, schemaType: e.target.value as SchemaType || undefined})}
                      >
                        <MenuItem value="">All Schemas</MenuItem>
                        <MenuItem value={SchemaType.EU_ESRS_CSRD}>EU ESRS/CSRD</MenuItem>
                        <MenuItem value={SchemaType.UK_SRD}>UK SRD</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Processing Status</InputLabel>
                      <Select
                        value={filters.processingStatus || ''}
                        onChange={(e) => setFilters({...filters, processingStatus: e.target.value as ProcessingStatus || undefined})}
                      >
                        <MenuItem value="">All Statuses</MenuItem>
                        <MenuItem value={ProcessingStatus.COMPLETED}>Completed</MenuItem>
                        <MenuItem value={ProcessingStatus.PROCESSING}>Processing</MenuItem>
                        <MenuItem value={ProcessingStatus.PENDING}>Pending</MenuItem>
                        <MenuItem value={ProcessingStatus.FAILED}>Failed</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Filename Contains"
                      value={filters.filenameContains || ''}
                      onChange={(e) => setFilters({...filters, filenameContains: e.target.value || undefined})}
                      placeholder="Enter filename text"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Typography gutterBottom>
                      Minimum Relevance Score: {filters.minRelevanceScore.toFixed(2)}
                    </Typography>
                    <Slider
                      value={filters.minRelevanceScore}
                      onChange={(_, value) => setFilters({...filters, minRelevanceScore: value as number})}
                      min={0}
                      max={1}
                      step={0.05}
                      marks={[
                        { value: 0, label: '0%' },
                        { value: 0.5, label: '50%' },
                        { value: 1, label: '100%' }
                      ]}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={filters.enableReranking}
                          onChange={(e) => setFilters({...filters, enableReranking: e.target.checked})}
                        />
                      }
                      label={
                        <Box display="flex" alignItems="center" gap={1}>
                          Enable Advanced Ranking
                          <Tooltip title="Uses additional algorithms to improve result relevance">
                            <InfoIcon fontSize="small" />
                          </Tooltip>
                        </Box>
                      }
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Button
                      variant="outlined"
                      startIcon={<ClearIcon />}
                      onClick={clearFilters}
                      disabled={!hasActiveFilters()}
                    >
                      Clear All Filters
                    </Button>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Box>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Search Results ({results.length})
              </Typography>
              {searchTime && (
                <Typography variant="body2" color="textSecondary">
                  Found in {searchTime}ms
                </Typography>
              )}
            </Box>
            
            <List>
              {results.map((result, index) => (
                <React.Fragment key={result.chunk_id}>
                  <ListItem alignItems="flex-start" sx={{ px: 0, py: 2 }}>
                    <ListItemText
                      primary={
                        <Box>
                          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                            <Typography variant="subtitle1" component="div" sx={{ fontWeight: 'medium' }}>
                              {result.document_filename}
                            </Typography>
                            <IconButton
                              size="small"
                              onClick={() => {
                                // TODO: Implement document viewer
                                console.log('Open document:', result.document_id);
                              }}
                              title="Open document"
                            >
                              <OpenInNewIcon fontSize="small" />
                            </IconButton>
                          </Box>
                          
                          <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                            <Chip 
                              label={`${(result.relevance_score * 100).toFixed(0)}%`} 
                              size="small" 
                              color={getRelevanceColor(result.relevance_score) as any}
                              variant="filled"
                            />
                            
                            {result.schema_elements && result.schema_elements.length > 0 && (
                              <>
                                {result.schema_elements.slice(0, 3).map((element) => (
                                  <Chip 
                                    key={element} 
                                    label={element} 
                                    size="small" 
                                    variant="outlined"
                                    color="primary"
                                  />
                                ))}
                                {result.schema_elements.length > 3 && (
                                  <Chip 
                                    label={`+${result.schema_elements.length - 3} more`}
                                    size="small" 
                                    variant="outlined"
                                    color="default"
                                  />
                                )}
                              </>
                            )}
                          </Box>
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary" sx={{ lineHeight: 1.6 }}>
                            {formatContent(result.content)}
                          </Typography>
                          
                          {result.content.length > 300 && (
                            <Link
                              component="button"
                              variant="body2"
                              onClick={() => {
                                // TODO: Implement full content view
                                console.log('Show full content for chunk:', result.chunk_id);
                              }}
                              sx={{ mt: 1 }}
                            >
                              Show full content
                            </Link>
                          )}
                          
                          <Box mt={1}>
                            <Typography variant="caption" color="textSecondary">
                              Document ID: {result.document_id} • Chunk ID: {result.chunk_id}
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < results.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* No Results */}
      {results.length === 0 && !loading && !error && query && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="textSecondary" gutterBottom>
              No results found
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={2}>
              Try adjusting your search terms or filters
            </Typography>
            
            {hasActiveFilters() && (
              <Button
                variant="outlined"
                onClick={clearFilters}
                startIcon={<ClearIcon />}
              >
                Clear Filters and Search Again
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Initial State */}
      {!query && !loading && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <SearchIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="textSecondary" gutterBottom>
              Search Your Sustainability Documents
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={3}>
              Enter keywords, questions, or specific requirements to find relevant information
            </Typography>
            
            <Box display="flex" flexWrap="wrap" gap={1} justifyContent="center">
              {[
                'climate change adaptation',
                'greenhouse gas emissions',
                'biodiversity conservation',
                'employee diversity',
                'governance practices'
              ].map((suggestion) => (
                <Chip
                  key={suggestion}
                  label={suggestion}
                  variant="outlined"
                  clickable
                  onClick={() => handleSuggestionClick(suggestion)}
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Search;