// Input validation utilities

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export interface FileValidationOptions {
  maxSize?: number; // in bytes
  allowedTypes?: string[];
  allowedExtensions?: string[];
  minSize?: number;
}

// File validation
export const validateFile = (file: File, options: FileValidationOptions = {}): ValidationResult => {
  const errors: string[] = [];
  
  const {
    maxSize = 50 * 1024 * 1024, // 50MB default
    minSize = 1024, // 1KB minimum
    allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'],
    allowedExtensions = ['.pdf', '.docx', '.txt']
  } = options;
  
  // Check file size
  if (file.size > maxSize) {
    errors.push(`File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(maxSize)})`);
  }
  
  if (file.size < minSize) {
    errors.push(`File size (${formatFileSize(file.size)}) is below minimum required size (${formatFileSize(minSize)})`);
  }
  
  // Check file type
  if (!allowedTypes.includes(file.type)) {
    errors.push(`File type "${file.type}" is not supported. Allowed types: ${allowedTypes.join(', ')}`);
  }
  
  // Check file extension
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!allowedExtensions.some(ext => ext.toLowerCase() === fileExtension)) {
    errors.push(`File extension "${fileExtension}" is not supported. Allowed extensions: ${allowedExtensions.join(', ')}`);
  }
  
  // Check for empty file name
  if (!file.name.trim()) {
    errors.push('File name cannot be empty');
  }
  
  // Check for suspicious file names
  if (file.name.includes('..') || file.name.includes('/') || file.name.includes('\\')) {
    errors.push('File name contains invalid characters');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// Text input validation
export const validateText = (text: string, options: {
  minLength?: number;
  maxLength?: number;
  required?: boolean;
  pattern?: RegExp;
  patternMessage?: string;
} = {}): ValidationResult => {
  const errors: string[] = [];
  const {
    minLength = 0,
    maxLength = 10000,
    required = false,
    pattern,
    patternMessage = 'Invalid format'
  } = options;
  
  const trimmedText = text.trim();
  
  if (required && !trimmedText) {
    errors.push('This field is required');
  }
  
  if (trimmedText && trimmedText.length < minLength) {
    errors.push(`Minimum length is ${minLength} characters`);
  }
  
  if (trimmedText.length > maxLength) {
    errors.push(`Maximum length is ${maxLength} characters`);
  }
  
  if (pattern && trimmedText && !pattern.test(trimmedText)) {
    errors.push(patternMessage);
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// Email validation
export const validateEmail = (email: string): ValidationResult => {
  const emailPattern = /^[a-zA-Z0-9][a-zA-Z0-9._%+-]*[a-zA-Z0-9]@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
  return validateText(email, {
    required: true,
    pattern: emailPattern,
    patternMessage: 'Please enter a valid email address'
  });
};

// URL validation
export const validateUrl = (url: string, required = false): ValidationResult => {
  if (!required && !url.trim()) {
    return { isValid: true, errors: [] };
  }
  
  try {
    const urlObj = new URL(url);
    // Only allow http and https protocols
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      return { isValid: false, errors: ['Please enter a valid URL (http:// or https://)'] };
    }
    return { isValid: true, errors: [] };
  } catch {
    return { isValid: false, errors: ['Please enter a valid URL'] };
  }
};

// Path validation for remote directories
export const validatePath = (path: string): ValidationResult => {
  const errors: string[] = [];
  
  if (!path.trim()) {
    errors.push('Path is required');
    return { isValid: false, errors };
  }
  
  // Basic path validation
  if (path.includes('..')) {
    errors.push('Path cannot contain ".." for security reasons');
  }
  
  if (path.length > 500) {
    errors.push('Path is too long (maximum 500 characters)');
  }
  
  // Check for invalid characters (basic check)
  const invalidChars = ['<', '>', '"', '|', '?', '*'];
  const hasInvalidChars = invalidChars.some(char => path.includes(char));
  if (hasInvalidChars) {
    errors.push(`Path contains invalid characters: ${invalidChars.join(', ')}`);
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// Schema type validation
export const validateSchemaType = (schemaType: string): ValidationResult => {
  const validSchemaTypes = ['EU_ESRS_CSRD', 'UK_SRD', 'OTHER'];
  
  if (!schemaType) {
    return { isValid: false, errors: ['Schema type is required'] };
  }
  
  if (!validSchemaTypes.includes(schemaType)) {
    return { 
      isValid: false, 
      errors: [`Invalid schema type. Must be one of: ${validSchemaTypes.join(', ')}`] 
    };
  }
  
  return { isValid: true, errors: [] };
};

// Query validation for search and RAG
export const validateQuery = (query: string): ValidationResult => {
  return validateText(query, {
    required: true,
    minLength: 3,
    maxLength: 1000,
  });
};

// Utility function to format file size
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const formattedSize = (bytes / Math.pow(k, i));
  
  // Only show decimals if they're not zero
  if (formattedSize % 1 === 0) {
    return formattedSize + ' ' + sizes[i];
  } else {
    return formattedSize.toFixed(2) + ' ' + sizes[i];
  }
};

import React from 'react';

// Real-time validation hook
export const useRealTimeValidation = (
  value: string,
  validator: (value: string) => ValidationResult,
  debounceMs = 300
) => {
  const [validationResult, setValidationResult] = React.useState<ValidationResult>({ isValid: true, errors: [] });
  const [isValidating, setIsValidating] = React.useState(false);
  
  React.useEffect(() => {
    setIsValidating(true);
    const timer = setTimeout(() => {
      const result = validator(value);
      setValidationResult(result);
      setIsValidating(false);
    }, debounceMs);
    
    return () => clearTimeout(timer);
  }, [value, validator, debounceMs]);
  
  return { validationResult, isValidating };
};

// Form validation helper
export const validateForm = (fields: Record<string, any>, validators: Record<string, (value: any) => ValidationResult>): {
  isValid: boolean;
  errors: Record<string, string[]>;
} => {
  const errors: Record<string, string[]> = {};
  let isValid = true;
  
  Object.keys(validators).forEach(fieldName => {
    const validator = validators[fieldName];
    const value = fields[fieldName];
    const result = validator(value);
    
    if (!result.isValid) {
      errors[fieldName] = result.errors;
      isValid = false;
    }
  });
  
  return { isValid, errors };
};