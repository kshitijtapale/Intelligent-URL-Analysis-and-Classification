import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Replace with your actual API URL

export const detectURL = async (url) => {
  try {
    const response = await axios.post(`${API_URL}/api/predict_url`, { url });
    return response.data;
  } catch (error) {
    throw error;
  }
};