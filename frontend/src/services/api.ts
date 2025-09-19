import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

// Enhanced error types
export interface ApiError {
  type: string;
  status_code: number;
  message: string;
  details?: any;
  path?: string;
  method?: string;
  timestamp?: number;
}

export interface ApiErrorResponse {
  error: ApiError;
}

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens and request ID
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add request ID for tracking
    config.headers['X-Request-ID'] = Date.now().toString();
    
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log request in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }
    
    return config;
  },
  (error: AxiosError) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Response: ${response.status} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    // Enhanced error handling
    const enhancedError = enhanceError(error);
    
    // Log error in development
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', enhancedError);
    }
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    
    return Promise.reject(enhancedError);
  }
);

// Enhanced error processing
function enhanceError(error: AxiosError<ApiErrorResponse>): ApiError {
  // If server returned structured error
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  
  // Network or timeout errors
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return {
      type: 'NetworkError',
      status_code: 0,
      message: 'Request timeout. Please check your connection and try again.',
      timestamp: Date.now()
    };
  }
  
  if (error.code === 'ERR_NETWORK' || !error.response) {
    return {
      type: 'NetworkError',
      status_code: 0,
      message: 'Network error. Please check your connection and try again.',
      timestamp: Date.now()
    };
  }
  
  // HTTP errors without structured response
  const status = error.response?.status || 0;
  let message = 'An unexpected error occurred';
  
  switch (status) {
    case 400:
      message = 'Invalid request. Please check your input and try again.';
      break;
    case 401:
      message = 'Authentication required. Please log in.';
      break;
    case 403:
      message = 'Access denied. You do not have permission to perform this action.';
      break;
    case 404:
      message = 'The requested resource was not found.';
      break;
    case 409:
      message = 'Conflict. The resource already exists or is in use.';
      break;
    case 413:
      message = 'File too large. Please select a smaller file.';
      break;
    case 422:
      message = 'Validation error. Please check your input.';
      break;
    case 429:
      message = 'Too many requests. Please wait a moment and try again.';
      break;
    case 500:
      message = 'Server error. Please try again later.';
      break;
    case 502:
    case 503:
    case 504:
      message = 'Service temporarily unavailable. Please try again later.';
      break;
  }
  
  return {
    type: 'HTTPError',
    status_code: status,
    message: error.response?.data?.message || message,
    details: error.response?.data,
    path: error.config?.url,
    method: error.config?.method?.toUpperCase(),
    timestamp: Date.now()
  };
}

// Utility functions for error handling
export const isNetworkError = (error: ApiError): boolean => {
  return error.type === 'NetworkError' || error.status_code === 0;
};

export const isValidationError = (error: ApiError): boolean => {
  return error.status_code === 422 || error.type === 'ValidationError';
};

export const isServerError = (error: ApiError): boolean => {
  return error.status_code >= 500;
};

export const isClientError = (error: ApiError): boolean => {
  return error.status_code >= 400 && error.status_code < 500;
};

export const getErrorMessage = (error: ApiError): string => {
  return error.message || 'An unexpected error occurred';
};

export const getErrorDetails = (error: ApiError): string | null => {
  if (error.details && typeof error.details === 'object') {
    if (Array.isArray(error.details)) {
      return error.details.map(detail => 
        typeof detail === 'string' ? detail : detail.msg || JSON.stringify(detail)
      ).join(', ');
    }
    return JSON.stringify(error.details, null, 2);
  }
  return null;
};

export default api;