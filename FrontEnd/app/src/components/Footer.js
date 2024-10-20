import React from 'react';
import { Box, Container, Grid, Link, Typography } from '@mui/material';
import { styled } from '@mui/system';

const StyledFooter = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  padding: theme.spacing(6, 0),
  borderTop: `1px solid ${theme.palette.primary.main}`,
}));

function Footer() {
  return (
    <StyledFooter component="footer">
      <Container maxWidth="lg">
        <Grid container spacing={4} justifyContent="space-evenly">
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="primary" gutterBottom>
              About Us
            </Typography>
            <Typography variant="body2">
              We are dedicated to providing top-notch cybersecurity solutions to keep you safe online.
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="primary" gutterBottom>
              Contact Us
            </Typography>
            <Typography variant="body2">
              Email: kshitijtaple@gmail.com
              <br />
              Phone: +44 791 858 5743
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="primary" gutterBottom>
              Quick Links
            </Typography>
            <Link href="#" color="secondary" display="block">Privacy Policy</Link>
            <Link href="#" color="secondary" display="block">Terms of Service</Link>
            <Link href="#" color="secondary" display="block">FAQ</Link>
          </Grid>
        </Grid>
        <Box mt={5}>
          <Typography variant="body2" color="text.secondary" align="center">
            © {new Date().getFullYear()} CyberGuard URL Detector. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </StyledFooter>
  );
}

export default Footer;