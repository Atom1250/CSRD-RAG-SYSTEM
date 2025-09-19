import React from 'react';
import {
  Box,
  LinearProgress,
  CircularProgress,
  Typography,
  Paper,
  Fade,
} from '@mui/material';

interface ProgressIndicatorProps {
  type?: 'linear' | 'circular';
  progress?: number; // 0-100
  message?: string;
  subMessage?: string;
  variant?: 'determinate' | 'indeterminate';
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  showPercentage?: boolean;
  inline?: boolean;
  elevation?: boolean;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  type = 'linear',
  progress,
  message,
  subMessage,
  variant = progress !== undefined ? 'determinate' : 'indeterminate',
  size = 'medium',
  color = 'primary',
  showPercentage = true,
  inline = false,
  elevation = false,
}) => {
  const getSizeProps = () => {
    switch (size) {
      case 'small':
        return type === 'circular' ? { size: 24 } : { sx: { height: 4 } };
      case 'large':
        return type === 'circular' ? { size: 60 } : { sx: { height: 12 } };
      default:
        return type === 'circular' ? { size: 40 } : { sx: { height: 8 } };
    }
  };

  const progressValue = variant === 'determinate' ? progress : undefined;

  const content = (
    <Box
      display="flex"
      flexDirection={inline ? 'row' : 'column'}
      alignItems="center"
      gap={inline ? 2 : 1}
      sx={{
        ...(inline && { minWidth: 200 }),
        ...(!inline && { textAlign: 'center', minWidth: 300 }),
      }}
    >
      {/* Progress Element */}
      <Box
        display="flex"
        alignItems="center"
        sx={{
          ...(type === 'linear' && !inline && { width: '100%' }),
          ...(inline && { flex: 1 }),
        }}
      >
        {type === 'circular' ? (
          <CircularProgress
            variant={variant}
            value={progressValue}
            color={color}
            {...getSizeProps()}
          />
        ) : (
          <Box sx={{ width: '100%', position: 'relative' }}>
            <LinearProgress
              variant={variant}
              value={progressValue}
              color={color}
              {...getSizeProps()}
              sx={{
                borderRadius: 4,
                ...getSizeProps().sx,
              }}
            />
            {variant === 'determinate' && showPercentage && (
              <Typography
                variant="caption"
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  color: 'white',
                  fontWeight: 'bold',
                  textShadow: '1px 1px 2px rgba(0,0,0,0.7)',
                  fontSize: size === 'small' ? '0.6rem' : '0.75rem',
                }}
              >
                {Math.round(progress || 0)}%
              </Typography>
            )}
          </Box>
        )}
      </Box>

      {/* Messages */}
      {(message || subMessage || (variant === 'determinate' && showPercentage && type === 'circular')) && (
        <Box
          sx={{
            ...(inline && { textAlign: 'left' }),
            ...(!inline && { textAlign: 'center', mt: 1 }),
          }}
        >
          {message && (
            <Typography
              variant={size === 'small' ? 'body2' : 'body1'}
              color="textPrimary"
              gutterBottom={!!subMessage}
            >
              {message}
            </Typography>
          )}
          
          {subMessage && (
            <Typography
              variant="caption"
              color="textSecondary"
              display="block"
            >
              {subMessage}
            </Typography>
          )}
          
          {variant === 'determinate' && showPercentage && type === 'circular' && (
            <Typography
              variant={size === 'large' ? 'h6' : 'body2'}
              color="textPrimary"
              sx={{ mt: 0.5 }}
            >
              {Math.round(progress || 0)}%
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );

  if (elevation) {
    return (
      <Fade in={true}>
        <Paper
          elevation={2}
          sx={{
            p: 3,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            borderRadius: 2,
          }}
        >
          {content}
        </Paper>
      </Fade>
    );
  }

  return <Fade in={true}>{content}</Fade>;
};

export default ProgressIndicator;