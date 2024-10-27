import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const detectURLWithExplanation = async (url) => {
  console.log('Sending URL to backend:', { url }); // Debug log

  const requestData = { url };
  console.log('Request payload:', requestData); // Debug log

  try {
    const response = await axios({
      method: 'post',
      url: `${API_URL}/api/predict_with_explanation`,
      data: requestData,
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    console.log('Response from backend:', response.data); // Debug log
    return response.data;
  } catch (error) {
    // Log the full error details
    if (error.response) {
      console.error('Response Error Data:', error.response.data);
      console.error('Response Error Status:', error.response.status);
      console.error('Response Error Headers:', error.response.headers);
    }
    throw error;
  }
};

