import React from 'react';
import { Container, Typography } from '@material-ui/core';
import URLDetectorForm from '../components/URLDetectorForm';

function Home() {
  return (
    <Container maxWidth="md" style={{ marginTop: '2rem' }}>
      <Typography variant="h4" gutterBottom>
        Detect Malicious URLs
      </Typography>
      <Typography variant="body1" paragraph>
        Enter a URL below to check if it's potentially malicious.
      </Typography>
      <URLDetectorForm />
    </Container>
  );
}

export default Home;