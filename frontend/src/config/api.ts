// API configuration for both local and Hugging Face deployment
export const getApiBaseUrl = () => {
  // Check if running on Hugging Face Spaces
  if (window.location.hostname.includes('hf.space') ||
      window.location.hostname.includes('huggingface.co')) {
    // Use relative URL for Hugging Face Spaces
    return '/api';
  }

  // Local development
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

export const API_BASE = getApiBaseUrl();