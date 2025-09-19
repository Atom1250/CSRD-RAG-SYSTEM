import React from 'react';
import { Button, ButtonProps, CircularProgress, Box } from '@mui/material';

interface LoadingButtonProps extends Omit<ButtonProps, 'startIcon' | 'endIcon'> {
  loading?: boolean;
  loadingText?: string;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  loadingPosition?: 'start' | 'end' | 'center';
}

const LoadingButton: React.FC<LoadingButtonProps> = ({
  loading = false,
  loadingText,
  children,
  disabled,
  startIcon,
  endIcon,
  loadingPosition = 'start',
  ...props
}) => {
  const isDisabled = disabled || loading;
  
  const loadingIndicator = (
    <CircularProgress
      size={16}
      color="inherit"
      sx={{
        ...(loadingPosition === 'start' && { mr: 1 }),
        ...(loadingPosition === 'end' && { ml: 1 }),
      }}
    />
  );

  const getStartIcon = () => {
    if (loading && loadingPosition === 'start') {
      return loadingIndicator;
    }
    return startIcon;
  };

  const getEndIcon = () => {
    if (loading && loadingPosition === 'end') {
      return loadingIndicator;
    }
    return endIcon;
  };

  const getChildren = () => {
    if (loading && loadingPosition === 'center') {
      return (
        <Box display="flex" alignItems="center" justifyContent="center">
          {loadingIndicator}
          {loadingText && <span style={{ marginLeft: 8 }}>{loadingText}</span>}
        </Box>
      );
    }
    
    if (loading && loadingText) {
      return loadingText;
    }
    
    return children;
  };

  return (
    <Button
      {...props}
      disabled={isDisabled}
      startIcon={getStartIcon()}
      endIcon={getEndIcon()}
    >
      {getChildren()}
    </Button>
  );
};

export default LoadingButton;