import React, { useState } from 'react';
import { TextField, Button, Box, Typography, CircularProgress, Paper, Grow } from '@mui/material';
import { styled } from '@mui/system';
import { detectURL } from '../services/api';
import LockIcon from '@mui/icons-material/Lock';
import ErrorIcon from '@mui/icons-material/Error';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  background: 'linear-gradient(45deg, #1a1a1a 30%, #2a2a2a 90%)',
  border: '1px solid #00ff00',
  boxShadow: '0 3px 5px 2px rgba(0, 255, 0, .3)',
}));

const ResultBox = styled(Box)(({ theme, ismalicious }) => ({
  marginTop: theme.spacing(2),
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  background: ismalicious === 'true' ? 'rgba(255, 0, 0, 0.1)' : 'rgba(0, 255, 0, 0.1)',
  border: `1px solid ${ismalicious === 'true' ? theme.palette.error.main : theme.palette.primary.main}`,
}));

function URLDetectorForm() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await detectURL(url);
      setResult(data.prediction);
    } catch (err) {
      setError('An error occurred while detecting the URL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <StyledPaper elevation={3}>
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
        <TextField
          fullWidth
          label="Enter URL"
          variant="outlined"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          margin="normal"
          InputProps={{
            startAdornment: <LockIcon color="primary" sx={{ mr: 1 }} />,
          }}
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={loading}
          sx={{ mt: 2, width: '100%' }}
        >
          {loading ? <CircularProgress size={24} /> : 'Scan URL'}
        </Button>
        <Grow in={result !== null}>
          <ResultBox ismalicious={result?.toString()}>
            <Typography variant="h6" color={result ? 'error' : 'primary'}>
              {result ? 'Malicious URL Detected!' : 'URL is Safe'}
            </Typography>
            <Typography variant="body1">
              {result
                ? 'This URL may be harmful. Proceed with caution.'
                : 'No threats detected. Stay vigilant!'}
            </Typography>
          </ResultBox>
        </Grow>
        {error && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', color: 'error.main' }}>
            <ErrorIcon sx={{ mr: 1 }} />
            <Typography>{error}</Typography>
          </Box>
        )}
      </Box>
    </StyledPaper>
  );
}

export default URLDetectorForm;