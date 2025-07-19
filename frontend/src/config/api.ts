/**
 * API configuration for the Vaidya medical chatbot frontend
 */

// API Configuration
type Environment = 'development' | 'production';

// Fallback for process.env in case @types/node is not installed
declare const process: {
  env: {
    NODE_ENV?: 'development' | 'production';
    REACT_APP_API_URL?: string;
  };
};

const ENV: Environment = process.env.NODE_ENV === 'production' ? 'production' : 'development';

const API_CONFIG = {
  development: {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
    timeout: 30000, // 30 seconds
  },
  production: {
    baseUrl: process.env.REACT_APP_API_URL || 'https://api.vaidya.com/api/v1',
    timeout: 60000, // 1 minute
  },
} as const;

export const API_BASE_URL = API_CONFIG[ENV].baseUrl;
export const API_TIMEOUT = API_CONFIG[ENV].timeout;

export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
    REFRESH: `${API_BASE_URL}/auth/refresh`,
    REGISTER: `${API_BASE_URL}/auth/register`,
  },
  
  // User
  USER: {
    PROFILE: `${API_BASE_URL}/user/profile`,
    PREFERENCES: `${API_BASE_URL}/user/preferences`,
  },
  
  // Chat
  CHAT: {
    QUERY: `${API_BASE_URL}/chat/query`,
    CONVERSATIONS: `${API_BASE_URL}/chat/conversations`,
    MESSAGES: (conversationId: string) => `${API_BASE_URL}/chat/conversations/${conversationId}/messages`,
  },
  
  // Documents
  DOCUMENTS: {
    UPLOAD: `${API_BASE_URL}/documents/upload`,
    LIST: `${API_BASE_URL}/documents`,
    GET: (documentId: string) => `${API_BASE_URL}/documents/${documentId}`,
    DELETE: (documentId: string) => `${API_BASE_URL}/documents/${documentId}`,
    SEARCH: `${API_BASE_URL}/documents/search`,
  },
  
  // Medical
  MEDICAL: {
    SYMPTOMS: `${API_BASE_URL}/medical/symptoms`,
    CONDITIONS: `${API_BASE_URL}/medical/conditions`,
    EMERGENCY: `${API_BASE_URL}/medical/emergency`,
  },
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
