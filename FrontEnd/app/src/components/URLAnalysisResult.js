import React from 'react';
import { Box, Typography, Paper, Chip, Grid, LinearProgress } from '@mui/material';
import { AlertTriangle, Shield, MapPin, Server, Globe, Check, AlertCircle } from 'lucide-react';

const URLAnalysisResult = ({ analysis, isLoading }) => {
  if (isLoading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress color="primary" />
      </Box>
    );
  }

  if (!analysis) return null;

  console.log("Analysis result:", analysis); // Debug log

  // Check prediction result directly
  const isMalicious = analysis?.prediction?.result === "BEWARE_MALICIOUS_WEBSITE";
  console.log("Is Malicious:", isMalicious); // Debug log
  
  // Theme colors based on result
  const themeColor = isMalicious ? '#ff0000' : '#00ff00';
  const statusColor = isMalicious ? 'error' : 'primary';
  const gradientBg = isMalicious 
    ? 'linear-gradient(45deg, #2a0000 30%, #3a0000 90%)'
    : 'linear-gradient(45deg, #1a1a1a 30%, #2a2a2a 90%)';

  return (
    <Box sx={{ mt: 4, width: '100%' }}>
      {/* Prediction Status */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          background: gradientBg,
          border: `1px solid ${themeColor}`,
          boxShadow: `0 3px 5px 2px ${isMalicious ? 'rgba(255, 0, 0, .3)' : 'rgba(0, 255, 0, .3)'}`
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            {isMalicious ? (
              <AlertTriangle size={32} color="#ff0000" />
            ) : (
              <Shield size={32} color="#00ff00" />
            )}
          </Grid>
          <Grid item xs>
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ color: themeColor }}
            >
              {analysis.prediction.result}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Confidence: {(analysis.prediction.confidence * 100).toFixed(2)}%
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Trust Analysis */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ 
            p: 2, 
            background: gradientBg,
            height: '100%',
            border: `1px solid ${themeColor}`
          }}>
            <Typography variant="h6" color={statusColor} gutterBottom>
              Trust Indicators
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {analysis.analysis.trust_analysis.trust_indicators.length > 0 ? (
                analysis.analysis.trust_analysis.trust_indicators.map((indicator, index) => (
                  <Chip
                    key={index}
                    label={indicator}
                    color={statusColor}
                    variant="outlined"
                    icon={<Check size={16} />}
                    sx={{ m: 0.5 }}
                  />
                ))
              ) : (
                <Typography variant="body2" color="error">
                  No trust indicators found
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ 
            p: 2, 
            background: gradientBg,
            height: '100%',
            border: isMalicious ? '1px solid #ff0000' : '1px solid transparent'
          }}>
            <Typography variant="h6" color="error" gutterBottom>
              Concerns
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {analysis.analysis.trust_analysis.concerns.length > 0 ? (
                analysis.analysis.trust_analysis.concerns.map((concern, index) => (
                  <Chip
                    key={index}
                    label={concern}
                    color="error"
                    variant="outlined"
                    icon={<AlertTriangle size={16} />}
                    sx={{ 
                      m: 0.5,
                      borderColor: '#ff0000',
                      '& .MuiChip-icon': { color: '#ff0000' }
                    }}
                  />
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No concerns detected
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Recommendation */}
      <Paper 
        sx={{ 
          p: 2, 
          mb: 3, 
          background: gradientBg,
          border: `1px solid ${themeColor}`
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          {isMalicious ? (
            <AlertCircle size={24} color="#ff0000" />
          ) : (
            <Check size={24} color="#00ff00" />
          )}
          <Typography variant="h6" color={statusColor}>
            Recommendation
          </Typography>
        </Box>
        <Typography color={isMalicious ? 'error' : 'inherit'}>
          {analysis.analysis.trust_analysis.recommendation}
        </Typography>
      </Paper>

      {/* Technical Details */}
      <Grid container spacing={3}>
        {/* Location Info */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ 
            p: 2, 
            background: gradientBg,
            border: `1px solid ${themeColor}`
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <MapPin size={24} color={themeColor} />
              <Typography variant="h6" sx={{ ml: 1 }} color={statusColor}>
                Location
              </Typography>
            </Box>
            <Typography variant="body1">
              {analysis.analysis.website_details.hosting_location.display}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Region: {analysis.analysis.website_details.hosting_location.region}
            </Typography>
          </Paper>
        </Grid>

        {/* Organization Info */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ 
            p: 2, 
            background: gradientBg,
            border: `1px solid ${themeColor}`
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Server size={24} color={themeColor} />
              <Typography variant="h6" sx={{ ml: 1 }} color={statusColor}>
                Organization
              </Typography>
            </Box>
            <Typography variant="body1">
              {analysis.analysis.website_details.organization.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              ISP: {analysis.analysis.website_details.organization.isp}
            </Typography>
          </Paper>
        </Grid>

        {/* Security Info */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ 
            p: 2, 
            background: gradientBg,
            border: `1px solid ${themeColor}`
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Globe size={24} color={themeColor} />
              <Typography variant="h6" sx={{ ml: 1 }} color={statusColor}>
                Security
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip
                label={`Email Security: ${analysis.analysis.website_details.security_features.email_security}`}
                color={analysis.analysis.website_details.security_features.email_security === "Present" ? statusColor : "default"}
                variant="outlined"
                sx={{ borderColor: isMalicious ? '#ff0000' : undefined }}
              />
              <Chip
                label={`Professional Setup: ${analysis.analysis.website_details.security_features.professional_setup ? "Yes" : "No"}`}
                color={analysis.analysis.website_details.security_features.professional_setup ? statusColor : "default"}
                variant="outlined"
                sx={{ borderColor: isMalicious ? '#ff0000' : undefined }}
              />
              <Chip
                label={`Direct Connection: ${analysis.analysis.website_details.security_features.direct_connection ? "Yes" : "No"}`}
                color={analysis.analysis.website_details.security_features.direct_connection ? statusColor : "default"}
                variant="outlined"
                sx={{ borderColor: isMalicious ? '#ff0000' : undefined }}
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default URLAnalysisResult;