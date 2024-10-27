// URLFeedbackDialog.js
import React, { useState } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  Typography,
  Box,
  Alert,
  IconButton,
} from '@mui/material';
import { ThumbsUp, ThumbsDown, X } from 'lucide-react';
import axios from 'axios';

const URLFeedbackDialog = ({ open, onClose, url }) => {
  const [selectedType, setSelectedType] = useState(null);
  const [confidence, setConfidence] = useState(50);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    if (!selectedType) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        url: url,
        is_malicious: selectedType === 'malicious',
        confidence: confidence / 100 // Convert percentage to decimal
      };

      await axios.post('http://localhost:8000/api/feedback', payload);
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setSelectedType(null);
        setConfidence(50);
      }, 2000);
    } catch (err) {
      setError('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      PaperProps={{
        sx: {
          background: 'linear-gradient(45deg, #1a1a1a 30%, #2a2a2a 90%)',
          border: '1px solid #00ff00',
          minWidth: '300px'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        borderBottom: '1px solid #00ff00'
      }}>
        Provide URL Feedback
        <IconButton onClick={onClose} size="small">
          <X size={20} />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ mt: 2 }}>
        {success ? (
          <Alert severity="success" sx={{ mb: 2 }}>
            Feedback submitted successfully!
          </Alert>
        ) : (
          <>
            <Typography gutterBottom>
              Is this URL safe or malicious?
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 3, mt: 2 }}>
              <Button
                variant={selectedType === 'safe' ? 'contained' : 'outlined'}
                color="primary"
                onClick={() => setSelectedType('safe')}
                startIcon={<ThumbsUp />}
                fullWidth
              >
                Safe
              </Button>
              <Button
                variant={selectedType === 'malicious' ? 'contained' : 'outlined'}
                color="error"
                onClick={() => setSelectedType('malicious')}
                startIcon={<ThumbsDown />}
                fullWidth
              >
                Malicious
              </Button>
            </Box>

            <Typography gutterBottom>
              How confident are you? ({confidence}%)
            </Typography>
            <Slider
              value={confidence}
              onChange={(_, value) => setConfidence(value)}
              aria-labelledby="confidence-slider"
              valueLabelDisplay="auto"
              step={1}
              marks
              min={0}
              max={100}
              sx={{
                '& .MuiSlider-thumb': {
                  backgroundColor: '#00ff00',
                },
                '& .MuiSlider-track': {
                  backgroundColor: '#00ff00',
                },
                '& .MuiSlider-rail': {
                  backgroundColor: '#005500',
                }
              }}
            />

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </>
        )}
      </DialogContent>

      {!success && (
        <DialogActions sx={{ borderTop: '1px solid #00ff00', p: 2 }}>
          <Button onClick={onClose} color="primary" disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="primary"
            disabled={!selectedType || isSubmitting}
            sx={{
              backgroundColor: '#00ff00',
              '&:hover': {
                backgroundColor: '#00cc00',
              }
            }}
          >
            Submit Feedback
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
};

export default URLFeedbackDialog;