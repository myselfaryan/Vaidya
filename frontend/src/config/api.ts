/**
 * API configuration for the Vaidya medical chatbot frontend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/api/v1/auth/login`,
  LOGOUT: `${API_BASE_URL}/api/v1/auth/logout`,
  REFRESH: `${API_BASE_URL}/api/v1/auth/refresh`,
  
  // User management
  REGISTER: `${API_BASE_URL}/api/v1/users/register`,
  USER_PROFILE: `${API_BASE_URL}/api/v1/users/me`,
  USER_STATS: `${API_BASE_URL}/api/v1/users/me/stats`,
  
  // Chat and medical queries
  MEDICAL_QUERY: `${API_BASE_URL}/api/v1/chat/query`,
  CONVERSATIONS: `${API_BASE_URL}/api/v1/chat/conversations`,
  SYMPTOM_ANALYSIS: `${API_BASE_URL}/api/v1/chat/symptoms/analyze`,
  EMERGENCY_INFO: `${API_BASE_URL}/api/v1/chat/emergency`,
  
  // WebSocket
  WEBSOCKET: `ws://localhost:8000/api/v1/ws/chat`,
  
  // Health
  HEALTH: `${API_BASE_URL}/health`,
  
  // Documents
  DOCUMENTS: `${API_BASE_URL}/api/v1/documents`,
  DOCUMENT_SEARCH: `${API_BASE_URL}/api/v1/documents/search`,
};

export const APP_CONFIG = {
  APP_NAME: 'Vaidya Medical Assistant',
  VERSION: '1.0.0',
  
  // Request timeouts
  REQUEST_TIMEOUT: 30000, // 30 seconds
  
  // UI settings
  MAX_MESSAGE_LENGTH: 5000,
  TYPING_INDICATOR_DELAY: 1000,
  
  // Local storage keys
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'vaidya_access_token',
    REFRESH_TOKEN: 'vaidya_refresh_token',
    USER_DATA: 'vaidya_user_data',
    CHAT_HISTORY: 'vaidya_chat_history',
  },
  
  // Medical disclaimer
  MEDICAL_DISCLAIMER: 'This information is for educational purposes only and should not replace professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for medical concerns.',
  
  // Emergency contacts
  EMERGENCY_CONTACTS: {
    us: '911',
    uk: '999',
    eu: '112',
    poison_control_us: '1-800-222-1222',
    suicide_prevention: '988',
  },
};

export default API_ENDPOINTS;
