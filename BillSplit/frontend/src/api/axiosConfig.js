import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000/api', // Default to Flask local
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt_token'); // Or a cookie
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle expired tokens, etc.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid. Clear token and redirect to login.
      localStorage.removeItem('jwt_token');
      // A more robust solution would be to use a callback from AuthContext
      // For now, a direct redirect.
      window.location.href = '/login'; 
    }
    return Promise.reject(error);
  }
);

export default api;