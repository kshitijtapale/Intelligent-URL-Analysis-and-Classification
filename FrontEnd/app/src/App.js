import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Container, Box, Typography, Grid } from '@mui/material';
import { styled } from '@mui/system';
import Header from './components/Header';
import Footer from './components/Footer';
import URLDetectorForm from './components/URLDetectorForm';
import ShieldIcon from '@mui/icons-material/Shield';

const GlowingText = styled(Typography)(({ theme }) => ({
  color: theme.palette.primary.main,
  textShadow: '0 0 10px #00ff00, 0 0 20px #00ff00, 0 0 30px #00ff00',
  marginBottom: theme.spacing(3),
}));

const IconWrapper = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  marginBottom: theme.spacing(3),
  '& svg': {
    fontSize: '5rem',
    color: theme.palette.primary.main,
  },
}));

function Home() {
  return (
    <Box sx={{ my: 4 }}>
      <IconWrapper>
        <ShieldIcon />
      </IconWrapper>
      <GlowingText variant="h4" align="center">
        Secure Your Browsing
      </GlowingText>
      <Grid container spacing={3} justifyContent="center">
        <Grid item xs={12} md={8}>
          <URLDetectorForm />
        </Grid>
      </Grid>
    </Box>
  );
}

function App() {
  return (
    <Router>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Header />
        <Container component="main" sx={{ mt: 8, mb: 2 }} maxWidth="lg">
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </Container>
        <Footer />
      </Box>
    </Router>
  );
}

export default App;