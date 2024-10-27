import React, { useState } from 'react';
import { TextField, Button, Box, Typography, CircularProgress, Paper } from '@mui/material';
import { styled } from '@mui/system';
import { detectURLWithExplanation } from '../services/api';
import LockIcon from '@mui/icons-material/Lock';
import ErrorIcon from '@mui/icons-material/Error';
import URLAnalysisResult from './URLAnalysisResult';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  background: 'linear-gradient(45deg, #1a1a1a 30%, #2a2a2a 90%)',
  border: '1px solid #00ff00',
  boxShadow: '0 3px 5px 2px rgba(0, 255, 0, .3)',
}));

function URLDetectorForm() {
  const [url, setUrl] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const ensureHttpPrefix = (url) => {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return `https://${url}`;
    }
    return url;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      // Format URL before sending
      const formattedUrl = ensureHttpPrefix(url.trim());
      console.log('Submitting URL:', formattedUrl); // Debug log

      const response = await detectURLWithExplanation(formattedUrl);
      console.log('Received response:', response); // Debug log
      setAnalysis(response);
    } catch (err) {
      console.error('Error details:', err.response?.data); // Debug log
      setError(err.response?.data?.detail || 'An error occurred while analyzing the URL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <StyledPaper elevation={3}>
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            fullWidth
            label="Enter URL to scan"
            placeholder="example.com"
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
            disabled={loading || !url.trim()}
            sx={{ mt: 2, width: '100%' }}
          >
            {loading ? <CircularProgress size={24} /> : 'Scan URL'}
          </Button>

          {error && (
            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', color: 'error.main' }}>
              <ErrorIcon sx={{ mr: 1 }} />
              <Typography>{error}</Typography>
            </Box>
          )}
        </Box>
      </StyledPaper>

      <URLAnalysisResult analysis={analysis} isLoading={loading} />
    </Box>
  );
}

export default URLDetectorForm;