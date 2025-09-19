import React, { useState, useEffect } from 'react';
import {
  TextField,
  TextFieldProps,
  FormHelperText,
  Box,
  Chip,
  Fade,
  CircularProgress,
} from '@mui/material';
import { CheckCircle, Error, Warning } from '@mui/icons-material';
import { ValidationResult } from '../../utils/validation';

interface ValidatedTextFieldProps extends Omit<TextFieldProps, 'error' | 'helperText'> {
  validator?: (value: string) => ValidationResult;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceMs?: number;
  showValidationIcon?: boolean;
  onValidationChange?: (isValid: boolean, errors: string[]) => void;
}

const ValidatedTextField: React.FC<ValidatedTextFieldProps> = ({
  validator,
  validateOnChange = true,
  validateOnBlur = true,
  debounceMs = 300,
  showValidationIcon = true,
  onValidationChange,
  value = '',
  onChange,
  onBlur,
  ...textFieldProps
}) => {
  const [validationResult, setValidationResult] = useState<ValidationResult>({ isValid: true, errors: [] });
  const [isValidating, setIsValidating] = useState(false);
  const [hasBlurred, setHasBlurred] = useState(false);
  const [validationTimer, setValidationTimer] = useState<NodeJS.Timeout | null>(null);

  const performValidation = (inputValue: string) => {
    if (!validator) {
      return { isValid: true, errors: [] };
    }

    setIsValidating(true);
    
    // Clear existing timer
    if (validationTimer) {
      clearTimeout(validationTimer);
    }

    const timer = setTimeout(() => {
      const result = validator(inputValue);
      setValidationResult(result);
      setIsValidating(false);
      
      if (onValidationChange) {
        onValidationChange(result.isValid, result.errors);
      }
    }, debounceMs);

    setValidationTimer(timer);
  };

  useEffect(() => {
    if (validateOnChange && (hasBlurred || value)) {
      performValidation(String(value));
    }

    return () => {
      if (validationTimer) {
        clearTimeout(validationTimer);
      }
    };
  }, [value, validator, validateOnChange, hasBlurred]);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (onChange) {
      onChange(event);
    }
  };

  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    setHasBlurred(true);
    
    if (validateOnBlur) {
      performValidation(event.target.value);
    }
    
    if (onBlur) {
      onBlur(event);
    }
  };

  const shouldShowValidation = hasBlurred || (validateOnChange && value);
  const hasErrors = !validationResult.isValid && validationResult.errors.length > 0;
  const isValid = validationResult.isValid && shouldShowValidation && value;

  const getValidationIcon = () => {
    if (!showValidationIcon || !shouldShowValidation) return null;
    
    if (isValidating) {
      return <CircularProgress size={20} />;
    }
    
    if (hasErrors) {
      return <Error color="error" />;
    }
    
    if (isValid) {
      return <CheckCircle color="success" />;
    }
    
    return null;
  };

  const getHelperText = () => {
    if (hasErrors && shouldShowValidation) {
      return validationResult.errors[0]; // Show first error
    }
    
    return textFieldProps.helperText;
  };

  return (
    <Box>
      <TextField
        {...textFieldProps}
        value={value}
        onChange={handleChange}
        onBlur={handleBlur}
        error={hasErrors && shouldShowValidation}
        helperText={getHelperText()}
        InputProps={{
          ...textFieldProps.InputProps,
          endAdornment: (
            <Box display="flex" alignItems="center" gap={1}>
              {textFieldProps.InputProps?.endAdornment}
              {getValidationIcon()}
            </Box>
          ),
        }}
      />
      
      {/* Show all validation errors as chips */}
      {hasErrors && shouldShowValidation && validationResult.errors.length > 1 && (
        <Fade in={true}>
          <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {validationResult.errors.slice(1).map((error, index) => (
              <Chip
                key={index}
                label={error}
                size="small"
                color="error"
                variant="outlined"
                icon={<Warning />}
              />
            ))}
          </Box>
        </Fade>
      )}
    </Box>
  );
};

export default ValidatedTextField;