/**
 * API service for handling HTTP requests to the Vaidya backend
 */

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { API_BASE_URL, API_TIMEOUT } from '../config/api';

// Define response types
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
}

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with a status code outside 2xx
      const apiError: ApiError = {
        message: (error.response.data as any)?.message || 'An error occurred',
        status: error.response.status,
        details: error.response.data,
      };
      return Promise.reject(apiError);
    } else if (error.request) {
      // Request was made but no response received
      return Promise.reject({
        message: 'No response from server. Please check your connection.',
      });
    } else {
      // Something happened in setting up the request
      return Promise.reject({
        message: error.message || 'An error occurred',
      });
    }
  }
);

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
}

class ApiService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = API_BASE_URL;
    this.timeout = API_TIMEOUT;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
    } = options;

    try {
      const response = await api({
        method,
        url: endpoint,
        headers: {
          ...this.getAuthHeaders(),
          ...headers,
        },
        data: body,
      });

      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Auth
  async login(credentials: { username: string; password: string }): Promise<ApiResponse> {
    try {
      const response = await api.post('/auth/login', credentials);
      return response;
    } catch (error) {
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      await this.request(API_BASE_URL + '/auth/logout', { method: 'POST' });
    } finally {
      // Clear local storage regardless of API response
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
    }
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(API_ENDPOINTS.REFRESH, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // Refresh failed, clear tokens
      localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    
    // Update tokens
    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
    
    return data;
  }

  // User management
  async register(userData: {
    username: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    phone_number?: string;
    data_sharing_consent?: boolean;
    marketing_consent?: boolean;
  }) {
    return this.request(API_ENDPOINTS.REGISTER, {
      method: 'POST',
      body: userData,
    });
  }

  async getUserProfile() {
    return this.request(API_ENDPOINTS.USER_PROFILE);
  }

  async updateUserProfile(userData: {
    first_name?: string;
    last_name?: string;
    phone_number?: string;
    data_sharing_consent?: boolean;
    marketing_consent?: boolean;
  }) {
    return this.request(API_ENDPOINTS.USER_PROFILE, {
      method: 'PUT',
      body: userData,
    });
  }

  async getUserStats() {
    return this.request(API_ENDPOINTS.USER_STATS);
  }

  // Medical queries
  async sendMedicalQuery(query: {
    question: string;
    context?: any;
    conversation_id?: string;
  }) {
    return this.request(API_ENDPOINTS.MEDICAL_QUERY, {
      method: 'POST',
      body: query,
    });
  }

  async analyzeSymptoms(symptoms: string[]) {
    return this.request(API_ENDPOINTS.SYMPTOM_ANALYSIS, {
      method: 'POST',
      body: symptoms,
    });
  }

  async getEmergencyInfo() {
    return this.request(API_ENDPOINTS.EMERGENCY_INFO);
  }

  // Conversations
  async createConversation(data: {
    title?: string;
    primary_concern?: string;
    symptoms?: string[];
  }) {
    return this.request(API_ENDPOINTS.CONVERSATIONS, {
      method: 'POST',
      body: data,
    });
  }

  async getConversations(skip: number = 0, limit: number = 20) {
    return this.request(`${API_ENDPOINTS.CONVERSATIONS}?skip=${skip}&limit=${limit}`);
  }

  async getConversation(conversationId: string) {
    return this.request(`${API_ENDPOINTS.CONVERSATIONS}/${conversationId}`);
  }

  async getConversationMessages(conversationId: string, skip: number = 0, limit: number = 50) {
    return this.request(`${API_ENDPOINTS.CONVERSATIONS}/${conversationId}/messages?skip=${skip}&limit=${limit}`);
  }

  async deleteConversation(conversationId: string) {
    return this.request(`${API_ENDPOINTS.CONVERSATIONS}/${conversationId}`, {
      method: 'DELETE',
    });
  }

  // Feedback
  async submitMessageFeedback(messageId: string, feedback: {
    rating: number;
    feedback?: string;
  }) {
    return this.request(`${API_ENDPOINTS.CONVERSATIONS}/messages/${messageId}/feedback`, {
      method: 'POST',
      body: feedback,
    });
  }

  // Documents
  async searchDocuments(query: string, documentTypes?: string[], limit: number = 10) {
    return this.request(API_ENDPOINTS.DOCUMENT_SEARCH, {
      method: 'POST',
      body: {
        query,
        document_types: documentTypes,
        limit,
      },
    });
  }

  async getDocuments(page: number = 1, size: number = 20, documentType?: string) {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    
    if (documentType) {
      params.append('document_type', documentType);
    }

    return this.request(`${API_ENDPOINTS.DOCUMENTS}?${params}`);
  }

  // Health check
  async healthCheck() {
    return this.request(API_ENDPOINTS.HEALTH);
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!localStorage.getItem(APP_CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
  }

  clearAuthData() {
    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER_DATA);
  }
}

export const apiService = new ApiService();
export default apiService;
