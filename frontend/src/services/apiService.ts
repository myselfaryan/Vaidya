/**
 * API service for handling HTTP requests to the Vaidya backend
 */

import { API_ENDPOINTS, APP_CONFIG } from '../config/api';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
}

class ApiService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = API_ENDPOINTS.LOGIN.replace('/api/v1/auth/login', '');
    this.timeout = APP_CONFIG.REQUEST_TIMEOUT;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.timeout
    } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders(),
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try to refresh
          await this.refreshToken();
          // Retry the request
          return this.request(endpoint, options);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  // Authentication
  async login(credentials: { username: string; password: string }) {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(API_ENDPOINTS.LOGIN, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    
    // Store tokens
    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
    localStorage.setItem(APP_CONFIG.STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
    
    return data;
  }

  async logout() {
    try {
      await this.request(API_ENDPOINTS.LOGOUT, { method: 'POST' });
    } finally {
      // Clear local storage regardless of API response
      localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER_DATA);
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
